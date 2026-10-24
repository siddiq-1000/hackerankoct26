#!/usr/bin/env python3
"""
Test to ensure all documentation strictly cites valid rule IDs from deletion_rules.csv.
Implements Section A3 requirements from HackerRank Orchestrate (October 2026) Brief 3B.
"""

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RULES_CSV = REPO_ROOT / "dataset" / "deletion_rules.csv"

def test_rule_references():
    print("Testing documentation rule references against deletion_rules.csv...")

    # 1. Load valid rule IDs
    assert RULES_CSV.exists(), f"Rules file not found at {RULES_CSV}"
    valid_rules = set()
    with open(RULES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            valid_rules.add(r["rule_id"].lower())

    print(f"[*] Valid rules in policy file ({len(valid_rules)} rules): {sorted(valid_rules)}")

    # 2. Scan all docs and evaluation reports
    doc_paths = list((REPO_ROOT / "code" / "docs").glob("*.md")) + \
                list((REPO_ROOT / "code" / "evaluation").glob("*.md")) + \
                [REPO_ROOT / "README.md"]

    rule_pattern = re.compile(r"\brule_(\d+)\b", re.IGNORECASE)
    alt_rule_pattern = re.compile(r"\bRule\s+(\d+)\b")

    invalid_citations = []

    for dp in doc_paths:
        if not dp.exists():
            continue
        text = dp.read_text(encoding="utf-8", errors="ignore")

        # Find rule_XX
        for m in rule_pattern.finditer(text):
            r_num = int(m.group(1))
            formatted_rule = f"rule_{r_num:02d}"
            if formatted_rule not in valid_rules:
                invalid_citations.append((dp.name, m.group(0), f"Not in policy table (expected rule_01..rule_{len(valid_rules):02d})"))

        # Find Rule XX
        for m in alt_rule_pattern.finditer(text):
            r_num = int(m.group(1))
            formatted_rule = f"rule_{r_num:02d}"
            if formatted_rule not in valid_rules:
                invalid_citations.append((dp.name, m.group(0), f"Not in policy table (expected Rule 1..Rule {len(valid_rules)})"))

    if invalid_citations:
        print(f"[FAIL] Found {len(invalid_citations)} invalid rule references:")
        for fn, cite, reason in invalid_citations:
            print(f"  - {fn}: '{cite}' -> {reason}")
        assert False, f"Documentation contains {len(invalid_citations)} invalid rule citations"

    print(f"[PASS] All rule citations in documentation strictly match dataset/deletion_rules.csv.")

if __name__ == "__main__":
    test_rule_references()
