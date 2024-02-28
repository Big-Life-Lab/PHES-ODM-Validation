import unittest

import common
from stdext import keep, swapDelete, try_parse_int

common.unused_import_dummy = 1


class TestStdExt(common.OdmTestCase):
    def setUp(self):
        self.maxDiff = None

    def test_try_parse_int(self):
        self.assertEqual(try_parse_int('1'), 1)
        self.assertEqual(try_parse_int('1.0'), 1)
        self.assertIsNone(try_parse_int('1.1'))

    def test_swapDelete(self):
        x = [0, 1, 2, 3, 4, 5]
        swapDelete(x, 2)
        self.assertEqual(x, [0, 1, 5, 3, 4])

    def test_keep(self):
        a = [
            {'a': 1},
            {'target': [{'a': 1}]},
        ]
        b = [
            {'a': 1},
            {'b': [{'a': 1, 'target': 1}]},
        ]
        keep(a, 'target')
        keep(b, 'target')
        self.assertEqual(a, [{'target': [{'a': 1}]}])
        self.assertEqual(b, [{'b': [{'target': 1}]}])


if __name__ == '__main__':
    unittest.main()
