""" Unit tests for rivoli.function_helpers.exceptions. """
import pathlib
import unittest
from unittest import mock

from rivoli import loader

import tests

# pylint: disable=protected-access

@mock.patch('rivoli.record_processor.db')
class LoaderTests(unittest.TestCase):

  def test_begin_processing_file_name(self, mocked_db: mock.Mock):
    # Test that the Loader class creates a filename with the File ID
    file = tests.get_mock_file()
    partner = tests.get_mock_partner()
    filetype = tests.get_mock_filetype()

    loadr = loader.DelimitedLoader(file, partner, filetype)

    # Typical filename
    loadr._begin_processing()
    self.assertEqual(pathlib.Path(loadr.local_file).name, 'loader_csv-123.csv')

    # Ensure it treats extention-less files properly
    loadr.file = tests.get_mock_file()
    loadr.file.name = 'loader_csv'
    loadr._begin_processing()
    self.assertEqual(pathlib.Path(loadr.local_file).name, 'loader_csv-123')


  def test_delimited_file(self, mocked_db: mock.Mock):
    file = tests.get_mock_file()
    partner = tests.get_mock_partner()
    filetype = tests.get_mock_filetype()

    delimited = loader.DelimitedLoader(file, partner, filetype)
    delimited.process()

    # Should have found the 5 header rows
    self.assertEqual(file.headerColumns, ['ID', 'COL_2', 'COL_3', 'COL_4'])

    # There are 6 "rows" (lines) including the header
    self.assertEqual(file.stats.totalRows, 6)

    insert_calls = tests.get_mock_calls_by_name(
        mocked_db.mock_calls, 'get_db().records.insert_many')

    # There should be one insert_many() call
    self.assertEqual(len(insert_calls), 1)
    # ... and it should insert 5 records (which is the first parameter)
    first_record = insert_calls[0][1][0]
    self.assertEqual(len(first_record), 5)

    self.assertEqual(
        first_record[0]['rawColumns'],
        ['123', 'row1_val2', 'row1_val3', 'row1_val4'])

  def test_fixedwidth_file(self, mocked_db: mock.Mock):
    file = tests.get_mock_file()
    partner = tests.get_mock_partner()
    filetype = tests.get_mock_filetype()

    file.name = 'loader_fixed.txt'

    delimited = loader.FixedWidthLoader(file, partner, filetype)
    delimited.process()

    # There are 2 "rows" (lines)
    self.assertEqual(file.stats.totalRows, 2)

    insert_calls = tests.get_mock_calls_by_name(
        mocked_db.mock_calls, 'get_db().records.insert_many')

    # There should be one insert_many() call
    self.assertEqual(len(insert_calls), 1)
    # ... and it should insert 5 records (which is the first parameter)
    first_record = insert_calls[0][1][0]
    self.assertEqual(len(first_record), 2)

    self.assertEqual(first_record[0]['rawLine'], '123  VAL1 VAL2')
