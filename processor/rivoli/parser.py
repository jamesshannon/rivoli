""" Parsing classes """
import collections
import typing as t

import pymongo

from rivoli import admin_entities

from rivoli.protobson import bson_format
from rivoli import protos

from rivoli import db
from rivoli import record_processor
from rivoli.utils import tasks
from rivoli import parser
from rivoli.utils import processing


@tasks.app.task
def parse(file_id: int) -> None:
  """ Parse a file that's already been loaded into the db. """
  mydb = db.get_db()

  file = bson_format.to_proto(protos.File,
      mydb.files.find_one({'_id': file_id}))

  # get the filetype config
  partner = admin_entities.get_partner(file.partnerId)
  filetype = admin_entities.get_filetype(file.fileTypeId)

  parser = DelimitedParser(file, partner, filetype)
  parser.parse()


class Parser(record_processor.DbRecordProcessor):
  """ Generic Parser """

class FlatFileParser(Parser):
 pass



class DelimitedParser(Parser):
  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self.fieldnames: dict[int, list[t.Optional[str]]] = {}
    self.shared_keys: dict[int, list[str]] = {}

  def parse(self):
    """ Parse the "raw data" in the records and save the struct. """
    # If File.header_columns has been set then we have a header row
    if self.file.headerColumns:
      assert len(self.filetype.recordTypes) == 1, \
          'More than one filetype found despite having a header row'

    for recordtype in self.filetype.recordTypes:
      # Set the fieldnames
      if self.file.headerColumns:
        # If row has a header then we use the columns we got from the loading
        # step plus the mapping from the FieldTypes. Not all columns will have
        # a mapped fieldname, in which case the list value will be None,
        fieldname_mapping = {field.headerColumn: field.name
                             for field in recordtype.fieldTypes if field.active}

        self.fieldnames[recordtype.id] = [fieldname_mapping.get(col)
                                          for col in self.file.headerColumns]
      else:
        # Otherwise we have to create a list of fieldnames, but with Nones
        # for columns that don't get imported.
        assert recordtype.fieldTypes, \
            f'Some fields are required for {recordtype.name}'

        fields: dict[int, str] = {field.columnIndex: field.name for field
                                  in recordtype.fieldTypes if field.active}
        self.fieldnames[recordtype.id] = [None] * max(fields.keys())
        for idx, fieldname in fields.items():
          self.fieldnames[recordtype.id][idx] = fieldname

      # Add any shared_key(s)
      self.shared_keys[recordtype.id] = [field.name for field
                                         in recordtype.fieldTypes
                                         if field.isSharedKey and field.active]

    self._update_status_to_processing(protos.File.PARSING)
    self._clear_stats('PARSE')
    self.file.times.parsingStartTime = bson_format.now()

    self._process_records(self._get_all_records())

    # Final update to the File record
    self.file.status = protos.File.PARSED
    self.file.log.append(processing.new_log_entry(
        'DelimitedParser.parse', 'Parsed records'))
    self._update_file(['status', 'log', 'stats'])

  def _process_one_record(self, record: protos.Record
      ) -> t.Optional[pymongo.UpdateOne]:
    if record.recordType == record.HEADER:
      # Ignore this for stats
      print('skipping header')
      return None

    # Check the status.
    if record.status < protos.Record.LOADED:
      # Don't generate stats off this invariant
      print('skipping record that wasnt loaded', record.status)
      return None

    stepstats = self.file.stats.steps[f'PARSE.{record.recordType}']
    stepstats.input += 1

    # Ensure that the loaded record ID is in our list of record ids
    if record.recordType not in self.fieldnames:
      # This is an invariant
      stepstats.failure += 1
      return None

    fieldnames = self.fieldnames[record.recordType]
    shared_keys = self.shared_keys[record.recordType]

    row = record.rawColumns

    # The fieldname list will likely have None values, which generates a dict
    # with None keys (sometimes overwritten), which is removed later.

    if len(row) < len(fieldnames):
      record.status = protos.Record.PARSE_ERROR
      # TODO: Add a log entry
      stepstats.failure += 1
      return self._make_update(record, ['status'])

    # zip() stops with the shortest iterable, which is OK when fieldnames is
    # shortest (we lose loaded fields that didn't have FieldTypes), but might
    # be confusing if the row has less values than the fieldnames
    parsed = dict(zip(fieldnames, row))
    # The zipping produces dict items keyed with None -- remove those
    parsed.pop(None, None)

    # We don't (currently) support extra fields or default values

    record.parsedFields.update(parsed)
    stepstats.success += 1
    record.status = protos.Record.PARSED

    if shared_keys:
      record.sharedKey = '++'.join(parsed[key] for key in shared_keys)

    self.file.stats.parsedRecordsSuccess += 1
    return self._make_update(record, ['parsedFields', 'status', 'sharedKey'])
