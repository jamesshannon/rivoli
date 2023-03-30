import abc
import itertools
import re
import typing as t

import pymongo

from rivoli import db
from rivoli import protos
from rivoli.protobson import bson_format

class RecordProcessor(abc.ABC):
  """ Abstract class to handle processing records in files or database. """
  log_source: protos.ProcessingLog.LogSource

  def __init__(self, file: protos.File, partner: protos.Partner,
               filetype: protos.FileType) -> None:
    self.file = file
    self.partner = partner
    self.filetype = filetype

    self.recordtypes_map = {rt.id: rt for rt in filetype.recordTypes}

    self.record_prefix = self.file.id << 32

    self.db = db.get_db()

    self.record_prefix: int

    self.unhandled_exception: t.Optional[Exception]

  def _update_status_to_processing(self, new_status: protos.File.Status,
      required_status: t.Optional['protos.File.Status'] = None):
    """ Update file status field, with an optional locking strategy.
    Update the file status in the database. If the `required_status` is provided
    then check that the current file has that status locally and within the
    database during the update. If 0 records are updated then that means that
    the status in the db didn't match.
    """
    new_file = protos.File(status=new_status, updated=bson_format.now())

    filter_fields = ['id']

    if required_status:
      if self.file.status != required_status:
        current_status = protos.File.Status.Name(self.file.status)
        raise ValueError(f'File status is {current_status}')

      filter_fields.append('status')

    result = self.db.files.update_one(
        bson_format.get_filter_map(self.file, filter_fields),
        bson_format.get_update_map(new_file, ['status', 'updated']))

    if not result.matched_count:
      # Unexpected status. Possibly another Loader is working on this file
      # But should we allow re-loading for any reason?
      print('Skip the loading because status could not be updated')

    # The db was updated, now reflect that in the File message
    self.file.MergeFrom(new_file)

  def _update_file(self, update_fields: list[str],
        status: t.Optional['protos.File.Status'] = None) -> None:
    """ Update the File record in the database. """
    if status:
      self.file.status = status

    self.db.files.update_one(
      *bson_format.get_update_args(self.file, update_fields))

  def _all_records_filter(self,
      status: t.Optional['protos.Record.Status'] = None,
      status_filter_gte: bool = True, sort: str = None) -> dict[str, t.Any]:
    """ Create a db filter for all Records for a file.
    The Record key is prefaced by the file key, so a primary-key-based filter
    can return all records.
    """
    # Since the record id is an int64 where the first 4 bytes are the file id,
    # the record IDs range from file ID shifted 4 bytes to the left to the same
    # value but if the last 4 bytes were all 0xFF. This filter creates that
    # range.
    max_record_id = self.record_prefix + ((1 << 32) - 1)
    fltr = {'_id': {'$gte': self.record_prefix, '$lte': max_record_id}}
    if status:
      operator = '$gte' if status_filter_gte else '$eq'
      # ideally should be using bson_format.get_filter_map but that doesn't
      # support operators
      fltr['status'] = {operator: status}

    return fltr

  def _clear_stats(self, step: str) -> None:
    """ Clear stats values for this step and later steps.
    Useful when re-running a step, especially for config testing. """
    # Get all the steps we should delete
    all_steps: dict[str, tuple[list[str], list[str]]] = {
        'LOAD': [
            ['loadedRecordsSuccess', 'loadedRecordsError', 'totalRows'],
            ['loadingStartTime', 'loadingEndTime']],
        'PARSE': [
            ['parsedRecordsSuccess', 'parsedRecordsError'],
            ['parsingStartTime', 'parsingEndTime']],
        'VALIDATE': [
            ['validatedRecordsSuccess', 'validatedRecordsError',
             'validationErrors', 'validationExecutionErrors'],
            ['validatingStartTime', 'validatingEndTime']],
        'UPLOAD': [
            ['uploadedRecordsSuccess', 'uploadedRecordsError',
             'uploadedRecordsSkipped'],
            ['uploadingStartTime', 'uploadingEndTime']],
    }

    all_step_prefixes = list(all_steps.keys())
    # Find the index of the current step
    step_idx = all_step_prefixes.index(step)
    # ... in order to get the "relevant" prefixes (ie, this one and later ones)
    step_prefixes = all_step_prefixes[step_idx:]

    if step == 'LOAD' and not self.file.stats.approximateRows:
      # If the file has been loaded then approximate_rows has been cleared out
      # Reset it to total_rows for a better UX
      self.file.stats.approximateRows = self.file.stats.totalRows

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

  def _get_regexp_matching_record(self, text: str,
        records: list[protos.RecordType],
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
    return protos.ProcessingLog(
      source=self.log_source,
      level=protos.ProcessingLog.ERROR if error else protos.ProcessingLog.INFO,
      errorCode=error_code,
      time=bson_format.now(),
      message=message,
      **kwargs
    )

class DbRecordProcessor(RecordProcessor):
  """ Abstract class to handle processing database records. """
  def _get_all_records(self, status: t.Optional['protos.Record.Status'] = None,
      status_filter_gte: bool = True, **kwargs: t.Any):
    """ Generator for all Record records for the class instance's File. """
    for record in self.db.records.find(
        self._all_records_filter(status, status_filter_gte), **kwargs):
      yield bson_format.to_proto(protos.Record, record)

  def _make_update(self, record: protos.Record, update_fields: list[str]
      ) -> pymongo.UpdateOne:
    """ Create a DB Update record which can be batched up. """
    return pymongo.UpdateOne(
        *bson_format.get_update_args(record, update_fields))

  def _process_records(self, records: t.Generator[protos.Record, None, None],
      file_update_fields: t.Optional[list[str]] = None):
    """ Batch loop through records in db, run callback, update status, etc. """
    file_update_fields = file_update_fields or ['stats']

    while records_chunk := list(itertools.islice(records, 1000)):
      bulk_writes: list[t.Optional[pymongo.UpdateOne]] = []

      try:
        for record in records_chunk:
          bulk_writes.append(self._process_one_record(record))

          if self.unhandled_exception:
            raise self.unhandled_exception

      except Exception as exc:
        # Configuration errors are handled at this level because we don't want
        # to continue validating (or uploading?) after a configuration error
        # Add ConfigurationError to the file and shut down cleanly
        # Signal to caller not to assume the processing was successful

        # LOGGER raising exception
        #  provide info on most recent record
        #  maybe write the error to the record, or the file?
        print('unhandled exception')
        self.file.status = protos.File.VALIDATED
        self.file.log.append(self._make_log_entry(True, str(exc)))

        raise exc

      finally:
        # Do the bulk write of the records batch
        bulk_writes = list(filter(None, bulk_writes))

        # LOGGER logging, maybe every 10k records?

        if bulk_writes:
          # Only call mongodb if we have writes to make
          self.db.records.bulk_write(bulk_writes, # pyright: reportUnknownMemberType=false
              ordered=False) # pyright: reportGeneralTypeIssues=false

        self.db.files.update_one(
          *bson_format.get_update_args(self.file, file_update_fields))

  @abc.abstractmethod
  def _process_one_record(self, record: protos.Record
      ) -> t.Optional[pymongo.UpdateOne]:
    """ Implementation-specific method to process one record.
    Called once for every record in the db to perform processing. """



