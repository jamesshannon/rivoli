""" Uploader Module. """
import typing as t

import pymongo

from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli import db
from rivoli import protos
from rivoli import record_processor
from rivoli.utils import processing
from rivoli.utils import tasks
from rivoli.validation import handler
from rivoli.validation import helpers

mydb = db.get_db()

def get_file(file_id: int) -> protos.File:
  return bson_format.to_proto(protos.File,
      mydb.files.find_one({'_id': file_id}))

@tasks.app.task
def upload(file_id: int) -> None:
  mydb = db.get_db()

  file = get_file(file_id)

  # get the filetype config
  partner = admin_entities.get_partner(file.partnerId)
  filetype = admin_entities.get_filetype(file.fileTypeId)

  uploader = Uploader(file, partner, filetype)
  uploader.upload()

  return None

class Uploader(record_processor.DbRecordProcessor):
  """ Class to upload records. """
  def __init__(self, file: protos.File, partner: protos.Partner,
        filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self.functions: dict[str, protos.Function]

  def upload(self):
    # create a map of record types -> upload functions
    # loop through all the records. work per record type
    # skip if no upload function exists. maybe mark in log

    function_ids: set[str] = set()

    for recordtype in self.filetype.recordTypes:
      if recordtype.successCheck:
        function_ids.add(recordtype.successCheck.functionId)
      if recordtype.upload:
        function_ids.add(recordtype.upload.functionId)

    self.functions = admin_entities.get_functions_by_ids(function_ids)

    self._clear_stats('UPLOAD')
    self._update_status_to_processing(protos.File.UPLOADING)
    self.file.times.uploadingStartTime = bson_format.now()

    self._process_records(self._get_all_records(protos.Record.VALIDATED))

    self.file.status = protos.File.UPLOADED
    self.file.log.append(processing.new_log_entry(
        'Uploader.upload', 'Uploaded records'))
    self._update_file(['status', 'log', 'times', 'stats'])

  def _process_one_record(self, record: protos.Record
      ) -> t.Optional[pymongo.UpdateOne]:

    #import pdb; pdb.set_trace()
    recordtype_id = record.recordType

    if recordtype_id == protos.Record.HEADER:
      # There should never be any VALIDATED header records
      return None

    ss_base_name = f'UPLOAD.{recordtype_id}'
    ss = self.file.stats.steps[ss_base_name]
    ss.input += 1

    if (record.status != protos.Record.VALIDATED
        and not (record.status == protos.Record.UPLOAD_ERROR
            and record.retriable)):
      # This should never happen.
      # Record needs to be validated, and we don't want to re-upload records
      ss.failure += 1
      #return None

    if record.uploadConfirmationId:
      # This should not happen
      ss.failure += 1
      return None

    if recordtype_id not in self.recordtypes_map:
      # This is an unexpected failure.
      # Add a note?
      ss.failure += 1
      return None

    recordtype = self.recordtypes_map[recordtype_id]

    if not recordtype.upload:
      # No upload function. Skip this record
      # If scenario becomes common then we could compile the recordTypes with
      # upload functions and only return those for the processing
      return None

    upload_func = self.functions[recordtype.upload.functionId]
    # call the function
    # if successful and there's a return value then update the Record. otherwise
    # clear the value (shouldn't happen)
    # if not successful then store the error  ... ? otherwise clear the error
    try:
      response = handler.call_function(protos.Function.RECORD_UPLOAD,
          recordtype.upload, upload_func, record.validatedFields)
    except (helpers.ValidationError, helpers.ExecutionError) as exc:
      record.uploadError.CopyFrom(protos.ProcessingError(
          functionId=upload_func.id, error=str(exc)))
      record.status = protos.Record.UPLOAD_ERROR
      record.retriable = getattr(exc, 'retriable', False)

      self.file.stats.uploadedRecordsError += 1
      ss.failure += 1

      return self._make_update(record,
          ['status', 'stats', 'uploadError', 'retriable'])

    record.status = protos.Record.UPLOADED
    record.uploadConfirmationId = str(response)
    record.retriable = False
    self.file.stats.uploadedRecordsSuccess += 1
    ss.success += 1

    return self._make_update(record,
        ['status', 'stats', 'uploadError', 'retriable'])
