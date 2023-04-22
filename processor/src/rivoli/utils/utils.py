""" Utils for processing files. """
import hashlib
import json
import pathlib

def get_file_hash(file_path: pathlib.Path) -> bytes:
  """ Return an md5 from file contents.
  This iterates through the file in blocks to prevent having to read the entire
  file into memory. """
  with open(file_path, 'rb') as fobj:
    md5 = hashlib.md5()
    while chunk := fobj.read(8192):
      md5.update(chunk)

    return md5.digest()

def get_dict_hash(dct: dict[str, str]) -> bytes:
  """ Return an md5 hash of a dictionary. """
  return hashlib.md5(json.dumps(dct, sort_keys=True).encode()).digest()
