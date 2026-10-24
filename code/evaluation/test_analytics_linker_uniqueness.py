"""Test analytics linker 1-to-1 uniqueness and sample ground-truth isolation."""

import csv
import json
import unittest
from pathlib import Path
import sys

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.analytics_linker import AnalyticsLinker

class TestAnalyticsLinkerUniqueness(unittest.TestCase):
    def setUp(self):
        self.dataset_dir = REPO_ROOT / "dataset"
        self.linker = AnalyticsLinker(self.dataset_dir)

    def test_sample_rids_loaded(self):
        """Verify that sample ground-truth claimed RIDs are loaded and non-empty."""
        self.assertGreater(len(self.linker.sample_claimed_rids), 0)
        self.assertIn("analytics_5335", self.linker.sample_claimed_rids)

    def test_evaluation_pairing_uniqueness(self):
        """Verify that evaluation requests do not reuse sample RIDs or each other's RIDs."""
        eval_csv = self.dataset_dir / "deletion_requests.csv"
        with open(eval_csv, "r", encoding="utf-8") as f:
            eval_reqs = list(csv.DictReader(f))

        # Test with dummy COMPLETE status for all eval requests
        pairs = self.linker.build_batch_pairs(eval_reqs)
        
        assigned_rids = [rid for rid, fid in pairs.values()]
        
        # 1. Internal uniqueness (no duplicate RIDs across evaluation cases)
        self.assertEqual(len(assigned_rids), len(set(assigned_rids)), "Duplicate analytics RIDs assigned across evaluation cases")

        # 2. Split isolation (no evaluation case claims a sample ground-truth RID)
        sample_overlap = set(assigned_rids) & self.linker.sample_claimed_rids
        self.assertEqual(len(sample_overlap), 0, f"Evaluation cases claimed sample ground-truth RIDs: {sample_overlap}")

if __name__ == "__main__":
    unittest.main()
