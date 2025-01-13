import unittest

from semver import Version

from odm_validation.versions import parse_version

import common


class TestParseVersion(common.OdmTestCase):
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


if __name__ == '__main__':
    unittest.main()
