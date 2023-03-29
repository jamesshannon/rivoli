""" Uploader Module. """
import time
import typing as t

import pymongo

from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli import db
from rivoli import protos
from rivoli import record_processor
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

  uploader = BatchRecordUploader(file, partner, filetype)
  uploader.upload()

  return None

class Uploader(record_processor.DbRecordProcessor):
  log_source = protos.ProcessingLog.UPLOADER
  update_fields = ['status', 'stats', 'log']

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

    # don't clear stats because this might be a continuation.
    # how to handle continuations? maybe check the status do some things if
    # stutus is currently UPLOADING? But also what about a lock?
    #self._clear_stats('UPLOAD')
    self._update_status_to_processing(protos.File.UPLOADING)
    self.file.times.uploadingStartTime = bson_format.now()
    self._update_file(['status', 'updated', 'times'])

    # when we're doing batch and there's a groupby key it would be good to
    # order by the groupby key, but ideally we'd copy that value into its own
    # column during the .. validation? step?
    kwargs = {}
    # IF STATEMENT
    # This will cause problems if we stop using validatedFields
    kwargs['sort'] = [('validatedFields.PORTFOLIO_ID', 1)]
    self._process_records(
        self._get_all_records(protos.Record.VALIDATED, False, **kwargs))

    self.file.status = protos.File.UPLOADED
    self.file.times.uploadingEndTime = bson_format.now()
    self.file.log.append(self._make_log_entry(False, 'Uploaded records'))
    self._update_file(['status', 'log', 'times', 'stats'])

class BatchRecordUploader(Uploader):
  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self.functions: dict[str, protos.Function]

    self._groupby_field = self.filetype.uploadBatchGroupKey
    self._current_groupby_value: t.Optional[str] = None
    self._should_upload_batch = False

    # Get the batch size from the filetype. Default to 1 (no batching)
    self._max_pending_uploads = self.filetype.uploadBatchSize or 1

    # Max # of pending Mongo Operations before we issue a bulk_write
    # In other stages this is around 1000, but that's 1:1 to the number of
    # actual documents to update. In this case each write might be updating
    # hundreds of documents, so we keep the # pending a little lower. We also
    # don't want to get too out-of-sync with what we've done via the API
    # This algorithm basically gives us a 5x benefit for bulk updates
    self._max_pending_updates = min(int(5000 / self._max_pending_uploads), 1000)

    self._is_batch = self._max_pending_uploads == 1

    if not self._is_batch and len(self.filetype.recordTypes) > 1:
      raise ValueError(('Batches not supported when FileType has more than one '
                        'RecordType'))

  def _process_one_record(self, record: protos.Record
       ) -> t.Optional[pymongo.UpdateOne]: ...

  def _process_upload(self, record: protos.Record
      ) -> t.Optional[helpers.ProcessedRecord]:
    recordtype_id = record.recordType

    if recordtype_id == protos.Record.HEADER:
      # There should never be any VALIDATED header records
      return None

    ss_base_name = f'UPLOAD.{recordtype_id}'
    ss = self.file.stats.steps[ss_base_name]
    ss.input += 1

    # TODO: Logs should probably be added in all of these cases
    if record.status != protos.Record.VALIDATED:
      # This should never happen.
      # Record needs to be validated, and we don't want to re-upload records
      ss.failure += 1
      return None

    if record.uploadConfirmationId:
      # This should not happen
      ss.failure += 1
      return None

    if recordtype_id not in self.recordtypes_map:
      # This is an unexpected failure.
      ss.failure += 1
      return None

    recordtype = self.recordtypes_map[recordtype_id]

    if not recordtype.upload:
      # No upload function. Skip this record
      # If scenario becomes common then we could compile the recordTypes with
      # upload functions and only return those for the processing
      return None

    fields = t.cast(dict[str, str], record.validatedFields)

    # Is this the beginning of a new batch?
    if self._groupby_field:
      if (self._current_groupby_value
          and self._current_groupby_value != fields[self._groupby_field]):
        self._should_upload_batch = True

      self._current_groupby_value = fields[self._groupby_field]

    return helpers.ProcessedRecord(record.id, recordtype, fields)

  def _process_records(self, records: t.Generator[protos.Record, None, None],
                       file_update_fields: t.Optional[list[str]] = None):
    """ batch """
    pending_uploads: list[helpers.ProcessedRecord] = []
    pending_updates: list[t.Union[pymongo.UpdateOne, pymongo.UpdateMany]] = []

    record_type: t.Optional[protos.RecordType] = None

    last_file_update = time.time()

    try:
      for record in records:
        processed = self._process_upload(record)
        if not processed:
          continue

        # If we're in a batch then this needs to be the same as all previous
        # RecordTypes. For now we assume it is because we don't allow batch
        # operations with > 1 recordType
        record_type = self.recordtypes_map[record.recordType]

        if (self._should_upload_batch
            or len(pending_uploads) >= self._max_pending_uploads):
          # upload. add result to pending_updates
          print('uploading', len(pending_uploads), 'records')
          update = self._upload_records(record_type, pending_uploads)
          if update:
            pending_updates.append(update)

          pending_uploads.clear()
          self._should_upload_batch = False

        if (len(pending_updates) >= self._max_pending_updates
            or time.time() > last_file_update + 30):
          # when to use LOGGER ?
          print('updating', len(pending_updates), 'documents')
          self.db.records.bulk_write(pending_updates, ordered=False)
          pending_updates.clear()

          # Always update the file when updating records
          self._update_file(['status', 'log', 'times', 'stats'])
          last_file_update = time.time()

        # Add the ProcessedRecords to the pending list. We do this down here
        # because this record might start a new batch, and can't be part of
        # the previous batch
        pending_uploads.append(processed)

      if pending_uploads:
        print('uploading', len(pending_uploads), 'records')
        update = self._upload_records(record_type, pending_uploads)
        pending_updates.append(update)

    except Exception as exc:
      # LOGGER raising exception
      #  provide info on most recent record
      #  maybe write the error to the record, or the file?
      print('unhandled excpetion')
      raise exc

    finally:
      # Bulk write of any remaining updates, whether remaining from a successful
      # loop or whatever was queued up when an unhandled exception occurred
      if pending_updates:
        print('updating', len(pending_updates), 'documents')
        self.db.records.bulk_write(pending_updates, ordered=False)
        self._update_file(['status', 'log', 'times', 'stats'])


  def _upload_records(self, recordtype: protos.RecordType,
        records: list[helpers.ProcessedRecord]
        ) -> t.Union[pymongo.UpdateOne, pymongo.UpdateMany]:
    # Get the upload function configured for this RecordType
    upload_func = self.functions[recordtype.upload.functionId]

    value: t.Union[list[helpers.ProcessedRecord], helpers.ProcessedRecord] = \
        records

    # We could have a) batch records + batch function, b) single record + single
    # function, or c) single record + batch function. (A) and (C) expect lists
    # while (B) expected a single ProcessedRecord
    if upload_func.type == protos.Function.RECORD_UPLOAD:
      # Assert that this is not (d) -- batch record + single function
      if self._is_batch:
        raise ValueError('Fucntion xxx doesnt support batch mode')

      if len(records) > 1:
        # Invariant
        raise ValueError(f'Not in batch mode but got {len(records)} records')

      # Set the value to the first (and only) record
      value = records[0]

    # If this is a batch update then we need a single representative record
    # from which to set the fields and create the changes. If this is a
    # non-batch update then we could use the actual Record, but this function
    # only gets ProcessedRecords. Regardless, we can still apply changes from
    # one (representative) Record onto the actual Record
    a_record = protos.Record()

    ss = self.file.stats.steps[f'UPLOAD.{recordtype.id}']

    try:
      # Let the configured function type determine what the handler does
      response = handler.call_function(upload_func.type, recordtype.upload,
          upload_func, value)

      # Success
      a_record.status = protos.Record.UPLOADED
      # Coerce None into an empty string
      a_record.uploadConfirmationId = str(response or '')
      a_record.log.append(self._make_log_entry(False, 'Uploaded'))

      # These are the default values, but let's be explicit
      a_record.autoRetry = False
      a_record.retryCount = 0

      self.file.stats.uploadedRecordsSuccess += len(records)
      ss.success += len(records)
    except (helpers.ValidationError, helpers.ExecutionError) as exc:
      # ValidationError should not occur. ExecutionError is more likely.
      # Either way, the error applies to all the records if in batch mode
      upload_error = self._make_log_entry(True, str(exc),
          error_code=exc.error_code, functionId=upload_func.id)

      # recentErrors and log will be empty because this is a representative
      # record. When updating, recentErrors should be replaced while log should
      # be appended
      a_record.recentErrors.append(upload_error)
      a_record.log.append(upload_error)

      a_record.status = protos.Record.UPLOAD_ERROR
      a_record.autoRetry = getattr(exc, 'auto_retry', False)

      self.file.stats.uploadedRecordsError += len(records)
      ss.failure += len(records)

    # Create an update_map which $sets most values but appends $log entries
    # This is necessary since we're working on a representative record
    update_map = bson_format.get_update_map(a_record,
        ['status', 'uploadConfirmationId', 'autoRetry', 'recentErrors'],
        ['log'])

    # The number of records in the "batch" determines the type of Update we
    # return, regardless of batch mode or function type. This is a probable
    # over-optimization so that we don't send UpdateManys with single updates
    if len(records) == 1:
      return pymongo.UpdateOne({'_id': records[0].id}, update_map)

    record_ids = [record.id for record in records]
    return pymongo.UpdateMany({'_id': {'$in': record_ids}}, update_map)
