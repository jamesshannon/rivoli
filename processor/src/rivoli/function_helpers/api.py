""" API function helpers. """
import os
import typing as t
import urllib.parse as urlparse

import requests
import requests.exceptions

from rivoli import protos
from rivoli.function_helpers import exceptions
from rivoli.utils import logging

DRYRUN_POST = os.getenv('API_POST_DRYRUN', 'FALSE') != 'FALSE'

logger = logging.get_logger(__name__)

# These codes allow for an automatic retry.
AUTORETRY_CODES: t.Sequence[t.Union[int, 'protos.ProcessingLog.ErrorCode']] = (
    408, 429, 500, 502, 503, 504,
    protos.ProcessingLog.CONNECTION_ERROR, protos.ProcessingLog.TIMEOUT_ERROR)

# TODO: Create a session and request pooling
# But first figure out if that will leak or cookies
def make_request(method: str, url: str, **kwargs: t.Any) -> t.Any:
  """ Call API, retry, and parse Exceptions. Returns a dict from JSON. """
  timeout = kwargs.pop('timeout', 10)

  if method.upper() == 'POST' and DRYRUN_POST:
    logger.warn(f'Skipping API post to {url} because of dryrun')
    return {}

  try:
    resp = requests.request(method, url, timeout=timeout, **kwargs)
    resp.raise_for_status()
  except (requests.exceptions.ConnectionError,
          requests.exceptions.ReadTimeout,
          requests.exceptions.HTTPError) as exc:
    # Various requests exceptions get re-written to Rivoli exceptions with
    # appropriate handling of status codes and determination of auto-retry
    error_code: t.Union[protos.ProcessingLog.ErrorCode, int]

    # By default we raise an ExecutionError, which is a record-level error. In
    # some cases we want to raise a more serious (file-level) error.
    if '[Errno 8] nodename nor servname provided' in str(exc):
      # This is basically a DNS error. It's actually a reraise of a lower-level
      # exception (socket.gaiaerror?) but we'll just parse the string
      raise exceptions.ConfigurationError(
          f'Cannot find host for {urlparse.urlparse(url).netloc}',
          summary='Cannot find host') from exc

    if isinstance(exc, requests.exceptions.HTTPError):
      error_code = exc.response.status_code
    elif isinstance(exc, requests.exceptions.ConnectionError):
      error_code = protos.ProcessingLog.CONNECTION_ERROR
    else: # ReadTimeout
      error_code = protos.ProcessingLog.TIMEOUT_ERROR

    autoretry = error_code in AUTORETRY_CODES

    raise exceptions.ExecutionError(str(exc), autoretry, resp,
                                    error_code=error_code)

  return resp.json()

def get(url: str, **kwargs: t.Any) -> t.Any:
  """ Call an API with the GET method. Returns a dict from JSON. """
  return make_request('GET', url, **kwargs)

def post(url: str, data: t.Any, **kwargs: t.Any) -> t.Any:
  """ Posts data as JSON. Returns a dict from JSON. """
  return make_request('POST', url, json=data, **kwargs)
