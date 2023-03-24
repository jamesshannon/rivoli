""" Module responsible for functions that call the actual validation. """
import importlib
import inspect
import types
import typing as t

from rivoli.validation.handlers import python_function
from rivoli.validation.handlers import sql
from rivoli import protos

HANDLER_MODULE_MAP: dict[str, types.ModuleType] = {
    'pythonFunction': python_function,
    'sqlCode': sql
}

# HANDLER_FUNCTION_MAP: dict[protos.Function.FunctionType, str] = {
#   protos.Function.FIELD_VALIDATION: 'field_validation',
#   protos.Function.RECORD_VALIDATION: 'record_validation',
#   protos.Function.RECORD_UPLOAD: 'record_upload',
# }

def call_function(function_type: protos.Function.FunctionType,
    cfg: protos.FunctionConfig,
    function: protos.Function, *args: t.Any, **kwargs: t.Any,
    ) -> t.Union[str, dict[str, str]]:
  """ Execute a "function" through a handler and return the value.
  Functions could be python functions, SQL statements, etc, and are configured
  in the Function message. The expected arguments and return value will be
  dictated by the FunctionType, but we don't (currently) check or enforce that.
  We expect that the module we choose (based on the functionStatement field)
  will have the appropriate function (name based on the FunctionType enum) and
  handle arguments / return correctly.
  """
  funcname = protos.Function.FunctionType.Name(function_type).lower()
  mod = HANDLER_MODULE_MAP[function.WhichOneof('functionStatement')]
  func = getattr(mod, funcname)
  return func(cfg, function, *args, **kwargs)
