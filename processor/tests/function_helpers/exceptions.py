""" Unit tests for rivoli.function_helpers.exceptions. """
import unittest

from rivoli.function_helpers import exceptions
from rivoli import protos

class ExceptionTests(unittest.TestCase):
  def test_exception_instances(self):

    # ConfigurationError
    exc = exceptions.ConfigurationError()
    self.assertIsInstance(exc, ValueError)
    self.assertIsInstance(exc, exceptions.RivoliError)

    # ValidationError
    exc = exceptions.ValidationError()
    self.assertIsInstance(exc, ValueError)
    self.assertIsInstance(exc, exceptions.RivoliError)

    # ExecutionError
    exc = exceptions.ExecutionError('some message')
    self.assertIsInstance(exc, RuntimeError)
    self.assertIsInstance(exc, exceptions.RivoliError)

  def test_default_error_codes(self):
    # ConfigurationError
    exc = exceptions.ConfigurationError()
    self.assertEqual(exc.error_code, protos.ProcessingLog.OTHER_CONFIGURATION_ERROR)

    # ValidationError
    exc = exceptions.ValidationError()
    self.assertEqual(exc.error_code, protos.ProcessingLog.OTHER_VALIDATION_ERROR)

    # ExecutionError
    exc = exceptions.ExecutionError('some message')
    self.assertEqual(exc.error_code, protos.ProcessingLog.OTHER_EXECUTION_ERROR)

  def test_mixin_error_codes(self):
    exc = exceptions.ValidationError(error_code=123)
    self.assertEqual(exc.error_code, 123)

    exc = exceptions.ExecutionError('msg', error_code=123)
    self.assertEqual(exc.error_code, 123)

  def test_mixin_summary(self):
    exc = exceptions.ValidationError(summary='sum')
    self.assertEqual(exc.summary, 'sum')

    exc = exceptions.ExecutionError('msg', summary='sum')
    self.assertEqual(exc.summary, 'sum')


