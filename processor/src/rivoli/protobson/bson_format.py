""" Convert to/from proto messages/dicts and filter and update MongoDB.
Protobuf's built-in JSON conversion drops a lot of datatype resolution; these
functions provide a layer to a module which converts to/from dicts and maintains
native-ish datatypes.
Also, some methods to set up mongodb filtering and updating dicts.
"""
import collections
import copy
import time
import typing as t

import bson
from google.protobuf import message

from rivoli.protobson import protobuf_dict

USE_ENUM_LABELS = False

TYPE_MAP_FROM_PROTO = (protobuf_dict.TYPE_CALLABLE_MAP |
                       {'type_object_id': bson.ObjectId})
_ObjectIdConverter: t.Callable[[t.Any], t.Any] = lambda oid: oid.binary
TYPE_MAP_TO_PROTO = (protobuf_dict.REVERSE_TYPE_CALLABLE_MAP |
                     {'ObjectId': _ObjectIdConverter})
M = t.TypeVar('M', bound=message.Message)

def to_proto(msgtype: type[M], dct: t.Optional[dict[str, t.Any]]) -> M:
  """ Convert from dict to a proto message. """
  if not dct:
    return msgtype()

  dct = copy.deepcopy(dct)

  if '_id' in dct:
    if isinstance(dct['_id'], bson.ObjectId):
      dct['_id'] = str(dct['_id'])

    dct['id'] = dct.pop('_id')

  return protobuf_dict.dict_to_protobuf(msgtype, dct, TYPE_MAP_TO_PROTO)

def from_proto(msg: message.Message, ordered: bool = False,
    rename_id: bool = True) -> dict[str, t.Any]:
  """ Convert from a proto message to a dict.
  If ordered=True, then we use an OrderedDict which will output items in the
  field order. """
  dct = protobuf_dict.protobuf_to_dict(msg, TYPE_MAP_FROM_PROTO,
                                       USE_ENUM_LABELS, ordered=ordered)

  # Do pymongo specific stuff
  if rename_id and 'id' in dct:
    dct['_id'] = dct.pop('id')

    if ordered:
      # Move _id back to the first to the first item of the dict
      t.cast(collections.OrderedDict[str, t.Any], dct).move_to_end('_id', False)

  return dct

def _get_from_nested_dict(key: str, dct: dict[str, t.Any]) -> t.Any:
  """ Helper function to get from nested dicts using dot-notated key.
  key='x.y.z' will return the entry for z inside of the y dict inside of the x
  dict. Raises a KeyError if the entry doesn't exist.
  NB: If the x dict has an entry for 'y.z' then that will be returned instead.
  """
  if key in dct:
    # Full (remaining) key. Could be be ambiguous and this prioritizes
    # (matching) keys with full dot notation
    return dct[key]

  # First item plus (rest of string, or None)
  k, rest = (key.split('.', 1) + [None])[:2]

  # Whether or not there are remaining items left, if the next key is not in
  # the dct then raise an error.
  if k not in dct:
    raise KeyError(k)

  # If there are no remaining keys then return this entry.
  if not rest:
    return dct[k]

  return _get_from_nested_dict(rest, dct[k])

def get_update_map(msg: message.Message, fields: t.Optional[list[str]] = None,
    list_append_fields: t.Optional[list[str]] = None) -> dict[str, t.Any]:
  """ Create a mongodb update map based on message and fields-to-update.
  Specified fields which are set in the message (and thus generated in the
  dictionary-creation, which is sparse) are $set in mongodb. Fields not set
  in the message are explicitly $unset. Fields can refer to nested values
  using dot-notation. Fields in `list_append_fields` are added to a list
  field within the mongodb document.
  """
  update_map: dict[str, t.Any] = collections.defaultdict(dict)
  dct = from_proto(msg)

  for field in (fields or []):
    assert field != 'id'

    try:
      update_map['$set'][field] = _get_from_nested_dict(field, dct)
    except KeyError:
      update_map['$unset'][field] = ""

  for field in (list_append_fields or []):
    if field in dct:
      # The field should be a list in its own right -- $each is the equivalent
      # of a_list.extend(...)
      assert isinstance(dct[field], list)
      update_map['$addToSet'][field] = {'$each': dct[field]}

  return dict(update_map)

def get_filter_map(msg: message.Message, fields: list[str]
    ) -> dict[str, t.Any]:
  """ Create a MongoDB filter map based on message and fields-to-filter. """
  # Convert any instances of 'id' to '_id' in the list
  fields = ['_id' if field == 'id' else field for field in fields]
  dct = from_proto(msg)
  return {field: dct[field] for field in fields}

def get_update_args(msg: message.Message,
    update_fields: t.Optional[list[str]] = None,
    filter_fields: t.Optional[list[str]] = None,
    list_append_fields: t.Optional[list[str]] = None
    ) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
  """ Get tuple of (filter, update_map) to pass to mongo functions.
  First item is the filter map using, by default, the Message's ID.
  Second item is the update map with fields from the Message to (un)set.
  """
  filter_fields = filter_fields or ['id']

  return (get_filter_map(msg, filter_fields),
          get_update_map(msg, update_fields, list_append_fields))

def get_array_item_update_args(msg: message.Message, field: str,
    submsg: message.Message) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
  """ Get tuple to update a specific sub-doc in an array in a mongo doc. """
  # The semantics for filering and updating a specific sub-document in an array
  # are such that this update must happen separately from any updates to the
  # rest of the document.

  # Array items must have their own ID to be updated by this function.
  # `_id` is only at the document level -- if array documents have an ID at all
  # then they use `id`.
  filter_: dict[str, str] = {'_id': msg.id, f'{field}.id': submsg.id}

  # Only support $set
  return (filter_,
          { "$set": { f'{field}.$': from_proto(submsg, rename_id=False) } })

def now() -> int:
  """ Now timestamp compatible with protobufs (ie, uint32) """
  return int(time.time())

def hex_id() -> str:
  """ Hex representation of BSON ObjectID. """
  return str(bson.ObjectId())
