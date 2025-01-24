import os
import re
import sys
from os.path import join
from pathlib import Path
from typing import Dict, List, Optional

from semver import Version

import odm_validation.utils as utils
from odm_validation.versions import parse_version


_odm_dir = join(utils.get_asset_dir(), 'odm')


def get_table_names_filepath(v: Version) -> str:
    return join(_odm_dir, f'tables-v{v}.txt')


def _get_odm_versions() -> list[Version]:
    '''returns list of current versions (not including legacy versions)'''
    versions = []
    for path in Path(_odm_dir).glob('tables-v*'):
        name = os.path.basename(path)
        if not (match := re.search('v(.+)', name)):
            continue
        v = parse_version(match.group(1), verbose=False)
        if v.major < 2:
            continue
        versions.append(v)
    if len(versions) == 0:
        sys.exit("failed to get latest ODM version")
    versions.sort()
    return versions


CURRENT_VERSIONS = _get_odm_versions()
CURRENT_VERSION_STRS = list(map(str, CURRENT_VERSIONS))
VERSION = CURRENT_VERSIONS[-1]
VERSION_STR = str(VERSION)
LEGACY_VERSIONS = sorted([
    Version(major=1),
    Version(major=1, minor=1),
])


def _load_table_names() -> Dict[Version, List[str]]:
    '''load ODM table names'''
    result = {}
    for v in LEGACY_VERSIONS + [VERSION]:
        path = get_table_names_filepath(v)
        with open(path, 'r') as f:
            tables = f.read().splitlines()
            result[v] = tables
    return result


TABLE_NAMES = _load_table_names()


def infer_table(name: str, v: Version) -> Optional[str]:
    '''infer actual ODM table name from sheet/file-name'''
    for table_id in TABLE_NAMES[v]:
        if name.endswith(table_id):
            return table_id
    return None
