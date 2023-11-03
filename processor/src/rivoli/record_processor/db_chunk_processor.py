""" Abstract class for iterative processing. """
import abc
import itertools
import time
import typing as t

import pymongo

from rivoli import protos
from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers
from rivoli.protobson import bson_format
from rivoli.record_processor import record_processor
from rivoli.utils import logging

logger = logging.get_logger(__name__)


class DbChunkProcessor(record_processor.RecordProcessor):
  """ Abstract class to handle processing database records in chunks. """
MONGO_UPDATE = pymongo.UpdateOne | pymongo.UpdateMany

T = t.TypeVar('T')

def _listify(inp: t.Sequence[T] | T | None) -> t.Sequence[T]:
  """ Create a list of T out of a single T, a list of T, or None (removed).
  This is used for accepting a variety of ways of returning T and the output is
  suitable for passing to a list's extend(). None is accepted, but removed.
  """
  if inp is None:
    return []

  if not isinstance(inp, t.Sequence):
    return [inp]

  # At this point inp must be a single instance of the value but pyright is
  # getting confused
  return inp # pyright: ignore[reportUnknownVariableType]
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

    for record in self.db.records.find(filter_, **kwargs).sort('_id'):
      # Sort by _id -- we were getting apparent repeated records and this is the only possibility
      # Otherwise might have to create a session and set the snapshot option
      yield bson_format.to_proto(protos.Record, record)

  def process(self, limit_records: t.Optional[int] = None):
    """ Process the records. """
    if limit_records:
      self._limit_records = limit_records
      # If limit_records is set then re-run calculations for max_pending_records
      self._set_max_pending_records(
          max(limit_records, self._max_pending_records))

    super().process()

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

      if self._processing_finished:
        break

    else:
      # Assume the file is complete if the while wasn't broken (and no
      # exception was raised).
      self._file_complete = True
      self._processing_finished = True

  def _preprocess_chunk(self, records: list[protos.Record]) -> None:
    """ Pre-process the chunk of records, if applicable. """

  def _process_chunk(self, records: list[protos.Record]) -> None:
    """ Process a chunk of records. """
    pending_updates: list[MONGO_UPDATE] = []
    last_update = time.time()

    record: t.Optional[protos.Record] = None

    # Records pending processing. Will often be max of 1 item.
    pending_records: list[helpers.Record] = []

    processed_records = 0

    record_h = None

    # TODO: Line ~525 catches any records which are still pending after the
    # loop and processes it. That's good, but it does it outside of the main
    # try/except loop, which means that we don't make updates to the record
    # (specifically the log)
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
            pending_updates.extend(
                _listify(self._process_record(pending_records)))

            pending_records.clear()
            self._should_process_records = False

          # Should the batch of updates be written to the database?
          # We update the db when we hit the max number of documents (~1000) or
          # it's been over 30 seconds
          if (len(pending_updates) >= self._max_pending_updates
              or time.time() > last_update + 30):
            logger.debug('Updating %s documents in db', len(pending_updates))

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
          if record_h:
            logger.debug(
                ('Uncaptured exception in Record processing '
                 'for record id %s: %s'), record_h.id, exc)
          else:
            logger.debug('Uncaptured exception in Record processing: %s', exc)
          # Uncaptured exception from a Record processing function. We update
          # the Record with the error and possibly raise the exception if it's
          # a File-level exception. In some cases the error has already been
          # "written" to the Record (via a pymongo.Update* instance being
          # returned or raised as part of the exception). If the Update wasn't
          # attached then we should automatically create one. There shouldn't be
          # any situations in which an exception occurs (in this loop)
          # but we don't want to attach it to the Record.
          exceptional_update = t.cast(list[MONGO_UPDATE] | None,
              getattr(exc, 'update', None))
          if exceptional_update:
            # Exception already has an attached update so nothing to add
            # At the same time the fact that called code was sophisticated
            # enough to attach and update but still raised the exception means
            # that this a File-level exception
            pending_updates.extend(_listify(exceptional_update))

            raise exc

          # Make a record update and add it to the updates queue
          log = self._make_exc_log_entry(exc)

          record.status = self._record_error_status
          record.log.append(log)
          record.recentErrors.append(log)

          pending_updates.extend(
              self._make_update(record, ['status', 'log', 'recentErrors']))

          # TOOD: This doesn't update the failed count

          if not isinstance(exc,
                (exceptions.ValidationError, exceptions.ExecutionError)):
            # File-level exception.
            raise exc

          # Otherwise it's a record-level exception so we continue the loop

        # End of the records for loop
        processed_records += 1
        if self._limit_records and processed_records >= self._limit_records:
          self._processing_finished = True
          break

      # If the chunk is empty and there are still pending records to process --
      # there should typically be at least one -- then do that now and add to
      # pending_updates which will get updated as part of the finally block
      if pending_records:
        pending_updates.extend(_listify(self._process_record(pending_records)))
        pending_records.clear()

    finally:
      if pending_updates:
        # Write the batch of updates to the database. This will include any
        # updates from the loop, plus possible remaining update after the loop
        # or and update from a raised exception
        logger.debug('Updating %s documents in db in finally block',
            len(pending_updates))
        self.db.records.bulk_write(pending_updates, ordered=False)
        self._update_file(['status', 'log', 'times', 'stats'])


  @abc.abstractmethod
  def _preprocess_record(self, record: PBR) -> t.Optional[HR]:
    """ Ensure the Record is ready to be processed, return helpers.Record.
    There may be soft failures, where None is returned, or hard failures, where
    an exception is raised.
    This also decides if a batch should be processed immediately.
    """

  def _make_helper_record(self, record: protos.Record) -> helpers.Record:
    """ Create a Helper Record, do basic checks, and log step stats. """
    recordtype_id = record.recordType

    step_stat = self._get_step_stat(record.recordType)
    step_stat.input += 1

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

    return helpers.Record(record, recordtype, self._fields_field,
        dict(self.file.tags))

  @abc.abstractmethod
  def _process_record(self, records: list[helpers.Record]
      ) -> list[MONGO_UPDATE] | MONGO_UPDATE | None:
    """ Process a (batch of) records.
    This is where the magic happens. An UpdateOne or UpdateMany should be
    returned with appropriate record update.
    Most errors should only affect the record(s), in which case they should
    be part of the DB update. If there are fatal errors then the exception
    should be raised with the UpdateOne/UpdateMany as part of the exception.
    """

  def _make_update(self, record: ProtoRecordGroup | protos.Record,
      update_fields: list[str]) -> list[pymongo.UpdateOne]:
    """ Create a DB UpdateOne(s) record which can be batched up. """
    if isinstance(record, protos.Record):
      # Single record
      return [pymongo.UpdateOne(*bson_format.get_update_args(record,
                                                             update_fields))]

    """
  def _preprocess_record(self, record: protos.Record) -> helpers.Record | None:
    record_h = self._make_helper_record(record)

    if record_h.record_type.id == protos.Record.HEADER:
      # Don't process the header record
      # Not technically a failure, though this should have been excluded
      return None

    return record_h
