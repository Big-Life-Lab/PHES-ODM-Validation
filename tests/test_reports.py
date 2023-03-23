import unittest

import common
import rules
from reports import DataKind, get_row_num
from validation import validate_data
from pprint import pprint

common.unused_import_dummy = 1


class TestReports(common.OdmTestCase):
    def test_get_row_num(self):
        self.assertEqual(get_row_num(0, 0, DataKind.python), 1)
        self.assertEqual(get_row_num(1, 0, DataKind.python), 2)
        self.assertEqual(get_row_num(2, 10, DataKind.python), 13)

        self.assertEqual(get_row_num(0, 0, DataKind.spreadsheet), 2)
        self.assertEqual(get_row_num(1, 0, DataKind.spreadsheet), 3)
        self.assertEqual(get_row_num(2, 10, DataKind.spreadsheet), 14)

    def test_column_rules_reported_once_for_spreadsheet(self):
        schema = {
            'schemaVersion': '2.0.0',
            'schema': {
                'addresses': {
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'addID': {
                                'required': True
                            }
                        }
                    }
                }
            }
        }
        data = {
            'addresses': [
                {'qwe': 'a'},  # row 2
                {'asd': 'b'},  # row 3
            ]
        }

        # just one error even tho there are 2 rows missing the
        report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(report.errors[0]['rowNumber'], 2)
        self.assertEqual(report.errors[0]['errorType'],
                         rules.missing_mandatory_column.__name__)

    def test_coercion_warnings_for_data_kind(self):
        schema = {
            'schemaVersion': '2.0.0',
            'schema': {
                'addresses': {
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'addID': {
                                'type': 'integer',
                                'coerce': 'integer',
                            }
                        }
                    }
                }
            }
        }
        data = {
            'addresses': [
                {'addID': '123'},
            ]
        }

        report = validate_data(schema, data, data_kind=DataKind.python)
        self.assertEqual(len(report.warnings), 1)
        report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        self.assertEqual(len(report.warnings), 0)


if __name__ == '__main__':
    unittest.main()
