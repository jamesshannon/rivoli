#!/usr/bin/env python
import base64

from rivoli import copier
from rivoli import db
from rivoli import loader
from rivoli import parser
from rivoli import validator
from rivoli import uploader

import importlib
import pathlib
import inspect
import types as t
from rivoli.utils import tasks

import bson
from rivoli.protos.processing_pb2 import RecordStats
from rivoli.protobson import bson_format
from rivoli import protos

FILE_ID = 18

if __name__ == '__main__':
  #print(str(bson.ObjectId()))
  #config.get_filetypes()
  copier.scan('641d47816af10755674ffdd1')
  copier.scan('641ddc817328627725c1e3a1')
  #copier.copy.delay('p1')

  #loader.load_from_id(FILE_ID)
  #loader.load.delay('64044842a3452308a9e59330')

  #parser.parse(FILE_ID)
  #print(db.get_db().records.index_information())

  #validator.validate(FILE_ID)

  #uploader.upload(FILE_ID)
  #db.get_next_id('some_collection')

  # a = RecordStats()
  # a.steps['LOAD'].input = 1
  # a.steps['LOAD'].failure = 10
  # a = protos.StepStats(input=1, failure=20)
  # dct = bson_format.from_proto(a)
  # print(bson_format.to_proto(protos.StepStats, dct))

  pass




