""" API Validators. """
# These are custom and would be in a separate package in production.
import typing as t

import requests
import requests.exceptions

from rivoli import protos
from rivoli.validation import helpers

# How to differentiate between retriable and auto-retry?
# E.g., 401 (auth) should be retriable,, but only after manual fixing
# In that case maybe retriable means auto-retry and all other records are
# retriable? But then what about fatal errors like "API responded that this is
# invalid"? Retry / retriable / fatal ?
RETRIABLE_CODES = (408, 429, 500, 502, 503, 504)

# def _make_request(url: str) -> dict[str, str]:
#   url = f'https://{service.hostname}{path}'
#   resp = requests.get(url, timeout=10)
#   return resp.json()

@helpers.register_func(protos.Function.FIELD_VALIDATION)
def lookup_id(value: str) -> str:
  """doc string"""
  url = 'http://localhost:8088/api/lookup'
  resp = requests.get(url, params={'value': value}, timeout=10)
  if resp.status_code == 404:
    raise helpers.ValidationError('ID could not be found')

  if resp.status_code != 200:
    raise helpers.ExecutionError(f'ID lookup failed with code {resp.status_code}')

  json = resp.json()

  return json['id']


def _make_request(method: str, url: str, **kwargs: t.Any) -> t.Any:
  """ Helper to call an API. """
  try:
    resp = requests.request(method, url, timeout=30, **kwargs)
    resp.raise_for_status()
  except (requests.exceptions.ConnectionError,
          requests.exceptions.ReadTimeout,
          requests.exceptions.HTTPError) as exc:
    retriable = (isinstance(exc, requests.exceptions.ConnectionError)
                 or (isinstance(exc, requests.exceptions.HTTPError)
                     and exc.response.status_code in RETRIABLE_CODES))
    raise helpers.ExecutionError(str(exc), retriable)

  return resp.json()

def get(url: str, **kwargs: t.Any) -> t.Any:
  return _make_request('GET', url, **kwargs)

def post(url: str, data: t.Any, **kwargs: t.Any) -> t.Any:
  """ Posts data as JSON. """
  return _make_request('POST', url, json=data, **kwargs)


@helpers.register_func(protos.Function.RECORD_UPLOAD)
def submit_record(record: helpers.RecordType) -> helpers.RecordType:
  """ Submit record to fake API """
  url = 'http://localhost:8088/api/create'

  print(record)

  try:
    resp = requests.post(url, data=record, timeout=10)
    resp.raise_for_status()

  except (requests.exceptions.ConnectionError,
          requests.exceptions.ReadTimeout) as exc:
    # Are these really retriable? A read timeout might have completed its work
    raise helpers.ExecutionError(str(exc), True)

  except requests.exceptions.HTTPError as exc:
    retriable = exc.response.status_code in (1000, 2000)
    raise helpers.ExecutionError(str(exc), retriable)

  json = resp.json()

  return json['id']

