""" API function helpers. """
import json
import os
import re
import sys
import typing as t
import urllib.parse as urlparse

import requests
import requests.exceptions

from rivoli import db
from rivoli import protos
from rivoli.function_helpers import exceptions
from rivoli.protobson import bson_format
from rivoli.utils import logging

DRYRUN_POST = os.getenv('API_POST_DRYRUN', 'FALSE') != 'FALSE'

logger = logging.get_logger(__name__)

# These codes allow for an automatic retry.
AUTORETRY_CODES: t.Sequence[t.Union[int, 'protos.ProcessingLog.ErrorCode']] = (
    408, 429, 500, 502, 503, 504,
    protos.ProcessingLog.CONNECTION_ERROR, protos.ProcessingLog.TIMEOUT_ERROR)

# Log requests on errors
# Options might be ALWAYS, POST, DRYRUN, ERROR
REQUEST_LOG_CRITERIA = 'POST'

# Limit apilog response content to 500kb
OVERFLOW_LENGTH = 500_000

def _text_overflow(text: str) -> str:
  """ Limit string length and add a note when string is sliced. """
  overage = len(text) - OVERFLOW_LENGTH
  if overage > 0:
    return f'{text[:OVERFLOW_LENGTH]}... [plus {overage} characters]'

  return text

def _clean_exc_msg(msg: str, url: str) -> str:
  """ Clean any high-cardinality-looking bits from exception messages """
  removal_pattern = rf'(for url)?(: )?{re.escape(url)}'
  return re.sub(removal_pattern, '', msg).strip()

# TODO: Create a session and request pooling
# But first figure out if that will leak or cookies
def make_request(method: str, url: str, **kwargs: t.Any) -> t.Any:
  """ Call API, retry, and parse Exceptions. Returns a dict from JSON. """
  timeout = kwargs.pop('timeout', 10)
  method = method.upper()

  apilog = protos.ApiLog(
      id=bson_format.hex_id(),
      dryrun=DRYRUN_POST,
      request=protos.ApiLog.Request(
          method=method.upper(),
          url=url,
          timeout=timeout
      )
  )
  # How to handle expiration and deletion?
  # Mongodb offers a TTL index and a capped collection, both of which serve to
  # auto-delete documents. But records may have references to log entries.
  # Without a (much) more complicated deletion strategy then those references
  # will become orphaned.
  apilog.timestamp.GetCurrentTime()

  if 'json' in kwargs:
    apilog.request.body = json.dumps(kwargs['json'])

  if method != 'GET' and DRYRUN_POST:
    # If dryrun then skip POSTs (which also include PATCHes and probably
    # every other verb than GET)
    logger.warn(f'Skipping API post to {url} because of dryrun')
    return {}

  resp = None

  try:
    resp = requests.request(method, url, timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp.json()

  except (requests.exceptions.RequestException) as exc:
    # Various requests exceptions get re-written to Rivoli exceptions with
    # appropriate handling of status codes and determination of auto-retry
    error_code: t.Union[protos.ProcessingLog.ErrorCode, int]

    exc_msg = str(exc)

    # By default we raise an ExecutionError, which is a record-level error. In
    # some cases we want to raise a more serious (file-level) error.
    if '[Errno 8] nodename nor servname provided' in exc_msg:
      # This is basically a DNS error. It's actually a reraise of a lower-level
      # exception (socket.gaiaerror?) but we'll just parse the string
      raise exceptions.ConfigurationError(
          f'Cannot find host for {urlparse.urlparse(url).netloc}',
          summary='Cannot find host') from exc

    if isinstance(exc, requests.exceptions.HTTPError):
      error_code = exc.response.status_code
    elif isinstance(exc, requests.exceptions.ConnectionError):
      error_code = protos.ProcessingLog.CONNECTION_ERROR
    elif isinstance(exc, requests.exceptions.ReadTimeout):
      error_code = protos.ProcessingLog.TIMEOUT_ERROR
    else:
      error_code = protos.ProcessingLog.OTHER_EXECUTION_ERROR

    autoretry = error_code in AUTORETRY_CODES

    summary = _clean_exc_msg(exc_msg, url)

    raise exceptions.ExecutionError(exc_msg, auto_retry=autoretry,
        http_response=resp, error_code=error_code, summary=summary)

  finally:
    # Any error, including a non-200, generates an exception. Some will get
    # modified and re-raised as a ConfigurationError or ExecutionError but some
    # Exceptions might come straight through
    exc = sys.exc_info()[1]

    if resp is None:
      # resp will be set in all HTTP responses (including non-200s)
      # It will only be None for exceptions like DNS errors
      apilog.response.exception.type = sys.exc_info()[0].__name__
      apilog.response.exception.message = str(exc)
    else:
      apilog.response.code = resp.status_code
      apilog.response.headers.update(resp.headers)
      apilog.response.elapsed_ms = int(resp.elapsed.microseconds / 1000)
      # Only the first 500k of response text
      apilog.response.content = _text_overflow(resp.content.decode())

    # Log only POST-ish requests (for now)
    if method != 'GET':
      db.get_db().apilog.insert_one(bson_format.from_proto(apilog))

      if exc:
        # Only propagate the ApiLog ID if we actually save the log entry
        setattr(exc, 'api_log_id', apilog.id)

def get(url: str, **kwargs: t.Any) -> t.Any:
  """ Call an API with the GET method. Returns a dict from JSON. """
  return make_request('GET', url, **kwargs)

def post(url: str, data: t.Any, **kwargs: t.Any) -> t.Any:
  """ Posts data as JSON. Returns a dict from JSON. """
  return make_request('POST', url, json=data, **kwargs)
