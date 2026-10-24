"""Test for No Hardcoded Participant/Case IDs in Core Pipeline Code.

Enforces AGENTS.md §6.7 requirements:
'Do not use organizer-only files, hardcoded golden labels, or case-family shortcuts.'
Scans non-test Python files under code/ for literal case_N, evidence_N, user_N, account_N identifiers.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = REPO_ROOT / "code"

ID_PATTERN = re.compile(r'\b(case_\d+|user_\d+|account_\d+|evidence_\d+)\b')

EXCLUDED_DIRS = {"evaluation", "cache", "__pycache__", "tools", "docs"}

def test_no_hardcoded_ids():
    hits = []
    for root, dirs, files in os.walk(CODE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if file.endswith(".py"):
                p = Path(root) / file
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        matches = ID_PATTERN.findall(line)
                        if matches:
                            hits.append((str(p.relative_to(REPO_ROOT)), line_no, matches, line.strip()))

    print(f"Hardcoded ID Scan completed across core code.")
    if hits:
        print(f"[FAIL] Found {len(hits)} hardcoded ID hits in core pipeline code:")
        for file_path, line_no, matches, line in hits:
            print(f"  {file_path}:{line_no} -> {matches} | {line}")
        assert False, f"Hardcoded ID violations detected: {len(hits)} occurrences"
    else:
        print("[PASS] 0 hardcoded IDs found in core pipeline code.")

if __name__ == "__main__":
    test_no_hardcoded_ids()
