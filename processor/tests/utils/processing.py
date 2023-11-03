import unittest

from rivoli import protos

from rivoli.function_helpers import helpers
from rivoli.utils import processing

FIELDS = [
    protos.Function.Field(key='tostr', type=protos.Function.STRING),
    protos.Function.Field(key='toint', type=protos.Function.INTEGER),
    protos.Function.Field(key='tofloat', type=protos.Function.FLOAT),
    protos.Function.Field(key='tobool', type=protos.Function.BOOLEAN),
    protos.Function.Field(key='toremove', type=protos.Function.STRING,
                          isOutputEphemeral=True),
]
DATA = {
  'tostr': 1.5,
  'toint': '1',
  'tofloat': '1.5',
  'tobool': 'FALSE',
  'toremove': 'FALSE',
  'isdict': {'a': 'b'},
}

class ProcessingTests(unittest.TestCase):
  def test_coerce(self):
    """ Test that record fields are properly coerced. """
    out = processing.coerce_record_fields(DATA, FIELDS)

    self.assertEqual(out['tostr'], '1.5')
    self.assertEqual(out['toint'], 1)
    self.assertEqual(out['tofloat'], 1.5)
    self.assertEqual(out['tobool'], True)
    self.assertEqual(out['tobool'], True)

  def test_prep_record_fields_for_db(self):
    """ Test that record fields are coerced for mongodb. """
    out = processing.prep_record_fields_for_db(DATA, FIELDS)

    self.assertNotIn('toremove', out)

    self.assertEqual(out['isdict'], '{"a": "b"}')
