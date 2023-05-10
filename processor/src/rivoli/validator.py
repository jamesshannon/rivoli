""" Validator """
import collections
import typing as t

import pymongo

from rivoli import admin_entities
from rivoli.protobson import bson_format
from rivoli import protos
from rivoli import db
from rivoli import record_processor
from rivoli import status_scheduler
from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers
from rivoli.validation import handler
from rivoli.utils import tasks

# Disable pyright checks due to Celery
# pyright: reportFunctionMemberAccess=false
# pyright: reportUnknownMemberType=false

@tasks.app.task
def validate(file_id: int) -> None:
  mydb = db.get_db()

  file = bson_format.to_proto(protos.File,
      mydb.files.find_one({'_id': file_id}))

  # get the filetype config
  partner = admin_entities.get_partner(file.partnerId)
  filetype = admin_entities.get_filetype(file.fileTypeId)

  #_validate(file, ft)
  v = Validator(file, partner, filetype)
  v.process()

  status_scheduler.next_step(file, filetype)


class Validator(record_processor.DbChunkProcessor):
  """ Class to validate records.
  No need to subclass this as validation will not differ by file type. """
  log_source = protos.ProcessingLog.VALIDATOR

  _only_process_record_status = protos.Record.PARSED
  _fields_field = 'parsedFields'

  _success_status = protos.File.VALIDATED
  _error_status = protos.File.VALIDATE_ERROR

  _step_stat_prefix = 'VALIDATE'

  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self.errors: list[protos.ProcessingLog] = []
    """ Accumulation of a Record's errors. """

    self._field_name_ids: dict[str, str] = {}
    """ Map of field names to field IDs. """

    # Dict in the form of dct[RecordTypeId, dct[FieldTypeId, functionconfigs]
    self.field_validations: dict[int, dict[str, list[protos.FunctionConfig]]] = \
        collections.defaultdict(lambda: collections.defaultdict(list))

  def _process(self):
    """ Validate all the records. """
    function_ids: set[str] = set()

    # 1) Get all function_ids that we'll need so that we can create a dict
    # 2) Create a mapping of this file's FieldTypes to list of
    #    validation configurations. We already have a recordtypes_map
    for recordtype in self.filetype.recordTypes:
      function_ids.update([val.functionId for val in recordtype.validations])

      for fieldtype in recordtype.fieldTypes:
        self._field_name_ids[fieldtype.name] = fieldtype.id

        for validation in fieldtype.validations:
          self.field_validations[recordtype.id][fieldtype.name].append(
              validation)
          function_ids.add(validation.functionId)

    self._functions = admin_entities.get_functions_by_ids(function_ids)

    self._clear_stats('VALIDATE')

    self._update_status_to_processing(protos.File.VALIDATING,
        protos.File.PARSED)
    self.file.times.validatingStartTime = bson_format.now()

    self._process_records(self._get_all_records(protos.Record.PARSED))
    # Need to decide how to move onto the next step. What is the status if >0
    # Records failed validation? Probably still VALIDATED?
    # Then do we go onto processing or place it on PROCESSING_HOLD?

    # Final update to the File record
    self.file.log.append(self._make_log_entry(False, 'Validated records'))

  # Will also need an entrypoint to call this so that the UI can try to
  # (re-)validate a Record after a manual edit
  def _process_record(self, records: list[helpers.Record]
      ) -> t.Optional[pymongo.UpdateOne]:
    assert len(records) == 1
    record = records[0]
    raw_record = record.updated_record

    validated_fields: dict[str, str] = {}

    self.errors.clear()
    file_exception: t.Optional[Exception] = None

    step_stat = self._get_step_stat(raw_record.recordType)
    step_stat.input += 1

    record_type_id = raw_record.recordType

    # Loop through each field and apply validations & modifications
    for field_name, value in record.items():
      field_id = self._field_name_ids[field_name]
      ss_field = self._get_step_stat(raw_record.recordType, field_id)
      ss_field.input += 1

      for cfg in self.field_validations[record_type_id][field_name]:
        ss_field_func = self._get_step_stat(
            raw_record.recordType, field_id, cfg.id)
        ss_field_func.input += 1

        try:
          value = t.cast(str, self._call_function(
              protos.Function.FIELD_VALIDATION, cfg, value, field_name))
          ss_field.success += 1
          ss_field_func.success += 1
        except Exception as exc: # pylint: disable=broad-exception-caught
          ss_field.failure += 1
          ss_field_func.failure += 1

          # No additional validations for this field

          # File level exceptions are any exception that's not a Record-level
          # exception, and requires us to re-raise later.
          if not isinstance(exc,
              (exceptions.ValidationError, exceptions.ExecutionError)):
            file_exception = exc

          break

      validated_fields[field_name] = str(value)

    # If we ever allow revalidation of previously-validated records then
    # we need to unset the previous values

    # Only do record validations if all fields validated successfully
    # At this point the validatedFields become the record's fields
    record.clear()
    record.update(validated_fields)

    if not self.errors:
      for cfg in self.recordtypes_map[record_type_id].validations:
        ss_record_func = self._get_step_stat(raw_record.recordType, cfg.id)
        ss_record_func.input += 1

        try:
          validated_fields = t.cast(dict[str, str],
              self._call_function(protos.Function.RECORD_VALIDATION, cfg,
              record))
          ss_record_func.success += 1
        except Exception as exc: # pylint: disable=broad-exception-caught
          ss_record_func.failure += 1

          # File level exceptions are any exception that's not a Record-level
          # exception, and requires us to re-raise later.
          if not isinstance(exc,
              (exceptions.ValidationError, exceptions.ExecutionError)):
            file_exception = exc

          break

        # result_dct should be complete -- if the record-validation function
        # removes a field then we don't want to keep it
        record.clear()
        record.update(validated_fields)

    # Clear the *record*-level field values, in case we're revalidating
    record.updated_record.validatedFields.clear()

    if not self.errors:
      # No errors for this Record.
      # Update Record with the validated_fields, which might be different from
      # parsed_fields, set status and add item to the log
      self.file.stats.validatedRecordsSuccess += 1
      record.updated_record.status = protos.Record.VALIDATED

      # Coerce all the fields to strings, in case they aren't
      record.updated_record.validatedFields.update({key: str(val) for key, val
                                                in validated_fields.items()})

      step_stat.success += 1
    else:
      # There was at least one error for this Record. It could be a validation
      # and/or execution error
      # Update Record with the errors, set the status, and add items to the logs
      self.file.stats.validatedRecordsError += 1

      record.updated_record.status = protos.Record.VALIDATION_ERROR
      # Add errors to the permanent log and also the recentErrors, which was
      # recently cleared
      record.updated_record.log.extend(self.errors)
      record.updated_record.recentErrors.extend(self.errors)

      step_stat.failure += 1

    # update the record
    update = self._make_update(record.updated_record,
        ['status', 'validatedFields', 'log', 'recentErrors'])

    # file_exception is any exception that's of a type that's not a record-
    # level exception and thus needs to be handled up-stack. If that was set
    # then we've already updated the record fields. Now we re-raise the
    # exception (with the record).
    if file_exception:
      file_exception.update = update # pyright: reportGeneralTypeIssues=false
      raise file_exception

    return update

  def _call_function(self, typ: 'protos.Function.FunctionType',
      cfg: 'protos.FunctionConfig', value: t.Union[str, helpers.Record],
      field_name: str = '') -> t.Union[str, dict[str, str]]:
    """ Call a validation function, handle exceptions, and return result. """
    validator = self._functions[cfg.functionId]
    try:
      result = handler.call_function(typ, cfg, validator, value)

      return result

    except Exception as exc:
      error_code = getattr(exc, 'error_code',
                           protos.ProcessingLog.ERRORCODE_UNKNOWN)

      log = self._make_log_entry(True, str(exc), field=field_name,
          functionId=validator.id, error_code=error_code)
      exc.record_updated = True
      self.errors.append(log)

      if isinstance(exc, exceptions.ValidationError):
        self.file.stats.validationErrors += 1
      elif isinstance(exc, exceptions.ExecutionError):
        self.file.stats.validationExecutionErrors += 1
      else: # ConfigurationError or other Exception
        # No stats to update. Set the instance method to this exception so that
        # it can be handled later
        self.file.stats.validationExecutionErrors += 1

      raise exc

  def _close_processing(self) -> None:
    self.file.times.validatingEndTime = bson_format.now()
    self._update_file(['status', 'log', 'recentErrors', 'times', 'stats'])
