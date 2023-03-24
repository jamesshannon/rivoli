""" Hello """
import pathlib
import typing as t

from bson import objectid
import pymongo

from google.protobuf import json_format

MY_PATH = pathlib.Path(__file__).parent
DB_NAME = 'testdb'
CERT = MY_PATH.parent / 'X509-cert-8051024250932727866.pem'

MDB_CLIENT: pymongo.MongoClient[dict[str, t.Any]] = pymongo.MongoClient('mongodb+srv://cluster0.ndszdhz.mongodb.net/?authSource=$external',
    authMechanism="MONGODB-X509",
    tls=True,
    tlsCertificateKeyFile=str(CERT),
    compressors='zstd')
MDB_DB = MDB_CLIENT[DB_NAME]

def get_db():
  return MDB_DB

def get_next_id(collection: str) -> int:
  """ Return the next unused ID for a given collection. """
  response = get_db().counters.find_one_and_update(
      {'_id': str(collection)}, {'$inc': {'value': 1}},
      upsert=True, return_document=True)
  return response['value']

def int_to_byte_id(entity_id: t.Union[bytes, int], length: int = 4) -> bytes:
  if isinstance(entity_id, bytes):
    return entity_id

  return entity_id.to_bytes(length, byteorder='big', signed=False)
