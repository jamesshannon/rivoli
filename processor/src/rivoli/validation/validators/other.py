""" Other validators. """
from datetime import datetime

from dateutil import parser

from rivoli.function_helpers import exceptions
from rivoli.function_helpers import helpers

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def parse_date(value: str, date_format: str = '') -> str:
  """ Parse date(time) and return ISO-formatted date.

  If `date_format` is not provided then `python-dateutil` is used, and it may
  make incorrect assumptions (such as reversing day and month). For this reason,
  it is recommended to provide a `date_format`, in which case the input is
  parsed according to Python's [`strptime` format
  codes](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior).
  """
  if not value:
    return value

  try:
    if date_format:
      return datetime.strptime(value, date_format).isoformat()

    # Clear an "empty" time value -- this will be parsed without a problem
    return parser.parse(value).isoformat().replace('T00:00:00', '')
  except ValueError as exc:
    raise exceptions.ValidationError( # pylint: disable=raise-missing-from
        str(exc), summary='Invalid Date Format')

@helpers.register_func(helpers.FunctionType.FIELD_VALIDATION)
def clear_field_if_value(value: str, value_to_clear: str) -> str:
  """ Clear (empty) a field if it contains a provided value.
  For example, fields with "N/A" can be emptied out for future functions
  which accept an empty field. The value must match exactly.
  """
  if value == value_to_clear:
    return ''

  return value
