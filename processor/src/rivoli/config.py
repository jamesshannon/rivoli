""" Application configuration. """
import os
import pathlib
import typing as t

import dotenv

_APP_ROOT = pathlib.Path(__file__).parent

dotenv.load_dotenv(verbose=True)

def get(key: str, default: t.Optional[str] = None) -> t.Optional[str]:
  """ Get a configuration value. """
  return os.getenv(key, default)
