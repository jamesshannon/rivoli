""" Validator parameter and return types and helpers. """
# Validator function signatures specify the types that the method *could* accept
# and will raise an exception if incompatible at runtime. For example, a
# validator that checks for a minimum numeric value would accept str, float, and
# int, with the assumption that the string can be converted and will try at
# runtime
import typing as t

from rivoli.validation import helpers

# pylint: disable=raise-missing-from

def to_integer(value: str) -> int:
  """ Modify value to an integer. """
  try:
    return int(value)
  except ValueError:
    raise helpers.ValidationError(f'{value} not an integer')

def to_float(value: str) -> float:
  """ Modify value to a float. """
  try:
    return float(value)
  except ValueError:
    raise helpers.ValidationError(f'{value} not a float')
