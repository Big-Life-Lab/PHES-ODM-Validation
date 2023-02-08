import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Set
# from pprint import pprint

import part_tables as pt
from rules import COERCION_RULE_ID
from stdext import (
    get_len,
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
    err_template: str = ''


@dataclass(frozen=True)
class ValidationReport:
    data_version: str
    schema_version: str
    package_version: str
    errors: List[str]
    warnings: List[str]

    def valid(self) -> bool:
        return len(self.errors) == 0


def _fmt_list(items: list) -> str:
    if len(items) > 1:
        return ','.join(map(str, items))
    else:
        return str(items[0])


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


def _fmt_rule_name(rule_id: str):
    return rule_id.replace('_', ' ').capitalize()


def _fmt_allowed_values(values: Set[str]) -> str:
    # XXX: The order of set-elements isn't deterministic, so we need to sort.
    return '/'.join(sorted(values))


def _gen_error_msg(ctx: ErrorCtx, template: Optional[str] = None):
    ":param template: overrides ctx.err_template"
    if not template:
        template = ctx.err_template
    return template.format(
        allowed_values=_fmt_allowed_values(ctx.allowed_values),
        column_id=ctx.column_id,
        constraint=_fmt_value(ctx.constraint),
        row_num=_fmt_list(ctx.row_numbers),
        rule_name=_fmt_rule_name(ctx.rule_id),
        table_id=ctx.table_id,
        value=_fmt_value(ctx.value),
        value_len=get_len(ctx.value),
        value_type=type_name(type(ctx.value)),
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
        'message': _gen_error_msg(ctx, err_template),
    }

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
    result = ('Value {value} in row {row_num} in column {column_id} '
              'in table {table_id} ')
    if kind == ErrorKind.WARNING:
        result += f'is a {orig_type_name} and was '
    else:
        result += 'cannot be '
    result += f'coerced into a {coerced_type_alias}'
    return result


def gen_coercion_error(ctx, kind: ErrorKind):
    msg = _gen_coercion_msg(ctx, kind)
    return gen_rule_error(ctx, err_template=msg, kind=kind)
