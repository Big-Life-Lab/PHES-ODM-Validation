#!/usr/bin/env python3

import logging
import os
import re
import sys
from os.path import join, normpath
from pathlib import Path

root_dir = join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(join(root_dir, 'src'))

import odm_validation.utils as utils  # noqa:E402
from odm_validation.validation import generate_validation_schema  # noqa:E402
from odm_validation.versions import parse_version  # noqa:E402


# setup default logger (to file)
log_dir = normpath(join(root_dir, 'logs'))
log_file = join(log_dir, 'generate_schemas.log')
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(log_file)
    ],
)


def info(x):
    print(x)
    logging.info(x)


def warning(x):
    print(x)
    logging.warning(x)


def main():
    dir = os.path.dirname(os.path.realpath(__file__))
    asset_dir = join(dir, '../assets')
    schema_dir = normpath(join(asset_dir, 'validation-schemas'))
    dataset_dir = normpath(join(asset_dir, 'dictionary'))

    info(f'looking for parts in {dataset_dir}')
    p = Path(dataset_dir)
    sources = list(p.glob('v*/parts.csv'))
    if len(sources) == 0:
        warning('no files found')
    info(f'writing schemas to {schema_dir}')

    for parts_file in sources:
        parts_filename = os.path.basename(parts_file)
        if not (match := re.search('.+/v(.+)/parts.csv', str(parts_file))):
            continue
        v = match.group(1)
        version = str(parse_version(v))
        schema_filename = f'schema-v{version}.yml'
        info(f'converting {parts_filename} --> {schema_filename}')
        parts = utils.import_dataset(parts_file)
        schema = generate_validation_schema(parts, version)
        path = join(schema_dir, schema_filename)
        utils.export_schema(schema, path)
    info('done')


if __name__ == "__main__":
    main()
