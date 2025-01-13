import json
import os
from enum import Enum
from typing import IO, Optional

import yaml

from odm_validation.reports import ErrorKind, ValidationReport


class ReportFormat(Enum):
    """Report file format."""
    TXT = 'txt'
    JSON = 'json'
    YAML = 'yaml'


def get_ext(path: Optional[str]) -> str:
    """returns path file extension without dot"""
    if not path:
        return
    ext = os.path.splitext(path)[1]
    if len(ext) > 1:
        return ext[1:]


def detect_report_format_from_path(path: Optional[str]
                                   ) -> Optional[ReportFormat]:
    ext = get_ext(path)
    try:
        return ReportFormat[ext.upper()]
    except KeyError:
        if ext.lower() == 'yml':
            return ReportFormat.YAML


def detect_report_format_from_content(data: str) -> Optional[ReportFormat]:
    end = data.find('\n')
    line = data[:end]
    if len(line) == 0:
        return
    elif line[0] == '#':
        return ReportFormat.TXT
    elif line[0] == '{':
        return ReportFormat.JSON
    elif line.startswith('---') or ':' in line:
        return ReportFormat.YAML


def write_txt_report(output: IO, report):
    # XXX: Make sure to start txt format output with '#' to be able to infer
    # the format later. '#' is chosen because it's how a text/markdown document
    # usually begins.
    def get_msg(e) -> str:
        return e['message']
    errorkind_messages = {
        ErrorKind.ERROR: list(map(get_msg, report.errors)),
        ErrorKind.WARNING: list(map(get_msg, report.warnings))
    }
    for error_kind, messages in errorkind_messages.items():
        error_name = error_kind.value.capitalize()
        n = len(messages)
        output.write(f'## {error_name}s: {n}\n')
        if n == 0:
            continue
        output.write(('-' * 79) + '\n')
        output.write('\n'.join(messages) + '\n\n')


def write_json_report(output: IO, report: ValidationReport):
    json.dump(report, output)


def write_yaml_report(output: IO, report: ValidationReport):
    # XXX: dump dict to avoid yaml-tags from class types
    yaml.dump(report.__dict__, output)


def read_report_from_file(file) -> ValidationReport:
    # - data is normalized as text/json before being deserialized into obj
    # - must use yaml.safe_load to avoid running arbitrary python code on
    #   the user machine
    raw_data: str = file.read()
    fmt = detect_report_format_from_content(raw_data)  # only peeks
    report_obj = None
    if fmt == ReportFormat.JSON:
        report_obj = json.loads(raw_data)
    elif fmt == ReportFormat.YAML:
        report_obj = yaml.safe_load(raw_data)
    elif fmt == ReportFormat.TXT:
        quit(f'report format {fmt} can\'t be summarized')
    else:
        quit('unable to detect report format')
    assert type(report_obj) is not str, \
           "report data should be dict/obj, but was loaded as string"
    report = ValidationReport(**report_obj)
    return report


def read_report(path: str) -> ValidationReport:
    with open(path, 'r') as f:
        return read_report_from_file(f)
