""" Utils for file and record processing. """
import json
import typing as t

from rivoli import protos
from rivoli.function_helpers import exceptions

def _convert_to_dict(input_: t.Any) -> dict[str, t.Any]:
  """ Possibly convert a JSON string to a dict. """
  if isinstance(input_, dict):
    return t.cast(dict[str, t.Any], input_)

  try:
    if isinstance(input_, str):
      return json.loads(input_)
  except json.decoder.JSONDecodeError:
    pass

  raise exceptions.ConfigurationError(
    f'Input of type {type(input_)} could not be converted to a dict')


ConversionDictType = dict[
    protos.Function.DataType, t.Callable[[t.Any], t.Any]]
""" Conversion Dict Type
The key is the proto type enum and the value is a function which
will return the appropriate type (or raise an exception if not possible).
"""

PROTO_TYPES_CONVERSIONS: ConversionDictType = {
  protos.Function.STRING: str,
  protos.Function.INTEGER: int,
  protos.Function.FLOAT:  float,
  protos.Function.BOOLEAN: bool,
  protos.Function.DICT: _convert_to_dict,
}

def coerce_record_fields(values: t.MutableMapping[str, t.Any],
    fields: t.Sequence[protos.Function.Field]) -> t.MutableMapping[str, t.Any]:
  """ Coerce record fields to the Function's desired type. """
  for field in fields:
    if field.key not in values:
      raise exceptions.ConfigurationError(f'{field.key} not available')

    conv = PROTO_TYPES_CONVERSIONS[field.type]
    try:
      values[field.key] = conv(values[field.key])
    except ValueError as exc:
      raise exceptions.ConfigurationError(str(exc))

  return values

def prep_record_fields_for_db(values: t.MutableMapping[str, t.Any],
    fields: t.Sequence[protos.Function.Field]) -> t.MutableMapping[str, t.Any]:
  """ Coerce fields to strings and remove ephemeral fields for mongodb. """
  # First remove any ephemeral items
  for field in fields:
    if field.isOutputEphemeral:
      del values[field.key]

  # Ensure all record fields are strings
  for key, value in values.items():
    if isinstance(value, dict):
      values[key] = json.dumps(value)
    else:
      values[key] = str(value)

  return values
