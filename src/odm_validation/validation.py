"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

from collections import defaultdict
from typing import Callable, Dict, List
from enum import Enum
# from pprint import pprint

import part_tables as pt
import reports
from cerberusext import ContextualCoercer, OdmValidator
from copy import deepcopy
from input_data import DataKind
from reports import ErrorVerbosity, TableInfo, ValidationCtx
from rule_filters import RuleFilter
from rules import RuleId, ruleset
from schemas import Schema
from stdext import deep_update, keep, strip_dict_key
from versions import __version__, parse_version

from rule_errors import (
    filter_errors,
    gen_additions_schema,
    map_aggregated_errors,
    map_cerb_errors,
)

TableDataset = Dict[pt.TableId, pt.Dataset]

_BATCH_SIZE = 20


def _generate_validation_schema_ext(parts: pt.Dataset,
                                    sets: pt.Dataset = [],
                                    schema_version: str = pt.ODM_VERSION_STR,
                                    schema_additions: dict = {},
                                    rule_blacklist: List[RuleId] = [],
                                    rule_whitelist: List[RuleId] = []
                                    ) -> Schema:
    """
    This is the extended version of `generate_validation_schema`, with
    additional parameters for setting advanced options.

    :param rule_whitelist: A list of rule ids to explicitly enable. An empty
        list represents all the rules.
    :param rule_blacklist: A list of rule ids to explicitly disable. This takes
        precedence over the whitelist.
    """
    # `parts` must be stripped before further processing. This is important for
    # performance and simplicity of implementation.
    # `rule_whitelist` determines which rules are included in the schema. It is
    # needed when testing schema generation, to be able to compare isolated
    # rule-specific schemas.
    assert isinstance(sets, list), "invalid sets param"
    version = parse_version(schema_version)
    odm_data = pt.gen_odmdata(parts, sets, version)

    rule_filter = RuleFilter(whitelist=rule_whitelist,
                             blacklist=rule_blacklist)
    enabled_rules = list(rule_filter.filter(ruleset))

    cerb_schema = {}
    for r in enabled_rules:
        assert r.gen_schema, f'missing `gen_schema` in rule {r.id}'
        s = r.gen_schema(odm_data, version)
        assert s is not None
        deep_update(cerb_schema, s)
    additions_schema = gen_additions_schema(schema_additions)
    deep_update(cerb_schema, additions_schema)

    # strip empty tables
    for table in list(cerb_schema):
        if cerb_schema[table]['schema']['schema'] == {}:
            del cerb_schema[table]

    return {
        "schemaVersion": schema_version,
        "schema": cerb_schema,
    }


def generate_validation_schema(parts: pt.Dataset,
                               sets: pt.Dataset = [],
                               schema_version=pt.ODM_VERSION_STR,
                               schema_additions={}) -> Schema:
    return _generate_validation_schema_ext(parts, sets, schema_version,
                                           schema_additions)


# OnProgress(action, table_id, processed, total)
OnProgress = Callable[[str, str, int, int], None]


def _strip_coerce_rules(cerb_schema):
    return strip_dict_key(deepcopy(cerb_schema), 'coerce')


def filter_dict_by_key(key: str, d: dict) -> dict:
    result = {}
    val = d.get(key, None)
    if val is not None:
        result[key] = val
    return result


def filter_column_schemas_by_key(key: str, column_schemas: dict) -> dict:
    result = {}
    for col_name, col_schema in column_schemas.items():
        d = filter_dict_by_key(key, col_schema)
        if d:
            result[col_name] = d
    return result


def gen_coercion_schema(cerb_schema: dict) -> dict:
    result = {}
    for table_name, table_schema in cerb_schema.items():
        cs = table_schema['schema']['schema']
        result[table_name] = {
            'schema': {
                'schema': filter_column_schemas_by_key('coerce', cs),
            }
        }
    return result


def _validate_data_ext(
    schema: Schema,
    data: TableDataset,
    data_kind: DataKind = DataKind.python,
    data_version: str = pt.ODM_VERSION_STR,
    rule_blacklist: List[RuleId] = [],
    rule_whitelist: List[RuleId] = [],
    on_progress: OnProgress = None,
    verbosity: ErrorVerbosity = ErrorVerbosity.LONG_METADATA_MESSAGE,
    with_metadata: bool = True,
) -> reports.ValidationReport:
    """
    Validates `data` with `schema`, using Cerberus.

    This is the extended version of `validate_data`, with additional parameters
    for setting advanced options.

    :param rule_whitelist: list of rule ids to explicitly enable.
    :param rule_blacklist: list of rule ids to explicitly disable.
    """
    # `rule_whitelist` determines which rules/errors are triggered during
    # validation. It is needed when testing data validation, to be able to
    # compare error reports in isolation.
    #
    # The schema is being put through two steps. First, coercion is done by
    # looking at the `coerce` rules, then those rules are stripped and
    # validation is performed on the remaining rules.

    # the following asserts exist to inform the user of any argument order/type
    # mistakes

    assert isinstance(data, dict), (
        '`data` must be a dict. Remember to wrap the datasets in a dict with '
        'the table names as keys.')

    # XXX: ideally we would check `data_kind` against DataKind itself but that
    # throws an Error when passing in a DataKind value
    assert isinstance(data_kind, Enum), 'invalid data_kind param type'

    assert isinstance(data_version, str), 'invalid data_version param type'
    assert isinstance(rule_whitelist, list), \
        'invalid rule_whitelist param type'

    vctx = ValidationCtx(verbosity=verbosity)

    errors = []
    warnings = []
    versioned_schema = schema
    cerb_schema = versioned_schema["schema"]

    # remove meta fields, except for dataType and ruleID
    if not with_metadata:
        for t in cerb_schema.values():
            s = t['schema']
            s.pop('meta', None)
            for c in s['schema'].values():
                for metaEntry in c.get('meta', []):
                    metaRuleDicts = metaEntry.get('meta')
                    if metaRuleDicts:
                        keep(metaRuleDicts, 'dataType')
                        if len(metaRuleDicts) == 0:
                            del metaEntry['meta']

    rule_filter = RuleFilter(whitelist=rule_whitelist,
                             blacklist=rule_blacklist)

    def batch_table_data(action, table_id, table_data):
        total = len(table_data)
        offset = 0
        while offset < total:
            n = min(total - offset, _BATCH_SIZE)
            first = offset
            last = offset + n
            batch_data = {table_id: table_data[first:last]}
            yield (batch_data, offset)
            offset += n
            if on_progress:
                on_progress(action, table_id, offset, total)

    coercion_schema = (cerb_schema if with_metadata else
                       gen_coercion_schema(cerb_schema))
    coerced_data = defaultdict(list)
    coercer = ContextualCoercer(warnings=warnings, errors=errors)
    for table_id, table_data in data.items():
        schema = {table_id: coercion_schema[table_id]}
        for batch in batch_table_data('coercing', table_id, table_data):
            batch_data, offset = batch
            coerce_result = coercer.coerce(batch_data, schema,
                                           offset, data_kind)
            coerced_data[table_id] += coerce_result[table_id]

    table_info: Dict[pt.TableId, TableInfo] = {}

    validation_schema = _strip_coerce_rules(cerb_schema)
    for table_id, table_data in coerced_data.items():
        table_info[table_id] = TableInfo(
            columns=len(table_data[0]),
            rows=len(table_data),
        )
        v = OdmValidator.new()
        schema = {table_id: validation_schema[table_id]}
        for batch in batch_table_data('validating', table_id, table_data):
            batch_data, offset = batch
            v._errors.clear()
            if v.validate(offset, data_kind, batch_data, schema):
                continue
            e, w = map_cerb_errors(vctx, table_id, v._errors,
                                   schema, rule_filter, offset,
                                   data_kind)
            errors += e
            warnings += w
        errors += map_aggregated_errors(vctx, table_id,
                                        v.error_state.aggregated_errors,
                                        rule_filter)

    errors = filter_errors(errors)

    return reports.ValidationReport(
        data_version=data_version,
        schema_version=versioned_schema["schemaVersion"],
        package_version=__version__,
        table_info=table_info,
        errors=errors,
        warnings=warnings,
    )


def validate_data(schema: Schema,
                  data: TableDataset,
                  data_kind: DataKind = DataKind.python,
                  data_version=pt.ODM_VERSION_STR,
                  rule_blacklist: List[RuleId] = [],
                  ) -> reports.ValidationReport:
    """
    :param rule_blacklist: A list of rule ids to explicitly disable.
    """
    return _validate_data_ext(schema, data, data_kind, data_version,
                              rule_blacklist)
