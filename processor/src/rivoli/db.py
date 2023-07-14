""" Mongodb connection setup. """
import typing as t

from google.protobuf import message
import pymongo
from pymongo import database

from rivoli import config
from rivoli.protobson import bson_format

Msg = t.TypeVar('Msg', bound=message.Message)

_mongo_client: t.Optional[pymongo.MongoClient[dict[str, t.Any]]] = None
_mongo_db: database.Database[dict[str, t.Any]]

def get_db() -> database.Database[dict[str, t.Any]]:
  """ Return a mongodb database (client). """
  # pylint: disable=global-statement
  global _mongo_client
  global _mongo_db

  if _mongo_client is None:
    print('creating db')
    if config.get('MONGO_USERNAME') and config.get('MONGO_PASSWORD'):
      auth = f'{config.get("MONGO_USERNAME")}:{config.get("MONGO_PASSWORD")}'
      url = f'mongodb://{auth}@{config.get("MONGO_ENDPOINT")}'
      _mongo_client = pymongo.MongoClient(url, compressors='zstd')

    elif config.get('MONGO_CERT'):
      url = f'mongodb+srv://{config.get("MONGO_ENDPOINT")}/?authSource=$external'
      _mongo_client = pymongo.MongoClient(url, authMechanism="MONGODB-X509",
          tls=True, tlsCertificateKeyFile=config.get('MONGO_CERT'),
          compressors='zstd')
    else:
      raise ValueError('No valid mongodb config parameters')

    _mongo_db = _mongo_client[config.get('MONGO_DB')]

  return _mongo_db

def get_next_id(collection: str, offset: int = 0) -> int:
  """ Return the next unused ID for a given collection. """
  response = get_db().counters.find_one_and_update(
      {'_id': str(collection)}, {'$inc': {'value': 1}},
      upsert=True, return_document=True)
  return int(response['value']) + offset

def get_one_by_id(collection: str, id_: t.Union[str, int], msgtype: type[Msg]
    ) -> Msg:
  """ Get a single message from the database by ID. """
  return bson_format.to_proto(
    msgtype, get_db()[collection].find_one({'_id': id_}))
