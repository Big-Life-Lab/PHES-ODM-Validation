#!/usr/bin/env python3

import logging
import os
import sys
from os.path import join, normpath, relpath
from pathlib import Path

import odm_validation.odm as odm
import odm_validation.schemas as schemas
import odm_validation.utils as utils
from odm_validation.validation import generate_validation_schema
from odm_validation.versions import Version


PARTS_FILENAME = 'parts.csv'
SETS_FILENAME = 'sets.csv'

tool_dir = Path(__file__).parent
root_dir = tool_dir.parent.parent.parent

# setup logging
log_dir = normpath(join(utils.get_pkg_dir(), 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = join(log_dir, 'generate_assets.log')
logging.basicConfig(
    level=logging.WARNING,
    handlers=[
        logging.StreamHandler(stream=sys.stderr),
        logging.FileHandler(log_file)
    ],
)


def generate_schema_from_version(dict_dir: str, schema_dir: str,
                                 version: Version) -> None:
    dict_ver = 'v2.0.0' if version.major < 2 else f'v{version}'
    odm_dir = join(dict_dir, dict_ver)
    parts = utils.import_dataset(join(odm_dir, PARTS_FILENAME))
    sets = utils.import_dataset(join(odm_dir, SETS_FILENAME))

    filename = f'schema-v{version}.yml'
    path = join(schema_dir, filename)
    print(f'generating {filename}')

    schema = generate_validation_schema(parts, sets, str(version))
    schemas.export_schema(schema, path)

    # generate file with table names, for table inference
    path = odm.get_table_names_filepath(version)
    filename = os.path.basename(path)
    print(f'generating {filename}')
    with open(path, 'w') as f:
        tables = list(schema['schema'])
        f.write(os.linesep.join(tables))


def main() -> None:
    # NOTE:
    # v1 schemas are generated from the v2.0 dictionary because v1-values are
    # absent from v2.1+.
    # v2 schemas are generated from their respective dictionary version.
    # Ex: schema v2.1 is generated from dictionary v2.1.
    asset_dir = utils.get_asset_dir()
    schema_dir = normpath(join(asset_dir, 'validation-schemas'))
    dict_dir = normpath(join(asset_dir, 'dictionary'))
    print(f'reading dictionaries from {relpath(dict_dir)}')
    print(f'writing schemas to {schema_dir}')
    for v in (odm.LEGACY_VERSIONS + odm.CURRENT_VERSIONS):
        generate_schema_from_version(dict_dir, schema_dir, v)
    print('done')


if __name__ == "__main__":
    main()
