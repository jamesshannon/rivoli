#!/usr/bin/env python
""" CLI to generate a callable configuration file from module inspection. """
import argparse
import enum
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
from rivoli.validation import typing
from rivoli import protos

# This dict maps from the inspect module's Parameter instance(s) to a protobuf
# enum. The inspect module signature doesn't return a `type` but instead returns
# a GenericAlias, so it's best to get the name attribute.
PYTHON_INSPECT_TYPE_MAP = {
  'str': protos.Function.STRING,
  'int': protos.Function.INTEGER,
  'float': protos.Function.FLOAT,
  'bool': protos.Function.BOOLEAN,
  'dict': protos.Function.DICT,
}

class _Param(t.NamedTuple):
  """ Python function value parameter. """
  name: str
  typ: type

class _Signature(t.NamedTuple):
  """ Python function expected signature. """
  params: list[_Param]
  return_: t.TypeAlias

FUNCTION_TYPE_SIGNATURE_REQUIREMENTS: dict[helpers.FunctionType, _Signature] = {
  helpers.FunctionType.FIELD_VALIDATION:
      _Signature([_Param('value', typing.ValFieldInput)],
                 typing.ValFieldReturn),
  helpers.FunctionType.RECORD_VALIDATION:
      _Signature([_Param('record', typing.ValRecordInput)],
                 typing.ValRecordReturn),
  helpers.FunctionType.RECORD_UPLOAD:
      _Signature([_Param('record', typing.UploadRecordInput)],
                 typing.UploadRecordReturn),
  helpers.FunctionType.RECORD_UPLOAD_BATCH:
      _Signature([_Param('records', typing.UploadBatchRecordInput)],
                 typing.UploadBatchRecordReturn),
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

def is_types_in_types(got: type, expected: type) -> bool:
  """ Return whether the gotten type(s) are a subset of expected type(s).
  A function might return one or more types (via a Union). All of those types
  should be in the expected type(s); the function should not have have any
  types that are not pre-defined.
  """
  def get_type_set(type_: type) -> set[type]:
    return set(t.get_args(type_)
               if isinstance(type_, t._UnionGenericAlias) else [type_])

  gots = get_type_set(got)
  exps = get_type_set(expected)

  return gots.issubset(exps)

def get_parameters(sig: inspect.Signature, function_type: helpers.FunctionType
    ) -> list[protos.Function.Parameter]:
  """ Generate proto Parameters from the function signature. """
  parameters: list[protos.Function.Parameter] = []

  reqs = FUNCTION_TYPE_SIGNATURE_REQUIREMENTS[function_type]

  sig_params: list[inspect.Parameter] = list(sig.parameters.values())
  param = sig_params[0]

  param_req = reqs.params[0]

  if not (param.name == param_req.name
          and is_types_in_types(param.annotation, param_req.typ)):
    raise ValueError(('First parameter is invalid. Expected '
                      f'`{param_req.name}: {param_req.typ}` but got '
                      f'`{param.name}: {param.annotation.__name__}`'))

  # Confirm that the function returns a str
  return_typ = sig.return_annotation if sig.return_annotation else None
  if not is_types_in_types(return_typ, reqs.return_):
    raise ValueError(('Return annotation is invalid. Expected '
                      f'`{reqs.return_}` but got `{return_typ}`'))

  # Now parse any additional parameters
  for param in sig_params[1:]:
    default = (None if param.default == inspect.Parameter.empty
               else param.default)

    if isinstance(param.annotation, enum.EnumMeta):
      # The parameter type is an enum, which means that any default is an enum
      # Function handlers will receive enums as the string value (aka name).
      parameters.append(protos.Function.Parameter(
        variableName=param.name,
        type=protos.Function.ENUM,
        enumValues=[e.name for e in param.annotation],
        defaultValue=t.cast(enum.Enum, default).name if default else None
      ))

    else:
      parameters.append(protos.Function.Parameter(
          variableName=param.name,
          type=PYTHON_INSPECT_TYPE_MAP[param.annotation.__name__],
          defaultValue=str(default) if default is not None else None,
      ))

  return parameters

def get_fields(fields: list[helpers.Field]) -> list[protos.Function.Field]:
  """ Get the list of defined fields and return list of proto fields.
  Input and output fields are defined in the python register_func() decorator,
  converted to a proto message, and saved to the database. Fields are part of
  the parsed record (as opposed to function parameters).
  """
  return [protos.Function.Field(key=field.key, type=field.typ.value,
                                isOutputEphemeral=field.out_ephemeral)
          for field in fields]

def get_callables(args: argparse.Namespace) -> list[protos.Function]:
  """ Generate proto Callables from all modules a directory. """
  callables: list[protos.Function] = []

  validators_base = args.module
  validators_base_mod = importlib.import_module(validators_base)
  validators_base_path = pathlib.Path(validators_base_mod.__path__[0])

  print((f'Searching for sub-modules of {validators_base} '
         f'in {validators_base_path}'))

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

            fieldsIn=get_fields(symbol._fields_in),
            fieldsOut=get_fields(symbol._fields_out),

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
