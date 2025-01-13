#!/usr/bin/env python3

import logging
import os
import re
import sys
from logging import warning
from os.path import join, normpath, relpath
from pathlib import Path
from semver import Version

import odm_validation.schemas as schemas
import odm_validation.utils as utils
from odm_validation.validation import generate_validation_schema
from odm_validation.versions import parse_version


PARTS_FILENAME = 'parts.csv'
SETS_FILENAME = 'sets.csv'
LEGACY_SCHEMA_VERSIONS = sorted([
    Version(major=1),
    Version(major=1, minor=1),
])

tool_dir = Path(__file__).parent
root_dir = tool_dir.parent.parent.parent

# setup logging
log_dir = normpath(join(utils.get_pkg_dir(), 'logs'))
log_file = join(log_dir, 'generate_schemas.log')
logging.basicConfig(
    level=logging.WARNING,
    handlers=[
        logging.StreamHandler(stream=sys.stderr),
        logging.FileHandler(log_file)
    ],
)


def generate_schema_for_version(parts, sets, version, schema_dir):
    filename = f'schema-v{version}.yml'
    path = join(schema_dir, filename)
    print(f'generating {os.path.basename(path)}')
    schema = generate_validation_schema(parts, sets, version)
    schemas.export_schema(schema, path)


def generate_schemas_from_odm_tables(odm_dir, schema_dir):
    print(f'using {relpath(odm_dir)}')
    path_version_re = '.+/v(.+)/?'
    if not (match := re.search(path_version_re, odm_dir)):
        return
    odm_version = parse_version(match.group(1))
    parts = utils.import_dataset(join(odm_dir, PARTS_FILENAME))
    sets = utils.import_dataset(join(odm_dir, SETS_FILENAME))
    for version in (LEGACY_SCHEMA_VERSIONS + [odm_version]):
        assert version <= odm_version
        generate_schema_for_version(parts, sets, str(version), schema_dir)


def main():
    asset_dir = utils.get_asset_dir()
    schema_dir = normpath(join(asset_dir, 'validation-schemas'))
    dataset_dir = normpath(join(asset_dir, 'dictionary'))

    print(f'looking for ODM-tables in {dataset_dir}')
    p = Path(dataset_dir)
    odm_dirs = list(map(str, p.glob('v*')))
    if len(odm_dirs) == 0:
        warning('no files found')
    else:
        print(f'writing schemas to {schema_dir}')

    for odm_dir in odm_dirs:
        generate_schemas_from_odm_tables(odm_dir, schema_dir)
    print('done')


if __name__ == "__main__":
    main()
