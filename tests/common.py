"""
This file is imported into all tests, and ensures that they can import the main
package modules.
"""

import os
import sys
from os.path import join

unused_import_dummy = 0


def setup_import_path():
    global __package__
    if __package__ not in {None, ''}:
        return
    __package__ = 'tests'
    dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = join(dir, '..')
    src_dir = join(root_dir, 'src')
    pkg_dir = join(src_dir, 'odm_validation')
    sys.path.append(pkg_dir)


setup_import_path()

import utils  # noqa:E402
from schemas import Schema  # noqa:E402


def import_schema_v2() -> Schema:
    dir = os.path.dirname(os.path.realpath(__file__))
    path = join(dir, '../assets/validation-schemas/schema-v2.0.0-rc.1.yml')
    return utils.import_schema(path)
