import unittest

import common
from part_tables import is_compatible
from versions import parse_version

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


if __name__ == '__main__':
    unittest.main()
