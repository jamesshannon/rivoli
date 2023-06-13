import pathlib

from rivoli import protos

TEST_FILES_DIR = str(pathlib.Path(__file__).parent / 'test_files')


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
