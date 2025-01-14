"""
This file is imported into all tests, and ensures that they can import the main
package modules.
"""

import logging
import unittest
from glob import glob
from os.path import join, splitext
from pathlib import Path


# TODO: make this global lower-case, since it's not constant
# FIXME: this global is unreliable, especially when assigned from the global
# scope of a (test-)module at import time
ASSET_SUBDIR = ''

# XXX: unit test currently have to be run in a development environment to have
# access to their assets. This means that we have to use a consistent local
# path instead of the dynamic 'package' path from utils.get_asset_dir.
ROOT_DIR = Path(__file__).parent.parent
ASSET_DIR = join(ROOT_DIR, 'assets')


class OdmTestCase(unittest.TestCase):
    def run(self, result=None):
        # This makes sure that tests fails when errors are logged.
        # XXX: assertNoLogs is not available in python < 3.10, so we need to do
        # an inverse check with assertLogs.
        single_entry = 'ERROR:root:this is the only valid error log entry'
        with self.assertLogs(None, logging.ERROR) as cm:
            super().run(result)
            logging.error(single_entry)
        self.assertTrue([single_entry], cm.output)

    def assertReportEqual(self, expected, report):
        self.assertEqual(expected['errors'], report.errors)
        self.assertEqual(expected['warnings'], report.warnings)


def param_range(start, stop):
    return list(map(lambda i: (i, ), range(start, stop)))


def _find_asset(glob_expr: str) -> str:
    res = glob(glob_expr)
    assert len(res) > 0, f'missing asset "{glob_expr}"'
    return res[0]


def asset(filename: str) -> str:
    """Returns path to `filename`, using `ASSET_SUBDIR`. The file extension may
    be a wildcard."""
    _, ext = splitext(filename)
    path = join(ASSET_DIR, ASSET_SUBDIR, filename)
    if ext == '.*':
        path = _find_asset(path)
    return path
