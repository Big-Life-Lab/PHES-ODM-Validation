import os
import sys
from os.path import join
from pathlib import Path
from typing import Dict, List, Optional

from semver import Version

import odm_validation.utils as utils
from odm_validation.versions import parse_version


LEGACY_VERSIONS = sorted([
    Version(major=1),
    Version(major=1, minor=1),
])


# the following directories are used by asset generation, and should always
# point to directories in the dev. repo.
_this_dir = os.path.dirname(os.path.realpath(__file__))
_repo_dir = join(_this_dir, '..', '..')
_repo_dict_dir = join(_repo_dir, 'assets', 'dictionary')

# the odm dir is included in the package, so it needs to use the dynamic asset
# path
_odm_dir = join(utils.get_asset_dir(), 'odm')


def get_table_names_filepath(v: Version) -> str:
    return join(_odm_dir, f'tables-v{v}.txt')


def _load_table_names() -> Dict[Version, List[str]]:
    '''load ODM table names'''
    # XXX: the table files are generated by the asset generation script, and so
    # they may not exist before running that script. That script also uses this
    # module, but not these table names, so it's not a circular dependency and
    # everything is fine
    result = {}
    prefix = 'tables-v'
    for path in Path(_odm_dir).glob(f'{prefix}*'):
        name = os.path.basename(path)
        v = parse_version(name[len(prefix):], verbose=False)
        assert str(path) == get_table_names_filepath(v)
        with open(path, 'r') as f:
            tables = f.read().splitlines()
            result[v] = tables
    return result


TABLE_NAMES = _load_table_names()


def _get_odm_versions() -> list[Version]:
    '''returns list of current versions (not including legacy versions)'''
    walk_default = ('', [], [])
    dirnames = next(os.walk(_repo_dict_dir), walk_default)[1]
    versions: List[Version] = []
    if len(dirnames) == 0:
        # if run from a package, then dictionaries aren't available and
        # versions from table-files are used instead
        versions = list(TABLE_NAMES.keys())
    else:
        for dir in dirnames:
            name = os.path.basename(dir)
            assert name.startswith('v')
            v = parse_version(name[1:], verbose=False)
            versions.append(v)
    versions = list(filter(lambda v: v.major >= 2, versions))
    if len(versions) == 0:
        sys.exit("failed to get latest ODM version")
    versions.sort()
    return versions


CURRENT_VERSIONS = _get_odm_versions()
CURRENT_VERSION_STRS = list(map(str, CURRENT_VERSIONS))
VERSION = CURRENT_VERSIONS[-1]
VERSION_STR = str(VERSION)


def infer_table(name: str, v: Version) -> Optional[str]:
    '''infer actual ODM table name from sheet/file-name'''
    for table_id in TABLE_NAMES[v]:
        if name.endswith(table_id):
            return table_id
    return None
