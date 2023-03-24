""" API Validators. """
# These are custom and would be in a separate package in production.

import requests
import requests.exceptions

from rivoli import protos
from rivoli.validation import helpers



def _make_request(url: str) -> dict[str, str]:
  url = f'https://{service.hostname}{path}'
  resp = requests.get(url, timeout=10)
  return resp.json()

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

@helpers.register_func(protos.Function.RECORD_UPLOAD)
def submit_record(record: helpers.RecordType) -> helpers.RecordType:
  """ Submit record to fake API """
  url = 'http://localhost:8088/api/create'

  print(record)

  try:

    resp = requests.post(url, data=record, timeout=10)
    resp.raise_for_status()

  except (requests.exceptions.ConnectionError, ) as exc:
    raise helpers.ExecutionError(str(exc), True)

  except requests.exceptions.HTTPError as exc:
    retriable = exc.response.status_code in (1000, 2000)
    raise helpers.ExecutionError(str(exc), retriable)

  json = resp.json()

  return json['id']

