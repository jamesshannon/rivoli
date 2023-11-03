""" Validation handler helpers.
Classes, datatypes, and functions in this file should be used by validation
handlers, including 3rd party handlers.
"""
from __future__ import annotations
import collections
from datetime import datetime
from datetime import timezone
import enum
import functools
import typing as t

from rivoli import protos
from rivoli.function_helpers import exceptions
from rivoli.utils import processing

TCallable = t.TypeVar("TCallable", bound=t.Callable)

class DataType(enum.Enum):
  """ Parameter types """
  STRING = protos.Function.STRING
  INTEGER = protos.Function.INTEGER
  FLOAT = protos.Function.FLOAT
  DICT = protos.Function.DICT

class FunctionType(enum.Enum):
  """ Function types """
  FIELD_VALIDATION = protos.Function.FIELD_VALIDATION
  RECORD_VALIDATION = protos.Function.RECORD_VALIDATION
  RECORD_UPLOAD = protos.Function.RECORD_UPLOAD
  RECORD_UPLOAD_BATCH = protos.Function.RECORD_UPLOAD_BATCH


class Field(t.NamedTuple):
  """ Fields are part of the Record and passed between functions. """
  key: str
  """ Key within the record. """
  typ: DataType = DataType.STRING
  """ Expected type. Data will be coerced, if possible. """
  out_ephemeral: bool = False
  """ Output fields only: This is an ephemeral field; delete after validation.
  """

class Record(collections.UserDict[str, t.Any]):
  """ Abstraction of a database record. Attributes are record's key/values.
  The key/values are imported from the file, and possibly modified in prior
  steps.
  """
  def __init__(self, record: protos.Record, record_type: protos.RecordType,
      fields_field: str | None, file_tags: dict[str, str]):
    super().__init__()

    self.id = record.id # pylint: disable=invalid-name
    """ Rivoli Record ID """
    self.updated_record = record
    """ Raw Record message """

    self.orig_record = protos.Record()
    """ Raw Record message """

    self.record_type = record_type
    """ Detected RecordType message for this Record """
    self.tags = file_tags
    """ Dict of parsed tags from Partner + File """

    # Duplicate the record (which is now a reference to updated_record) to the
    # orig_record property
    self.orig_record.CopyFrom(record)

    # Now that orig_record is a copy, make modifications to updated_record
    del self.updated_record.recentErrors[:]

    # The field values mapping will have a different name depending on the
    # step (e.g., parsedFields, validatedFields)
    if fields_field:
      self.update(dict(getattr(record, fields_field)))

  def coerce_fields(self, fields: t.Sequence[protos.Function.Field]) -> None:
    """ Coerce the fields to the Function's desired type. """
    self.update(processing.coerce_record_fields(self, fields))

  def get_record_or_tag(self, key: str) -> str:
    """ Get item from record and fall back to the partner + file tags.
    Returns KeyError if key is not found in either.
    """
    try:
      return self[key]

    except KeyError:
      pass

    return self.tags[key]

  def __bool__(self) -> bool:
    return True

def register_func(function_type: FunctionType, deprecated: bool = False,
    function_id: t.Optional[str] = None, tags: list[str] = None,
    fields_in: list[Field] = None, fields_out: list[Field] = None):
  """ Register a handler function.
  Registered functions can be scanned-for and inserted into the application.
  `fields_in` should be used for any record-level function to declare the
  expected record fields, and `fields_out` should be used where the function
  returns a dict (ie, record validations). Where `fields_in` is provided but
  not `fields_out` and a dict is returned, then `fields_out` will have the same
  values as `fields_in`.
  """
  # pyright: reportGeneralTypeIssues=false, reportUnknownVariableType=false
  # pylint: disable=protected-access
  def wrapped(func: TCallable) -> TCallable:
    @functools.wraps(func)
    def wrapped_f(*args: t.Any, **kwargs: t.Any) -> t.Any:
      return func(*args, **kwargs)

    wrapped_f._function_type = function_type
    wrapped_f._deprecated = deprecated

    wrapped_f._function_id = function_id
    wrapped_f._tags = tags or []

    wrapped_f._fields_in = fields_in or []
    wrapped_f._fields_out = fields_out or []
    return wrapped_f

  return wrapped

def parse_iso_datetime(value: str) -> datetime:
  """ Parse ISO datetime to a python datetime. """
  try:
    dtime = datetime.fromisoformat(value)

    # assume that if timezone wasn't specified then it was UTC
    if not dtime.tzinfo:
      dtime = dtime.replace(tzinfo=timezone.utc)

    return dtime
  except ValueError:
    raise exceptions.ValidationError( # pylint: disable=raise-missing-from
        f'Invalid isoformat string: {value}')

def parse_iso_datetime_to_timestamp(value: str, as_ms: bool = False) -> int:
  """ Parse ISO datetime as a unix epoch timestamp. """
  return int(parse_iso_datetime(value).timestamp() * (1000 if as_ms else 1))
