import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from copy import deepcopy
# from pprint import pprint

from cerberus import Validator

import part_tables as pt
import rules as validation_rules
from part_tables import Row
from stdext import (
    inc,
    parse_datetime,
    parse_int,
    type_name,
)


class LogLevel(Enum):
    WARNING = 'warning'
    ERROR = 'error'


@dataclass(frozen=True)
class CoercionCtx:
    """Coercion context."""
    cerb_type_name: str
    column: str
    column_meta: dict
    row: dict
    row_num: str
    table: str
    value: str


def _get_meta_rule_ids(column_meta) -> List[str]:
    if not column_meta:
        return []
    return [m['ruleID'] for m in column_meta]


def _generalize_cerb_type_name(name: str) -> str:
    if name in {'float', 'integer'}:
        return 'number'
    else:
        return name


def _gen_coercion_msg(lvl: LogLevel, ctx: CoercionCtx):
    orig_type_name = type_name(type(ctx.value))
    coerced_type_alias = _generalize_cerb_type_name(ctx.cerb_type_name)
    result = (f'Value {ctx.value} in row {ctx.row_num} in column {ctx.column} '
              f'in table {ctx.table} ')
    if lvl == LogLevel.WARNING:
        result += f'is a {orig_type_name} and was '
    elif lvl == LogLevel.ERROR:
        result += 'cannot be '
    else:
        assert False, "invalid log lvl"
    result += f'coerced into a {coerced_type_alias}'
    return result


def _gen_coercion_log_entry(log_lvl, ctx):
    rule_ids = _get_meta_rule_ids(ctx.column_meta)
    rule_fields = pt.get_validation_rule_fields(ctx.column_meta, rule_ids)
    msg = _gen_coercion_msg(log_lvl, ctx)
    return {
        (log_lvl.value + 'Type'): validation_rules._COERCION,
        'coercionRules': rule_ids,
        'tableName': ctx.table,
        'columnName': ctx.column,
        'rowNumber': ctx.row_num,
        'row': ctx.row,
        'invalidValue': ctx.value,
        'validationRuleFields': rule_fields,
        'message': msg
    }


def _convert_value(orig_value, type_class) -> int:
    if type_class is int:
        return parse_int(orig_value)
    elif type_class is datetime:
        return parse_datetime(orig_value)
    else:
        return type_class(orig_value)


class ContextualCoercer(Validator):
    """Construct this with the `errors` and `warnings` parameters set to
    existing lists, to retrieve coercion errors and warnings."""
    # This class performs coercion on data, to prepare it for the actual
    # validation. Cerberus' native coercion doesn't give contextual info about
    # where the coercions take place, which is why we need this custom extended
    # class. The Cerberus validation routine, combined with the 'check_with'
    # rule is used to implement coercion in our own context-aware way.
    #
    # Data is stored/passed using the `_config` dict of the base class. It can
    # be initialized during construction by passing extra key-value parameters
    # to the base constructor. Existing list objects must be passed to retain
    # the data after coercion. Normal fields in this derived class doesn't seem
    # to be able to pass state to the internal cerberus calls (like
    # `_check_with_int`, which is why we're using this base-class field
    # instead.
    #
    # Alternative solutions for coercion have been tried without luck,
    # including:
    # - Native coercion (no context).
    # - Validation rule (not able to set new value for remaining rules).
    # - Retrieving the coerced document from Cerberus' validation step didn't
    #   seem to work either.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_unknown = True

    def _extract_coercion_schema(schema):
        """Strips `schema` of all rules except 'meta' and 'coerce', and
        replaces 'coerce' with 'check_with'."""
        result = deepcopy(schema)
        for table in result.keys():
            schema = result[table]['schema']['schema']
            for field, rules in list(schema.items()):
                for key in list(rules.keys()):
                    if key == 'coerce':
                        rules['check_with'] = rules.pop(key)
                    elif key != 'meta':
                        del rules[key]
                if len(rules) == 0:
                    del schema[field]
        return result

    def coerce(self, document, schema) -> Optional[dict]:
        # Coercion is performed by validating using a coercion-only schema.
        # Native cerberus normalization can't be used because it doesn't
        # provide context. Coercions are kept track of using `_config`.
        #
        # Cerberus' `Validator.validate` is invoked without error handling, as
        # we're not expecting any errors, and we're already handling errors in
        # the `_check_with_x` functions. We are, however, logging any errors to
        # file, just in case we miss something.
        coercion_schema = ContextualCoercer._extract_coercion_schema(schema)
        self.schema = coercion_schema
        self._config["coerced_document"] = deepcopy(document)
        if not super().validate(document):
            logging.error(self.errors, stack_info=True)
        return self._config["coerced_document"]

    def _log_coercion(self, lvl, ctx):
        entry = _gen_coercion_log_entry(lvl, ctx)
        self._config[lvl.value + 's'].append(entry)

    def _set_value(self, field, orig_value, type_class):
        if isinstance(orig_value, type_class):
            return
        if type_class is float and isinstance(orig_value, int):
            return
        table = self.document_path[0]
        row_ix = self.document_path[1]
        row = self.document
        column_meta = self.schema[field].get('meta')
        ctx = CoercionCtx(
            cerb_type_name=type_name(type_class),
            column=field,
            column_meta=column_meta,
            row=row,
            row_num=row_ix+1,
            table=table,
            value=orig_value,
        )
        try:
            value = _convert_value(orig_value, type_class)
            self._config["coerced_document"][table][row_ix][field] = value
            self._log_coercion(LogLevel.WARNING, ctx)
        except (ArithmeticError, ValueError):
            value = orig_value
            self._log_coercion(LogLevel.ERROR, ctx)

    def _check_with_datetime(self, field, value):
        self._set_value(field, value, datetime)

    def _check_with_float(self, field, value):
        self._set_value(field, value, float)

    def _check_with_integer(self, field, value):
        self._set_value(field, value, int)


DateStr = str
TableId = str
PrimaryKey = Tuple[pt.PartId, DateStr]
TableKey = Tuple[TableId, PrimaryKey]
Index = int


@dataclass
class AggregatedError:
    cerb_rule: str
    table_id: str
    column_id: str
    row_numbers: List[int]
    rows: List[dict]
    column_meta: List[dict]
    value: Any


class UniqueRuleState:
    """State for the 'unique' rule."""
    def __init__(self):
        self.table_keys: Dict[TableId, Set[PrimaryKey]] = defaultdict(set)
        self.tablekey_rows: Dict[TableKey, (Index, Row)] = {}
        self.tablekey_errors: Dict[TableKey, AggregatedError] = \
            defaultdict(AggregatedError)


class ErrorState:
    def __init__(self):
        self.aggregated_errors: List[AggregatedError] = []


class OdmValidator(Validator):
    # This is the main class used for validation.

    @staticmethod
    def new():
        """Constructs this class with initialized state."""
        # `__init__` can't be used to init state because Cerberus creates
        # multiple instances of the validator, so the same instance/state won't
        # be passed to our custom validation methods. The arguments passed in
        # here are automatically assigned to `Validator._config` by Cerberus.
        return OdmValidator(
            unique_state=UniqueRuleState(),
            error_state=ErrorState(),
        )

    def __init__(self, *args, **kwargs):
        # Unknown fields must be allowed because we're only generating a schema
        # for the requirements, not the optional data.
        super().__init__(*args, **kwargs)
        self.allow_unknown = True
        self.unique_state = self._config['unique_state']
        self.error_state = self._config['error_state']

    def _validate_unique(self, constraint, field, value):
        """{'type': 'boolean'}"""
        # the primary key (pk) is a compound key of partID and lastUpdated
        if not constraint:
            return
        table_id = self.document_path[0]
        row_ix = self.document_path[1]
        row = self.document
        lastUpdated = row.get('lastUpdated', '') or ''
        assert isinstance(lastUpdated, str)
        pk = (value.strip(), lastUpdated.strip())
        state = self.unique_state
        primary_keys = state.table_keys[table_id]
        tablekey = (table_id, pk)
        if pk in primary_keys:
            err = state.tablekey_errors.get(tablekey)
            if not err:
                (first_ix, first_row) = state.tablekey_rows[tablekey]
                err = AggregatedError(
                    cerb_rule='unique',
                    table_id=table_id,
                    column_id=field,
                    row_numbers=[inc(first_ix)],
                    rows=[first_row],
                    column_meta=self.schema[field].get('meta'),
                    value=pk[0]
                )
                state.tablekey_errors[tablekey] = err
            err.row_numbers.append(inc(row_ix))
            err.rows.append(row)
        else:
            state.tablekey_rows[tablekey] = (row_ix, row)
            primary_keys.add(pk)

    def validate(self, *args, **kwargs) -> bool:
        self.error_state.aggregated_errors.clear()
        result = super().validate(*args, **kwargs)
        self.error_state.aggregated_errors += \
            self.unique_state.tablekey_errors.values()
        result = result and len(self.error_state.aggregated_errors) == 0
        return result
