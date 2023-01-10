import logging
from enum import Enum
from typing import List, Optional
from copy import deepcopy
# from pprint import pprint

from cerberus import Validator

import part_tables as pt
from stdext import strip_dict_key


class LogLevel(Enum):
    WARNING = 'warning'
    ERROR = 'error'


def _get_meta_rule_ids(column_meta) -> List[str]:
    if not column_meta:
        return []
    return [m['ruleID'] for m in column_meta]


def _type_name(x) -> str:
    result = type(x).__name__
    if result == 'int':
        result = 'integer'
    if result == 'str':
        result = 'string'
    return result


def _gen_coercion_msg(log_lvl, table, column, row_num, value, column_meta):
    value_type_name = _type_name(value)
    result = (f'Value {value} in row {row_num} in column {column} '
              f'in table {table} ')
    if log_lvl == 'warning':
        result += f'is a {value_type_name} and was '
    elif log_lvl == 'error':
        result += 'cannot be '
    else:
        assert False, "invalid log lvl"
    result += 'coerced into a number'
    return result


def _gen_coercion_log_entry(log_lvl, table, column, row_index, row,
                            orig_value, column_meta):
    row_num = row_index + 1
    rule_ids = _get_meta_rule_ids(column_meta)
    rule_fields = pt.get_validation_rule_fields(column_meta, rule_ids)
    msg = _gen_coercion_msg(log_lvl, table, column, row_num, orig_value,
                            column_meta)
    return {
        (str(log_lvl) + 'Type'): '_coercion',
        'coercionRules': rule_ids,
        'tableName': table,
        'columnName': column,
        'rowNumber': row_num,
        'row': row,
        'invalidValue': orig_value,
        'validationRuleFields': rule_fields,
        'message': msg
    }


def _gen_coercion_warning(table, column, row_index, row, orig_value,
                          column_meta):
    return _gen_coercion_log_entry('warning', table, column, row_index, row,
                                   orig_value, column_meta)


def _gen_coercion_error(table, column, row_index, row, orig_value,
                        column_meta):
    return _gen_coercion_log_entry('error', table, column, row_index, row,
                                   orig_value, column_meta)


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
            logging.error(self.errors)
        return self._config["coerced_document"]

    def _log_warning(self, table, field, row_ix, row, orig_value, column_meta):
        warning = _gen_coercion_warning(table, field, row_ix, row, orig_value,
                                        column_meta)
        self._config["warnings"].append(warning)

    def _log_error(self, table, field, row_ix, row, orig_value, column_meta):
        error = _gen_coercion_error(table, field, row_ix, row, orig_value,
                                    column_meta)
        self._config["errors"].append(error)

    def _set_value(self, field, orig_value, type_class):
        if isinstance(orig_value, type_class):
            return
        table = self.document_path[0]
        row_ix = self.document_path[1]
        row = self.document
        column_meta = self.schema[field].get('meta')
        try:
            value = type_class(orig_value)
            self._config["coerced_document"][table][row_ix][field] = value
            self._log_warning(table, field, row_ix, row, orig_value,
                              column_meta)
        except ValueError:
            value = orig_value
            self._log_error(table, field, row_ix, row, orig_value,
                            column_meta)

    def _check_with_float(self, field, value):
        self._set_value(field, value, float)

    def _check_with_integer(self, field, value):
        self._set_value(field, value, int)


class OdmValidator(Validator):
    """Must be constructed with `coercion_warnings` and `coercion_errors`
    parameters set to existing lists."""
    # This is the main class used for validation. It wraps the
    # ContextualCoercer class to perform coercion before the validation step.

    def __init__(self, *args, **kwargs):
        # Cerberus is filling in `_config` with any extra key-value
        # parameters, which is how the coercion-warning/error lists are set.
        #
        # Unknown fields must be allowed because we're only generating a schema
        # for the requirements, not the optional data.
        super().__init__(*args, **kwargs)
        self.allow_unknown = True

    def validate(self, data, schema):
        warnings = self._config['coercion_warnings']
        errors = self._config['coercion_errors']
        coercer = ContextualCoercer(warnings=warnings, errors=errors)
        coerced_data = coercer.coerce(data, schema)

        validation_schema = strip_dict_key(deepcopy(schema), 'coerce')
        result = super().validate(coerced_data, validation_schema)
        return result
