#!/usr/bin/env python3

import os
import sys
import tempfile
from functools import reduce
from math import ceil
from os.path import basename, join, normpath, splitext
from pathlib import Path
from typing import List, Optional
# from pprint import pprint

from xlsx2csv import Xlsx2csv

root_dir = join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(join(root_dir, 'src'))

import odm_validation.reports as reports  # noqa:E402
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
        if sheet_name.endswith(' ' + table_id):
            return table_id


def write_results(report, outdir: str, name: str):
    entries = {
        ErrorKind.WARNING: report.warnings,
        ErrorKind.ERROR: report.errors,
    }
    for kind in ErrorKind:
        outfile = os.path.join(outdir, name + f'_{kind.value}s.txt')
        messages = list(map(lambda x: x['message'], entries[kind]))
        with open(outfile, 'w') as f:
            f.write('\n'.join(messages))


def write_summary(text: Optional[str], outdir):
    if not text:
        text = 'no errors'
    outfile = os.path.join(outdir, 'summary.txt')
    with open(outfile, 'w') as f:
        f.write(text)


def gen_summary(summary: reports.ValidationSummary) -> Optional[str]:
    result = '# error summary\n'
    total = 0
    for table_id, table_summary in summary.table_summaries.items():
        result += f'\n## {table_id}\n'
        table_count_max = reduce(lambda a, b: max(a, b),
                                 table_summary.error_counts.values())
        width = len(str(table_count_max))
        for rule_id, count in table_summary.error_counts.items():
            result += f'- {count:{width}d} {rule_id}\n'
            total += count
    if total == 0:
        return
    return result


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

    full_summary = reports.ValidationSummary()
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
        if report.valid():
            continue
        full_summary.table_summaries[table_id] = \
            report.summary.table_summaries[table_id]
        write_results(report, outdir, name)

    summary_text = gen_summary(full_summary)
    write_summary(summary_text, outdir)

    print()
    print(summary_text)

    print(f'output dir: {outdir}')
    print('done!')


if __name__ == '__main__':
    main()
