""" Module responsible for functions that call the actual validation. """
import types
import typing as t

from rivoli.validation import typing
from rivoli.validation.handlers import python_function
from rivoli.validation.handlers import sql
from rivoli import protos

HANDLER_MODULE_MAP: dict[str, types.ModuleType] = {
    'pythonFunction': python_function,
    'sqlCode': sql
}

def call_function(function_type: protos.Function.FunctionType,
    cfg: protos.FunctionConfig, function: protos.Function,
    *args: t.Any, **kwargs: t.Any) -> typing.ValReturn:
  """ Execute a "function" through a handler and return the value.
  Functions could be python functions, SQL statements, etc, and are configured
  in the Function message. The expected arguments and return value will be
  dictated by the FunctionType, but we don't (currently) check or enforce that.
  We expect that the module we choose (based on the functionStatement field)
  will have the appropriate function (name based on the FunctionType enum) and
  handle arguments / return correctly.
  Overrides aren't possible due to use of protobuf enums; here are the expected
  signatures:
    FIELD_VALIDATION: [value: str] -> str
    RECORD_VALIDATION: [value: Record] -> dict[str, str] | Record | None
    RECORD_UPLOAD: [value: Record] -> str
    RECORD_UPLOAD_BATCH: [value: list[Record]] -> str
  See `typing` for more information.
  All functions can raise a ValidationError, ExecutionError,
  ConfigurationError, or pass through any other Python Error, which are handled
  by the processor.
  """
  funcname = protos.Function.FunctionType.Name(function_type).lower()
  mod = HANDLER_MODULE_MAP[function.WhichOneof('functionStatement')]
  func = getattr(mod, funcname)
  return func(cfg, function, *args, **kwargs)
