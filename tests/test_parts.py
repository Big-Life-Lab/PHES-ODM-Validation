import unittest

import odm_validation.part_tables as pt
from odm_validation.part_tables import is_compatible
from odm_validation.validation import generate_validation_schema
from odm_validation.versions import Version, parse_version

import common


def get_row(first: str, last: str, active: bool):
    return {
        pt.PART_ID: 'dummy-partid',
        'firstReleased': first,
        'lastUpdated': last,
        pt.STATUS: pt.ACTIVE if active else 'depreciated',
    }


class TestVersionCompat(common.OdmTestCase):
    def test_same(self):
        row = get_row('1.0.0', '1.0.0', True)
        self.assertTrue(is_compatible(row, parse_version('1.0.0')))

    def test_eq_first(self):
        row = get_row('1.0.0', '2.0.0', False)
        self.assertTrue(is_compatible(row, parse_version('1.0.0')))

    def test_eq_last(self):
        row = get_row('1.0.0', '2.0.0', False)
        self.assertFalse(is_compatible(row, parse_version('2.0.0')))

    def test_incomplete(self):
        row = get_row('2', '2.0', True)
        self.assertTrue(is_compatible(row, parse_version('2.0.')))


class TestVersion1FieldsExist(common.OdmTestCase):
    parts_pass = [
        {
            'version1Location': 'tables',
            'version1Table': 'a',
        },
        {
            'version1Location': 'variables',
            'version1Variable': 'b',
        },
        {
            'version1Location': 'variableCategories',
            'version1Category': 'c;d',
        }
    ]
    parts_fail = [
        {
            'version1Table': 'a',
        },
        {
            'version1Location': 'variables',
        },
        {
            'version1Location': 'variableCategories',
            'version1Category': '',
        }
    ]

    def test(self):
        v = Version(major=1)
        id_list_pass = [pt._get_mappings(p, v) for p in self.parts_pass]
        id_list_fail = [pt._get_mappings(p, v) for p in self.parts_fail]
        self.assertEqual(id_list_pass, [['a'], ['b'], ['c', 'd']])
        self.assertEqual(id_list_fail, [[], [], []])


class TestVersion1Table(common.OdmTestCase):
    parts = [
        {
            'partID': 'mynewtable',
            'partType': 'tables',
            'version1Table': 'myoldtable',
            'version1Location': 'tables',
            'status': 'active',
        },
        {
            'partID': 'mynewtable2',
            'partType': 'tables',
            'version1Table': 'myoldtable2',
            'version1Location': 'tables',
            'status': 'active',
        },
        {
            'partID': 'myoldpart',
            'partType': 'attributes',
            'dataType': 'integer',
            'firstReleased': '1',
            'lastUpdated': '2',
            'status': 'depreciated',
            'version1Table': 'myoldtable;myoldtable2',
            'version1Location': 'variables',
            'version1Variable': 'myoldpart',
        }
    ]

    expected_schema = {
        'myoldtable': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {'myoldpart': {
                    'type': 'integer',
                    'coerce': 'integer',
                    'meta': [{
                        'meta': [{
                            'partID': 'myoldpart',
                            'dataType': 'integer',
                            'version1Location': 'variables',
                            'version1Table': 'myoldtable;myoldtable2',
                            'version1Variable': 'myoldpart'
                            }],
                        'ruleID': 'invalid_type'}],
                }},
                'meta': [{
                    'partID': 'mynewtable',
                    'partType': 'tables',
                    'version1Location': 'tables',
                    'version1Table': 'myoldtable'}]}},
        'myoldtable2': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {'myoldpart': {
                    'type': 'integer',
                    'coerce': 'integer',
                    'meta': [{
                        'meta': [{
                            'partID': 'myoldpart',
                            'dataType': 'integer',
                            'version1Location': 'variables',
                            'version1Table': 'myoldtable;myoldtable2',
                            'version1Variable': 'myoldpart'
                            }],
                        'ruleID': 'invalid_type'}],
                }},
                'meta': [{
                    'partID': 'mynewtable2',
                    'partType': 'tables',
                    'version1Location': 'tables',
                    'version1Table': 'myoldtable2'}]}}}

    def test(self):
        self.maxDiff = None
        schema = generate_validation_schema(self.parts, schema_version='1.0.0')
        self.assertDictEqual(self.expected_schema, schema['schema'])


if __name__ == '__main__':
    unittest.main()
