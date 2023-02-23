#!/usr/bin/env python3

import os
import sys
import tempfile
from math import ceil
from os.path import basename, join, normpath, splitext
from pathlib import Path
from typing import List, Optional
from pprint import pprint

from xlsx2csv import Xlsx2csv

root_dir = join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(join(root_dir, 'src'))

import odm_validation.utils as utils  # noqa:E402
from odm_validation.reports import ErrorKind  # noqa:E402
from odm_validation.validation import _validate_data_ext  # noqa:E402


def import_xlsx(src_file, dst_dir) -> List[str]:
    "Returns list of imported csv files."
    result = []
    print(f'importing {basename(src_file)}')
    xl = Xlsx2csv(src_file)
    for sheet in xl.workbook.sheets:
        name = sheet['name']
        csv_path = join(dst_dir, name + '.csv')
        sheet_id = xl.getSheetIdByName(name)
        print(f'converting sheet {name}...', flush=True)
        xl.convert(csv_path, sheet_id)
        result.append(csv_path)
    return result


def get_sheet_table_id(schema, sheet_name) -> Optional[str]:
    table_ids = list(schema['schema'].keys())
    for table_id in table_ids:
        if table_id in sheet_name:
            return table_id


def write_results(report, kind: ErrorKind, outdir: str, name: str):
    outfile = os.path.join(outdir, name + f'_{kind.value}s.txt')
    entries = report.errors if kind == ErrorKind.ERROR else report.warnings
    messages = list(map(lambda x: x['message'], entries))
    with open(outfile, 'w') as f:
        f.write('\n'.join(messages))


def filename_without_ext(path):
    return splitext(basename(path))[0]


def on_progress(action, table_id, offset, total):
    percent = int(ceil(offset/total * 100))
    print('\r' + f'{action}: {percent}%', end='', flush=True)
    if offset == total:
        print()


def main():
    xlsx_file = sys.argv[1]
    ver = sys.argv[2]

    dir = os.path.dirname(os.path.realpath(__file__))
    asset_dir = join(dir, '../assets')
    schema_dir = Path(normpath(join(asset_dir, 'validation-schemas')))
    schema_file = join(schema_dir, f'schema-v{ver}.yml')

    schema = utils.import_schema(schema_file)

    outdir = tempfile.mkdtemp(suffix='-'+filename_without_ext(xlsx_file))
    print(f'writing files to {outdir}\n')

    csv_files = import_xlsx(xlsx_file, outdir)
    for file in csv_files:
        name = filename_without_ext(file)
        print(f'\nvalidating sheet "{name}" ', end='', flush=True)
        data = utils.import_dataset(file)
        table_id = get_sheet_table_id(schema, name)
        if not table_id:
            print('-- SKIPPING: unable to infer table name')
            continue
        print(f'(table {table_id}) ...')
        data = {table_id: data}
        report = _validate_data_ext(schema, data, ver,
                                    on_progress=on_progress)
        write_results(report, ErrorKind.WARNING, outdir, name)
        write_results(report, ErrorKind.ERROR, outdir, name)

    print()
    print('done!')


if __name__ == '__main__':
    main()
