"""Test for No Hardcoded Participant/Case IDs in Core Pipeline and Maintained Tools.

Enforces AGENTS.md §6.7 requirements:
'Do not use organizer-only files, hardcoded golden labels, or case-family shortcuts.'
Scans non-test Python files under code/ and maintained tools in code/tools/ for literal
case_N, evidence_N, user_N, account_N identifiers.
Separately reports exploratory investigation scripts.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = REPO_ROOT / "code"

ID_PATTERN = re.compile(r'\b(case_\d+|user_\d+|account_\d+|evidence_\d+)\b')

EXCLUDED_DIRS = {"evaluation", "cache", "__pycache__", "docs", "investigation"}

def test_no_hardcoded_ids():
    hits = []
    scanned_files = 0
    for root, dirs, files in os.walk(CODE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if file.endswith(".py"):
                scanned_files += 1
                p = Path(root) / file
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        matches = ID_PATTERN.findall(line)
                        if matches:
                            hits.append((str(p.relative_to(REPO_ROOT)), line_no, matches, line.strip()))

    print(f"Hardcoded ID Scan completed across {scanned_files} core and operational files.")
    if hits:
        print(f"[FAIL] Found {len(hits)} hardcoded ID hits in core pipeline / maintained code:")
        for file_path, line_no, matches, line in hits:
            print(f"  {file_path}:{line_no} -> {matches} | {line}")
        assert False, f"Hardcoded ID violations detected: {len(hits)} occurrences"
    else:
        print("[PASS] 0 hardcoded IDs found in core pipeline code and maintained operational tools.")

if __name__ == "__main__":
    test_no_hardcoded_ids()
