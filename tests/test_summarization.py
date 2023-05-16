import unittest

import common
from part_tables import ODM_VERSION_STR
from reports import ErrorKind, TableInfo, ValidationReport
from rules import RuleId
from versions import __version__
# from pprint import pprint

from summarization import (
    _calc_summary_entry_totals,
    ErrorSummary,
    SummaryEntry,
    SummaryKey,
    summarize_report,
)

SE = SummaryEntry

ALL = RuleId._all
W0 = RuleId._coercion
E0 = RuleId.invalid_type
E1 = RuleId.less_than_min_value

errors_in = [
    {
        'errorType': 'invalid_type',
        'tableName': 'addresses',
        'columnName': 'addID',
        'rowNumber': 1,
    },
    {
        'errorType': 'invalid_type',
        'tableName': 'addresses',
        'columnName': 'addID',
        'rowNumber': 2,
    },
    {
        'errorType': 'invalid_type',
        'tableName': 'sites',
        'columnName': 'siteID',
        'rowNumber': 1,
    },
]

errors_out: ErrorSummary = {
    'addresses': [
        SE(rule_id=E0, count=2, key=SummaryKey.table, value='addresses'),
        SE(rule_id=E0, count=2, key=SummaryKey.column, value='addID'),
        SE(rule_id=E0, count=1, key=SummaryKey.row, value='1'),
        SE(rule_id=E0, count=1, key=SummaryKey.row, value='2'),
        SE(rule_id=ALL, count=2, key=SummaryKey.table, value='addresses'),
        SE(rule_id=ALL, count=2, key=SummaryKey.column, value='addID'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='1'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='2'),
    ],
    'sites': [
        SE(rule_id=E0, count=1, key=SummaryKey.table, value='sites'),
        SE(rule_id=E0, count=1, key=SummaryKey.column, value='siteID'),
        SE(rule_id=E0, count=1, key=SummaryKey.row, value='1'),
        SE(rule_id=ALL, count=1, key=SummaryKey.table, value='sites'),
        SE(rule_id=ALL, count=1, key=SummaryKey.column, value='siteID'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='1'),
    ]
}

warnings_in = [
    {
        'warningType': '_coercion',
        'tableName': 'addresses',
        'columnName': 'addID',
        'rowNumber': 1,
    },
    {
        'warningType': '_coercion',
        'tableName': 'sites',
        'columnName': 'siteID',
        'rowNumbers': list(range(1, 4)),
    },
]

warnings_out = {
    'addresses': [
        SE(rule_id=W0, count=1, key=SummaryKey.table, value='addresses'),
        SE(rule_id=W0, count=1, key=SummaryKey.column, value='addID'),
        SE(rule_id=W0, count=1, key=SummaryKey.row, value='1'),
        SE(rule_id=ALL, count=1, key=SummaryKey.table, value='addresses'),
        SE(rule_id=ALL, count=1, key=SummaryKey.column, value='addID'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='1'),
    ],
    'sites': [
        SE(rule_id=W0, count=3, key=SummaryKey.table, value='sites'),
        SE(rule_id=W0, count=3, key=SummaryKey.column, value='siteID'),
        SE(rule_id=W0, count=1, key=SummaryKey.row, value='1'),
        SE(rule_id=W0, count=1, key=SummaryKey.row, value='2'),
        SE(rule_id=W0, count=1, key=SummaryKey.row, value='3'),
        SE(rule_id=ALL, count=3, key=SummaryKey.table, value='sites'),
        SE(rule_id=ALL, count=3, key=SummaryKey.column, value='siteID'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='1'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='2'),
        SE(rule_id=ALL, count=1, key=SummaryKey.row, value='3'),
    ]
}

overview = {
    'tables': {
        'addresses': {
            'columns': 1,
            'rows': 2,
        },
        'sites': {
            'columns': 1,
            'rows': 1,
        },
    },
    'errors': {
        E0: 3,
    },
    'warnings': {
        W0: 4,
    }
}


def init_report(errors: list, warnings: list) -> ValidationReport:
    return ValidationReport(
        data_version=ODM_VERSION_STR,
        schema_version=ODM_VERSION_STR,
        package_version=__version__,
        table_info={
            'addresses': TableInfo(columns=1, rows=2),
            'sites': TableInfo(columns=1, rows=1),
        },
        errors=errors,
        warnings=warnings,
    )


def filter_errorsummary(summary: ErrorSummary, key: SummaryKey):
    result = {}
    for table_id, entries in summary.items():
        result[table_id] = list(
            filter(lambda e: e.key == key, entries))
    return result


class TestSummarizationInternals(common.OdmTestCase):
    errorkind_summaries = {
        ErrorKind.ERROR: errors_out,
        ErrorKind.WARNING: warnings_out,
    }
    table_counts = {
        'addresses': {
            E0: 2,
            W0: 1,
        },
        'sites': {
            E0: 1,
            W0: 3,
        }
    }
    errorkind_counts = {
        ErrorKind.ERROR: {
            E0: 3,
        },
        ErrorKind.WARNING: {
            W0: 4,
        },
    }

    def setUp(self):
        # print(self._testMethodName)
        self.maxDiff = None

    def test_calc_summary_entry_totals(self):
        entries_in = [
            SE(rule_id=E0, count=2, key=SummaryKey.table, value='addresses'),
            SE(rule_id=E1, count=2, key=SummaryKey.table, value='addresses'),
        ]
        entries_out = [
            SE(rule_id=ALL, count=4, key=SummaryKey.table, value='addresses')
        ]
        result = _calc_summary_entry_totals(entries_in)
        self.assertEqual(entries_out, result)


class TestSummarizationApi(common.OdmTestCase):
    report: ValidationReport

    def setUp(self):
        # print(self._testMethodName)
        self.maxDiff = None
        self.report = init_report(errors_in, warnings_in)

    def check_summary(self, summary, key: SummaryKey):
        expected_e = filter_errorsummary(errors_out, key)
        expected_w = filter_errorsummary(warnings_out, key)
        self.assertEqual(expected_e, summary.errors)
        self.assertEqual(expected_w, summary.warnings)

    def test_by_table(self):
        summary = summarize_report(self.report, by={SummaryKey.table})
        self.check_summary(summary, SummaryKey.table)

    def test_by_column(self):
        summary = summarize_report(self.report, by={SummaryKey.column})
        self.check_summary(summary, SummaryKey.column)

    def test_by_row(self):
        summary = summarize_report(self.report, by={SummaryKey.row})
        self.check_summary(summary, SummaryKey.row)

    def test_by_all(self):
        summary = summarize_report(self.report, by={SummaryKey.table,
                                                    SummaryKey.column,
                                                    SummaryKey.row})
        self.assertEqual(errors_out, summary.errors)
        self.assertEqual(warnings_out, summary.warnings)

    def test_by_none(self):
        summary = summarize_report(self.report, by=set())
        self.assertEqual({}, summary.errors)
        self.assertEqual({}, summary.warnings)

    def test_overview(self):
        summary = summarize_report(self.report, by=set())
        self.assertEqual(overview, summary.overview)


if __name__ == '__main__':
    unittest.main()
