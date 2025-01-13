from collections.abc import Iterable, Iterator
from typing import List, Tuple
# from pprint import pprint

from odm_validation.rules import Rule, RuleId

RuleError = Tuple[RuleId, dict]


class RuleFilter:
    """A rule filter.

    The blacklist takes precedence over the whitelist, and an empty whitelist
    represents all rules."""
    # `whitelist` is needed when testing schema generation and data validation.
    # Users may be more interested in `blacklist`, to remove certain irrelevant
    # errors from their reports.

    blacklist: List[RuleId]
    whitelist: List[RuleId]

    def __init__(self, blacklist=[], whitelist=[]):
        self.blacklist = blacklist
        self.whitelist = whitelist

    def enabled(self, rule: Rule):
        "Returns true if the rule `rule_id` is enabled."
        rule_id = rule.id
        return (rule_id not in self.blacklist and
                (rule_id in self.whitelist or self.whitelist == []))

    def filter(self, rules: Iterable) -> Iterator:
        return filter(self.enabled, rules)
