""" Abstract class for iterative processing. """
import abc
import re
import traceback
import typing as t

from rivoli import db
from rivoli import protos
from rivoli.function_helpers import exceptions
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

    # Record limiting, especially for testing scenarios.
    # It might seem easiest to set _max_pending_records and/or
    # _max_pending_updates to this value, but there are scenarios where the
    # limit value could be greater than those values (e.g., a limit of 5000).
    self._limit_records: t.Optional[int] = None
    """ Processing records limit. None == unlimited. """

    self.recordtypes_map = {rt.id: rt for rt in filetype.recordTypes}

    self.record_prefix: int = self.file.id << 32
    """ 32-bit-shifted File ID """

    # Update batching
    self._max_pending_updates = 1000
    """ Max updates to queue for writing to mongodb. """

    self._processing_finished = False
    """ Processing has sufficiently completed.
    This could be because all records in the file have processed (the file is
    complete) or because of other reasons that would cause processing of less
    than a full file, other than errors. (E.g., a record limit) """
    self._file_complete = False
    """ Processing is finished because all records were processed. """

    self.db = db.get_db() # pylint: disable=invalid-name

  def process(self, limit_records: t.Optional[int] = None):
    """ Process the records.
    This is the public entrypoint for record processing. It mostly calls
    `_process()` (which must be implemented on child classes) and handles any
    exceptions from that call. It also calls `_close_processing()` (also
    in the child class) at the end in a finally block (ie, regardless of any
    exceptions).
    """
    # This method simply calls the child class' _process() method, but
    # captures exceptions and add them to the file, which is a common pattern

    if limit_records:
      self._limit_records = limit_records

    try:
      self._process()

      if self._success_status:
        self.file.status = self._success_status

    except Exception as exc: # pylint: disable=broad-exception-caught
      # Specify the record_id as a kwarg here so that _make_exc_log_entry
      # doesn't include it on record-level exceptions
      record_id = getattr(exc, 'rivoli_record_id', None)
      log = self._make_exc_log_entry(exc, record_id=record_id)
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
      apiLogId=getattr(exc, 'api_log_id', None),
      time=bson_format.now(),
      summary=summary,
      message=message,
      stackTrace=stack_trace,
      **kwargs
    )
