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
from rivoli import validator
from rivoli.function_helpers import helpers

# Disable pyright checks due to Celery
# pyright: reportFunctionMemberAccess=false
# pyright: reportUnknownMemberType=false

# pylint: disable=too-few-public-methods

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
  parser.process()

  validator.validate.delay(file_id)

class Parser(record_processor.DbChunkProcessor):
  """ Generic Parser """
  log_source = protos.ProcessingLog.PARSER

  _only_process_record_status = protos.Record.LOADED

  _success_status = protos.File.PARSED
  _error_status = protos.File.PARSE_ERROR

  _step_stat_prefix = 'PARSE'

class DelimitedParser(Parser):
  """ Delimited file parser """
  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self.fieldnames: dict[int, list[t.Optional[str]]] = {}
    """ Fieldnames by RecordType ID.
    Not all headers will have an associated field and fieldname, in which
    case the list needs to have None placeholder for each field.
    """
    self.shared_keys: dict[int, list[str]] = {}
    """ Shared Keys by RecordType ID.
    Shared keys are used to look up matching records in the aggregation step.
    """

  def _process(self):
    """ Parse the "raw data" in the records and save the struct. """
    # If File.headerColumns has been set then we have a header row
    if self.file.headerColumns and len(self.filetype.recordTypes) > 1:
      raise ValueError('Header row but more than one filetype')

    for recordtype in self.filetype.recordTypes:
      # Set the fieldnames
      if self.file.headerColumns:
        # If row has a header then we use the columns we got from the loading
        # step plus the mapping from the FieldTypes. Not all columns will have
        # a mapped fieldname, in which case the list value will be None for
        # each field

        # Create a mapping from the field's configured headerColumn to the
        # field name (ie, the dict key under which values are stored)
        fieldname_mapping = {field.headerColumn: field.name
                             for field in recordtype.fieldTypes if field.active}

        self.fieldnames[recordtype.id] = [fieldname_mapping.get(col)
                                          for col in self.file.headerColumns]

        del self.file.parsedColumns[:]
        self.file.parsedColumns.extend(list(fieldname_mapping.values()))
      else:
        # Otherwise we have to create a list of fieldnames, but with Nones
        # for columns that don't get imported.
        assert recordtype.fieldTypes, \
            f'At least one field is required for {recordtype.name}'

        fields: dict[int, str] = {field.columnIndex: field.name for field
                                  in recordtype.fieldTypes if field.active}
        self.fieldnames[recordtype.id] = [None] * max(fields.keys())
        for idx, fieldname in fields.items():
          self.fieldnames[recordtype.id][idx] = fieldname

      # Add any shared_key(s)
      self.shared_keys[recordtype.id] = [field.name for field
                                         in recordtype.fieldTypes
                                         if field.isSharedKey and field.active]

    self._update_status_to_processing(protos.File.PARSING, protos.File.LOADED)
    self._clear_stats('PARSE')
    self.file.times.parsingStartTime = bson_format.now()

    self._process_records(self._get_all_records())

    # Final update to the File record
    self.file.log.append(self._make_log_entry(False, 'Parsed records'))

  def _process_record(self, records: list[helpers.Record]
      ) -> t.Optional[t.Union[pymongo.UpdateOne, pymongo.UpdateMany]]:
    assert len(records) == 1
    record = records[0].updated_record

    # Parent class' pre-processing confirmed that the record type is in the
    # self.recordtypes_map. We need it in the self.fieldnames, but we assume
    # they're equivalent

    step_stat = self._get_step_stat(record.recordType)

    fieldnames = self.fieldnames[record.recordType]
    shared_keys = self.shared_keys[record.recordType]

    row = record.rawColumns

    # The fieldname list will likely have None values, which generates a dict
    # with None keys (sometimes overwritten), which are removed later.
    # zip() stops with the shortest iterable, which is OK when fieldnames is
    # shortest (we lose loaded fields that didn't have FieldTypes), but would
    # be confusing if the row had less values than the fieldnames
    if len(row) < len(fieldnames):
      # This is probably better treated as a File-level ConfigurationError
      record.status = protos.Record.PARSE_ERROR
      log = self._make_log_entry(True,
          (f'Fewer values than fields: Found {len(row)} values but expected at '
           f'least {len(fieldnames)}'),
          protos.ProcessingLog.OTHER_CONFIGURATION_ERROR)
      record.log.append(log)
      record.recentErrors.append(log)

      step_stat.failure += 1
      return self._make_update(record, ['status', 'log', 'recentErrors'])

    parsed = dict(zip(fieldnames, row))
    # The zipping produces dict items keyed with None -- remove those
    parsed.pop(None, None)

    # We don't support extra fields or default values
    record.parsedFields.update(t.cast(dict[str, str], parsed))
    step_stat.success += 1
    record.status = protos.Record.PARSED

    if shared_keys:
      record.sharedKey = '++'.join(parsed[key] for key in shared_keys)

    self.file.stats.parsedRecordsSuccess += 1
    return self._make_update(record, ['parsedFields', 'status', 'sharedKey'])

  def _close_processing(self) -> None:
    """ Close the file object and update the db File fields. """
    self.file.times.parsingEndTime = bson_format.now()

    self._update_file(
      ['headerColumns', 'parsedColumns', 'status', 'stats', 'times', 'log',
       'recentErrors'])
