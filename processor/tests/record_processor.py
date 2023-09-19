""" Unit tests for rivoli.record_processor. """
import unittest

from rivoli.record_processor import record_processor
from rivoli.function_helpers import exceptions
from rivoli import protos

import tests

class RecordProcessor(record_processor.RecordProcessor):
  log_source = protos.ProcessingLog.COPIER

  def _process(self):
    pass

  def _close_processing(self) -> None:
    pass

class ExceptionTests(unittest.TestCase):
  def test_make_exc_log_entry_native_exception(self):
    # We need to do this inside of a try/except so that the method can get
    # the stacktrace
    try:
      raise ValueError('message')
    except ValueError as exc:
      rp = RecordProcessor(tests.get_mock_file(), tests.get_mock_partner(),
          tests.get_mock_filetype())
      log = rp._make_exc_log_entry(exc)

      self.assertEqual(log.level, protos.ProcessingLog.ERROR)
      self.assertEqual(log.summary, 'ValueError')
      self.assertIn('in test_make_exc_log_entry', log.stackTrace)

  def test_make_exc_log_entry_custom_exception(self):
    # We need to do this inside of a try/except so that the method can get
    # the stacktrace
    try:
      raise exceptions.ConfigurationError('message', summary='sum')
    except exceptions.ConfigurationError as exc:
      rp = RecordProcessor(tests.get_mock_file(), tests.get_mock_partner(),
          tests.get_mock_filetype())
      log = rp._make_exc_log_entry(exc)

      self.assertEqual(log.level, protos.ProcessingLog.ERROR)
      self.assertEqual(log.summary, 'sum')
      # RivoliErrors don't get stack trace include in logs
      self.assertEqual(log.stackTrace, '')
