#!/usr/bin/env python3

import csv
import json
import sys
import logging
import yaml
from enum import Enum
from typing import IO, Optional

import typer

from odm_validation.reports import ErrorKind, ValidationReport
from odm_validation.summarization import (
    SummarizedReport,
    SummaryEntry,
    SummaryKey,
    summarize_report
)

from odm_validation.tools.reportutils import (
    ReportFormat,
    detect_report_format_from_content,
    write_json_report,
    write_yaml_report,
)


# types
class SummaryFormat(Enum):
    CSV = 'csv'
    JSON = 'json'
    YAML = 'yaml'


# constants
REPORT_FILE_DESC = 'The report file to summarize.'
BY_DESC = ('The key(s) to summarize by. This can be specified multiple times, '
           'for instance: `--by=table --by=column`.')
ERRLVL_DESC = ('The level of detail for errors. '
               'Selecting `warning` will also include `error`.')
OUT_DESC = 'The path to write the summary file to.'
FMT_DESC = 'The output format.'


def write_csv_summary(sum_report: SummarizedReport, output: IO) -> None:
    headers = ['errorLevel'] + list(SummaryEntry.__dataclass_fields__)
    errorkind_summaries = {
        ErrorKind.ERROR: sum_report.errors,
        ErrorKind.WARNING: sum_report.warnings,
    }
    writer = csv.DictWriter(output, headers)
    writer.writeheader()
    for error_kind in ErrorKind:
        summary = errorkind_summaries[error_kind]
        row_ext = {'errorLevel': error_kind.value}
        for table_id, entries in summary.items():
            for e in entries:
                data = e.__dict__
                data['rule_id'] = data['rule_id'].name
                data['key'] = data['key'].value
                row = (row_ext | data)
                writer.writerow(row)


def write_summary(output: IO, sum_report: SummarizedReport,
                  fmt: SummaryFormat) -> None:
    if fmt == SummaryFormat.CSV:
        write_csv_summary(sum_report, output)
    elif fmt == SummaryFormat.JSON:
        write_json_report(output, sum_report)
    elif fmt == SummaryFormat.YAML:
        write_yaml_report(output, sum_report)


def read_report_from_file(file: IO) -> Optional[ValidationReport]:
    # XXX: must use yaml.safe_load to avoid running arbitrary python code on
    # the user's machine, however, it's extremely slow
    raw_data: str = file.read()
    fmt = detect_report_format_from_content(raw_data)  # only peeks
    report_obj: Optional[dict] = None
    if fmt == ReportFormat.JSON:
        report_obj = json.loads(raw_data)
    elif fmt == ReportFormat.YAML:
        logging.warn('you should use json-reports instead of yaml when ' +
                     'summarizing, since yaml parsing is extremely slow')
        report_obj = yaml.safe_load(raw_data)
    elif fmt is not None:
        logging.error(f'report format {fmt} can\'t be summarized')
    else:
        logging.error('unable to detect report format')
    if report_obj is None:
        return None
    report = ValidationReport(**report_obj)
    return report


def read_report(path: str) -> Optional[ValidationReport]:
    with open(path, 'r') as f:
        return read_report_from_file(f)


# XXX: locals are too noisy
app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def main(
    report_file: str = typer.Argument(default='', help=REPORT_FILE_DESC),
    by: list[SummaryKey] = typer.Option(default=[SummaryKey.TABLE.value],
                                        help=BY_DESC),
    errorLevel: ErrorKind = typer.Option(default=ErrorKind.ERROR.value,
                                         help=ERRLVL_DESC),
    out: str = typer.Option(default='', help=OUT_DESC),
    format: SummaryFormat = typer.Option(default=SummaryFormat.CSV.value,
                                         help=FMT_DESC)
) -> None:
    in_path = report_file
    out_fmt = format
    out_path = out
    if out_fmt == ReportFormat.TXT:
        quit(f'output format {format} is not supported yet')

    # XXX: Don't print anything before reading of input is completed, to avoid
    # pollusion of stdout when piping from the validate tool.
    if in_path:
        report = read_report(in_path)
    else:
        report = read_report_from_file(sys.stdin)
    if not report:
        quit('failed to read report')

    sum_report = summarize_report(report, by=set(by))

    output = open(out_path, 'w') if out_path else sys.stdout
    try:
        write_summary(output, sum_report, format)
    finally:
        if output != sys.stdout:
            output.close()


if __name__ == '__main__':
    app()
