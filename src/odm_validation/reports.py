import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TypedDict

import odm_validation.part_tables as pt
from odm_validation.input_data import DataKind
from odm_validation.rules import get_anyof_constraint, RuleId
from odm_validation.stdext import (
    get_len,
    quote,
    type_name,
)


class ErrorKind(Enum):
    WARNING = 'warning'
    ERROR = 'error'


class ErrorVerbosity(int, Enum):
    MESSAGE = 0
    SHORT_METADATA = 1
    SHORT_METADATA_MESSAGE = 2
    LONG_METADATA_MESSAGE = 3


@dataclass(frozen=True)
class ValidationCtx:
    verbosity: ErrorVerbosity


@dataclass(frozen=True)
class ErrorCtx:
    column_id: str
    column_meta: dict
    row_numbers: list[int]
    rows: list[dict]
    rule_id: RuleId
    table_id: str
    value: Any

    allowed_values: set[str] = field(default_factory=set)
    cerb_type_name: str = ''
    constraint: Any = None
    data_kind: DataKind = DataKind.python
    err_template: str = ''
    is_column: bool = False
    verbosity: ErrorVerbosity = ErrorVerbosity.LONG_METADATA_MESSAGE


class TableInfo(TypedDict):
    columns: int
    rows: int


@dataclass(frozen=True)
class ValidationReport:
    data_version: str
    schema_version: str
    package_version: str
    table_info: dict[pt.TableId, TableInfo]
    errors: list[dict]
    warnings: list[dict]

    def valid(self) -> bool:
        return len(self.errors) == 0


def join_reports(a, b: ValidationReport) -> ValidationReport:
    """Joins two reports together into a new report."""
    if a is None:
        assert b is not None
        return b
    assert a.data_version == b.data_version
    assert a.schema_version == b.schema_version
    assert a.package_version == b.package_version
    return ValidationReport(
        data_version=a.data_version,
        schema_version=a.schema_version,
        package_version=a.package_version,
        table_info=(a.table_info | b.table_info),
        errors=(a.errors + b.errors),
        warnings=(a.warnings + b.warnings),
    )


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


def _fmt_dataset_values(rows: list[pt.Row]) -> list[pt.Row]:
    """Returns a copy of `rows` with formated values."""
    def _fmt_row(row: pt.Row) -> pt.Row:
        return {key: _fmt_value(val) for key, val in row.items()}

    return list(map(_fmt_row, rows))


def _fmt_allowed_values(values: set[str]) -> str:
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

    # prefix and suffix, with increasing verbosity
    is_col = ctx.is_column

    short_template = {
        'prefix': '{table_id}({column_id}',
        'prefix_end': ('' if is_col else ', {row_num}') + '): ',
        'suffix': ' [{rule_id}]',
    }

    long_template = {
        'prefix': ('{rule_id} rule ' + verb + ' in table {table_id}, '
                   'column {column_id}'),
        'prefix_end': ('' if is_col else ', row(s) {row_num}') + ': ',
        'suffix': '',
    }

    xfix_templates: dict[ErrorVerbosity, dict] = {
        ErrorVerbosity.MESSAGE: {},
        ErrorVerbosity.SHORT_METADATA: short_template,
        ErrorVerbosity.SHORT_METADATA_MESSAGE: short_template,
        ErrorVerbosity.LONG_METADATA_MESSAGE: long_template,
    }

    xfix = xfix_templates[ctx.verbosity]

    # use rule error template if not overridden
    template = template or ctx.err_template

    # remove message from SHORT_METADATA
    if ctx.verbosity == ErrorVerbosity.SHORT_METADATA:
        template = ''

    full_template = ''.join([
        xfix.get('prefix', ''),
        xfix.get('prefix_end', ''),
        template,
        xfix.get('suffix', ''),
    ])

    # XXX: constraint may be a combination of rules due to a need for the
    # 'empty' rule, which we'll have to exclude to get the actual rule value we
    # want. This is the case when constraint has the type list[dict]
    constraint_val = ctx.constraint
    if isinstance(constraint_val, list):
        rules = constraint_val[0]
        if isinstance(rules, dict):
            (_, val) = get_anyof_constraint(rules)
            constraint_val = val

    return full_template.format(
        allowed_values=_fmt_allowed_values(ctx.allowed_values),
        column_id=ctx.column_id,
        constraint=_fmt_msg_value(constraint_val, relaxed=True),
        row_num=_fmt_list(ctx.row_numbers),
        rule_id=ctx.rule_id.name,
        table_id=ctx.table_id,
        value=_fmt_msg_value(ctx.value),
        value_len=get_len(ctx.value),
        value_type=type_name(type(ctx.value))
    )


def get_error_kind(report_error) -> ErrorKind:
    if 'warningType' in report_error:
        return ErrorKind.WARNING
    else:
        return ErrorKind.ERROR


def get_error_type_field_name(error_kind: ErrorKind) -> str:
    return error_kind.value + 'Type'


def get_error_rule_id(report_error: dict, error_kind: ErrorKind) -> RuleId:
    rule_name = report_error[get_error_type_field_name(error_kind)]
    return RuleId[rule_name]


def gen_rule_error(ctx: ErrorCtx,
                   kind: ErrorKind,
                   err_template: Optional[str] = None,
                   ) -> dict:
    """
    :param err_template: overrides rule error-template
    """
    rule_ids = _get_meta_rule_ids(ctx.column_meta)
    rule_fields = pt.get_validation_rule_fields(ctx.column_meta, rule_ids)
    error = {
        (get_error_type_field_name(kind)): ctx.rule_id.name,
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
    if ctx.rule_id == RuleId._coercion:
        error['coercionRules'] = rule_ids

    return error


def _generalize_cerb_type_name(name: str) -> str:
    if name in {'float', 'integer'}:
        return 'number'
    else:
        return name


def _get_meta_rule_ids(column_meta: Optional[dict]) -> list[str]:
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
    return gen_rule_error(ctx, kind, err_template=msg)
