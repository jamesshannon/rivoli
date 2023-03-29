""" Validation handler helpers. """
import dataclasses
import functools
import typing as t

from rivoli import protos

TCallable = t.TypeVar("TCallable", bound=t.Callable)
RecordType = dict[str, str]

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
  id: int
  recordtype: protos.RecordType
  validated_fields: dict[str, str]

def register_func(function_type: protos.Function.FunctionType,
                  deprecated: bool = False):
  def wrapped(func: TCallable) -> TCallable:
    @functools.wraps(func)
    def wrapped_f(*args, **kwargs): #type: ignore
      return func(*args, **kwargs) # type: ignore

    wrapped_f._function_type = function_type
    wrapped_f._deprecated = deprecated
    return wrapped_f

  return wrapped
