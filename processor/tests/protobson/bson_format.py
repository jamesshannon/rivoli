""" Unit tests for rivoli.protobson.bson_format. """
import unittest
import typing as t

from rivoli.protobson import bson_format
from rivoli import protos

import tests

# pyright: reportPrivateUsage=false
# pylint: disable=protected-access

TEST_DICT: dict[str, t.Any] = {
    'a': {'b': {'d': 'value', 'c': None }, 'x.y': 'otherval' },
    'e': 'val' }
TEST_MSG = protos.File(
  id=123,
  name='xyz',
  stats=protos.RecordStats(
    approximateRows=456,
    steps={
      'step1': protos.StepStats(
        input=123
      )
    }
  ),
  outputs=[
    protos.OutputInstance(
      id='abc',
      outputId='abc-123'),
    protos.OutputInstance(
      id='def',
      outputId='def-123'),
    protos.OutputInstance(
      id='ghi',
      outputId='ghi-123'),

  ]
)

class BsonFormatTests(unittest.TestCase):
  def test_get_from_nested_dct(self):
    self.assertDictEqual(
        bson_format._get_from_nested_dict('a', TEST_DICT), TEST_DICT['a'])
    self.assertDictEqual(
        bson_format._get_from_nested_dict('a.b', TEST_DICT),
                                          TEST_DICT['a']['b'])
    self.assertIsNone(bson_format._get_from_nested_dict('a.b.c', TEST_DICT))
    self.assertEqual(bson_format._get_from_nested_dict('a.b.d', TEST_DICT),
                                                       'value')
    self.assertEqual(bson_format._get_from_nested_dict('a.x.y', TEST_DICT),
                                                       'otherval')

    self.assertEqual(bson_format._get_from_nested_dict('e', TEST_DICT), 'val')

    with self.assertRaises(KeyError):
      bson_format._get_from_nested_dict('a.c', TEST_DICT)

  def test_get_update_map_fields(self):
    def get_set_field(update_dct: dict[str, t.Any], is_set: bool, field: str):
      return update_dct['$set' if is_set else '$unset'][field]

    mp = bson_format.get_update_map
    msg_dict = bson_format.from_proto(TEST_MSG)

    self.assertEqual(
        get_set_field(mp(TEST_MSG, ['name']), True, 'name'), 'xyz')
    self.assertDictEqual(
        get_set_field(mp(TEST_MSG, ['stats']), True, 'stats'),
        msg_dict['stats'])
    self.assertDictEqual(
        get_set_field(mp(TEST_MSG, ['stats.steps']), True, 'stats.steps'),
        msg_dict['stats']['steps'])
    self.assertDictEqual(
        get_set_field(mp(TEST_MSG, ['stats.steps.step1']), True,
                         'stats.steps.step1'),
        msg_dict['stats']['steps']['step1'])

    self.assertEqual(
        get_set_field(mp(TEST_MSG, ['stats.steps.step2']), False,
                         'stats.steps.step2'),
        '')

  def test_get_subitem_update_args(self):
    # Create an update command which only updates the second output (id = def)
    filter_, update = bson_format.get_array_item_update_args(
        TEST_MSG, 'outputs', TEST_MSG.outputs[2])

    self.assertDictEqual({'_id': 123, 'outputs.id': 'ghi'}, filter_)
    self.assertDictEqual({'id': 'ghi', 'outputId': 'ghi-123'},
                         update['$set']['outputs.$'])
