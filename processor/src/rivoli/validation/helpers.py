""" Validation handler helpers.
Classes, datatypes, and functions in this file should be used by validation
handlers, including 3rd party handlers.
"""
import dataclasses
import functools
import typing as t

from rivoli import protos

TCallable = t.TypeVar("TCallable", bound=t.Callable)
RecordType = dict[str, str]

class ConfigurationError(ValueError):
  """ A configuration error is systemic and fatal. """
  error_code = protos.ProcessingLog.OTHER_CONFIGURATION_ERROR

class ValidationError(ValueError):
  """ A validation error which is raised and saved to the Record. """
  error_code = protos.ProcessingLog.OTHER_VALIDATION_ERROR

class ExecutionError(RuntimeError):
  """ An execution error which is raised and saved to the Record. """
  def __init__(self, msg: str,
      error_code: t.Union['protos.ProcessingLog.ErrorCode', int] =
        protos.ProcessingLog.OTHER_EXECUTION_ERROR,
      auto_retry: bool = False) -> None:
    super().__init__(msg)

    self.error_code = error_code
    self.auto_retry = auto_retry

@dataclasses.dataclass
class ProcessedRecord():
  """ A ProcessedRecord is a stable Record format sent to Upload handlers. """
  id: int # pylint: disable=invalid-name
  """ Rivoli Record ID """
  recordtype: protos.RecordType
  """ RecordType of this Record """
  validated_fields: dict[str, str]
  """ Dict of key/value from the file, possibly modified in prior steps. """


def register_func(function_type: protos.Function.FunctionType,
                  deprecated: bool = False):
  """ Register a handler function.
  Registered functions can be scanned-for and inserted into the application.
  """
  # pyright: reportGeneralTypeIssues=false, reportUnknownVariableType=false
  # pylint: disable=protected-access
  def wrapped(func: TCallable) -> TCallable:
    @functools.wraps(func)
    def wrapped_f(*args: t.Any, **kwargs: t.Any) -> t.Any:
      return func(*args, **kwargs)

    wrapped_f._function_type = function_type
    wrapped_f._deprecated = deprecated
    return wrapped_f

  return wrapped
