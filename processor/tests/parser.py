""" Unit tests for rivoli.function_helpers.exceptions. """
import unittest
from unittest import mock

from rivoli import parser
from rivoli import protos

import tests

# pylint: disable=protected-access
# pyright: reportPrivateUsage=false

@mock.patch('rivoli.record_processor.db')
class ParserTests(unittest.TestCase):

  def test_fixedwidth_parse_fields(self, mocked_db: mock.Mock):
    # Test that the Loader class creates a filename with the File ID
    file = tests.get_mock_file()
    partner = tests.get_mock_partner()
    filetype = tests.get_mock_filetype()

    # charRanges as configured are 1-based and inclusive
    filetype.recordTypes[0].fieldTypes.extend([
      # First character, one character long
      protos.FieldType(
        name='f1',
        active=True,
        charRange={'start': 1, 'end': 1}
      ),
      # Second and third characters
      protos.FieldType(
        name='f2',
        active=True,
        charRange={'start': 2, 'end': 3}
      ),
      # Emtpy space around the A
      protos.FieldType(
        name='f3',
        active=True,
        charRange={'start': 15, 'end': 20}
      ),
      # Indices not in the string
      protos.FieldType(
        name='f4',
        active=True,
        charRange={'start': 50, 'end': 55}
      ),
    ])

    fwparser = parser.FixedWidthParser(file, partner, filetype)

    # The parser initialization subtracts 1 from the start position
    fields = fwparser._create_recordtype_fields(filetype.recordTypes)
    self.assertDictEqual(fields,
        {1001: [
            ((0, 1), 'f1'), ((1, 3), 'f2'), ((14, 20), 'f3'), ((49, 55), 'f4')]
        })

    dct = fwparser._parse_fields('ABCDEFGHIJKLMN   A  ', fields[1001])
    self.assertDictEqual(dct, {'f1': 'A', 'f2': 'BC', 'f3': 'A', 'f4': ''})
