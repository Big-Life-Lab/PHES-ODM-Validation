import unittest

import common
from stdext import deduplicate_dict_list, try_parse_int

common.unused_import_dummy = 1


class TestStdExt(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_deduplicate_dict_list(self):
        d = {'a': 1}
        self.assertEqual(deduplicate_dict_list([d, d]), [d])

    def test_try_parse_int(self):
        self.assertEqual(try_parse_int('1'), 1)
        self.assertEqual(try_parse_int('1.0'), 1)
        self.assertIsNone(try_parse_int('1.1'))


if __name__ == '__main__':
    unittest.main()
