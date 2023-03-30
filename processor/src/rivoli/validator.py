""" Validator """
import collections
import typing as t

import pymongo

from rivoli import admin_entities
from rivoli.protobson import bson_format
from rivoli import protos
from rivoli.utils import tasks
from rivoli import db
from rivoli import record_processor
from rivoli.validation import handler
from rivoli.validation import helpers
from rivoli.utils import processing



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
  v.validate()

  # decide what to do next.
  # aggregating if there are aggregation steps
  # if not, then waiting for approval if that flag is set and there are >0 errors
  # if not, then upload if upload is configured
  # if not, then direct to completed

class Validator(record_processor.DbRecordProcessor):
  """ Class to validate records.
  No need to subclass this as validation will not differ by file type. """

  log_source = protos.ProcessingLog.VALIDATOR

  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType) -> None:
    super().__init__(file, partner, filetype)

    self.errors: list[protos.ProcessingLog] = []

    # Dict in the form of dct[RecordTypeId, dct[FieldTypeId, functionconfigs]
    self.field_validations: dict[int, dict[str, list[protos.FunctionConfig]]] = \
        collections.defaultdict(lambda: collections.defaultdict(list))

    self.functions: dict[str, protos.Function]

  def validate(self):
    """ Validate all the records. """
    function_ids: set[str] = set()

    # 1) Get all function_ids that we'll need so that we can create a dict
    # 2) Create a mapping of this file's (RecordTypes, FieldTypes) to list of
    #    validation configurations
    for recordtype in self.filetype.recordTypes:
      function_ids.update([val.functionId for val in recordtype.validations])
      for fieldtype in recordtype.fieldTypes:
        for validation in fieldtype.validations:
          self.field_validations[recordtype.id][fieldtype.name].append(
              validation)
          function_ids.add(validation.functionId)

    self.functions = admin_entities.get_functions_by_ids(function_ids)

    self._clear_stats('VALIDATE')

    self._update_status_to_processing(protos.File.VALIDATING)
    self.file.times.validatingStartTime = bson_format.now()

    # This will not (currently) return records which need to be re-validated.
    # protos.Record.PARSED
    try:
      self._process_records(self._get_all_records())
    except Exception as exc:
      pass

    # Need to decide how to move onto the next step. What is the status if >0
    # Records failed validation? Probably still VALIDATED?
    # Then do we go onto processing or place it on PROCESSING_HOLD?

    # Final update to the File record
    self.file.status = protos.File.VALIDATED
    self.file.log.append(self._make_log_entry(False, 'Validated records'))
    self._update_file(['status', 'log', 'recentErrors', 'times', 'stats'])

  # Will also need an entrypoint to call this so that the UI can try to
  # (re-)validate a Record after a manual edit
  def _process_one_record(self, record: protos.Record
      ) -> t.Optional[pymongo.UpdateOne]:
    validated_fields: dict[str, str] = {}

    self.errors.clear()

    recordtype = record.recordType

    if recordtype == protos.Record.HEADER:
      return None

    ss_base_name = f'VALIDATE.{recordtype}'
    ss = self.file.stats.steps[ss_base_name]
    ss.input += 1

    # Ideally the record is *only* parsed, but make sure that it's *at least*
    # parsed. This is an invariant.
    if record.status < protos.Record.PARSED:
      ss.failure += 1
      return None

    # Loop through each field and apply validations & modifications
    for field_name, value in record.parsedFields.items():
      ss_field = self.file.stats.steps[f'{ss_base_name}.{field_name}']
      ss_field.input += 1

      for cfg in self.field_validations[recordtype][field_name]:
        success, value = self._call_function(protos.Function.FIELD_VALIDATION,
            cfg, value, field_name)

        if not success:
          ss_field.failure += 1
          # No additional validations for this field
          break

      validated_fields[field_name] = str(value)

    # If we ever allow revalidation of previously-validated records then
    # we need to unset the previous values

    # Only do record validations if all fields validated successfully
    if not self.errors:
      for cfg in self.recordtypes_map[recordtype].validations:
        success, result = self._call_function(protos.Function.RECORD_VALIDATION,
            cfg, validated_fields)

        if not success:
          # No additional validations for this record
          break

        validated_fields = t.cast(dict[str, str], result)

    # Clear the *record*-level recent validation errors, in case we're
    # re-validating this record
    del record.recentErrors[:]
    record.validatedFields.clear()

    if not self.errors:
      # No errors for this Record.
      # Update Record with the validated_fields, which might be different from
      # parsed_fields, set status and add item to the log
      self.file.stats.validatedRecordsSuccess += 1
      record.status = record.VALIDATED

      # Coerce all the fields to strings, in case they aren't
      validated_fields = {key: str(val) for key, val
                          in validated_fields.items()}
      record.validatedFields.update(validated_fields)

      ss.success += 1
    else:
      # There was at least one error for this Record. It could be a validation
      # and/or execution error
      # Update Record with the errors, set the status, and add items to the logs
      self.file.stats.validatedRecordsError += 1

      record.status = record.VALIDATION_ERROR
      # Add errors to the permanent log and also the recentErrors, which was
      # recently cleared
      record.log.extend(self.errors)
      record.recentErrors.extend(self.errors)

      ss.failure += 1

    # update the record
    return self._make_update(record,
        ['status', 'validatedFields', 'log', 'recentErrors'])

  def _call_function(self, typ: 'protos.Function.FunctionType',
      cfg: 'protos.FunctionConfig', value: t.Union[str, dict[str, str]],
      field_name: str = '') -> t.Tuple[bool, t.Union[str, dict[str, str]]]:
    """ Call a validation function, handle exceptions, and return result. """
    validator = self.functions[cfg.functionId]
    try:
      result = handler.call_function(typ, cfg, validator, value)

      return (True, result)

    except Exception as exc: # type: ignore=broad-exception-caught
      error_code = getattr(exc, 'error_code', '')

      log = self._make_log_entry(True, str(exc), field=field_name,
          functionId=validator.id, error_code=error_code)
      self.errors.append(log)

      if isinstance(exc, helpers.ValidationError):
        self.file.stats.validationErrors += 1
      elif isinstance(exc, helpers.ExecutionError):
        self.file.stats.validationExecutionErrors += 1
      else: # ConfigurationError or other Exception
        # No stats to update. Set the instance method to this exception so that
        # it can be handled later
        self.file.stats.validationExecutionErrors += 1
        self.unhandled_exception = exc

      return (False, '')
