""" Function-related exceptions and helpers. """
import functools
import typing as t

from rivoli import protos

TCallable = t.TypeVar("TCallable", bound=t.Callable[[t.Any], t.Any])

class ConfigurationError(ValueError):
  """ A configuration error is systemic and fatal. Stops file processing.
  It's up to the validation function to decide what a systemic error is, but
  it can be anything that should stop not just record processing but also the
  entire file. Invalid or missing configuration parameters (e..g., API keys)
  is a good example. Also non-existent fields during record validation, since
  that implies that RecordType's FieldType configuration is invalid and the
  field will never exist.
  """
  error_code = protos.ProcessingLog.OTHER_CONFIGURATION_ERROR

class ValidationError(ValueError):
  """ A validation error concerns a specific Field or Record.
  Validation errors are the most likely error raised during field processing.
  Validation errors do not automatically get retried since the value should
  be stable and attempting to re-validate should have the same outcome.
  """
  error_code = protos.ProcessingLog.OTHER_VALIDATION_ERROR

class ExecutionError(RuntimeError):
  """ An execution error concerns a Field or Record but unrelated to its value.
  An execution error is usually a transient error while attempting to validate,
  modify, or process and *may* be auto-retriable. An example is an API error,
  while an API timeout may cause the error to be retriable.
  """
  def __init__(self, msg: str,
      error_code: t.Union['protos.ProcessingLog.ErrorCode', int] =
        protos.ProcessingLog.OTHER_EXECUTION_ERROR,
      auto_retry: bool = False) -> None:
    super().__init__(msg)

    self.error_code = error_code
    self.auto_retry = auto_retry

def raise_config_error(
    python_exceptions: tuple[t.Type[Exception]] = (KeyError, )):
  """ Convert specified exception types to a ConfigurationError """

  def wrapped(func: TCallable) -> TCallable:
    @functools.wraps(func)
    def wrapped_f(*args: t.Any, **kwargs: t.Any) -> t.Any:
      try:
        return func(*args, **kwargs)
      except python_exceptions as exc:
        msg = (f'Could not find key {exc} while executing {func.__name__}.'
               'This is likely a configuration error.')
        raise ConfigurationError(msg) # pylint: disable=raise-missing-from

    return wrapped_f # pyright: reportGeneralTypeIssues=false

  return wrapped
