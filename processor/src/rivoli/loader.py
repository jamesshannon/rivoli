""" Load file into multiple records. """
import csv
import hashlib
import itertools
import io
import pathlib
import typing as t

from rivoli import protos
from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli import record_processor
from rivoli import status_scheduler
from rivoli.function_helpers import exceptions
from rivoli.utils import tasks

# pylint: disable=too-few-public-methods

@tasks.app.task
def load_from_id(file_id: int):
  """ Loader entrypoint for celery.
  Loads file based on just a file_id, and relies on using the currently-live
  FileType from the database.
  """
  file, partner, filetype = admin_entities.get_file_entities(file_id)

  loader = DelimitedLoader(file, partner, filetype)
  loader.process()

  status_scheduler.next_step(file, filetype)

def load_from_file():
  # Takes FileType, which might be different than the live version.
  # Do we need a filerecord id or a live one? Probably a file, so that the caller
  # can confirm that this is a development file?
  pass


class Loader(record_processor.RecordProcessor):
  """ Iterate through a local file and create Records. """
  log_source = protos.ProcessingLog.LOADER

  _success_status = protos.File.LOADED
  _error_status = protos.File.LOAD_ERROR

  _step_stat_prefix = 'LOAD'

  local_file: pathlib.Path
  fileobj: t.Optional[io.TextIOWrapper] = None

  def _begin_processing(self):
    """ Setup the File and Records to begin loading. """
    name = pathlib.Path(self.file.name)
    new_name = f'{name.stem}-{self.file.id}{name.suffix}'
    self.local_file = pathlib.Path(self.file.location) / new_name

    # check size and md5?

    self._update_status_to_processing(protos.File.LOADING,
        protos.File.NEW)
    # Delete any existing records
    self.db.records.delete_many(self._all_records_filter())
    self._clear_stats('LOAD')

    # Clear out any previous header column value from the file object
    del self.file.headerColumns[:]

    self.file.times.loadingStartTime = bson_format.now()

  def _create_new_record(self, line_num: int, line: list[str],
      record_type: t.Union[int, 'protos.Record.RecordTypeRef', None],
      status: protos.Record.Status = protos.Record.LOADED,
      log_msg: t.Optional[str] = None) -> dict[str, t.Any]:
    """ Create an individual Record to be uploaded. Return a dict. """

    record = protos.Record(
        id=self.record_prefix + line_num,
        rawColumns=line,
        hash=hashlib.md5(','.join(line).encode()).digest(),
        recordType=record_type,
        status=status,
    )

    if log_msg:
      # If log_msg is passed then it's only due to an error
      log = self._make_log_entry(True, log_msg,
          protos.ProcessingLog.OTHER_OPERATION_ERROR)
      record.log.append(log)
      record.recentErrors.append(log)

    return bson_format.from_proto(record)

class DelimitedLoader(Loader):
  """ Iterate through a local delimited file and create Records. """
  _reader: t.Iterator[list[str]]
  _has_header: bool
  _delimiter: str

  _line_num: int = 1

  def _process(self):
    """ Load CSV rows. """
    self._begin_processing()
    self._open_and_validate_file()
    self._upload_records()

    # Parent method is responsible for updating File status and updating db

  def _open_and_validate_file(self) -> None:
    """ Open file from the filesystem and confirm file properties. """
    # Get 8k of sample text from the file and use that to try to detect the
    # dialect and existence of a header
    self.fileobj = open(self.local_file, 'rt', newline='', encoding='UTF-8')

    sample = self.fileobj.read(8192)
    self.fileobj.seek(0)

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(sample)

    self._has_header = sniffer.has_header(sample)
    self._delimiter = dialect.delimiter

    # should confirm dialect and has_header matches anything that's been set on
    # the file record

    # Create a CSV reader iterator
    self._reader = csv.reader(self.fileobj, dialect)

    if self._has_header != self.filetype.hasHeader:
      # File configuration doesn't match what we see in the file. This is a
      # ConfigurationError and we should stop processing.
      def _fmt(header: bool) -> str:
        return 'a header' if header else 'no header'

      raise exceptions.ConfigurationError(
          (f'Unexpected file header: Expected {_fmt(self.filetype.hasHeader)} '
           f'but found {_fmt(self._has_header)}'))

    if self._delimiter != self.filetype.delimitedSeparator:
      raise exceptions.ConfigurationError(
          (f'Unexpected delimiter: Expected {self.filetype.delimitedSeparator} '
           f'but found {self._delimiter}'))

  def _upload_records(self) -> None:
    """ Iterate through file rows and upload to database. """
    if self._has_header:
      # File has header so we treat this first row differently
      line = next(self._reader)

      self.db.records.insert_one(self._create_new_record(self._line_num, line,
          record_type=protos.Record.HEADER))

      self.file.headerColumns.extend(line)

      # Files with headers should only have one recordType... right?
      assert len(self.filetype.recordTypes) == 1

      # Files with headers should have the FieldTypes' headerColumn field set
      field_keys = {f.headerColumn for f
                    in self.filetype.recordTypes[0].fieldTypes}
      # Create a unique list of headers
      columns = set(line)

      if not field_keys.issubset(columns):
        # The file should have at least the fields configured in the record
        raise exceptions.ConfigurationError(
            ('Unexpected file header: Missing columns '
             f'{field_keys.difference(columns)}. Expected at least {field_keys} '
             f'but got {columns}'))

      self._update_file(['headerColumns', 'stats'])

      self._line_num += 1

    while lines := list(itertools.islice(self._reader, 1000)):
      records: list[dict[str, t.Any]] = []

      for line in lines:
        recordtype: t.Optional[protos.RecordType] = None

        if len(self.filetype.recordTypes) == 1:
          recordtype = self.filetype.recordTypes[0]
        else:
          # Find the matching RecordType based on each RecordType's patterns
          # Re-create the line's values as a single string
          recordtype = self._get_regexp_matching_record(
              self._delimiter.join(line), self.filetype.recordTypes,
              'recordMatches')

        if recordtype:
          records.append(self._create_new_record(
            self._line_num, line, recordtype.id))
          self._get_step_stat(recordtype.id).input += 1
          self._get_step_stat(recordtype.id).success += 1
          self.file.stats.loadedRecordsSuccess += 1
        else:
          # No RecordType found. Create an error record.
          records.append(self._create_new_record(
            self._line_num, line, None, protos.Record.LOAD_ERROR,
            'No record type match found'))
          self.file.stats.loadedRecordsError += 1

        self._line_num += 1

      self.db.records.insert_many(records, ordered=False)
      self._update_file(['stats'])

    # Final stats update, now that we finished the loading
    self.file.stats.totalRows = self._line_num - 1

    stepstats = self._get_step_stat()

    stepstats.input = self._line_num - 1
    stepstats.success = self.file.stats.loadedRecordsSuccess
    stepstats.failure = self.file.stats.loadedRecordsError

    self.file.log.append(self._make_log_entry(False, 'Loaded records'))

  def _close_processing(self) -> None:
    """ Close the file object and update the db File fields. """
    if self.fileobj:
      self.fileobj.close()

    self.file.times.loadingEndTime = bson_format.now()

    return super()._update_file(
      ['headerColumns', 'status', 'stats', 'times', 'log', 'recentErrors'])
