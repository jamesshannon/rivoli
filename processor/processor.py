#!/usr/bin/env python
import base64

from rivoli import copier
from rivoli import db
from rivoli import loader
from rivoli import parser
from rivoli import validator
from rivoli import uploader
from rivoli import reporter

import importlib
import pathlib
import inspect
import types as t
from rivoli.utils import tasks

import bson
from rivoli.protos.processing_pb2 import RecordStats
from rivoli.protobson import bson_format
from rivoli import protos

FILE_ID = 59

def reset_file(file_id: int) -> None:
  """ Reset file for testing. """
  # remove records and reset file status
  file = db.get_one_by_id('files', file_id, protos.File)
  file.status = protos.File.NEW
  db.get_db().files.update_one(*bson_format.get_update_args(file, ['status']))

  prefix = file.id << 32
  filter_ = {'_id': {'$gte': prefix, '$lte': prefix + ((1 << 32) - 1)}}
  db.get_db().records.delete_many(filter_)

if __name__ == '__main__':
  #copier.setup_scan_tasks()
  #copier.scan('641d47816af10755674ffdd1')
  #copier.scan('641ddc817328627725c1e3a1')
  #copier.copy.delay('p1')

  #reset_file(FILE_ID)

  #loader.load_from_id(FILE_ID)

  #parser.parse(FILE_ID)
  #print(db.get_db().records.index_information())

  validator.validate(FILE_ID)

  #uploader.upload(FILE_ID)

  #reporter.report(FILE_ID, '645c27c8592438e670453a97')

  # a = RecordStats()
  # a.steps['LOAD'].input = 1
  # a.steps['LOAD'].failure = 10
  # a = protos.StepStats(input=1, failure=20)
  # dct = bson_format.from_proto(a)
  # print(bson_format.to_proto(protos.StepStats, dct))

  pass

