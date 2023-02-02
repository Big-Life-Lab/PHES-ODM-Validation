import unittest

import common
import part_tables as pt
from part_tables import get_mappings
from versions import Version, parse_version

common.unused_import_dummy = 1


def get_row(first: str, last: str, active: bool):
    return {
        'firstReleased': first,
        'lastUpdated': last,
        pt.STATUS: pt.ACTIVE if active else 'depreciated',
    }


def part_is_compatible(part: pt.Part, version: Version) -> bool:
    first, last = pt.get_version_range(part)
    active: bool = part.get(pt.STATUS) == pt.ACTIVE
    return pt.is_compatible(active, first, last, version)


class TestVersionCompat(common.OdmTestCase):
    def test_same(self):
        row = get_row('1.0.0', '1.0.0', True)
        self.assertTrue(part_is_compatible(row, parse_version('1.0.0')))

    def test_eq_first(self):
        row = get_row('1.0.0', '2.0.0', False)
        self.assertTrue(part_is_compatible(row, parse_version('1.0.0')))

    def test_eq_last(self):
        row = get_row('1.0.0', '2.0.0', False)
        self.assertFalse(part_is_compatible(row, parse_version('2.0.0')))

    def test_incomplete(self):
        row = get_row('2', '2.0', True)
        self.assertTrue(part_is_compatible(row, parse_version('2.0.')))


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
        id_list_pass = [get_mappings(p, v) for p in self.parts_pass]
        id_list_fail = [get_mappings(p, v) for p in self.parts_fail]
        self.assertEqual(id_list_pass, [['a'], ['b'], ['c', 'd']])
        self.assertEqual(id_list_fail, [None, None, None])


if __name__ == '__main__':
    unittest.main()
