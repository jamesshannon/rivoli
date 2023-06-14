""" API module unit tests """
import json
import unittest
from unittest import mock

import requests
import requests.exceptions

from rivoli.function_helpers import api
from rivoli.function_helpers import exceptions

import tests

@mock.patch('rivoli.function_helpers.api.requests.request')
@mock.patch('rivoli.function_helpers.api.db')
class ApiTests(unittest.TestCase):
  def test_request_http_error(self, mocked_db: mock.Mock,
      mocked_request: mock.Mock):
    """ Test when the API request returns an HTTP (404) error. """
    mock_resp = requests.Response()
    mock_resp.status_code = 408
    mock_resp._content = str.encode('RESPONSE')

    mocked_request.return_value = mock_resp

    with self.assertRaises(exceptions.ExecutionError) as ctx:
      api.make_request('post', 'http://www.google.com', json={'test': 1})

    apilog = tests.get_mock_calls_by_name(
        mocked_db.mock_calls, 'get_db().apilog.insert_one')[0][1][0]

    self.assertTrue(ctx.exception.auto_retry)
    self.assertEqual(ctx.exception.error_code, 408)
    self.assertEqual(ctx.exception.http_response, mock_resp)

    self.assertDictEqual(json.loads(apilog['request']['body']), {'test': 1})
    self.assertEqual(apilog['response']['code'], 408)
    self.assertEqual(apilog['_id'], ctx.exception.api_log_id)

  def test_request_tcp_error(self, mocked_db: mock.Mock,
      mocked_request: mock.Mock):
    """ Test when the API request returns a TCP (DNS) error. """
    mocked_request.side_effect = requests.exceptions.ConnectionError(
        '[Errno 8] nodename nor servname provided')

    with self.assertRaises(exceptions.ConfigurationError) as ctx:
      api.make_request('post', 'http://www.google.com', json={'test': 1})

    apilog = tests.get_mock_calls_by_name(
        mocked_db.mock_calls, 'get_db().apilog.insert_one')[0][1][0]

    self.assertFalse(ctx.exception.auto_retry)
    self.assertEqual(ctx.exception.error_code, 900)
    self.assertIsNone(ctx.exception.http_response)

    self.assertDictEqual(json.loads(apilog['request']['body']), {'test': 1})
    self.assertEqual(apilog['response']['exception']['type'],
                     'ConfigurationError')
    self.assertEqual(apilog['_id'], ctx.exception.api_log_id)
