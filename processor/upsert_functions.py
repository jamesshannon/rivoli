#!/usr/bin/env python
""" CLI to generate a callable configuration file from module inspection. """
import argparse
import json
import pathlib

import bson
import pymongo

from rivoli import db
from rivoli.protobson import bson_format
from rivoli import protos

PYTHON_INSPECT_TYPE_MAP = {
  'str': protos.Function.STRING,
  'int': protos.Function.INTEGER,
  'float': protos.Function.FLOAT,
  'bool': protos.Function.BOOLEAN,
}

def parse_args() -> argparse.Namespace:
  """ Argparser for this file. """
  parser = argparse.ArgumentParser()
  parser.add_argument('directory')

  return parser.parse_args()

def get_functions(args: argparse.Namespace) -> list[protos.Function]:
  config_dir_path = pathlib.Path(args.directory)

  funcs: list[protos.Function] = []

  for file in config_dir_path.iterdir():
    if not file.is_dir() and file.suffix == '.json':
      with file.open('r', encoding='ascii') as fobj:
        for func_dct in json.load(fobj):
          funcs.append(bson_format.to_proto(protos.Function, func_dct))

  return funcs

if __name__ == '__main__':
  parsed = parse_args()
  functions = get_functions(parsed)

  upserts: list[pymongo.UpdateOne] = []
  for func in functions:
    func_dct = bson_format.from_proto(func)
    upserts.append(pymongo.UpdateOne({'_id': func_dct['_id']},
                                     {'$set': func_dct}, upsert=True))

  response = db.get_db().functions.bulk_write(upserts, ordered=False)
  print(response.bulk_api_result)
