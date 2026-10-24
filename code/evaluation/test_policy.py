"""
Synthetic Unit Tests for Deletion Policy & Conflict Resolution Engine.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.conflicts import ConflictResolver, PolicyRule

class TestPolicyConflictResolution(unittest.TestCase):
    def test_retention_wins_over_deletion(self):
        """Rule 1: Retention strictly overrides deletion."""
        actions = ["DELETE", "RETAIN"]
        winner = ConflictResolver.resolve_conflicting_actions(actions)
        self.assertEqual(winner, "RETAIN")

        rules = [
            PolicyRule("RULE_DEL", "SECURITY_LOG", "ALL", "DELETE"),
            PolicyRule("RULE_RET", "SECURITY_LOG", "AUDIT_REQUIRED", "RETAIN")
        ]
        winning_rule = ConflictResolver.resolve_rule_conflict(rules)
        self.assertEqual(winning_rule.rule_id, "RULE_RET")

    def test_redact_wins_over_keep(self):
        """Rule 2: Redaction of direct PII overrides unrestricted retention."""
        actions = ["KEEP", "REDACT"]
        winner = ConflictResolver.resolve_conflicting_actions(actions)
        self.assertEqual(winner, "REDACT")

    def test_anonymize_wins_over_keep(self):
        """Rule 3: Anonymization overrides unrestricted retention."""
        actions = ["KEEP", "ANONYMIZE"]
        winner = ConflictResolver.resolve_conflicting_actions(actions)
        self.assertEqual(winner, "ANONYMIZE")

    def test_disable_data_flow_wins_over_keep(self):
        """Rule 4: Disabling an active flow overrides keeping it active."""
        actions = ["ACTIVE", "DISABLE"]
        winner = ConflictResolver.resolve_conflicting_actions(actions)
        self.assertEqual(winner, "DISABLE")

    def test_block_restore_wins_over_keep(self):
        """Rule 5: Blocking a restore risk overrides backup retention."""
        actions = ["KEEP", "BLOCK"]
        winner = ConflictResolver.resolve_conflicting_actions(actions)
        self.assertEqual(winner, "BLOCK")

    def test_complex_multi_rule_hierarchy(self):
        """Rule 6: Complex multi-action dispute resolution."""
        actions = ["DELETE", "KEEP", "ANONYMIZE", "REDACT"]
        # Anonymize has higher weight than Redact or Delete in unrestricted keeping
        winner = ConflictResolver.resolve_conflicting_actions(actions)
        self.assertEqual(winner, "ANONYMIZE")

if __name__ == "__main__":
    unittest.main()
