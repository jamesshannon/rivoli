""" Validation handler helpers. """

import functools
import typing as t

from rivoli import protos

TCallable = t.TypeVar("TCallable", bound=t.Callable)
RecordType = dict[str, str]

class ValidationError(ValueError):
  """ A validation error which is raised and saved to the Record. """

class ExecutionError(RuntimeError):
  """ An execution error which is raised and saved to the Record. """
  def __init__(self, msg: str, retriable: bool = False) -> None:
    super().__init__(msg)

    self.retriable = retriable


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
