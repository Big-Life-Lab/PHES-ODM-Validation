import unittest

import common
from reports import DataKind, get_row_num

common.unused_import_dummy = 1


class TestReports(common.OdmTestCase):
    def test_get_row_num(self):
        self.assertEqual(get_row_num(0, 0, DataKind.python), 1)
        self.assertEqual(get_row_num(1, 0, DataKind.python), 2)
        self.assertEqual(get_row_num(2, 10, DataKind.python), 13)

        self.assertEqual(get_row_num(0, 0, DataKind.spreadsheet), 2)
        self.assertEqual(get_row_num(1, 0, DataKind.spreadsheet), 3)
        self.assertEqual(get_row_num(2, 10, DataKind.spreadsheet), 14)


if __name__ == '__main__':
    unittest.main()
