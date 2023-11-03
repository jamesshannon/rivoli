""" Entities from mongodb. """
import typing as t

from rivoli.protobson import bson_format

from rivoli import db
from rivoli import protos

def get_all_partners() -> dict[str, protos.Partner]:
  """ Get mapping of all Partners by Partner ID. """
  cursor = db.get_db().partners.find()
  return {partner.id: partner for partner in
          [bson_format.to_proto(protos.Partner, doc) for doc in cursor]}

def get_partner(partner_id: str) -> protos.Partner:
  """ Get a single Partner by ID. """
  return get_all_partners()[partner_id]

def get_all_filetypes() -> dict[str, protos.FileType]:
  """ Get mapping of all FileTypes by FileType ID. """
  # This is all FileTypes for all Partners and will quickly need to be
  # optimized.
  return {filetype.id: filetype for partner in get_all_partners().values()
          for filetype in partner.fileTypes}

def get_filetype(filetype_id: str) -> protos.FileType:
  """ Get a single FileType by ID. """
  return get_all_filetypes()[filetype_id]

def get_functions_by_ids(function_ids: t.Iterable[str]
    ) -> dict[str, protos.Function]:
  """ Get mapping of functions from function IDs. """
  fltr = {'_id': {'$in': list(function_ids)}}
  cursor = db.get_db().functions.find(fltr)
  return {function.id: function for function in
          [bson_format.to_proto(protos.Function, doc) for doc in cursor]}

def get_file_entities(id_: int
    ) -> t.Tuple[protos.File, protos.Partner, protos.FileType]:
  """ Get a File and its associated entities. """
  file = db.get_one_by_id('files', id_, protos.File)
  partner = get_partner(file.partnerId)
  filetype = get_filetype(file.fileTypeId)

  return (file, partner, filetype)
