import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
# from pprint import pprint

import part_tables as pt
from input_data import DataKind
from rules import RuleId, COERCION_RULE_ID
from stdext import (
    get_len,
    quote,
    type_name,
)


class ErrorKind(Enum):
    WARNING = 'warning'
    ERROR = 'error'


@dataclass(frozen=True)
class ErrorCtx:
    column_id: str
    column_meta: dict
    row_numbers: List[int]
    rows: List[dict]
    rule_id: str
    table_id: str
    value: Any

    allowed_values: Set[str] = field(default_factory=set)
    cerb_type_name: str = ''
    constraint: Any = None
    data_kind: DataKind = DataKind.python
    err_template: str = ''
    is_column: bool = False


class TableSummary:
    error_counts: Dict[RuleId, int]

    def __init__(self):
        self.error_counts = defaultdict(int)


class ValidationSummary:
    table_summaries: Dict[pt.TableId, TableSummary]

    def __init__(self):
        self.table_summaries = defaultdict(TableSummary)

    def record_error(self, table_id, rule_id):
        self.table_summaries[table_id].error_counts[rule_id] += 1


@dataclass(frozen=True)
class ValidationReport:
    data_version: str
    schema_version: str
    package_version: str
    errors: List[str]
    warnings: List[str]
    summary: ValidationSummary

    def valid(self) -> bool:
        return len(self.errors) == 0


def _fmt_list(items: list) -> str:
    if len(items) > 1:
        return ','.join(map(str, items))
    else:
        return str(items[0])


def get_row_num(row_index: int, offset: int, data_kind: DataKind) -> int:
    "Returns the dataset row number, starting from 1."
    # spreadsheets have a header row, which increases the number by one
    result = offset + row_index + 1
    if data_kind == DataKind.spreadsheet:
        result += 1
    return result


def _fmt_value(val: Any) -> Any:
    # needed to avoid the default `datetime.datetime(year, month, day, ...)`
    if isinstance(val, datetime.date) or isinstance(val, datetime.datetime):
        return str(val)
    return val


def _fmt_dataset_values(rows: List[pt.Row]) -> List[pt.Row]:
    """Returns a copy of `rows` with formated values."""
    def _fmt_row(row: pt.Row) -> pt.Row:
        return {key: _fmt_value(val) for key, val in row.items()}

    return list(map(_fmt_row, rows))


def _fmt_allowed_values(values: Set[str]) -> str:
    # XXX: The order of set-elements isn't deterministic, so we need to sort.
    return '/'.join(sorted(values))


def _fmt_msg_value(value: Any, relaxed=False) -> Any:
    """Quote `value` as needed, in addition to the formatting done by
    `_fmt_value`. This is meant to be used as part of another string/message.

    :param relaxed: skips quotation when not needed.
    """
    fval = _fmt_value(value)
    if relaxed and isinstance(fval, str):
        if (fval != '') and (' ' not in fval):
            return fval
    return quote(str(fval))


def _gen_error_msg(ctx: ErrorCtx, template: Optional[str] = None,
                   error_kind: Optional[ErrorKind] = None):
    ":param template: overrides ctx.err_template"
    # requirements for error message:
    # - prefix with sortable order: table before column, etc.
    # - prefix with natural order, as if it was a sentence:
    #   "<rule> in <table> in <column>", etc.
    # - quote values and constraints, since it's hard to distinguish them from
    #   the text otherwise.
    verb = 'violated' if error_kind == ErrorKind.ERROR else 'triggered'

    # prefix gen
    prefix = ('{rule_id} rule ' + verb + ' in '
              'table {table_id}, column {column_id}')
    if not (ctx.is_column and ctx.data_kind == DataKind.spreadsheet):
        if len(ctx.row_numbers) == 1:
            prefix += ', row '
        else:
            prefix += ', rows '
        prefix += '{row_num}'
    prefix += ': '

    if not template:
        template = ctx.err_template
    template = prefix + template
    return template.format(
        allowed_values=_fmt_allowed_values(ctx.allowed_values),
        column_id=ctx.column_id,
        constraint=_fmt_msg_value(ctx.constraint, relaxed=True),
        row_num=_fmt_list(ctx.row_numbers),
        rule_id=ctx.rule_id,
        table_id=ctx.table_id,
        value=_fmt_msg_value(ctx.value),
        value_len=get_len(ctx.value),
        value_type=type_name(type(ctx.value))
    )


def gen_rule_error(ctx: ErrorCtx,
                   err_template: Optional[str] = None,
                   kind: Optional[ErrorKind] = None,
                   ) -> dict:
    """
    :param err_template: overrides rule error-template
    """
    rule_ids = _get_meta_rule_ids(ctx.column_meta)
    rule_fields = pt.get_validation_rule_fields(ctx.column_meta, rule_ids)
    error = {
        (kind.value + 'Type'): ctx.rule_id,
        'tableName': ctx.table_id,
        'columnName': ctx.column_id,
        'validationRuleFields': _fmt_dataset_values(rule_fields),
        'message': _gen_error_msg(ctx, err_template, kind),
    }

    # skip row info for spreadsheet-column errors
    if ctx.data_kind == DataKind.spreadsheet and ctx.is_column:
        return error

    # row numbers
    if len(ctx.row_numbers) > 1:
        error['rowNumbers'] = ctx.row_numbers
    else:
        error['rowNumber'] = ctx.row_numbers[0]

    # rows
    rows = _fmt_dataset_values(ctx.rows)
    if len(ctx.rows) > 1:
        error['rows'] = rows
    else:
        error['row'] = rows[0]

    # value
    if ctx.value is not None:
        error['invalidValue'] = _fmt_value(ctx.value)

    # coercion
    if ctx.rule_id == COERCION_RULE_ID:
        error['coercionRules'] = rule_ids

    return error


def _generalize_cerb_type_name(name: str) -> str:
    if name in {'float', 'integer'}:
        return 'number'
    else:
        return name


def _get_meta_rule_ids(column_meta) -> Set[str]:
    if not column_meta:
        return []
    return [m['ruleID'] for m in column_meta]


def _gen_coercion_msg(ctx: ErrorCtx, kind: ErrorKind):
    orig_type_name = type_name(type(ctx.value))
    coerced_type_alias = _generalize_cerb_type_name(ctx.cerb_type_name)
    result = 'Value {value} '
    if kind == ErrorKind.WARNING:
        result += f'is a {orig_type_name} and was '
    else:
        result += 'cannot be '
    result += f'coerced into a {coerced_type_alias}'
    return result


def gen_coercion_error(ctx, kind: ErrorKind):
    msg = _gen_coercion_msg(ctx, kind)
    return gen_rule_error(ctx, err_template=msg, kind=kind)
