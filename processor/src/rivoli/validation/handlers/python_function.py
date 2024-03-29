""" Module responsible for functions that call the actual validation. """
import enum
import importlib
import inspect
import typing as t

from rivoli import protos

from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers
from rivoli.validation import typing

PARAM_TYPE_CONVERTERS: dict[str, t.Callable[[str], t.Any]] = {
  'INTEGER': int,
  'FLOAT': float,
  'BOOLEAN': lambda val: val.upper() in ('TRUE', ),
  'STRING': str,
}

FunctionInputValue = t.Union[
    str,
    helpers.Record,
    list[helpers.Record]
]

Parameters = list[t.Union[str, int, float, bool, protos.Function, enum.EnumMeta]]
""" List of parameter values which might be passed to a function. """

# What to do with native Python exceptions? The upstream functions will capture
# our custom exceptions but stop file execution on native Python exceptions.
# This is probably good for things like SyntaxError but causes problems for
# things like KeyError which should probably only affect the Record. We offer
# an exceptions.raise_validation_error() wrapper, but should we do that
# automatically?
# Probably not?

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
    function_msg: protos.Function, record: helpers.Record
    ) -> typing.ValRecordReturn:
  """ Validate an entire record with an external function.
  These functions will run after all the field-level validations and only if
  those validations did not raise an exception.
  "Validation" could also modify the record. We return the entire record dict.
  """
  result = _call_python_function(cfg, function_msg, record)

  if not typing.is_typing_instance(result, typing.ValRecordReturn):
    raise TypeError((f'Python function returned a {type(result)} instead '
                     f'of {typing.ValRecordReturn}'))

  return t.cast(typing.ValRecordReturn, result)

def record_upload(cfg: protos.FunctionConfig, function_msg: protos.Function,
    records: list[helpers.Record]) -> str:
  """ Upload a single record, probably via an API. """
  result = _call_python_function(cfg, function_msg, records[0])

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

  sig = inspect.signature(func)

  # All parameters are stored as strings, do necessary conversion
  for idx, (param_val, param) in enumerate(zip(cfg.parameters,
                                               funcmsg.parameters), start=1):
    typ = protos.Function.DataType.Name(param.type)
    if typ == 'ENUM':
      # Need to convert the string an instance of the required enum
      func_param = list(sig.parameters.values())[idx]
      assert isinstance(func_param.annotation, enum.EnumMeta)
      # We assume all enum values are UPPERCASE and that this does not introduce
      # ambiguity
      params.append(func_param.annotation[param_val.upper()])
    else:
      params.append(PARAM_TYPE_CONVERTERS[typ](param_val))

  if len(sig.parameters.keys()) > len(cfg.parameters) + 1:
    # For now we just assume that if there is an additional parameter it's for
    # the callable
    params.append(funcmsg)

  return params
