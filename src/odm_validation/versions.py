"""
The `_coerce` function is taken from:
https://python-semver.readthedocs.io/en/3.0.0-dev.3/usage.html?highlight=coerce#dealing-with-invalid-versions
"""

from logging import warning
import re
from semver import Version
from typing import Optional, Tuple

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


def parse_version(version: str, id='') -> Version:
    """Returns 1.0.0 when `version` is empty."""
    if version is None or version == '':
        warning(f'corrected version 0.0.0 --> 1.0.0 for "{id}"')
        return Version(major=1)
    try:
        return Version.parse(version)
    except ValueError:
        (result, _) = _coerce(version)
        warning(f'corrected version {version} --> {result} for "{id}"')
        return result


def validate_version(row, version, id=''):
    # v < first --> False
    # first < v < last --> True
    # last <= v --> active

    first: Version = parse_version(row.get('firstReleased'), id)
    last: Version = parse_version(row.get('lastUpdated'), id)
    active: bool = row.get('status') == 'active'

    v = parse_version(version)
    if v.compare(first) < 0:
        return False
    if v.compare(last) < 0:
        return True
    return active
