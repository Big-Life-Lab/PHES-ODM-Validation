#!/usr/bin/env python3

import os
import sys
import tempfile
from enum import Enum
from math import ceil
from os.path import basename, join, splitext
from typing import IO, Optional


import typer
from semver import Version
from xlsx2csv import Xlsx2csv

import odm_validation.odm as odm
import odm_validation.part_tables as pt
import odm_validation.utils as utils
from odm_validation.reports import ErrorVerbosity
from odm_validation.schemas import import_schema
from odm_validation.validation import _validate_data_ext, DataKind

from odm_validation.reports import (
    ErrorKind,
    ValidationReport,
    join_reports
)

from odm_validation.tools.reportutils import (
    ReportFormat,
    detect_report_format_from_path,
    get_ext,
    write_json_report,
    write_txt_report,
    write_yaml_report,
)


class DataFormat(Enum):
    CSV = 'csv'
    XLSX = 'xlsx'


DEF_VER = odm.VERSION_STR

DATA_FILE_DESC = "Path of input files (xlsx/csv)."
VERSION_DESC = "ODM version to validate against."
OUT_DESC = "Output path of validation report. Defaults to stdout/console."
FORMAT_DESC = "Output format. Defaults to txt if unable to autodetect."
VERB_DESC = "Error message verbosity, between 0 and 2."


def info(s: str = "", line: bool = True) -> None:
    file = sys.stderr
    if line:
        print(s, file=file)
    else:
        print(s, file=file, end='', flush=True)


def import_xlsx(src_file: str, dst_dir: str) -> list[str]:
    "Returns list of imported csv files."
    result = []
    info(f'importing {basename(src_file)}')
    os.makedirs(dst_dir, exist_ok=True)
    xl = Xlsx2csv(src_file, skip_empty_lines=True)
    for sheet in xl.workbook.sheets:
        name = sheet['name']
        csv_path = join(dst_dir, name + '.csv')
        sheet_id = xl.getSheetIdByName(name)
        info(f'converting sheet {name}...')
        xl.convert(csv_path, sheet_id)
        result.append(csv_path)
    return result


def filename_without_ext(path: str) -> str:
    return splitext(basename(path))[0]


def on_progress(action: str, table_id: str, offset: int, total: int) -> None:
    percent = int(ceil(offset/total * 100))
    info('\r' + f'# {table_id:20} \t{action} {percent}%', line=False)


def enum_values(E) -> list[str]:  # type: ignore
    return list(map(lambda e: e.value, iter(E)))


def detect_data_format(path: str) -> Optional[DataFormat]:
    ext = get_ext(path)
    try:
        return DataFormat[ext.upper()]
    except KeyError:
        return None


def get_schema_path(version: str) -> str:
    asset_dir = utils.get_asset_dir()
    schema_dir = join(asset_dir, 'validation-schemas')
    schema_filename = f'schema-v{version}.yml'
    return join(schema_dir, schema_filename)


def convert_excel_to_csv(path: str) -> list[str]:
    """Returns list of csv file paths."""
    tmpdir = tempfile.mkdtemp(suffix='-'+filename_without_ext(path))
    csvdir = join(tmpdir, 'csv-files')
    info(f'writing intermediary files to {tmpdir}\n')
    return import_xlsx(path, csvdir)


def infer_tables(in_paths: list, version: Version) -> dict[pt.TableId, str]:
    result = {}
    for in_path in in_paths:
        name = filename_without_ext(in_path)
        table_id = odm.infer_table(name, version)
        if not table_id:
            info(f'sheet "{name}": unable to infer table name')
            continue
        result[table_id] = in_path
    if len(result) == 0:
        info('no tables recognized. Did you specify the correct ODM version?')
        quit(1)
    info('found tables:')
    for table_id in result:
        info(f'- {table_id}')
    return result


def load_db_data(tables: dict[pt.TableId, str]) -> dict:
    info('\nloading data...')
    result = {}
    for table_id, path in tables.items():
        result[table_id] = utils.import_dataset(path)
    return result


def strip_report(report: ValidationReport) -> None:
    """Removes the error debug fields 'validationRuleFields' and
    'row'/'rows'."""
    errorkind_errors = {
        ErrorKind.ERROR: report.errors,
        ErrorKind.WARNING: report.warnings,
    }
    for errors in errorkind_errors.values():
        for e in errors:
            e.pop('validationRuleFields', None)
            e.pop('row', None)
            e.pop('rows', None)


def write_report(output: IO, report: ValidationReport, fmt: ReportFormat
                 ) -> None:
    if fmt == ReportFormat.TXT:
        write_txt_report(output, report)
    elif fmt == ReportFormat.JSON:
        write_json_report(output, report)
    elif fmt == ReportFormat.YAML:
        write_yaml_report(output, report)


# XXX: locals must be disabled to avoid `schema` being dumped to console on an
# exception (which makes it unreadable)
app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def main_cli(
    data_file: list[str] = typer.Argument(default=..., help=DATA_FILE_DESC),
    version: str = typer.Option(default=DEF_VER, help=VERSION_DESC),
    out: str = typer.Option(default="", help=OUT_DESC),
    format: Optional[ReportFormat] = typer.Option(default=None,
                                                  help=FORMAT_DESC),
    verbosity: int = typer.Option(default=2, help=VERB_DESC)
) -> None:
    out_path = out
    out_fmt = format
    in_paths: list = data_file
    in_fmt = detect_data_format(in_paths[0])

    if not in_fmt:
        info(f'Invalid data file type for "{os.path.basename(in_paths[0])}". '
             f'Valid file types are {enum_values(DataFormat)}.')
        quit(1)

    assert in_fmt != DataFormat.XLSX or len(in_paths) == 1, \
           'multiple excel files are not supported'

    for path in in_paths:
        fmt = detect_data_format(path)
        assert fmt == in_fmt, 'all input files must have the same format'

    if not out_fmt:
        if out_path:
            out_fmt = detect_report_format_from_path(out_path)
            if not out_fmt:
                out_fmt = ReportFormat.TXT
                info('Unable to infer output format from filename, ' +
                     f'using {out_fmt}.')
        else:
            out_fmt = ReportFormat.TXT
    assert out_fmt

    schema_path = get_schema_path(version)
    schema = import_schema(schema_path)

    if out_path:
        info(f'writing result to {out_path}\n')

    output = open(out_path, 'w') if out_path else sys.stdout
    try:
        info(f'validating {in_paths}')
        info(f'using schema "{os.path.basename(schema_path)}"')

        if in_fmt == DataFormat.XLSX:
            in_paths = convert_excel_to_csv(in_paths[0])
        tables = infer_tables(in_paths, Version.parse(version))
        db_data = load_db_data(tables)

        def validate(data: dict[pt.TableId, pt.Dataset]) -> ValidationReport:
            report = _validate_data_ext(schema, data, DataKind.spreadsheet,
                                        version, on_progress=on_progress,
                                        with_metadata=False,
                                        verbosity=ErrorVerbosity(verbosity))
            strip_report(report)
            info()  # newline after progressbar

            # XXX: just in case the validation wrote anything to the console,
            # to avoid race-conditions with upcoming report output
            sys.stdout.flush()
            sys.stderr.flush()
            return report

        # TODO: we should write continuously to output when the user is
        # watching in realtime on the terminal, however, stdout can be piped to
        # somewhere else, so we should detect and take that into account
        info()
        is_terminal = out_fmt == ReportFormat.TXT and not out_path
        if is_terminal:
            for table_id, table_data in db_data.items():
                report = validate({table_id: table_data})
                write_report(output, report, ReportFormat.TXT)
                info()
        else:
            main_report = None
            for table_id, table_data in db_data.items():
                report = validate({table_id: table_data})
                main_report = join_reports(main_report, report)
            assert main_report
            write_report(output, main_report, out_fmt)

        # XXX: report data doesn't have newline at the end, so we need to add
        # it here
        info()

        # XXX: flush to prevent race-condition between stdout and stderr, due
        # to cached writing of the big reports
        sys.stdout.flush()
    finally:
        if out_path:
            output.close()

    info()
    if out_path:
        info(f'result file: {out_path}')
    info('done!')


def main() -> None:
    # XXX: needed to make odm-validate work
    # runs main_cli
    app()


if __name__ == '__main__':
    main()
