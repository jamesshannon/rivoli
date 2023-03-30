""" Utils for processing files. """
import hashlib
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
