""" Mongodb connection setup. """
import typing as t

import pymongo

from rivoli import config

DB_NAME = 'testdb'
mongo_client:  pymongo.MongoClient[dict[str, t.Any]]

if config.get('MONGO_USERNAME') and config.get('MONGO_PASSWORD'):
  auth = f'{config.get("MONGO_USERNAME")}:{config.get("MONGO_PASSWORD")}'
  url = f'mongodb://{auth}@{config.get("MONGO_ENDPOINT")}'
  mongo_client = pymongo.MongoClient(url, compressors='zstd')

elif config.get('MONGO_CERT'):
  url = f'mongodb+srv://{config.get("MONGO_ENDPOINT")}/?authSource=$external'
  mongo_client = pymongo.MongoClient(url, authMechanism="MONGODB-X509",
      tls=True, tlsCertificateKeyFile=config.get('MONGO_CERT'),
      compressors='zstd')

else:
  raise ValueError('No valid mongodb config parameters')

MDB_DB = mongo_client[DB_NAME]


def get_db():
  """ Return a mongodb database (client). """
  return MDB_DB

def get_next_id(collection: str, offset: int = 0) -> int:
  """ Return the next unused ID for a given collection. """
  response = get_db().counters.find_one_and_update(
      {'_id': str(collection)}, {'$inc': {'value': 1}},
      upsert=True, return_document=True)
  return int(response['value']) + offset
