import unittest

import common
from part_tables import get_mappings, is_compatible
from versions import Version, parse_version

common.unused_import_dummy = 1


def get_row(first: str, last: str, active: bool):
    return {
        'firstReleased': first,
        'lastUpdated': last,
        'status': 'active' if active else 'depreciated',
    }


class TestVersionCompat(unittest.TestCase):
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


class TestVersion1FieldsExist(unittest.TestCase):
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
        id_list_pass = [get_mappings(p, v) for p in self.parts_pass]
        id_list_fail = [get_mappings(p, v) for p in self.parts_fail]
        self.assertEqual(id_list_pass, [['a'], ['b'], ['c', 'd']])
        self.assertEqual(id_list_fail, [None, None, None])


if __name__ == '__main__':
    unittest.main()
