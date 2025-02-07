import json
import os
from enum import Enum
from typing import IO, Optional, Union

import yaml

from odm_validation.reports import ErrorKind, ValidationReport
from odm_validation.summarization import SummarizedReport


SomeReport = Union[SummarizedReport, ValidationReport]


class ReportFormat(Enum):
    """Report file format."""
    TXT = 'txt'
    JSON = 'json'
    YAML = 'yaml'


def get_ext(path: Optional[str]) -> str:
    '''returns path file extension without dot'''
    if path:
        ext = os.path.splitext(path)[1]
        if len(ext) > 1:
            return ext[1:]
    return ''


def detect_report_format_from_path(path: Optional[str]
                                   ) -> Optional[ReportFormat]:
    ext = get_ext(path)
    try:
        return ReportFormat[ext.upper()]
    except KeyError:
        if ext.lower() == 'yml':
            return ReportFormat.YAML
    return None


def detect_report_format_from_content(data: str) -> Optional[ReportFormat]:
    end = data.find('\n')
    line = data[:end]
    if len(line) == 0:
        return None
    elif line[0] == '#':
        return ReportFormat.TXT
    elif line[0] == '{':
        return ReportFormat.JSON
    elif line.startswith('---') or ':' in line:
        return ReportFormat.YAML
    else:
        return None


def write_txt_report(output: IO, report: ValidationReport) -> None:
    # XXX: Make sure to start txt format output with '#' to be able to infer
    # the format later. '#' is chosen because it's how a text/markdown document
    # usually begins.
    def get_msg(e: dict) -> str:
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


def write_json_report(output: IO, report: SomeReport) -> None:
    json.dump(report, output, default=vars, indent=4)


def write_yaml_report(output: IO, report: SomeReport) -> None:
    # XXX: dump dict to avoid yaml-tags from class types
    yaml.dump(report.__dict__, output)
