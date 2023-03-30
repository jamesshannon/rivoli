from __future__ import annotations
import abc
import base64
import typing as t

from google.protobuf import message

from rivoli import protos

# Record ID is b85(object_id) + b85(4 byte int)

IdType = t.Union[bytes, str, int]

class IDCodec(abc.ABC):
  pass


class Wrapper():
  collection = ''
  msg_type = None
  id_type = 'objectid'

  def __init__(self, msg: message.Message):
    self.msg = msg

  @classmethod
  def get_one(id: IdType) -> Wrapper:


  @property
  def c_id_str(self) -> str:
    return self.msg.id

  def c_id_b85(self) -> str:
    return ''

  @c_id_str.setter
  def c_id_str(self, value: str):
    self.msg.id = str

  def __getattribute__(self, __name: str) -> Any:
    return getattr(self.msg, __name)

  def c_id_filter(self) => Any:


  def c_get_update_obje(self) -> Any:
    pass

def User(Wrapper):



class File(Wrapper):
  def __init__(self, file_record: protos.File) -> None:

    self.file = file_record

  @property
  def record_id_regex(self):
    return {'_id': {'$regex': f'^{self.file.id}-'}}

  def to_dict(self):

