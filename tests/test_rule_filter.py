
import unittest

import common
import rules
from rules import ruleset
from validation import RuleFilter

common.unused_import_dummy = 1


def get_enabled_ids(rule_filter):
    return list(map(lambda r: r.id, rule_filter.filter(ruleset)))


class TestRuleFilter(common.OdmTestCase):

    def test_blacklist(self):
        unwanted_rule_id = rules.invalid_category.__name__
        rule_filter = RuleFilter(blacklist=[unwanted_rule_id])
        enabled_rule_ids = get_enabled_ids(rule_filter)
        self.assertNotIn(unwanted_rule_id, enabled_rule_ids)

    def test_whitelist(self):
        wanted_rule_id = rules.invalid_category.__name__
        rule_filter = RuleFilter(whitelist=[wanted_rule_id])
        enabled_rule_ids = get_enabled_ids(rule_filter)
        self.assertEqual([wanted_rule_id], enabled_rule_ids)

    def test_both(self):
        # should ignore whitelisted rule if it's in blacklist
        unwanted_rule_id = rules.invalid_category.__name__
        wanted_rule_id = rules.invalid_type.__name__
        rule_filter = RuleFilter(blacklist=[unwanted_rule_id],
                                 whitelist=[unwanted_rule_id,
                                            wanted_rule_id])
        enabled_rule_ids = get_enabled_ids(rule_filter)
        self.assertEqual([wanted_rule_id], enabled_rule_ids)


if __name__ == '__main__':
    unittest.main()
