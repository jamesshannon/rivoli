""" Hello """
import pathlib
import typing as t

import pymongo

from rivoli import config

if t.TYPE_CHECKING:
  from pymongo.mongo_client import MongoClient
  from pymongo.database import Database

MY_PATH = pathlib.Path(__file__).parent
CERT = MY_PATH.parent / 'X509-cert-8051024250932727866.pem'
MDB_CLIENT = pymongo.MongoClient('mongodb+srv://cluster0.ndszdhz.mongodb.net',
    tls=True,
    tlsCertificateKeyFile=str(CERT))
MDB_DB = MDB_CLIENT.test

def create_file():
  """ call """
  #filetypes = MDB_DB.get_collection('file_types')
  # create file record with NEW status get object id
  # add file to proccessed directory
  # create task to process file
  config.get_filetypes()



def process_file(file_id: str):
  # get file record with file ID
  # -> take out lock, check that file is "NEW", update to "PROCESSING". confirm that the update happened and someone else hadn't updated
  # check md5
  # loop through lines
  # Add raw line to
  """ hello """
