""" Module responsible for functions that call the actual validation. """
import importlib
import inspect
import typing as t

from rivoli import protos

from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers

PARAM_TYPE_CONVERTERS: dict[str, t.Callable[[str], t.Any]] = {
  'integer': int,
  'float': float,
  'bool': lambda val: val.upper() in ('TRUE', ),
  'string': str,
}

FunctionInputValue = t.Union[
    str,
    helpers.Record,
    list[helpers.Record]
]

Parameters = list[t.Union[str, int, float, bool, protos.Function]]
""" List of parameter values which might be passed to a function. """

def _call_python_function(cfg: protos.FunctionConfig,
    function_msg: protos.Function, value: FunctionInputValue
    ) -> t.Union[str, dict[str, str]]:
  """ Call a python function.
  """
  fq_fn_pieces = function_msg.pythonFunction.split('.')
  # Remove the function name and leave the package + module
  module_name = '.'.join(fq_fn_pieces[:-1])

  try:
    mod = importlib.import_module(module_name)
  except ModuleNotFoundError:
    # This might be something more serious than a ConfigurationError,
    # like a CompilationError or something?
    raise exceptions.ConfigurationError( # pylint: disable=raise-missing-from
      f'Python function module {module_name} could not be imported')

  # Get the function from the module
  func: t.Callable[[t.Any], str] = getattr(mod, fq_fn_pieces[-1])
  # Create parameters list from the Function and FunctionConfig messages
  # Parameters are set by the user in the Config message
  fn_parameters = _create_parameters(func, cfg, function_msg)

  # Call the python function and return
  return func(value, *fn_parameters)

def field_validation(cfg: protos.FunctionConfig,
    function_msg: protos.Function, value: str) -> str:
  """ Validate a specific field with an external function.
  "Validation" could also modify the field. We return the function result
  regardless.
  """
  return str(_call_python_function(cfg, function_msg, value))

def record_validation(cfg: protos.FunctionConfig,
    function_msg: protos.Function, record: helpers.Record) -> dict[str, str]:
  """ Validate an entire record with an external function.
  These functions will run after all the field-level validations and only if
  those validations did not raise an exception.
  "Validation" could also modify the record. We return the entire record dict.
  """
  result = _call_python_function(cfg, function_msg, record)

  if not isinstance(result, dict):
    raise TypeError((f'Python function returned a {type(result)} instead '
                     'of a dict'))

  return result

def record_upload(cfg: protos.FunctionConfig, function_msg: protos.Function,
    record: helpers.Record) -> str:
  """ Upload a record, probably via an API. """
  result = _call_python_function(cfg, function_msg, record)

  return str(result)

def record_upload_batch(cfg: protos.FunctionConfig,
    function_msg: protos.Function, records: list[helpers.Record]) -> str:
  """ Upload a multiple records, probably via an API. """
  result = _call_python_function(cfg, function_msg, records)

  return str(result)

def _create_parameters(func: t.Callable[[t.Any], str],
    cfg: protos.FunctionConfig, funcmsg: protos.Function
    ) -> Parameters:
  """ Create a list of parameter values. """
  # The function might take parameters, in which case those are defined by the
  # callable and parameter values are provided by the instance.
  params: Parameters = []

  # Provided parameters should equal # of required parameters. No defaults.
  assert len(funcmsg.parameters) == len(cfg.parameters)

  # All parameters are stored as strings, do necessary conversion
  for param_val, param in zip(cfg.parameters, funcmsg.parameters):
    typ = protos.Function.DataType.Name(param.type).lower()
    params.append(PARAM_TYPE_CONVERTERS[typ](param_val))

  sig = inspect.signature(func)
  if len(sig.parameters.keys()) > len(cfg.parameters) + 1:
    # For now we just assume that if there is an additional parameter it's for
    # the callable
    params.append(funcmsg)

  return params
