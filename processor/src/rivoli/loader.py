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

LineGenerator = t.Generator[t.Tuple[str, t.Optional[list[str]]], None, None]

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


class Loader(record_processor.RecordProcessor):
  """ Iterate through a local file and create Records. """
  log_source = protos.ProcessingLog.LOADER

  _success_status = protos.File.LOADED
  _error_status = protos.File.LOAD_ERROR

  _step_stat_prefix = 'LOAD'

  local_file: pathlib.Path
  fileobj: t.Optional[io.TextIOWrapper] = None

  _line_num: int = 1

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

  def _create_db_records(self, lines: LineGenerator):
    """ Create records from lines and into the database.
    Iterate through a chunk of lines, create new records, and insert those into
    the database.
    This accepts a generator so that the generator can do any formatting
    without pre-processing the entire file.
    """
    while line_chunk := list(itertools.islice(lines,
                                              self._max_pending_updates)):
      records: list[dict[str, t.Any]] = []

      for line in line_chunk:
        recordtype: t.Optional[protos.RecordType] = None

        line_raw = line[0]
        line_fields = line[1]

        if len(self.filetype.recordTypes) == 1:
          recordtype = self.filetype.recordTypes[0]
        else:
          # Find the matching RecordType based on each RecordType's patterns
          # Re-create the line's values as a single string
          recordtype = self._get_regexp_matching_record(
              line_raw, self.filetype.recordTypes,
              'recordMatches')

        if recordtype:
          records.append(self._create_new_record(
            self._line_num, line_raw, line_fields, recordtype.id))
          self._get_step_stat(recordtype.id).input += 1
          self._get_step_stat(recordtype.id).success += 1
          self.file.stats.loadedRecordsSuccess += 1
        else:
          # No RecordType found. Create an error record.
          records.append(self._create_new_record(
            self._line_num, line_raw, line_fields, None,
            protos.Record.LOAD_ERROR, 'No record type match found'))
          self.file.stats.loadedRecordsError += 1

        self._line_num += 1

      self.db.records.insert_many(records, ordered=False)
      self._update_file(['stats'])

  def _create_new_record(self, line_num: int, line: str,
      columns: t.Optional[list[str]],
      record_type: t.Union[int, 'protos.Record.RecordTypeRef', None],
      status: protos.Record.Status = protos.Record.LOADED,
      log_msg: t.Optional[str] = None) -> dict[str, t.Any]:
    """ Create an individual Record to be uploaded. Return a dict. """

    # line (string) will always be passed but only save it if columns
    # is not passed.
    record = protos.Record(
        id=self.record_prefix + line_num,
        rawLine=None if columns else line,
        rawColumns=columns,
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

  def _close_processing(self) -> None:
    """ Close the file object and update the db File fields. """
    if self.fileobj:
      self.fileobj.close()

    # Final stats update, now that we finished the loading
    self.file.stats.totalRows = self._line_num - 1

    stepstats = self._get_step_stat()

    stepstats.input = self._line_num - 1
    stepstats.success = self.file.stats.loadedRecordsSuccess
    stepstats.failure = self.file.stats.loadedRecordsError

    self.file.log.append(self._make_log_entry(False, 'Loaded records'))

    self.file.times.loadingEndTime = bson_format.now()

    return super()._update_file(
      ['headerColumns', 'status', 'stats', 'times', 'log', 'recentErrors'])

class DelimitedLoader(Loader):
  """ Iterate through a local delimited file and create Records. """
  _has_header: bool
  _detected_delimiter: str

  def _process(self):
    """ Load CSV rows. """
    self._begin_processing()
    reader = self._open_and_validate_file()
    self._process_csv_file(reader)

    # Parent method is responsible for updating File status and updating db

  def _open_and_validate_file(self) -> t.Iterator[list[str]]:
    """ Open file from the filesystem and confirm file properties. """
    # Get 8k of sample text from the file and use that to try to detect the
    # dialect and existence of a header
    self.fileobj = open(self.local_file, 'rt', newline='', encoding='UTF-8')

    sample = self.fileobj.read(8192)
    self.fileobj.seek(0)

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(sample)

    self._has_header = sniffer.has_header(sample)
    self._detected_delimiter = dialect.delimiter

    # Regardless of the sniffed delimiter, set it to the configured delimiter
    dialect.delimiter = self.filetype.delimitedSeparator

    # Create a CSV reader iterator
    reader = csv.reader(self.fileobj, dialect)

    if self._has_header != self.filetype.hasHeader:
      # File configuration doesn't match what we see in the file. This is a
      # ConfigurationError and we should stop processing.
      def _fmt(header: bool) -> str:
        return 'a header' if header else 'no header'

      raise exceptions.ConfigurationError(
          (f'Unexpected file header: Expected {_fmt(self.filetype.hasHeader)} '
           f'but found {_fmt(self._has_header)}'))

    if self._detected_delimiter != self.filetype.delimitedSeparator:
      # We used to raise a ConfigurationError if the sniffed delimiter didn't
      # match the configured delimiter but this caused false positives.
      self.file.log.append(self._make_log_entry(False,
          ('Unexpected delimiter: Expected '
           f"'{self.filetype.delimitedSeparator}' "
           f"but detected '{self._detected_delimiter}'")))

    return reader

  def _delimited_rows(self, reader: t.Iterator[list[str]]) -> LineGenerator:
    """ Generate line data from a CSV reader.
    Since this is a CSV we return the line as both text and a list of cell
    values.
    """
    for row in reader:
      yield (self.filetype.delimitedSeparator.join(row), row)

  def _process_csv_file(self, reader: t.Iterator[list[str]]) -> None:
    """ Iterate through file rows and upload to database. """
    if self._has_header:
      # File has header so we treat this first row differently
      line = next(reader)

      self.db.records.insert_one(self._create_new_record(self._line_num, '',
          line, record_type=protos.Record.HEADER))

      self.file.headerColumns.extend(line)

      # Files with headers should only have one recordType... right?
      assert len(self.filetype.recordTypes) == 1

      # Files with headers should have the FieldTypes' headerColumn field set
      field_keys = {f.headerColumn for f
                    in self.filetype.recordTypes[0].fieldTypes
                    if f.active}
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

    self._create_db_records(self._delimited_rows(reader))

class FixedWidthLoader(Loader):
  """ Iterate through a fixed-width file and create Records. """

  def _raw_lines(self, fileobj: io.TextIOWrapper) -> LineGenerator:
    """ Generate line data from a CSV reader.
    Since this is a CSV we return the line as both text and a list of cell
    values.
    """
    for line in fileobj:
      # File lines end in the newline character
      line = line.strip()

      # The file might end with a double-newline. Though this will also stop
      # iteration if there are any empty lines within the file
      if not line:
        return

      yield (line, None)

  def _process(self):
    self._begin_processing()

    # Equivalent of _open_and_validate_file()
    self.fileobj = open(self.local_file, 'rt', encoding='UTF-8')

    # Equivalent of _process_csv_file()
    self._create_db_records(self._raw_lines(self.fileobj))
