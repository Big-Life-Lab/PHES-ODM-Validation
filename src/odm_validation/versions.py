"""
The `_coerce` function is taken from:
https://python-semver.readthedocs.io/en/3.0.0-dev.3/usage.html?highlight=coerce#dealing-with-invalid-versions
"""

import os
import re
import toml
from importlib import metadata
from logging import warning
from os import path
from semver import Version
from typing import Optional, Tuple


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
    """Returns 1.0.0 when `version` is empty."""
    origin = '' if id == '' and label == '' else f'for "{id}.{label}"'
    if version is None or version == '':
        if not default:
            raise ValueError(f'missing version {origin}')
        warning(f'missing version defaulted to "{str(default)}" {origin}')
        return default
    try:
        return Version.parse(version)
    except ValueError:
        (result, _) = _coerce(version)
        warning(f'corrected version {version} --> {result} {origin}')
        return result


def parse_row_version(row, field, default=None):
    return parse_version(row.get(field), row.get('partID'), field, default)


def validate_version(row, version):
    # v < first --> False
    # first < v < last --> True
    # last <= v --> active

    first: Version = parse_row_version(row, 'firstReleased')
    last: Version = parse_row_version(row, 'lastUpdated', default=first)
    active: bool = row.get('status') == 'active'

    v = parse_version(version)
    if v.compare(first) < 0:
        return False
    if v.compare(last) < 0:
        return True
    return active
