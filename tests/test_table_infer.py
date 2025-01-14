import unittest

import odm_validation.odm as odm

import common


class TestTableInfer(common.OdmTestCase):
    def test(self):
        for version, tables in odm.TABLE_NAMES.items():
            for table in tables:
                self.assertEqual(odm.infer_table(table, version), table)


if __name__ == '__main__':
    unittest.main()
