#!/usr/bin/env python3

import logging
import os
import re
import sys
from logging import warning
from os.path import join, normpath, relpath
from pathlib import Path
from semver import Version

root_dir = join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(join(root_dir, 'src'))

import odm_validation.utils as utils  # noqa:E402
from odm_validation.validation import generate_validation_schema  # noqa:E402
from odm_validation.versions import parse_version  # noqa:E402

PARTS_FILENAME = 'parts.csv'
LEGACY_SCHEMA_VERSIONS = sorted([
    Version(major=1),
    Version(major=1, minor=1),
])

# setup logging
log_dir = normpath(join(root_dir, 'logs'))
log_file = join(log_dir, 'generate_schemas.log')
logging.basicConfig(
    level=logging.WARNING,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ],
)


def generate_schema_for_version(parts, version, schema_dir):
    filename = f'schema-v{version}.yml'
    path = join(schema_dir, filename)
    print(f'generating {os.path.basename(path)}')
    schema = generate_validation_schema(parts, version)
    utils.export_schema(schema, path)


def generate_schemas_from_parts(parts_path, schema_dir):
    print(f'using {relpath(parts_path)}')
    parts_path_regex = f'.+/v(.+)/{PARTS_FILENAME}'
    if not (match := re.search(parts_path_regex, str(parts_path))):
        return
    parts = utils.import_dataset(parts_path)
    parts_version = parse_version(match.group(1))
    for version in (LEGACY_SCHEMA_VERSIONS + [parts_version]):
        assert version <= parts_version
        generate_schema_for_version(parts, str(version), schema_dir)


def main():
    dir = os.path.dirname(os.path.realpath(__file__))
    asset_dir = join(dir, '../assets')
    schema_dir = normpath(join(asset_dir, 'validation-schemas'))
    dataset_dir = normpath(join(asset_dir, 'dictionary'))

    print(f'looking for parts in {dataset_dir}')
    p = Path(dataset_dir)
    parts_paths = list(p.glob(f'v*/{PARTS_FILENAME}'))
    if len(parts_paths) == 0:
        warning('no files found')
    else:
        print(f'writing schemas to {schema_dir}')

    for parts_path in parts_paths:
        generate_schemas_from_parts(parts_path, schema_dir)
    print('done')


if __name__ == "__main__":
    main()
