import json
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import groupby
from typing import Dict, List, Set, Tuple
# from pprint import pprint

import reports
from part_tables import TableId
from reports import ErrorKind, ValidationReport
from rules import RuleId
from versions import __version__


# types
# -----------------------------------------------------------------------------


Count = int
EntityId = str


class SummaryKey(int, Enum):
    # XXX:
    # - int-values are for comparison/order
    # - values are overloaded as lower-case names
    TABLE = 1
    COLUMN = 2
    ROW = 3

    @property
    def value(self):
        return self.name.lower()

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ < other._value_
        return NotImplemented


# this is the core error/rule-to-count data structure
ErrorCounts = Dict[RuleId, Count]

# table -> entity -> error/rule -> count
# ex: SummaryKey.COLUMN -> 'addresses' -> 'addID' -> 'invalid_type' -> 3
EntityCounts = Dict[EntityId, ErrorCounts]
TableCounts = Dict[TableId, EntityCounts]

# simplified data structures for total counts
TableErrorCounts = Dict[TableId, ErrorCounts]
ErrorKindErrorCounts = Dict[ErrorKind, ErrorCounts]


@dataclass(frozen=True)
class Counts:
    total_counts: ErrorCounts
    key_counts: Dict[SummaryKey, TableCounts]


@dataclass(frozen=True)
class SummaryEntry:
    rule_id: RuleId
    count: int

    key: SummaryKey
    """The group/summary-key this entry is summarized by."""

    value: str
    """Id of the entity in group `key` that this entry is derived from. This
    corresponds to the table-id when grouping by `table`, the column-id when
    grouping by `column`, etc."""


SummaryEntryList = List[SummaryEntry]
ErrorSummary = Dict[TableId, SummaryEntryList]


@dataclass(frozen=True)
class SummarizedReport:
    data_version: str
    schema_version: str
    package_version: str
    overview: dict
    errors: ErrorSummary
    warnings: ErrorSummary

    def toJson(self):
        return json.dumps(self, default=lambda x: x.__dict__)


# error counting
# -----------------------------------------------------------------------------


def _get_error_table_rule(e) -> (TableId, RuleId):
    error_kind = reports.get_error_kind(e)
    rule_id = reports.get_error_rule_id(e, error_kind)
    table_id = e['tableName']
    return (table_id, rule_id)


def _get_error_row_ids(e) -> List[int]:
    row_id0 = e.get('rowNumber')
    if row_id0 is not None:
        return [row_id0]
    else:
        return e['rowNumbers']


def _count_errors(keys: Set[SummaryKey], errors: list) -> Counts:
    """Counts errors. Should be called once for every error kind, with its list
    of errors."""

    def _update_entity(key, table_id, entity_id, rule_id, count):
        table_counts: TableCounts = key_counts[key]
        if table_id not in table_counts:
            table_counts[table_id] = defaultdict(dict)
        entity_counts: EntityCounts = table_counts[table_id]
        if entity_id not in entity_counts:
            entity_counts[entity_id] = defaultdict(Count)
        entity_counts[entity_id][rule_id] += count

    # XXX: errors are only iterated once, to avoid counting the same error
    # multiple times
    total_counts: ErrorCounts = defaultdict(Count)
    key_counts: Dict[SummaryKey, TableCounts] = defaultdict(dict)
    for e in errors:
        table_id, rule_id = _get_error_table_rule(e)
        row_ids = _get_error_row_ids(e)
        count = len(row_ids)
        total_counts[rule_id] += count
        for key in keys:
            if key == SummaryKey.ROW:
                for row_id in row_ids:
                    entity_id = str(row_id)
                    _update_entity(key, table_id, entity_id, rule_id, 1)
            else:
                column_id = e['columnName']
                entity_id = table_id if key == SummaryKey.TABLE else column_id
                _update_entity(key, table_id, entity_id, rule_id, count)

    return Counts(
        total_counts=total_counts,
        key_counts=key_counts,
    )


# error-summary generation
# -----------------------------------------------------------------------------


def _gen_summary_list(key: SummaryKey, entity_counts: EntityCounts
                      ) -> SummaryEntryList:
    """Generates a list of SummaryEntry objects from `entity_counts` that
    correspond to `key`."""
    summary_list = []
    for entity_id, error_count in entity_counts.items():
        for rule_id, count in error_count.items():
            entry = SummaryEntry(
                rule_id=rule_id,
                count=count,
                key=key,
                value=entity_id,
            )
            summary_list.append(entry)
    return summary_list


def _gen_summary(keys: Set[SummaryKey], counts: Counts) -> ErrorSummary:
    """generates summary lists per table, for all `keys`

    :param keys: the set of keys to summarize by.
    :param errors: the list of validation errors to count.
    """
    # keys must be sorted to make equality work in tests
    summary: ErrorSummary = defaultdict(list)
    for key in sorted(keys):
        table_counts: TableCounts = counts.key_counts[key]
        for table_id, entity_counts in table_counts.items():
            summary[table_id] += _gen_summary_list(key, entity_counts)
    return summary


# post-processing
# -----------------------------------------------------------------------------


def _increment_error_counts(a, b: ErrorCounts):
    for rule_id, count in b.items():
        a[rule_id] += count


def _get_keyval(e: SummaryEntry) -> Tuple[int, str]:
    """Returns tuple for sorting/grouping summary entries"""
    return (e.key, e.value)


def _calc_summary_entry_totals(entries: SummaryEntryList) -> SummaryEntryList:
    """Returns new entries with total counts per unique (key, value) pair."""
    result = []
    sorted_entries = sorted(entries, key=_get_keyval)
    for keyval, kv_entries in groupby(sorted_entries, key=_get_keyval):
        key, val = keyval
        total = sum(map(lambda e: e.count, kv_entries))
        entry = SummaryEntry(
            rule_id=RuleId._all,
            count=total,
            key=key,
            value=val,
        )
        result.append(entry)
    return result


def _gen_overview(report: ValidationReport,
                  errorkind_totals: Dict[ErrorKind, ErrorCounts]) -> dict:
    table_overviews = {}
    for table_id, info in report.table_info.items():
        table_overviews[table_id] = {
            'columns': info['columns'],
            'rows': info['rows'],
        }

    overview = {
        'tables': table_overviews,
        'errors': dict(errorkind_totals[ErrorKind.ERROR]),
        'warnings': dict(errorkind_totals[ErrorKind.WARNING]),
    }
    return overview


def _remove_summary_entries(summary: ErrorSummary, key: SummaryKey):
    """Removes summary entries with `key`."""
    for table_id, entries in summary.items():
        summary[table_id] = list(filter(lambda e: e.key != key, entries))
    assert key not in map(lambda e: e.key, summary[table_id])


# API
# -----------------------------------------------------------------------------


def summarize_report(report: ValidationReport,
                     by: Set[SummaryKey] = {SummaryKey.TABLE}
                     ) -> SummarizedReport:
    """Summarizes `report`.

    :param report: the validation report to be summarized
    :param by: what to summarize by. An error/warning summarization will be
    performed for each group/key specified. Defaults to `table`.
    """
    assert isinstance(report, ValidationReport), \
           "invalid type for param `report`"
    assert isinstance(by, set), "invalid type for param `by`"
    keys = by

    # count errors and generate summaries, one per error kind
    errorkind_summaries: Dict[ErrorKind, ErrorSummary] = {}
    errorkind_totals: Dict[ErrorKind, ErrorCounts] = {}
    errorkind_errors = {
        ErrorKind.ERROR: report.errors,
        ErrorKind.WARNING: report.warnings,
    }
    for error_kind in ErrorKind:
        errors: list = errorkind_errors[error_kind]
        counts = _count_errors(keys, errors)
        summary = _gen_summary(keys, counts)
        errorkind_summaries[error_kind] = summary
        errorkind_totals[error_kind] = counts.total_counts

    # add totals to the summary lists
    # for error_kind in ErrorKind:
    for summary in errorkind_summaries.values():
        for entries in summary.values():
            new_entries = _calc_summary_entry_totals(entries)
            entries += new_entries

    # generate the overview
    overview = _gen_overview(report, errorkind_totals)

    return SummarizedReport(
        data_version=report.data_version,
        schema_version=report.schema_version,
        package_version=__version__,
        overview=overview,
        errors=dict(errorkind_summaries[ErrorKind.ERROR]),
        warnings=dict(errorkind_summaries[ErrorKind.WARNING]),
    )
