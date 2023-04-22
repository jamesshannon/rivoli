""" Validation helpers for type validation and modification. """
import re
import typing as t

from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers

# pylint: disable=raise-missing-from

def _regexp_flags(ignore_case: bool) -> int:
  """ Generate regexp flags. """
  return re.IGNORECASE if ignore_case else 0

def _regexp_match(value: str, pattern: str, full_match: bool = True,
    error_msg: t.Optional[str] = None, flags: int = 0) -> re.Match[str]:
  func = re.fullmatch if full_match else re.search

  match = func(pattern, value, flags)
  if not match:
    error_msg = error_msg or f'{value} did not match the pattern {pattern}'
    raise exceptions.ValidationError(error_msg)

  return match

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def match_full(value: str, pattern: str, ignore_case: bool = True) -> str:
  """ Validate that the entire input matches a pattern using regexp.
  Equivalent to ^pattern$. Uses the Python regexp parser. """
  _regexp_match(value, pattern, True, flags=_regexp_flags(ignore_case))
  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def match_part(value: str, pattern: str, ignore_case: bool = True) -> str:
  """ Validate that some part of the input matches a pattern using regexp.
  Uses the Python regexp parser. """
  _regexp_match(value, pattern, True, flags=_regexp_flags(ignore_case))
  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def regexp_extract(value: str, pattern: str, ignore_case: bool = True) -> str:
  """ Return a subset of the string based on a pattern, or an empty string.
  Uses the Python regexp parser. Returns the entire match if there is no
  grouping (`()`) in the pattern, the first group if groups are used, or an
  empty string if there was no match.
  """
  try:
    match = _regexp_match(value, pattern, False,
                          flags=_regexp_flags(ignore_case))
  except exceptions.ValidationError:
    return ''

  # Return the first sub-match group if it exists, otherwise return the first
  # group, which is the entire match.
  try:
    return match.group(1)
  except IndexError:
    return match.group(0)

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def is_not_empty(value: str) -> str:
  """ Validate that the input is not empty. """
  if not value:
    raise exceptions.ValidationError('Value is empty')

  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def length_is_at_least(value: str, min_length: int) -> str:
  """ Validate that the string is at least a number of characters. """
  if len(value) < min_length:
    raise exceptions.ValidationError(
        f'{value} is shorter than {min_length} characters')
  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def length_is_at_most(value: str, max_length: int) -> str:
  """ Validate that the string is at most a number of characters. """
  if len(value) > max_length:
    raise exceptions.ValidationError(
        f'{value} is longer than than {max_length} characters')
  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def length_is(value: str, length: int) -> str:
  """ Validate that the string length is exactly a number of characters. """
  if len(value) != length:
    raise exceptions.ValidationError(f'{value} is not {length} characters')

  return value

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def is_hex(value: str) -> str:
  """ Validate that the input is only hex characters. """
  _regexp_match(value, r'[A-F0-9]*', True,
      f'{value} is not hexadecimal ([A-F0-9]*)', re.IGNORECASE)
  return value
