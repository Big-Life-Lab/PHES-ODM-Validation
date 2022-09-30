import unittest

from semver import Version

import context
from versions import parse_version, is_compatible

context.unused_import_dummy = 1


def get_row(first: str, last: str, active: bool):
    return {
        'firstReleased': first,
        'lastUpdated': last,
        'status': 'active' if active else 'depreciated',
    }


class TestParseVersion(unittest.TestCase):
    def test_default(self):
        default = Version(major=123)
        self.assertEqual(parse_version('', default=default), default)
        with self.assertRaises(ValueError):
            parse_version('')

    def test_incomplete(self):
        self.assertEqual(parse_version('1'), '1.0.0')
        self.assertEqual(parse_version('2.0'), '2.0.0')
        self.assertEqual(parse_version('3.0.'), '3.0.0')

    def test_garbage(self):
        self.assertEqual(parse_version('1.2.3garbage'), '1.2.3')


class TestValidateVersion(unittest.TestCase):
    def test_same(self):
        row = get_row('1.0.0', '1.0.0', True)
        self.assertTrue(is_compatible(row, '1.0.0'))

    def test_eq_first(self):
        row = get_row('1.0.0', '2.0.0', False)
        self.assertTrue(is_compatible(row, '1.0.0'))

    def test_eq_last(self):
        row = get_row('1.0.0', '2.0.0', False)
        self.assertFalse(is_compatible(row, '2.0.0'))

    def test_incomplete(self):
        row = get_row('2', '2.0', True)
        self.assertTrue(is_compatible(row, '2.0.'))


if __name__ == '__main__':
    unittest.main()
