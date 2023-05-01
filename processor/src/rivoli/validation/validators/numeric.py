""" Validation helpers for type validation and modification. """
from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers
from rivoli.validation import types

# pylint: disable=raise-missing-from

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def is_integer(value: str) -> str:
  """ Validate that the value can be converted to an integer. """
  types.to_integer(value)
  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def is_float(value: str) -> str:
  """ Validate that the value can be converted to an integer. """
  types.to_float(value)
  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def is_greater_than_equal_to(value: str, min_value: float) -> str:
  """ Validate that the value is numeric and at least a number. """
  valflt = types.to_float(value)
  if valflt < min_value:
    raise exceptions.ValidationError(f'{value} is less than {min_value}')

  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def is_less_than_equal_to(value: str, max_value: float) -> str:
  """ Validate that the value is numeric and at most a number. """
  valflt = types.to_float(value)
  if valflt > max_value:
    raise exceptions.ValidationError(f'{value} is greater than {max_value}')

  return value
