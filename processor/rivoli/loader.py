""" Load file into multiple records. """
import base64
import csv
import hashlib
import itertools
import pathlib
import re
import typing as t

from bson import objectid

from rivoli import protos
from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli.utils import tasks
from rivoli import record_processor
from rivoli import db
from rivoli.utils import processing


# HOW TO GET CHANGES BACK AS DATA CHUNKS FOR DB ISOLATION & TESTING
@tasks.app.task
def load_from_id(file_id: int):
  """ Loader entrypoint for celery.
  Loads file based on just a file_id, and relies on using a "live" FileType from
  the database.
  """
  mydb = db.get_db()
  file = bson_format.to_proto(protos.File,
      mydb.files.find_one({'_id': file_id}))

  # get the filetype config
  partner = admin_entities.get_partner(file.partnerId)
  filetype = admin_entities.get_filetype(file.fileTypeId)

  loader = DelimitedLoader(file, partner, filetype)
  loader.prep_record()
  loader.load()

  #parser.parse.delay(file_id)

def load_from_file():
  # Takes FileType, which might be different than the live version.
  # Do we need a filerecord id or a live one? Probably a file, so that the caller
  # can confirm that this is a development file?
  pass


class Loader(record_processor.RecordProcessor):
  """ hello """
  def prep_record(self):
    name = pathlib.Path(self.file.name)
    new_name = f'{name.stem}-{self.file.id}{name.suffix}'
    self.local_file = pathlib.Path(self.file.location) / new_name

    self.fileobj = open(self.local_file, 'r', newline='')

    # check size and md5

    self._update_status_to_processing(protos.File.LOADING)
    # Delete any existing records
    self.db.records.delete_many(self._all_records_filter())
    self._clear_stats('LOAD')
    self.file.times.loadingStartTime = bson_format.now()



class DelimitedLoader(Loader):
  """ hello """
  def _create_new_record(self, line_num: int, line: list[str],
      record_type: t.Union[int, 'protos.Record.RecordTypeRef', None],
      status: protos.Record.Status = protos.Record.LOADED,
      log_msg: t.Optional[str] = None) -> dict[str, t.Any]:

    record = protos.Record(
        id=self.record_prefix + line_num,
        rawColumns=line,
        hash=hashlib.md5(','.join(line).encode()).digest(),
        recordType=record_type,
        status=status,
    )
    # Create a new record so that the timestamp is fresh
    if log_msg:
      record.log.append(processing.new_log_entry('DelimitedLoader.load',
                                                 log_msg))
    return bson_format.from_proto(record)

  def load(self):
    # get 8k of sample text from the file and use that to try to detect the
    # dialect and existence of a header
    sample = self.fileobj.read(8192)
    self.fileobj.seek(0)

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(sample)
    has_header = sniffer.has_header(sample)

    # should confirm dialect and has_header matches anything that's been set on
    # the file record

    # Create a CSV reader iterator
    reader = csv.reader(self.fileobj, dialect)
    line_num: int = 1
    self.file.stats.loadedRecordsSuccess = 0
    self.file.stats.loadedRecordsError = 0

    separator = ','

    if has_header:
      line = next(reader)

      self.db.records.insert_one(
          self._create_new_record(line_num, line,
                                  record_type=protos.Record.HEADER))

      # Clear out any previous header column value from the file object
      del self.file.headerColumns[:]
      self.file.headerColumns.extend(line)
      self.db.files.update_one(
          *bson_format.get_update_args(self.file, ['headerColumns', 'stats']))

      line_num += 1

    while lines := list(itertools.islice(reader, 1000)):
      records: list[dict[str, t.Any]] = []

      for line in lines:
        recordtype_id = None

        if len(self.filetype.recordTypes) == 1:
          recordtype_id = self.filetype.recordTypes[0].id
        else:
          recordtype_id = self._get_regexp_matching_record(separator.join(line),
              self.filetype.recordTypes, 'recordMatches')

        if recordtype_id:
          records.append(self._create_new_record(
            line_num, line, recordtype_id))
          self.file.stats.loadedRecordsSuccess += 1
        else:
          records.append(self._create_new_record(
            line_num, line, None, protos.Record.LOAD_ERROR,
            'No record type match found'))
          self.file.stats.loadedRecordsError += 1

        line_num += 1

      self.db.records.insert_many(records, ordered=False)
      self.db.files.update_one(
          *bson_format.get_update_args(self.file, ['stats']))

    # Final stats update, now that we finished the loading
    self.file.status = protos.File.LOADED
    self.file.stats.approximateRows = 0
    self.file.stats.totalRows = line_num - 1

    self.file.times.loadingEndTime = bson_format.now()

    stepstats = self.file.stats.steps['LOAD']
    stepstats.input = line_num - 1
    stepstats.success = self.file.stats.loadedRecordsSuccess
    stepstats.failure = self.file.stats.loadedRecordsError

    self.file.log.append(processing.new_log_entry(
        'DelimitedLoader.load', 'Loaded records'))
    self.db.files.update_one(*bson_format.get_update_args(
        self.file, ['status', 'stats', 'times', 'log']))
