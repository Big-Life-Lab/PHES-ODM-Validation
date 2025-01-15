import shutil
import unittest
import os
from os.path import join, relpath

import common
from odm_validation.utils import get_pkg_dir


tool_asset_dir = join(common.ASSET_DIR, 'tools')  # from repo
tools_dir = join(get_pkg_dir(), 'tools')  # from pkg

summarize_tool = relpath(join(tools_dir, 'summarize.py'), os.getcwd())
validate_tool = 'odm-validate'


class TestSummarizeTool(common.OdmTestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('diff'):
            quit('missing "diff" executable')

    def cmd(self, s: str) -> int:
        # print(s)
        rc = os.system(s)
        self.assertEqual(0, rc)

    def test_validate_and_summarize(self):
        expected_summary = relpath(join(tool_asset_dir, 'summary.csv'))
        v = f'{validate_tool} --version=1.1.0 --format=yaml'
        s = f'{summarize_tool}'
        d = f'diff {expected_summary} -'
        self.cmd(f'{v} {tool_asset_dir}/*.csv 2> /dev/null | {s} | {d}')


if __name__ == '__main__':
    unittest.main()
