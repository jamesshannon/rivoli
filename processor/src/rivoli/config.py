""" Application configuration. """
import os
import pathlib
import typing as t

import dotenv

_APP_ROOT = pathlib.Path(__file__).parent

dotenv.load_dotenv(verbose=True)

def get(key: str, default: t.Optional[str] = None, strict: bool = False
    ) -> t.Optional[str]:
  """ Get a configuration value. """
  val = os.getenv(key, default)
  if not val and strict:
    raise ValueError(f'No value for config key: {key}')

  return val
