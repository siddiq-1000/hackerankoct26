"""
Unit Tests for Canonical Step Ordering and Step Schema Validation.
"""

import sys
import unittest
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.planner import canonical_step_sort_key, PHASE_RANK, OP_RANK

class TestPlannerCanonicalOrdering(unittest.TestCase):
    def test_phase_ordering(self):
        """FINDING (1) < REMEDIATION (2) < VERIFICATION (3)."""
        steps = [
            {"phase": "VERIFICATION", "operation": "VERIFY_RECORD_ABSENT", "system_id": "a", "resource_id": "1"},
            {"phase": "FINDING", "operation": "REPORT_REMAINING_RECORD", "system_id": "a", "resource_id": "1"},
            {"phase": "REMEDIATION", "operation": "DELETE_RECORD", "system_id": "a", "resource_id": "1"},
        ]
        sorted_steps = sorted(steps, key=canonical_step_sort_key)
        self.assertEqual(sorted_steps[0]["phase"], "FINDING")
        self.assertEqual(sorted_steps[1]["phase"], "REMEDIATION")
        self.assertEqual(sorted_steps[2]["phase"], "VERIFICATION")

    def test_operation_ordering_within_remediation(self):
        """
        Remediation order:
        1. DISABLE_DATA_FLOW
        2. BLOCK_RESTORE
        3. DELETE_RECORD
        4. REDACT_RECORD
        5. ANONYMIZE_RECORD
        """
        ops = [
            "ANONYMIZE_RECORD",
            "DELETE_RECORD",
            "DISABLE_DATA_FLOW",
            "REDACT_RECORD",
            "BLOCK_RESTORE"
        ]
        steps = [{"phase": "REMEDIATION", "operation": op, "system_id": "sys", "resource_id": "res"} for op in ops]
        sorted_steps = sorted(steps, key=canonical_step_sort_key)
        expected_order = [
            "DISABLE_DATA_FLOW",
            "BLOCK_RESTORE",
            "DELETE_RECORD",
            "REDACT_RECORD",
            "ANONYMIZE_RECORD"
        ]
        actual_order = [s["operation"] for s in sorted_steps]
        self.assertEqual(actual_order, expected_order)

    def test_tie_breakers(self):
        """Tie breaker: system_id then resource_id."""
        steps = [
            {"phase": "FINDING", "operation": "REPORT_REMAINING_RECORD", "system_id": "support_service", "resource_id": "ticket_2"},
            {"phase": "FINDING", "operation": "REPORT_REMAINING_RECORD", "system_id": "account_service", "resource_id": "account_2"},
            {"phase": "FINDING", "operation": "REPORT_REMAINING_RECORD", "system_id": "account_service", "resource_id": "account_1"},
        ]
        sorted_steps = sorted(steps, key=canonical_step_sort_key)
        self.assertEqual(sorted_steps[0]["system_id"], "account_service")
        self.assertEqual(sorted_steps[0]["resource_id"], "account_1")
        self.assertEqual(sorted_steps[1]["system_id"], "account_service")
        self.assertEqual(sorted_steps[1]["resource_id"], "account_2")
        self.assertEqual(sorted_steps[2]["system_id"], "support_service")

    def test_shuffle_invariance(self):
        """Sorting must produce identical ordering regardless of shuffle order."""
        base_steps = [
            {"phase": "FINDING", "operation": "REPORT_REMAINING_RECORD", "system_id": "sys1", "resource_id": "res1"},
            {"phase": "FINDING", "operation": "REPORT_ACTIVE_DATA_FLOW", "system_id": "sys2", "resource_id": "res2"},
            {"phase": "REMEDIATION", "operation": "DISABLE_DATA_FLOW", "system_id": "sys2", "resource_id": "res2"},
            {"phase": "REMEDIATION", "operation": "DELETE_RECORD", "system_id": "sys1", "resource_id": "res1"},
            {"phase": "VERIFICATION", "operation": "VERIFY_RECORD_ABSENT", "system_id": "sys1", "resource_id": "res1"},
            {"phase": "VERIFICATION", "operation": "VERIFY_DATA_FLOW_DISABLED", "system_id": "sys2", "resource_id": "res2"},
        ]
        canonical = sorted(base_steps, key=canonical_step_sort_key)
        
        for _ in range(20):
            shuffled = list(base_steps)
            random.shuffle(shuffled)
            resorted = sorted(shuffled, key=canonical_step_sort_key)
            self.assertEqual(canonical, resorted)

if __name__ == "__main__":
    unittest.main()
