import unittest

import common
from stdext import deduplicate_dict_list

common.unused_import_dummy = 1


class TestStdExt(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_deduplicate_dict_list(self):
        d = {'a': 1}
        self.assertEqual(deduplicate_dict_list([d, d]), [d])


if __name__ == '__main__':
    unittest.main()
