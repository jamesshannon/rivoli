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
  # Note that calling this will
  if not dct:
    return msgtype()

  dct = copy.deepcopy(dct)

  if '_id' in dct:
    if isinstance(dct['_id'], bson.ObjectId):
      dct['_id'] = str(dct['_id'])

    dct['id'] = dct.pop('_id')


  return protobuf_dict.dict_to_protobuf(msgtype, dct, TYPE_MAP_TO_PROTO)

def from_proto(msg: message.Message, ordered: bool = False) -> dict[str, t.Any]:
  """ If ordered, then we use an OrderedDict which will output items in the
   field order """
  dct = protobuf_dict.protobuf_to_dict(msg, TYPE_MAP_FROM_PROTO,
                                       USE_ENUM_LABELS, ordered=ordered)

  # Do pymongo specific stuff
  if 'id' in dct:
    dct['_id'] = dct.pop('id')

    if ordered:
      # Move _id back to the first to the first item of the dict
      t.cast(collections.OrderedDict[str, t.Any], dct).move_to_end('_id', False)

  return dct

def get_update_map(msg: message.Message, fields: list[str],
    list_append_fields: t.Optional[list[str]] = None) -> dict[str, t.Any]:
  update_map: dict[str, t.Any] = collections.defaultdict(dict)
  dct = from_proto(msg)

  # Only support direct children for now
  for field in fields:
    assert field != 'id'

    if field in dct:
      update_map['$set'][field] = dct[field]
    else:
      update_map['$unset'][field] = ""

  for field in (list_append_fields or []):
    if field in dct:
      assert isinstance(dct[field], list)
      update_map['$addToSet'][field] = {'$each': dct[field]}

  return dict(update_map)

def get_filter_map(msg: message.Message, fields: list[str]
    ) -> dict[str, t.Any]:
  # convert any instances of 'id' to '_id' in the list
  fields = ['_id' if field == 'id' else field for field in fields]
  dct = from_proto(msg)
  return {field: dct[field] for field in fields}

def get_update_args(msg: message.Message, update_fields: list[str],
    filter_fields: t.Optional[list[str]] = None
    ) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
  """ Get tuple of (filter, update_map) to pass to mongo functions.
  First item is the filter map using, by default, the Message's ID.
  Second item is the update map with fields from the Message to (un)set.
  """
  filter_fields = filter_fields or ['id']

  return (get_filter_map(msg, filter_fields),
          get_update_map(msg, update_fields))

def now() -> int:
  """ Now timestamp compatible with protobufs (ie, uint32) """
  return int(time.time())

def hex_id() -> str:
  """ Hex representation of BSON ObjectID. """
  return str(bson.ObjectId())
