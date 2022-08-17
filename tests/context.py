"""
This file is imported into all tests, and ensures that they can import the main
package modules.
"""

import os
import sys

unused_import_dummy = 0


def setup_path():
    global __package__
    if __package__ not in {None, ""}:
        return
    __package__ = "tests"
    dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.join(dir, "..")
    src_dir = os.path.join(root_dir, "src")
    pkg_dir = os.path.join(src_dir, "odm_validation")
    sys.path.append(pkg_dir)


setup_path()
