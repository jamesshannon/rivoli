import pathlib
from unittest import mock

from rivoli import protos

TEST_FILES_DIR = str(pathlib.Path(__file__).parent / 'test_files')

# pyright: reportPrivateUsage=false

def get_mock_calls_by_name(mocked_calls: mock._CallList,
    name: str) -> list[mock._Call]:
  """ Return all mock calls with given function name. """
  return [call for call in mocked_calls if call[0] == name]

def get_mock_file() -> protos.File:
  """ Return a File. """
  return protos.File(
    id=123,
    partnerId='pABC',
    status=protos.File.NEW,
    location=TEST_FILES_DIR,
    name='loader_csv.csv',
  )

def get_mock_partner() -> protos.Partner:
  """ Return a Partner. """
  return protos.Partner(
    id='pABC',
  )

def get_mock_filetype() -> protos.FileType:
  """ Return a FileType. """
  return protos.FileType(
    id='ftDEF',
    # deprecated
    hasHeader=True,
    delimitedSeparator=',',

    recordTypes=[
        protos.RecordType(
          id=1001,
        )
    ]
  )
