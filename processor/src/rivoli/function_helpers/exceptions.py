""" Function-related exceptions and helpers. """
import functools
import typing as t

import requests

from rivoli import protos

TCallable = t.TypeVar("TCallable", bound=t.Callable[..., t.Any])

class RivoliError:
  error_code: t.Union['protos.ProcessingLog.ErrorCode', int] = 0
  summary: str = ''
  auto_retry: bool = False
  http_response: t.Optional[requests.Response] = None
  api_log_id: t.Optional[str] = None

  def __init__(self, *args: t.Any, **kwargs: t.Any):
    """ Shared RivoliError initialization. """

    def _set_from_kwargs(prop: str) -> None:
      """ Helper to set properties from kwargs. """
      val = kwargs.pop(prop, None)
      if val is not None:
        setattr(self, prop, val)

    _set_from_kwargs('error_code')
    _set_from_kwargs('summary')
    _set_from_kwargs('auto_retry')
    _set_from_kwargs('http_response')

class ConfigurationError(RivoliError, ValueError):
  """ A configuration error is systemic and fatal. Stops file processing.
  It's up to the validation function to decide what a systemic error is, but
  it can be anything that should stop not just record processing but also the
  entire file. Invalid or missing configuration parameters (e..g., API keys)
  is a good example. Also non-existent fields during record validation, since
  that implies that RecordType's FieldType configuration is invalid and the
  field will never exist.
  """
  error_code = protos.ProcessingLog.OTHER_CONFIGURATION_ERROR

class ValidationError(RivoliError, ValueError):
  """ A validation error concerns a specific Field or Record.
  Validation errors are the most likely error raised during field processing.
  Validation errors do not automatically get retried since the value should
  be stable and attempting to re-validate should have the same outcome.
  """
  error_code = protos.ProcessingLog.OTHER_VALIDATION_ERROR

class ExecutionError(RivoliError, RuntimeError):
  """ An execution error concerns a Field or Record but unrelated to its value.
  An execution error is usually a transient error while attempting to validate,
  modify, or process and *may* be auto-retriable. An example is an API error,
  while an API timeout may cause the error to be retriable.
  """
  error_code = protos.ProcessingLog.OTHER_EXECUTION_ERROR

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

    return wrapped_f # pyright: ignore[reportGeneralTypeIssues]

  return wrapped

def raise_validation_error(
    python_exceptions: tuple[t.Type[Exception]] = (KeyError, )):
  """ Convert specified exception types to a ValidationError """

  def wrapped(func: TCallable) -> TCallable:
    @functools.wraps(func)
    def wrapped_f(*args: t.Any, **kwargs: t.Any) -> t.Any:
      try:
        return func(*args, **kwargs)
      except python_exceptions as exc:
        msg = f'Could not find key {exc} while executing {func.__name__}.'
        raise ValidationError(msg) # pylint: disable=raise-missing-from

    return wrapped_f # pyright: ignore[reportGeneralTypeIssues]

  return wrapped
