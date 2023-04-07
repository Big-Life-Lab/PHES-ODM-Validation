import unittest
from copy import deepcopy

import common
from input_data import DataKind
from reports import get_row_num
from validation import validate_data
# from pprint import pprint

common.unused_import_dummy = 1

base_schema = {
    'schemaVersion': '2.0.0',
    'schema': {
        'addresses': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {}
            }
        }
    }
}


def get_table_schema(schema):
    return schema['schema']['addresses']['schema']['schema']


class TestReports(common.OdmTestCase):
    def test_get_row_num(self):
        self.assertEqual(get_row_num(0, 0, DataKind.python), 1)
        self.assertEqual(get_row_num(1, 0, DataKind.python), 2)
        self.assertEqual(get_row_num(2, 10, DataKind.python), 13)

        self.assertEqual(get_row_num(0, 0, DataKind.spreadsheet), 2)
        self.assertEqual(get_row_num(1, 0, DataKind.spreadsheet), 3)
        self.assertEqual(get_row_num(2, 10, DataKind.spreadsheet), 14)

    def test_row_num_from_validate_data(self):
        schema = deepcopy(base_schema)
        table_schema = get_table_schema(schema)
        table_schema['addID'] = {'max': 1, 'type': 'integer'}
        data = {'addresses': [{'addID': 0}, {'addID': 1}, {'addID': 2}]}
        py_report = validate_data(schema, data, data_kind=DataKind.python)
        ss_report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        self.assertEqual(py_report.errors[0]['rowNumber'], 3)
        self.assertEqual(ss_report.errors[0]['rowNumber'], 4)

    def test_column_rules_reported_once_for_spreadsheet(self):
        schema = deepcopy(base_schema)
        table_schema = get_table_schema(schema)
        table_schema['addID'] = {'required': True}
        data = {
            'addresses': [
                {'qwe': 'a'},  # row 2
                {'asd': 'b'},  # row 3
            ]
        }

        # just one error even tho there are 2 rows missing the column
        report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        expected_errors = [{
            'columnName': 'addID',
            'errorType': 'missing_mandatory_column',
            'message': ('missing_mandatory_column rule violated in '
                        'table addresses, column addID: '
                        'Missing mandatory column addID'),
            'tableName': 'addresses',
            'validationRuleFields': []
        }]
        self.assertEqual(expected_errors, report.errors)

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
                            },
                            'somedate': {
                                'type': 'datetime',
                                'coerce': 'datetime',
                            }
                        }
                    }
                }
            }
        }
        data = {
            'addresses': [
                {'addID': '123', 'somedate': '2023-01-01'},
            ]
        }

        report = validate_data(schema, data, data_kind=DataKind.python)
        self.assertEqual(len(report.warnings), 2)
        report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        self.assertEqual(len(report.warnings), 0)

    def test_spreadsheet_error_has_row_prefix(self):
        schema = deepcopy(base_schema)
        table_schema = get_table_schema(schema)
        table_schema['addID'] = {'max': 1, 'type': 'integer'}
        data = {'addresses': [{'addID': '123'}]}
        report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        self.assertTrue(', row 2: ' in report.errors[0]['message'], report)

    def test_spreadsheet_column_error_does_not_have_row_prefix(self):
        schema = deepcopy(base_schema)
        table_schema = get_table_schema(schema)
        table_schema['addID'] = {'required': True}
        data = {'addresses': [{'asd': '123'}]}
        report = validate_data(schema, data, data_kind=DataKind.spreadsheet)
        msg = report.errors[0]['message']
        self.assertFalse('row' in msg)
        self.assertTrue('column addID:' in msg)


if __name__ == '__main__':
    unittest.main()
