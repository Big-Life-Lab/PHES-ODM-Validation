import unittest

from odm_validation.rules import RuleId, ruleset
from odm_validation.validation import RuleFilter

import common


def get_enabled_ids(rule_filter):
    return list(map(lambda r: r.id, rule_filter.filter(ruleset)))


class TestRuleFilter(common.OdmTestCase):

    def test_blacklist(self):
        unwanted_rule_id = RuleId.invalid_category
        rule_filter = RuleFilter(blacklist=[unwanted_rule_id])
        enabled_rule_ids = get_enabled_ids(rule_filter)
        self.assertNotIn(unwanted_rule_id, enabled_rule_ids)

    def test_whitelist(self):
        wanted_rule_id = RuleId.invalid_category
        rule_filter = RuleFilter(whitelist=[wanted_rule_id])
        enabled_rule_ids = get_enabled_ids(rule_filter)
        self.assertEqual([wanted_rule_id], enabled_rule_ids)

    def test_both(self):
        # should ignore whitelisted rule if it's in blacklist
        unwanted_rule_id = RuleId.invalid_category
        wanted_rule_id = RuleId.invalid_type
        rule_filter = RuleFilter(blacklist=[unwanted_rule_id],
                                 whitelist=[unwanted_rule_id,
                                            wanted_rule_id])
        enabled_rule_ids = get_enabled_ids(rule_filter)
        self.assertEqual([wanted_rule_id], enabled_rule_ids)


if __name__ == '__main__':
    unittest.main()
