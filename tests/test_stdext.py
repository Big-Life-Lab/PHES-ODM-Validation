import unittest

import common
from stdext import try_parse_int

common.unused_import_dummy = 1


class TestStdExt(common.OdmTestCase):
    def setUp(self):
        self.maxDiff = None

    def test_try_parse_int(self):
        self.assertEqual(try_parse_int('1'), 1)
        self.assertEqual(try_parse_int('1.0'), 1)
        self.assertIsNone(try_parse_int('1.1'))


if __name__ == '__main__':
    unittest.main()
