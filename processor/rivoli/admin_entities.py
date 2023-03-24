""" Entities from mongodb. """
import typing as t

from rivoli.protobson import bson_format

from rivoli import db
from rivoli import protos

DB = db.get_db()

def get_all_partners() -> dict[str, protos.Partner]:
  cursor = DB.partners.find()
  return {partner.id: partner for partner in
          [bson_format.to_proto(protos.Partner, doc) for doc in cursor]}

def get_partner(partner_id: str) -> protos.Partner:
  return get_all_partners()[partner_id]

def get_all_filetypes() -> dict[str, protos.FileType]:
  return {filetype.id: filetype for partner in get_all_partners().values()
          for filetype in partner.fileTypes}

def get_filetype(filetype_id: str) -> protos.FileType:
  return get_all_filetypes()[filetype_id]

def get_functions_by_ids(function_ids: t.Iterable[str]) -> dict[str, protos.Function]:
  fltr = {'_id': {'$in': list(function_ids)}}
  cursor = DB.functions.find(fltr)
  return {function.id: function for function in
          [bson_format.to_proto(protos.Function, doc) for doc in cursor]}
