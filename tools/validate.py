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

import typer
from xlsx2csv import Xlsx2csv

root_dir = join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(join(root_dir, 'src'))

import odm_validation.part_tables as pt  # noqa:E402
import odm_validation.reports as reports  # noqa:E402
import odm_validation.utils as utils  # noqa:E402
from odm_validation.reports import ErrorKind  # noqa:E402
from odm_validation.validation import _validate_data_ext, DataKind  # noqa:E402


def import_xlsx(src_file, dst_dir) -> List[str]:
    "Returns list of imported csv files."
    result = []
    print(f'importing {basename(src_file)}')
    os.makedirs(dst_dir, exist_ok=True)
    xl = Xlsx2csv(src_file, skip_empty_lines=True)
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
        messages = list(map(lambda x: x['message'], entries[kind]))
        if len(messages) == 0:
            continue
        outfile = os.path.join(outdir, name + f'-{kind.value}s.txt')
        with open(outfile, 'w') as f:
            f.write('\n'.join(messages))


def write_summary(text: Optional[str], outdir):
    outfile = os.path.join(outdir, 'summary.txt')
    with open(outfile, 'w') as f:
        f.write(text)


def gen_summary(summary: reports.ValidationSummary) -> str:
    "Returns a text summary report with error counts."
    # The error counts are formatted with 'width' to make subsequent error
    # counts line up nicely in the output.
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
        result += '\nno errors'
    return result


def filename_without_ext(path):
    return splitext(basename(path))[0]


def on_progress(action, table_id, offset, total):
    percent = int(ceil(offset/total * 100))
    print('\r' + f'{action}: {percent}%', end='', flush=True)
    if offset == total:
        print()


DEF_VER = pt.ODM_VERSION_STR

XLSX_FILE_DESC = "path to input file (excel/xlsx)"
VERSION_DESC = "ODM version to validate against"
OUTDIR_DESC = "Output directory for generated files"


def main(xlsx_file: str = typer.Argument(..., help=XLSX_FILE_DESC),
         version: str = typer.Option(default=DEF_VER, help=VERSION_DESC),
         outdir: str = typer.Option(default="", help=OUTDIR_DESC)):

    if not outdir:
        outdir = tempfile.mkdtemp(suffix='-'+filename_without_ext(xlsx_file))
    csvdir = join(outdir, 'csv-files')
    print(f'writing files to {outdir}\n')

    csv_files = import_xlsx(xlsx_file, csvdir)

    dir = os.path.dirname(os.path.realpath(__file__))
    asset_dir = join(dir, '../assets')
    schema_dir = Path(normpath(join(asset_dir, 'validation-schemas')))
    schema_file = join(schema_dir, f'schema-v{version}.yml')
    schema = utils.import_schema(schema_file)

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
        report = _validate_data_ext(schema, data, DataKind.spreadsheet,
                                    version, on_progress=on_progress)
        if report.valid():
            continue
        full_summary.table_summaries[table_id] = \
            report.summary.table_summaries[table_id]
        write_results(report, outdir, name)

    summary_text = gen_summary(full_summary)
    write_summary(summary_text, outdir)

    print()
    print(summary_text)

    print()
    print(f'output dir: {outdir}')
    print('done!')


if __name__ == '__main__':
    typer.run(main)
