#!/usr/bin/env python3

import os
import re
import sys
from os.path import join
from pathlib import Path
sys.path.append(join(os.path.dirname(os.path.realpath(__file__)), '../src'))

from odm_validation.validation import generate_validation_schema
import odm_validation.utils as utils


def main():
    dir = os.path.dirname(os.path.realpath(__file__))
    asset_dir = join(dir, '../../../assets')
    schema_dir = join(asset_dir, 'validation-schemas')
    dataset_dir = join(asset_dir, 'datasets')

    p = Path(dataset_dir)
    for parts_file in list(p.glob('parts-v*.csv')):
        parts_filename = os.path.basename(parts_file)
        if not (match := re.search('parts-v(.+).csv', parts_filename)):
            continue
        version = match.group(1)
        parts = utils.import_dataset(parts_file)
        schema = generate_validation_schema(parts, version)
        schema_filename = f'schema-v{version}.yml'
        utils.export_schema(schema, join(schema_dir, schema_filename))


if __name__ == "__main__":
    main()
