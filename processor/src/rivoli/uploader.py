""" Uploader Module. """
import typing as t

import pymongo

from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli import db
from rivoli import protos
from rivoli import record_processor
from rivoli import status_scheduler
from rivoli.utils import tasks
from rivoli.validation import handler
from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers

mydb = db.get_db()

def get_file(file_id: int) -> protos.File:
  return bson_format.to_proto(protos.File,
      mydb.files.find_one({'_id': file_id}))

@tasks.app.task
def upload(file_id: int) -> None:
  file = db.get_one_by_id('files', file_id, protos.File)

  # get the partner and filetype info
  partner = admin_entities.get_partner(file.partnerId)
  filetype = admin_entities.get_filetype(file.fileTypeId)

  uploader = RecordUploader(file, partner, filetype)
  uploader.process()

  status_scheduler.next_step(file, filetype)

class RecordUploader(record_processor.DbChunkProcessor):
  """ Class to upload records. """
  log_source = protos.ProcessingLog.UPLOADER
  _fields_field = 'validatedFields'
  _only_process_record_status = protos.Record.VALIDATED

  _success_status = protos.File.UPLOADED
  _error_status = protos.File.UPLOAD_ERROR

  _record_error_status = protos.Record.UPLOAD_ERROR

  _step_stat_prefix = 'UPLOAD'

  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self._set_max_pending_records(self.filetype.uploadBatchSize)

    self._groupby_field = filetype.uploadBatchGroupKey
    """ Name of the field, if any, that uploads are grouped by. """
    self._current_groupby_value: t.Optional[str] = None
    """ Value of the current group's groups-by key. """

    self._uploaded_hashes: set[bytes]
    """ Set of hashes of matching successfully-uploaded records. """
    self._chunk_hashes: set[bytes] = set()
    """ Set of hashes of previous records in chunk. """

    # Retriable count is not part of the file.stats, so we track separately
    self._retriable_record_cnt = 0
    """ Numer of retriable from this run. """

  def _process(self):
    """ Upload the records. """
    # create a map of record types -> upload functions
    function_ids: set[str] = set()

    for recordtype in self.filetype.recordTypes:
      if recordtype.successCheck:
        function_ids.add(recordtype.successCheck.functionId)
      if recordtype.upload:
        function_ids.add(recordtype.upload.functionId)

    self._functions = admin_entities.get_functions_by_ids(function_ids)

    # Don't clear stats because this might be a retry or continuation.
    # How to handle continuations? maybe check the status do some things if
    # Status is currently UPLOADING? But also what about a lock?
    self._update_status_to_processing(protos.File.UPLOADING)
    self.file.times.uploadingStartTime = bson_format.now()
    self._update_file(['status', 'updated', 'times'])

    # When we're doing batch and there's a groupby key we need to
    # order by the groupby key. For optimization, we'd ideally have copied that
    # value into its own field during the ... validation step?
    kwargs = {}
    if self._groupby_field:
      # This will need to be modified if we stop using validatedFields
      kwargs['sort'] = [(f'validatedFields.{self._groupby_field}', 1)]

    self._process_records(
        self._get_all_records(protos.Record.VALIDATED, False, **kwargs))

    self._end_upload()

  def _end_upload(self):
    """ Determine next steps, such as marking the file as complete. """
    # Resetting retriable records should only occur when file is otherwise
    # complete
    # How much of this should be part of the class vs not?
    # At the least any celery-calls should not be part of this?
    if self._retriable_record_cnt and False: # Records to retry
      # If we just use the internal count rather than a file count then
      # this will break after retry.
      # Update the records. This should mirror the webui files/ID/records code
      log = self._make_log_entry(False,
          'Reverted status to VALIDATED for auto-retry')
      filter_ = self._all_records_filter(protos.Record.UPLOAD_ERROR, False) | {
        'autoRetry': True
      }

      update: dict[str, t.Any] = {
          # Set the status to VALIDATED
          '$set': { 'status': protos.Record.VALIDATED },
          # Remove the log of recentErrors and autoRetry flag
          '$unset': { 'recentErrors': {}, 'autoRetry': {} },
          # Add a log entry describing this action
          '$addToSet': {
            'log': bson_format.from_proto(log)
          },
          # Increment the retry count
          '$inc': { 'retryCount': 1 }
      }

      print(filter_, update)
      resp = self.db.records.update_many(filter_, update)
      if resp.modified_count == 0:
        # Something went wrong
        print('retry result', resp)
        pass

      log = self._make_log_entry(False,
          (f'Uploaded records and reverted record status to VALIDATED '
           f'on {resp.modified_count} records for auto-retry'))
      self.file.log.append(log)
      self.file.status = protos.File.UPLOADING_RETRY_PAUSE
      # Need to add the increment, somehow

      # db.collection('files').updateOne(
      #   { _id: parseInt(fileId) },
      #   {
      #     $addToSet: { log: log.toJson({ enumAsInteger: true }) },
      #     $inc: { 'stats.uploadedRecordsError': -1 * modified }
      #   }
      # );

      self._update_file(['status', 'log', 'times', 'stats'])
      # schedule new task

      return

    # Uploading is finished. What's the next step?
    # For now the file goes to completed. In the future we might move to a
    # COORECT_ERRORS state or something
    self.file.status = protos.File.COMPLETED
    self.file.times.uploadingEndTime = bson_format.now()
    self.file.log.append(self._make_log_entry(False, 'Uploaded records'))
    self._update_file(['status', 'log', 'times', 'stats'])

  def _retry_retriable_records(self):
    """ Reset retriable records to VALIDATED status """
    # Ignore records with > 4 retries. Backoff strategy?

    # 1) If pause, then set status and create a new task immediately
    # 1) Retry records, then set to retry_pause and create a new task
    # 2) Set to "pause" then create a new task
    # or 3) set to done and end task

  def _preprocess_chunk(self, records: list[protos.Record]) -> None:
    """ Pre-process the chunk of records and look for duplicates.
    Query the database for matching hashes of already-uploaded records,
    (including from other Files) then save them to the instance so that they can
    be checked during processing.
    """
    hashes = list(filter(None, [r.hash for r in records]))
    hashes_cursor = self.db.records.find(
        {'hash': {'$in': hashes}, 'status': {'$gte': protos.Record.UPLOADED}},
        {'hash': 1, '_id': 0}
    )

    self._uploaded_hashes = set(doc['hash'] for doc in hashes_cursor)

  def _preprocess_record(self, record: protos.Record
      ) -> t.Optional[helpers.Record]:
    record_h = super()._preprocess_record(record)
    if not record_h:
      return None

    step_stat = self._get_step_stat(record.recordType)
    step_stat.input += 1

    if not record_h.record_type.upload:
      # No upload function. Skip this record
      # If scenario becomes common then we could compile the recordTypes with
      # upload functions and filter for those in mongo
      step_stat.failure += 1
      self.file.stats.uploadedRecordsError += 1
      return None

    if record.uploadConfirmationId:
      # This should not happen, but since we the parent method already filtered
      # on status then something might be wrong internally
      step_stat.failure += 1
      self.file.stats.uploadedRecordsError += 1
      raise ValueError('uploadConfirmationId is not empty')

    if (record.hash in self._uploaded_hashes
        or record.hash in self._chunk_hashes):
      # A record with the same hash already exists, either in the database or
      # earlier in this chunk
      step_stat.failure += 1
      self.file.stats.uploadedRecordsError += 1
      msg = ('Record data already uploaded'
             if record.hash in self._uploaded_hashes
             else 'Duplicate record data found in previous row')
      raise exceptions.ValidationError(msg)

    self._chunk_hashes.add(record.hash)

     # Is this Record the beginning of a new batch?
    if self._groupby_field:
      record_value = record_h[self._groupby_field]

      if (self._current_groupby_value
          and self._current_groupby_value != record_value):
        self._should_process_records = True

      self._current_groupby_value = record_value

    return record_h

  def _process_record(self, records: list[helpers.Record]
      ) -> t.Optional[pymongo.UpdateMany]:
    # A batch should never have more than one unique RecordType
    record_type = records[0].record_type
    # Get the upload function for this RecordType
    upload_func = self._functions[record_type.upload.functionId]

    # These both specifically count the number of records not the number of
    # "uploads" (which might be far fewer, if batched).
    step_stat = self._get_step_stat(record_type.id)
    step_stat_fn = self._get_step_stat(record_type.id, record_type.upload.id)

    # The non-function step has already been created and incremented in
    # _preprocess_record
    step_stat_fn.input += 1

    # Uploading is unique because the function might take multiple Records or
    # a single Record.

    # We could have a) batch records + batch function, b) single record + single
    # function, or c) single record + batch function. (A) and (C) expect lists
    # while (B) expects a single helpers.Record
    # Value could be a list or a single Record
    value: t.Union[list[helpers.Record], helpers.Record] = records

    if upload_func.type == protos.Function.RECORD_UPLOAD:
      # Assert that this is not (d) -- batch record + single function
      if self._is_batch_mode:
        raise exceptions.ConfigurationError(
            f"Function {upload_func.name} doesn't support batch mode")

      if len(records) > 1:
        # Invariant
        raise exceptions.ConfigurationError(
            f'Not in batch mode but got {len(records)} records')

      # Set the value to the first (and only) record
      value = records[0]

    # If this is a batch update then we need a single representative record
    # from which to set the fields and create the changes. If this is a
    # non-batch update then we could use the actual Record message though we
    # can still apply changes from one (representative) protos.Record onto the
    # actual database Record
    a_record = protos.Record()

    try:
      # Let the configured function type determine what the handler does
      response = handler.call_function(upload_func.type, record_type.upload,
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
      step_stat.success += len(records)
      step_stat_fn.success += len(records)
    except (exceptions.ValidationError, exceptions.ExecutionError) as exc:
      # ValidationError should not occur. ExecutionError is more likely.
      # Either way, the error applies to all the records if in batch mode
      upload_error = self._make_exc_log_entry(exc, functionId=upload_func.id)

      # recentErrors and log will be empty because this is a representative
      # record. When updating, recentErrors should be replaced while log should
      # be appended
      a_record.recentErrors.append(upload_error)
      a_record.log.append(upload_error)

      a_record.status = protos.Record.UPLOAD_ERROR
      a_record.autoRetry = getattr(exc, 'auto_retry', False)

      self.file.stats.uploadedRecordsError += len(records)
      step_stat.failure += len(records)
      step_stat_fn.failure += len(records)

      self._retriable_record_cnt += len(records) if a_record.autoRetry else 0

    # Create an update_map which $sets most values but appends $log entries
    # This is necessary since we're working on a representative record
    update_map = bson_format.get_update_map(a_record,
        ['status', 'uploadConfirmationId', 'autoRetry', 'recentErrors'],
        ['log'])

    return pymongo.UpdateMany(
        {'_id': {'$in': [record.id for record in records]}}, update_map)

  def _close_processing(self) -> None:
    self.file.times.uploadingEndTime = bson_format.now()
    self._update_file(['status', 'log', 'recentErrors', 'times', 'stats'])
