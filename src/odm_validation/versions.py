import os
import re
import toml
from dataclasses import dataclass
from enum import Enum
from importlib import metadata
from logging import warning
from os import path
from semver import Version
from typing import Optional, Tuple

from utils import meta_get


# __all__ = [
#     '__version__',
#     'Version',
#     'get_mapping',
#     'is_compatible',
#     'parse_version',
# ]


class MapKind(Enum):
    TABLE = 0
    ATTRIBUTE = 1
    CATEGORY = 2


# TODO: rename id to part_id?
@dataclass(frozen=True)
class Mapping:
    kind: MapKind
    id: str
    table: str
    meta: dict


def _get_package_version():
    try:
        return metadata.version("odm_validation")
    except metadata.PackageNotFoundError:
        dir = os.path.abspath(os.path.dirname(__file__))
        proj = path.join(dir, '../../pyproject.toml')
        return toml.load(proj)['project']['version']


__version__ = _get_package_version()

BASEVERSION = re.compile(
    r"""[vV]?
        (?P<major>0|[1-9]\d*)
        (\.
        (?P<minor>0|[1-9]\d*)
        (\.
            (?P<patch>0|[1-9]\d*)
        )?
        )?
    """,
    re.VERBOSE,
)

V1_KIND_MAP = {
    'tables': MapKind.TABLE,
    'variables': MapKind.ATTRIBUTE,
    'variableCategories': MapKind.CATEGORY,
}


def _coerce(version: str) -> Tuple[Version, Optional[str]]:
    """
    Convert an incomplete version string into a semver-compatible Version
    object.

    * Tries to detect a "basic" version string (``major.minor.patch``).
    * If not enough components can be found, missing components are
        set to zero to obtain a valid semver version.

    :param str version: the version string to convert
    :return: a tuple with a :class:`Version` instance (or ``None``
        if it's not a version) and the rest of the string which doesn't
        belong to a basic version.
    :rtype: tuple(:class:`Version` | None, str)

    This function is taken from:
    https://python-semver.readthedocs.io/en/3.0.0-dev.3/usage.html?highlight=coerce#dealing-with-invalid-versions
    """

    match = BASEVERSION.search(version)
    if not match:
        return (None, version)

    iter = match.groupdict().items()
    ver = {
        key: (0 if value is None else value) for key, value in iter
    }
    ver = Version(**ver)
    rest = match.string[match.end() :]  # noqa:E203
    return ver, rest


def parse_version(version: str, id='', label='', default: Version = None
                  ) -> Version:
    origin = '' if id == '' and label == '' else f'for "{id}.{label}"'
    correctionMsg = 'corrected version 0 --> {} ' + origin

    if version is None or version == '':
        if not default:
            raise ValueError(f'missing version {origin}')
        warning(correctionMsg.format(default))
        return default

    try:
        return Version.parse(version)
    except ValueError:
        (result, _) = _coerce(version)
        warning(correctionMsg.format(result))
        return result


def parse_row_version(row, field, default=None):
    return parse_version(row.get(field), row.get('partID'), field, default)


def is_compatible(part: dict, version: Version) -> bool:
    # TODO: remove default for `firstReleased` when parts-v2 is complete
    row = part
    v1 = Version(major=1)
    first = parse_row_version(row, 'firstReleased', default=v1)
    last = parse_row_version(row, 'lastUpdated', default=first)
    active: bool = row.get('status') == 'active'

    # not (v < first) and ((v < last) or active)
    v = version
    if v.compare(first) < 0:
        return False
    if v.compare(last) < 0:
        return True
    return active


def get_mapping(part: dict, version: Version) -> Mapping:
    """Returns `None` when no mapping exists."""
    if version.major != 1:
        return
    meta = {}
    table = meta_get(meta, part, 'version1Table')
    loc = meta_get(meta, part, 'version1Location')
    kind = V1_KIND_MAP.get(loc)
    if kind == MapKind.TABLE:
        id = table
    else:
        id = meta_get(meta, part, 'version1Variable')
    if not (kind and table and id):
        return
    return Mapping(kind=kind, id=id, table=table, meta=meta)


def has_mapping(part: dict, version: Version) -> bool:
    return get_mapping(part, version) is not None
