import unittest
from copy import deepcopy

import common
from stdext import deep_update, keep, swapDelete, try_parse_int

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

    def test_deep_update(self):
        a = {
            'attr': {
                'meta': [
                    {
                        'meta': [
                            {'maxLength': 10}
                        ],
                        'ruleID': 'ml'
                    }
                ]
            }
        }
        b = {
            'attr': {
                'meta': [
                    {
                        'meta': [
                            {'dataType': 'varchar'}
                        ],
                        'ruleID': 't'
                    }
                ]
            }
        }
        expected = {
            'attr': {
                'meta': [
                    {
                        'meta': [
                            {'maxLength': 10}
                        ],
                        'ruleID': 'ml'
                    },
                    {
                        'meta': [
                            {'dataType': 'varchar'}
                        ],
                        'ruleID': 't'
                    },
                ]
            }
        }
        actual = deepcopy(a)
        deep_update(actual, b)
        self.assertEqual(actual, expected)

    def test_deep_update_with_merge_dict_lists(self):
        initial = {
            'a': {
                'b': [
                    {
                        'x': [1, 2],
                        'y': True,
                    }
                ]
            }
        }
        addition = {
            'a': {
                'b': [
                    {
                        'x': [3, 4]
                    }
                ]
            }
        }
        expected = {
            'a': {
                'b': [
                    {
                        'x': [1, 2, 3, 4],
                        'y': True,
                    }
                ]
            }
        }
        actual = deepcopy(initial)
        deep_update(actual, addition, merge_dict_lists=True)
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
