import shutil
import unittest
import os
from os.path import join, relpath

import common

cwd = os.getcwd()
asset_dir = relpath(join(common.root_dir, join('assets', 'tools')), cwd)
tools_dir = relpath(join(common.root_dir, 'tools'), cwd)
validate_tool = relpath(join(tools_dir, 'validate.py'), cwd)
summarize_tool = relpath(join(tools_dir, 'summarize.py'), cwd)


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
        expected_summary = relpath(join(asset_dir, 'summary.csv'))
        v = f'{validate_tool} --version=1.1.0 --format=yaml'
        s = f'{summarize_tool}'
        d = f'diff {expected_summary} -'
        self.cmd(f'{v} {asset_dir}/*.csv 2> /dev/null | {s} | {d}')


if __name__ == '__main__':
    unittest.main()
