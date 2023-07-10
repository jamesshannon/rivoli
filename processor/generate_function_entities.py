#!/usr/bin/env python
""" CLI to generate a callable configuration file from module inspection. """
import argparse
import hashlib
import importlib
import inspect
import json
import os
import pathlib
import sys
import types
import typing as t

from rivoli.function_helpers import helpers
from rivoli.protobson import bson_format
from rivoli import protos

PYTHON_INSPECT_TYPE_MAP = {
  'str': protos.Function.STRING,
  'int': protos.Function.INTEGER,
  'float': protos.Function.FLOAT,
  'bool': protos.Function.BOOLEAN,
}

Param = t.Tuple[str, t.Type[t.Any]]
Return = t.Union[list[t.Type[t.Any]], t.Type[t.Any]]

FUNCTION_TYPE_SIGNATURE_REQUIREMENTS: \
    dict[helpers.FunctionType, t.Tuple[Param, Return]] = {
  helpers.FunctionType.FIELD_VALIDATION: (('value', str), str),
  helpers.FunctionType.RECORD_VALIDATION: (('record', helpers.Record), dict[str, str]),
  helpers.FunctionType.RECORD_UPLOAD: (('record', helpers.Record), str),
  helpers.FunctionType.RECORD_UPLOAD_BATCH: (('records', list[helpers.Record]),
                                        str),
}

def parse_args() -> argparse.Namespace:
  """ Argparser for this file. """
  parser = argparse.ArgumentParser()
  parser.add_argument('output_file')
  parser.add_argument('--I', dest='include', default='.')
  parser.add_argument('--module', dest='module',
                      default='rivoli.validation.validators')

  return parser.parse_args()

def set_id(function: protos.Function):
  """ Sets the function ID from the first 24 characters of the MD5 hex.
  This provides ID stability based on "important" attributes, and also forces
  a new ID if those attributes are changed.
  """
  attributes = '|'.join([str(function.type), function.pythonFunction] +
                        [str(p.type) for p in function.parameters])
  function.id = hashlib.md5(attributes.encode('utf-8')).hexdigest()[:24]

def get_parameters(sig: inspect.Signature, function_type: helpers.FunctionType
    ) -> list[protos.Function.Parameter]:
  """ Generate proto Parameters from the function signature. """
  parameters: list[protos.Function.Parameter] = []

  reqs = FUNCTION_TYPE_SIGNATURE_REQUIREMENTS[function_type]

  sig_params: list[inspect.Parameter] = list(sig.parameters.values())
  # Check that the first parameter is value:str
  param = sig_params[0]

  if not (param.name == reqs[0][0] and param.annotation == reqs[0][1]):
    raise ValueError(('First parameter is invalid. Expected '
                      f'`{reqs[0][0]}: {reqs[0][1]}` but got '
                      f'`{param.name}: {param.annotation.__name__}`'))

  # Confirm that the function returns a str
  return_typ = sig.return_annotation if sig.return_annotation else None
  if not return_typ == reqs[1]:
    raise ValueError(('Return annotation is invalid. Expected '
                      f'`{reqs[1]}` but got `{return_typ}`'))

  # Now parse any additional parameters
  for param in sig_params[1:]:
    default = (None if param.default == inspect.Parameter.empty
               else str(param.default))
    parameters.append(protos.Function.Parameter(
        variableName=param.name,
        type=PYTHON_INSPECT_TYPE_MAP[param.annotation.__name__],
        defaultValue=default,
    ))

  return parameters

def get_callables(args: argparse.Namespace) -> list[protos.Function]:
  """ Generate proto Callables from all modules a directory. """
  callables: list[protos.Function] = []

  validators_base = args.module
  validators_base_mod = importlib.import_module(validators_base)
  validators_base_path = pathlib.Path(validators_base_mod.__path__[0])

  for file in validators_base_path.iterdir():
    if (not file.is_dir() and not file.name.startswith('_')
        and file.suffix == '.py'):
      module_name = f'{validators_base}.{file.stem}'
      print('Parsing', module_name, ': ', end='')

      module = importlib.import_module(module_name)

      for symbol_name in dir(module):
        symbol = getattr(module, symbol_name)
        if (not symbol_name.startswith('_')
            and isinstance(symbol, types.FunctionType)
            and hasattr(symbol, '_deprecated')
            and hasattr(symbol, '_function_type')):
          print(symbol_name, end=', ')

          full_function_name = f'{module_name}.{symbol_name}'

          # pylint: disable=protected-access
          # pyright: reportUnknownMemberType=false
          # pyright: reportGeneralTypeIssues=false
          # pyright: reportUnknownArgumentType=false
          deprecated = t.cast(bool, symbol._deprecated)
          function_type = t.cast(helpers.FunctionType,
                                 symbol._function_type)

          # Format the docstring as markdown. Markdown ignores most newlines so
          # double the first newline.
          docs = str(inspect.getdoc(symbol)).strip().replace('\n', '\n\n', 1)

          signature = inspect.signature(symbol)

          params = get_parameters(signature, function_type)

          function = protos.Function(
            active=True,
            isGlobal=True,
            isSystem=True,
            type=function_type.value,

            name=symbol_name,
            description=docs,

            tags=symbol._tags,

            pythonFunction=full_function_name,
            parameters=params,
          )

          if symbol._function_id:
            function.id = symbol._function_id
          else:
            set_id(function)

          callables.append(function)

      print('')

  return callables

if __name__ == '__main__':
  os.environ['RIVOLI_FUNCTION_PARSE'] = 'true'

  parsed = parse_args()

  # add include path to sys.path
  if parsed.include:
    sys.path.append(str(pathlib.Path(parsed.include).absolute()))

  calls = get_callables(parsed)
  with open(parsed.output_file, 'w', encoding='ascii') as fobj:
    json.dump([bson_format.from_proto(c, ordered=True) for c in calls],
              fobj, indent=2)
