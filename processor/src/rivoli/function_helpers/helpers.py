""" Validation handler helpers.
Classes, datatypes, and functions in this file should be used by validation
handlers, including 3rd party handlers.
"""
import dataclasses
import functools
import typing as t

from rivoli import protos

TCallable = t.TypeVar("TCallable", bound=t.Callable[[t.Any], t.Any])
RecordType = dict[str, str]

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
