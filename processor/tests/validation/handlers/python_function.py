""" Unit tests for rivoli.validation.handlers.python_function. """
import enum
import unittest

from rivoli import protos
from rivoli.validation.handlers import python_function

import tests

# pylint: disable=protected-access
# pyright: reportPrivateUsage=false


class PythonFunctionTests(unittest.TestCase):
  def test_create_params_no_params(self):
    # Test that the Loader class creates a filename with the File ID
    def test_func(record: str) -> str:
      return ''

    func = protos.Function()
    cfg = protos.FunctionConfig(parameters=None)

    params = python_function._create_parameters(test_func, cfg, func)
    self.assertEqual([], params)

  def test_create_params(self):
    class Color(enum.Enum): RED = 1
    def test_func(record: str, an_int: int, a_str: str, a_color: Color,
        a_float: float, a_bool1: bool, a_bool2: bool) -> str:
      return ''

    func = protos.Function(
      parameters=[
        protos.Function.Parameter(type='INTEGER'),
        protos.Function.Parameter(type='STRING'),
        protos.Function.Parameter(type='ENUM'),
        protos.Function.Parameter(type='FLOAT'),
        protos.Function.Parameter(type='BOOLEAN'),
        protos.Function.Parameter(type='BOOLEAN'),
      ]
    )
    cfg = protos.FunctionConfig(
        parameters=['1', 'a string', 'RED', '1.2', 'true', 'false'])

    params = python_function._create_parameters(test_func, cfg, func)
    self.assertEqual([1, 'a string', Color.RED, 1.2, True, False], params)
