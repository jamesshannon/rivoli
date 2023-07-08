#!/usr/bin/env python
""" CLI to generate a callable configuration file from module inspection. """
import abc
import argparse
import csv
import json
import pathlib
import typing as t

import pymongo.cursor

from rivoli import db
from rivoli.protobson import bson_format
from rivoli import protos

def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument('--csv_header', action='store_true')
  return parser.parse_args()


class CollectionWriter(abc.ABC):
  """ Write a mongodb collection to a CSV. """
  collection: str
  filename: str
  fields: list[str]

  def __init__(self, directory: pathlib.Path, write_header: bool) -> None:
    self.write_header = write_header
    self.file_path = directory / self.filename

  @abc.abstractmethod
  def _generate(self, cursor: pymongo.cursor.Cursor[dict[str, t.Any]]
      ) -> t.Generator[dict[str, t.Any], None, None]:
    """ Collection-specific generator
    Child classes should override this to take a cursor of mongodb documents
    and yield a dict with all fields to write.
    """

  def write(self):
    """ Shared method to find documents and write them to a CSV file. """
    with open(self.file_path, 'w', encoding='utf-8', newline=None) as fobj:
      writer = csv.DictWriter(fobj, self.fields)
      if self.write_header:
        writer.writeheader()

      line_num = 1

      cursor = db.get_db().get_collection(self.collection).find()
      for line in self._generate(cursor):
        writer.writerow(line)

        line_num += 1
        if line_num % 10000 == 0:
          print('.', end='', flush=True)

class FileWriter(CollectionWriter):
  """ Write file documents. """
  collection = 'files'
  filename = 'files.csv'
  fields = ['id', 'name', 'status', 'partner', 'file_type']

  def __init__(self, directory: pathlib.Path) -> None:
    super().__init__(directory)

    # Create lookups for partners and filetypes.
    self.partners: dict[str, str] = {}
    self.file_types: dict[str, str] = {}

    for doc in db.get_db().partners.find():
      partner = bson_format.to_proto(protos.Partner, doc)
      self.partners[partner.id] = partner.name
      for file_type in partner.fileTypes:
        self.file_types[file_type.id] = file_type.name

  def _generate(self, cursor: pymongo.cursor.Cursor[dict[str, t.Any]]
      ) -> t.Generator[dict[str, t.Any], None, None]:
    for doc in cursor:
      file = bson_format.to_proto(protos.File, doc)
      yield {
        'id': file.id,
        'name': file.name,
        'status': protos.File.Status.Name(file.status),
        'partner': self.partners[file.partnerId],
        'file_type': self.file_types[file.fileTypeId],
      }

class RecordWriter(CollectionWriter):
  """ Write record documents. """
  collection = 'records'
  filename = 'records.csv'
  fields = ['id', 'file_id', 'row_num', 'status',
            'parsed_fields', 'validated_fields',
            'errors', 'errors_string']

  recordIdMask = (1 << 32) - 1

  def _generate(self, cursor: pymongo.cursor.Cursor[dict[str, t.Any]]
      ) -> t.Generator[dict[str, t.Any], None, None]:
    for doc in cursor:
      record = bson_format.to_proto(protos.Record, doc)
      yield {
        'id': record.id,
        'file_id': record.id >> 32,
        'row_num': self.recordIdMask & record.id,
        'status': protos.Record.Status.Name(record.status),
        'parsed_fields': json.dumps(dict(record.parsedFields)),
        'validated_fields': json.dumps(dict(record.validatedFields)),
        'errors': json.dumps([e.message for e in record.recentErrors]),
        'errors_string': ', '.join([e.message for e in record.recentErrors]),
      }

def app(args: argparse.Namespace):
  """ Write CSVs for all configured collection types. """
  my_dir = pathlib.Path(__file__).parent

  filewriter = FileWriter(my_dir)
  filewriter.write()

  recordwriter = RecordWriter(my_dir)
  recordwriter.write()

if __name__ == '__main__':
  app(_parse_args())
