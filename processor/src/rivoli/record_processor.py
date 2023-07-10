""" Abstract class for iterative processing. """
import abc
import itertools
import re
import time
import traceback
import typing as t

import pymongo

from rivoli import db
from rivoli import protos
from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers
from rivoli.protobson import bson_format
from rivoli.utils import logging

logger = logging.get_logger(__name__)

class RecordProcessor(abc.ABC):
  """ Abstract class to handle processing records in files or database. """
  log_source: protos.ProcessingLog.LogSource

  _success_status: t.Optional['protos.File.Status'] = None
  _error_status: t.Optional['protos.File.Status'] = None

  _record_error_status: protos.Record.Status
  """ Status for Records which caused an exception. """

  _step_stat_prefix: t.Optional[str] = None

  def __init__(self, file: protos.File, partner: protos.Partner,
               filetype: protos.FileType) -> None:
    self.file = file
    self.partner = partner
    self.filetype = filetype

    self.recordtypes_map = {rt.id: rt for rt in filetype.recordTypes}

    self.record_prefix: int = self.file.id << 32
    """ 32-bit-shifted File ID """

    # Update batching
    self._max_pending_updates = 1000
    """ Max updates to queue for writing to mongodb. """

    self.db = db.get_db() # pylint: disable=invalid-name

  def process(self):
    """ Process the records.
    This is the public entrypoint for record processing. It mostly calls
    `_process()` (which must be implemented on child classes) and handles any
    exceptions from that call. It also calls `_close_processing()` (also
    in the child class) at the end in a finally block (ie, regardless of any
    exceptions).
    """
    # This method simply calls the child class' _process() method, but
    # captures exceptions and add them to the file, which is a common pattern
    try:
      self._process()

      if self._success_status:
        self.file.status = self._success_status

    except Exception as exc: # pylint: disable=broad-exception-caught
      log = self._make_exc_log_entry(exc)
      self.file.log.append(log)
      self.file.recentErrors.append(log)

      if isinstance(exc, (exceptions.ConfigurationError, )):
        # ConfigurationErrors are "expected" errors and not indicative of
        # a bug in the code
        logger.info('Updating File ID %s status to %s because of exception %s',
            self.file.id, self._error_status, str(exc))
      else:
        # Other exceptions are possibly a bug in the code
        logger.error('Updating File ID %s status to %s because of exception %s',
            self.file.id, self._error_status, str(exc))
        traceback.print_exc()

      if self._error_status:
        self.file.status = self._error_status

    finally:
      self._close_processing()

  @abc.abstractmethod
  def _process(self):
    """ Do the module-specific processing.
    _process() will typically do some setup then call
    _update_status_to_processing() and _process_records()
    """

  @abc.abstractmethod
  def _close_processing(self) -> None:
    """ Close the processing and update the File. """
    # This can be overridden and will get called during the finally

  def _update_status_to_processing(self, new_status: protos.File.Status,
      required_status: t.Optional[t.Union['protos.File.Status',
                                          list['protos.File.Status']]] = None):
    """ Update File status field, with an optional locking strategy.
    Update the file status in the database. If the `required_status` is provided
    then check that the current file has that status locally and within the
    database during the update. If 0 records are updated then that means that
    the status in the db didn't match.
    """
    new_file = protos.File(status=new_status, updated=bson_format.now())

    filter_fields = ['id']

    current_status = protos.File.Status.Name(self.file.status)

    if required_status:
      required_statuses = (required_status if isinstance(required_status, list)
                           else [required_status])
      if self.file.status not in required_statuses:
        raise ValueError(('Unable to begin processing because File status is '
                          f'{current_status}'))

      # This filter checks that the db status is the file status (which we just
      # checked is one of the required statuses)
      filter_fields.append('status')

    result = self.db.files.update_one(
        bson_format.get_filter_map(self.file, filter_fields),
        bson_format.get_update_map(new_file, ['status', 'updated']))

    if not result.matched_count:
      # Unexpected status. Possibly another Loader is working on this file
      # But should we allow re-loading for any reason?
      raise ValueError((f'File status is {current_status} but could not update '
                        'status in database'))

    # The db was updated, now reflect that in the instance's File message
    self.file.MergeFrom(new_file)

  def _update_file(self, update_fields: list[str],
        status: t.Optional['protos.File.Status'] = None,
        list_append_fields: t.Optional[list[str]] = None) -> None:
    """ Update the File record in the database. """
    if status:
      self.file.status = status

    self.db.files.update_one(
      *bson_format.get_update_args(self.file, update_fields,
                                   list_append_fields=list_append_fields))

  def _all_records_filter(self,
      status: t.Optional['protos.Record.Status'] = None,
      status_filter_gte: bool = True) -> dict[str, t.Any]:
    """ Create a db filter for all Records for a file.
    The Record key is prefaced by the file key, so a primary-key-based filter
    can return all records.
    """
    # Since the record id is an int64 where the first 4 bytes are the file id,
    # the record IDs range from file ID shifted 4 bytes to the left to the same
    # value but if the last 4 bytes were all 0xFF. This filter creates that
    # range.
    max_record_id = self.record_prefix + ((1 << 32) - 1)
    filter_ = {'_id': {'$gte': self.record_prefix, '$lte': max_record_id}}

    if status:
      operator = '$gte' if status_filter_gte else '$eq'
      # ideally would use bson_format.get_filter_map but that doesn't
      # support operators
      filter_['status'] = {operator: status}

    return filter_

  def _clear_stats(self, step: str) -> None:
    """ Clear stats values for this step and later steps.
    Useful when re-running a step, especially for config testing. """
    # Get all the steps we should delete
    all_steps: dict[str, tuple[list[str], list[str]]] = {
        'LOAD': (
            ['loadedRecordsSuccess', 'loadedRecordsError', 'totalRows'],
            ['loadingStartTime', 'loadingEndTime']),
        'PARSE': (
            ['parsedRecordsSuccess', 'parsedRecordsError'],
            ['parsingStartTime', 'parsingEndTime']),
        'VALIDATE': (
            ['validatedRecordsSuccess', 'validatedRecordsError',
             'validationErrors', 'validationExecutionErrors'],
            ['validatingStartTime', 'validatingEndTime']),
        'UPLOAD': (
            ['uploadedRecordsSuccess', 'uploadedRecordsError',
             'uploadedRecordsSkipped'],
            ['uploadingStartTime', 'uploadingEndTime']),
    }

    all_step_prefixes = list(all_steps.keys())
    # Find the index of the current step
    step_idx = all_step_prefixes.index(step)
    # ... in order to get the "relevant" prefixes (ie, this one and later ones)
    step_prefixes = all_step_prefixes[step_idx:]

    # if step == 'LOAD':
    #   # If the file has been loaded then approximate_rows has been cleared out
    #   # Reset it to total_rows for a better UX
    #   self.file.stats.approximateRows = self.file.stats.totalRows

    key: str
    for key in step_prefixes:
      # Clear the stats fields
      for field in all_steps[key][0]:
        self.file.stats.ClearField(field)

      # Clear the time fields
      for field in all_steps[key][1]:
        self.file.times.ClearField(field)

    # Clear the stats.steps fields
    for key in list(self.file.stats.steps.keys()):
      if any(key.startswith(step_prefix) for step_prefix in step_prefixes):
        del self.file.stats.steps[key]

  def _get_step_stat_key(self, *args: t.Any) -> str:
    """ Get the StepStat key for this particular step.
    *args is any additional arbitrary string(s) that are added at end and
    separated by .'s.
    """
    prefix = self._step_stat_prefix or ''
    # If prefix is None then an empty string will cause a leading _
    return ':'.join([prefix] + [str(x) for x in args]).lstrip(':')

  def _get_step_stat(self, *args: t.Any) -> protos.StepStats:
    """ Get the StepStat for this particular step.
    *args is any additional arbitrary string(s) that are added at end and
    separated by .'s. The StepStat comes from the File instance and so any
    changes made will be saved to the db when an Update instance is created.
    If _step_stat_prefix is empty (the default) then we return a "disconnected"
    instance of a StepStat. This makes it easier for shared RecordProcessor
    code not use StepStats without a lot of logic.
    """
    if not self._step_stat_prefix:
      return protos.StepStats()

    return self.file.stats.steps[self._get_step_stat_key(*args)]

  def _get_regexp_matching_record(self, text: str,
        records: t.Sequence[protos.RecordType],
        matches_field: str) -> t.Optional[protos.RecordType]:
    """ Find matching entity from a list based on any of its matching patterns.
    This addresses the pattern in which we look for a match against a string
    from a number of "records" (e.g., filetypes or recordtypes) which can each
    have multiple matching patterns.
    """
    for record in records:
      matches_list: list[str] = getattr(record, matches_field)
      for pattern in matches_list:
        if re.fullmatch(pattern, text):
          return record

    return None

  def _make_log_entry(self, error: bool, message: str,
      error_code: t.Optional[t.Union['protos.ProcessingLog.ErrorCode', int]] =
          None,
      **kwargs: t.Any
      ) -> protos.ProcessingLog:
    """ Create a log entry. """
    return protos.ProcessingLog(
      source=self.log_source,
      level=protos.ProcessingLog.ERROR if error else protos.ProcessingLog.INFO,
      errorCode=error_code,
      time=bson_format.now(),
      message=message,
      **kwargs
    )

  def _make_exc_log_entry(self, exc: Exception, **kwargs: t.Any):
    """ Create a log entry from an exception. """
    classname = exc.__class__.__name__
    summary = str(getattr(exc, 'summary', ''))
    message = f'{classname}: {exc}'
    error_code = getattr(exc, 'error_code',
                         protos.ProcessingLog.ERRORCODE_UNKNOWN)

    # Only include the stack trace if it's an "unexpected" error. RivoliErrors
    # are expected validation-related errors.
    # RivoliErrors also tend to be intentionally crafted. If a summary isn't
    # provided then defer to the message. OTOH, system exceptions can have a
    # lot of noise in the exception message so we use the classname.
    stack_trace = None
    if isinstance(exc, exceptions.RivoliError):
      summary = summary or message
    else:
      summary = summary or classname
      stack_trace = traceback.format_exc()

    return protos.ProcessingLog(
      source=self.log_source,
      level=protos.ProcessingLog.ERROR,
      errorCode=error_code,
      time=bson_format.now(),
      summary=summary,
      message=message,
      stackTrace=stack_trace,
      **kwargs
    )


class DbChunkProcessor(RecordProcessor):
  """ Abstract class to handle processing database records in chunks. """
  _fields_field: str = ''
  """ Name of the field on the Record which stores *existing* record data. """
  _only_process_record_status: t.Union['protos.Record.Status', t.Literal[False]]

  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self._functions: dict[str, protos.Function]
    """ Function lookup map. """

    self._db_chunk_size = 1000
    """ Chunk size to load records from database. """

    ### Processing batching
    self._max_pending_records = 1
    """ Max records to queue for processing. """
    self._should_process_records = False
    """ True to force processing of records. """
    self._is_batch_mode = False
    """ If this processing is being done in batch mode. """

  def _set_max_pending_records(self, max_records: t.Optional[int]) -> None:
    """ Set the max records to process at once. Recalcs max_pending_updates.
    Limited to 1000.
    """
    self._max_pending_records = min(max_records or 1, 1000)

    # Max # of pending Mongo Operations before we issue a bulk_write
    # By default this is 1000, but that's when each Update updates one document.
    # In this case each write might be updating hundreds of documents, so we
    # keep the # pending a little lower. We also don't want to get too
    # out-of-sync with what we've done via the API.
    self._max_pending_updates = min(
        int(5000 / self._max_pending_records), 1000)

    # Update the chunk size. This keeps the chunk size a multiple of
    # the pending records queue size
    self._db_chunk_size = (max(int(1000 / self._max_pending_records), 1)
                           * self._max_pending_records)

    self._is_batch_mode = self._max_pending_records > 1

    if self._is_batch_mode and len(self.filetype.recordTypes) > 1:
      raise AssertionError(('Batches not supported when FileType has more than '
                            'one RecordType'))

  def _get_all_records(self, status: t.Optional['protos.Record.Status'] = None,
      status_filter_gte: bool = True, **kwargs: t.Any):
    """ Generator for filtered Records for the class instance's File. """
    return self._get_some_records(
        self._all_records_filter(status, status_filter_gte), **kwargs)

  def _get_some_records(self, filter_: dict[str, t.Any], **kwargs: t.Any):
    """ Generator for filtered Records for the class instance's File.
    Combines the filter_ parameter dict with a base filter for the Record IDs
    for this file. Allows for more customized record iterations than
    get_all_records(). Additional pymongo find() parameters can be passed in
    kwargs.
    """
    filter_ = self._all_records_filter() | filter_

    for record in self.db.records.find(filter_, **kwargs):
      yield bson_format.to_proto(protos.Record, record)

  def _process_records(self, records: t.Generator[protos.Record, None, None],
      file_update_fields: t.Optional[list[str]] = None) -> None:
    """ Process iterator of records in chunks.
    This is typically called by the child-implemented _process() and simply
    iterates through chunks (~1000 records) from the records generator. It then
    calls `_preprocess_chunk()` and then `_process_chunk()`.

    """
    while records_chunk := list(itertools.islice(records, self._db_chunk_size)):
      # Pre-process the *chunk*
      self._preprocess_chunk(records_chunk)
      # Process the *chunk*
      self._process_chunk(records_chunk)

  def _preprocess_chunk(self, records: list[protos.Record]) -> None:
    """ Pre-process the chunk of records, if applicable. """

  def _process_chunk(self, records: list[protos.Record]) -> None:
    """ Process a chunk of records. """
    pending_updates: list[t.Optional[
        t.Union[pymongo.UpdateOne, pymongo.UpdateMany]]] = []
    last_update = time.time()

    record: t.Optional[protos.Record] = None

    # Records pending processing. Will often be max of 1 item.
    pending_records: list[helpers.Record] = []
    exceptional_update: t.Optional[pymongo.UpdateOne]

    #record_type: t.Optional[protos.RecordType] = None
    import pdb

    try:
      for record in records:
        # RecordType needs to be be the same as all previous RecordTypes. For
        # now we assume it is because we don't allow batch operations with >1
        # RecordType
        try:
          record_h = self._preprocess_record(record)
          if not record_h:
            continue

          # Should the (batch of) records be processed?
          if (self._should_process_records
              or len(pending_records) >= self._max_pending_records):
            # Process the (batch?) of records. E.g. validate or upload
            pending_updates.append(self._process_record(pending_records))

            pending_records.clear()
            self._should_process_records = False

          # Should the batch of updates be written to the database?
          # We update the db when we hit the max number of documents (~1000) or
          # it's been over 30 seconds
          if (len(pending_updates) >= self._max_pending_updates
              or time.time() > last_update + 30):
            pending_updates = list(filter(None, pending_updates))
            logger.debug('Updating %s documents in db', len(pending_updates))

            if pending_updates:
              self.db.records.bulk_write(pending_updates, ordered=False)
              pending_updates.clear()

            # Always update the file when updating record (in the db)
            self._update_file(['status', 'log', 'times', 'stats'])
            last_update = time.time()

          # Add the helpers.Record to the pending list. We do this down here
          # because this record might start a new batch, and can't be part of
          # the previous batch
          pending_records.append(record_h)

        except Exception as exc:
          logger.debug('Uncaptured exception in Record processing function')
          # Uncaptured exception from a Record processing function. We update
          # the Record with the error and possibly raise the exception if it's
          # a File-level exception. In some cases the error has already been
          # "written" to the Record (via a pymongo.Update* instance being
          # returned or raised as part of the exception). If the Update wasn't
          # attached then we should automatically create one. There shouldn't be
          # any situations in which an exception occurs (in this loop)
          # but we don't want to attach it to the Record.
          exceptional_update = t.cast(t.Optional[pymongo.UpdateOne],
              getattr(exc, 'update', None))
          if exceptional_update:
            # Exception already has an attached update so nothing to add
            # At the same time the fact that called code was sophisticated
            # enough to attach and update but still raised the exception means
            # that this a File-level exception
            pending_updates.append(exceptional_update)

            raise exc

          # Make a record update and add it to the updates queue
          log = self._make_exc_log_entry(exc)

          record.status = self._record_error_status
          record.log.append(log)
          record.recentErrors.append(log)

          pending_updates.append(
              self._make_update(record, ['status', 'log', 'recentErrors']))

          # TOOD: This doesn't update the failed count

          if isinstance(exc,
                (exceptions.ValidationError, exceptions.ExecutionError)):
            # Record-level exception. Continue the loop
            continue

          # File-level exception.
          raise exc

      # If the chunk is empty and there are still pending records to process --
      # there should typically be at least one -- then do that now and add to
      # pending_updates which will get updated as part of the finally block
      if pending_records:
        pending_updates.append(self._process_record(pending_records))

    finally:
      pending_updates = list(filter(None, pending_updates))

      if pending_updates:
        # Write the batch of updates to the database. This will include any
        # updates from the loop, plus possible remaining update after the loop
        # or and update from a raised exception
        logger.debug('Updating %s documents in db in finally block',
            len(pending_updates))
        self.db.records.bulk_write(pending_updates, ordered=False)
        self._update_file(['status', 'log', 'times', 'stats'])


  def _preprocess_record(self, record: protos.Record
      ) -> t.Optional[helpers.Record]:
    """ Ensure the Record is ready to be processed, return helpers.Record.
    There may be soft failures, where None is returned, or hard failures, where
    an exception is raised.
    This also decides if a batch should be processed immediately.
    """
    recordtype_id = record.recordType

    # Duplicate the record before we make any changes to it
    record_orig = protos.Record()
    record_orig.CopyFrom(record)

    # Clear any recent errors for this record
    del record.recentErrors[:]

    step_stat = self._get_step_stat(record.recordType)
    step_stat.input += 1

    if recordtype_id == protos.Record.HEADER:
      # Don't process the header record
      # Not technically a failure, though this should have been excluded
      return None

    if recordtype_id not in self.recordtypes_map:
      # This should not happen. `ValueError`s will stop file processing, which
      # is desirable since this is a systemic error.
      step_stat.failure += 1
      raise ValueError("Record's recordType is not in the File's map")

    recordtype = self.recordtypes_map[recordtype_id]

    # Check for a specific record status
    if (self._only_process_record_status
        and record.status != self._only_process_record_status):
      # These should have been excluded from the query and this should never
      # happen. `ValueError`s will stop file processing, which is desirable
      # since this is a systemic error.
      step_stat.failure += 1
      raise ValueError('Record status is invalid for this step')

    # The field values mapping will have a different name depending on the
    # step (e.g., parsedFields, validatedFields)
    fields: dict[str, str] = {}
    if self._fields_field:
      fields = dict(getattr(record, self._fields_field))

    return helpers.Record(record, record_orig, recordtype, fields,
        dict(self.file.tags))

  @abc.abstractmethod
  def _process_record(self, records: list[helpers.Record]
      ) -> t.Optional[t.Union[pymongo.UpdateOne, pymongo.UpdateMany]]:
    """ Process a (batch of) records.
    This is where the magic happens. An UpdateOne or UpdateMany should be
    returned with appropriate record update.
    Most errors should only affect the record(s), in which case they should
    be part of the DB update. If there are fatal errors then the exception
    should be raised withh the UpdateOne/UpdateMany as part of the exception.
    """

  def _make_update(self, record: protos.Record, update_fields: list[str]
      ) -> pymongo.UpdateOne:
    """ Create a DB UpdateOne record which can be batched up. """
    return pymongo.UpdateOne(
        *bson_format.get_update_args(record, update_fields))
