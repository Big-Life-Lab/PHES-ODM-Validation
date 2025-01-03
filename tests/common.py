"""
This file is imported into all tests, and ensures that they can import the main
package modules.
"""

import logging
import os
import sys
import unittest
from glob import glob
from os.path import join, splitext

unused_import_dummy = 0

ASSET_DIR = ''
PKG_NAME = 'odm_validation'

_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = join(_dir, '..')


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


def setup_import_path():
    global __package__
    if __package__ not in {None, ''}:
        return
    __package__ = 'tests'
    src_dir = join(root_dir, 'src')
    pkg_dir = join(src_dir, 'odm_validation')
    sys.path.append(pkg_dir)


setup_import_path()


def param_range(start, stop):
    return list(map(lambda i: (i, ), range(start, stop)))


def _find_asset(glob_expr: str) -> str:
    res = glob(glob_expr)
    assert len(res) > 0, f'missing asset "{glob_expr}"'
    return res[0]


def asset(filename: str) -> str:
    """Returns path to `filename`, using `ASSET_DIR`. The file extension may be
    a wildcard."""
    _, ext = splitext(filename)
    path = join(ASSET_DIR, filename)
    if ext == '.*':
        path = _find_asset(path)
    return path
