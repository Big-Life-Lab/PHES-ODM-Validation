import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple
from copy import deepcopy
from pprint import pformat

from cerberus import Validator
from cerberus.errors import ErrorDefinition

import part_tables as pt
import reports
from input_data import DataKind
from reports import get_row_num
from rules import RuleId
from part_tables import Dataset, Row
from schemas import CerberusSchema
from stdext import (
    parse_datetime,
    parse_int,
    type_name,
)


EMPTY_TRIMMED_RULE = 0x101


def _convert_value(val: Any, type_class) -> Any:
    "Convert `val` to `type_class`."
    # `parse_int` is explicitly called because floats without decimals
    # (ex: 1.0) also are valid integers.
    if isinstance(val, type_class):
        return val
    elif type_class is int:
        return parse_int(val)
    elif type_class is datetime and isinstance(val, str):
        return parse_datetime(val)
    else:
        return type_class(val)


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

    def coerce(self, document: Dataset, schema: CerberusSchema,
               offset: int, data_kind=DataKind.python) -> Dataset:
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
        self._config["offset"] = offset
        self._config["data_kind"] = data_kind
        if not super().validate(document):
            logging.error(__name__ + '.coerce:\n' + pformat(self.errors))
        return self._config["coerced_document"]

    def _log_coercion(self, kind, ctx):
        # set `errors` and `warnings`
        entry = reports.gen_coercion_error(ctx, kind)
        self._config[kind.value + 's'].append(entry)

    def _set_value(self, field, value, type_class):
        # ignore empty values, they can't be coerced anyway
        if not value:
            return
        if isinstance(value, type_class):
            return
        if type_class is float and isinstance(value, int):
            return
        offset = self._config['offset']
        data_kind = self._config['data_kind']
        table = self.document_path[0]
        row_ix = self.document_path[1]
        row = self.document
        column_meta = self.schema[field].get('meta', [])
        ctx = reports.ErrorCtx(
            rule_id=RuleId._coercion,
            cerb_type_name=type_name(type_class),
            column_id=field,
            column_meta=column_meta,
            rows=[row],
            row_numbers=[get_row_num(row_ix, offset, data_kind)],
            table_id=table,
            value=value,
        )
        try:
            new_value = _convert_value(value, type_class)
            self._config["coerced_document"][table][row_ix][field] = new_value
            if data_kind != DataKind.spreadsheet:
                self._log_coercion(reports.ErrorKind.WARNING, ctx)
        except (ArithmeticError, ValueError):
            self._log_coercion(reports.ErrorKind.ERROR, ctx)

    def _check_with_datetime(self, field, value):
        self._set_value(field, value, datetime)

    def _check_with_float(self, field, value):
        self._set_value(field, value, float)

    def _check_with_integer(self, field, value):
        self._set_value(field, value, int)


DateStr = str
PrimaryKey = Tuple[pt.PartId, DateStr]
TableKey = Tuple[pt.TableId, PrimaryKey]
RowNum = int


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
        self.table_keys: Dict[pt.TableId, Set[PrimaryKey]] = defaultdict(set)
        self.tablekey_rows: Dict[TableKey, (RowNum, Row)] = {}
        self.tablekey_errors: Dict[TableKey, AggregatedError] = \
            defaultdict(AggregatedError)


class ErrorState:
    def __init__(self):
        self.offset = 0
        self.data_kind = DataKind.python
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

    def _validate_emptyTrimmed(self, constraint, field, raw_value):
        """{'type': 'boolean'}"""
        expect_empty = constraint
        is_str = isinstance(raw_value, str)
        value = raw_value.strip() if is_str else raw_value
        is_empty = not value or (is_str and value == '')
        if is_empty != expect_empty:
            err = ErrorDefinition(EMPTY_TRIMMED_RULE, 'emptyTrimmed')
            self._error(field, err)

    def _validate_unique(self, constraint, field, value):
        """{'type': 'boolean'}"""
        # the primary key (pk) is a compound key of partID and lastUpdated
        if not constraint:
            return
        offset = self.error_state.offset
        data_kind = self.error_state.data_kind
        table_id = self.document_path[0]
        row = self.document
        row_ix = self.document_path[1]
        row_num = get_row_num(row_ix, offset, data_kind)
        lastUpdated = row.get('lastUpdated', '') or ''
        assert isinstance(lastUpdated, str)
        pk = (str(value).strip(), lastUpdated.strip())
        state = self.unique_state
        primary_keys = state.table_keys[table_id]
        tablekey = (table_id, pk)
        if pk in primary_keys:
            err = state.tablekey_errors.get(tablekey)
            if not err:
                (first_row_num, first_row) = state.tablekey_rows[tablekey]
                err = AggregatedError(
                    cerb_rule='unique',
                    table_id=table_id,
                    column_id=field,
                    row_numbers=[first_row_num],
                    rows=[first_row],
                    column_meta=self.schema[field].get('meta', []),
                    value=pk[0]
                )
                state.tablekey_errors[tablekey] = err
            err.row_numbers.append(row_num)
            err.rows.append(row)
        else:
            state.tablekey_rows[tablekey] = (row_num, row)
            primary_keys.add(pk)

    def validate(self, offset: int, data_kind: DataKind,
                 *args, **kwargs) -> bool:
        self.error_state.offset = offset
        self.error_state.data_kind = data_kind
        self.error_state.aggregated_errors.clear()
        result = super().validate(*args, **kwargs)
        self.error_state.aggregated_errors += \
            self.unique_state.tablekey_errors.values()
        result = result and len(self.error_state.aggregated_errors) == 0
        return result
