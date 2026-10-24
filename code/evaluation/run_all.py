"""
Unified Test Runner for HackerRank Orchestrate Deletion Audit Agent.

Executes all verification gates:
1. Public Sample Evaluation (Accuracy & Schema)
2. Custom Cases A through E (Adversarial Edge Cases)
3. Intent Classifier Shuffle Invariance
4. Canonical Step Ordering & Tie-Breaker Logic
5. Policy Conflict Resolution Precedence
6. CSV Format & Contract Validation
7. Independent Oracle Discrepancy Analysis

Exits with code 0 only if all suites pass.
"""

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON_EXE = sys.executable

TEST_SUITES = [
    ("Canonical Step Ordering", ["code/evaluation/test_planner_order.py"]),
    ("Policy Conflict Resolution", ["code/evaluation/test_policy.py"]),
    ("Intent Classifier Shuffle Invariance", ["code/evaluation/test_intent_shuffling.py"]),
    ("Custom Evaluation Cases A-E", ["code/evaluation/test_custom_cases.py"]),
    ("Public Sample Evaluation", ["code/evaluation/main.py"]),
    ("CSV Format & Contract Validation", ["code/validate.py"]),
    ("Independent Oracle Discrepancy Scan", ["code/tools/analyze_discrepancies.py"]),
    ("Cross-Document Consistency Check", ["code/tools/consistency_check.py"]),
    ("Automated Document Claims Verification", ["code/tools/doc_claims_check.py"]),
    ("AGENTS.md §6.7 No Hardcoded Literal IDs", ["code/evaluation/test_no_hardcoded_ids.py"]),
    ("Pipeline Determinism (SHA-256 Check)", ["code/evaluation/test_determinism.py"]),
]

def main():
    print("=" * 60)
    print("RUNNING UNIFIED EVALUATION SUITE FOR DELETION AUDIT AGENT")
    print(f"Repo Root: {REPO_ROOT}")
    print(f"Python:    {PYTHON_EXE}")
    print("=" * 60)

    failed = []
    for name, args in TEST_SUITES:
        print(f"\n[SUITE] Running {name}...")
        cmd = [PYTHON_EXE] + args
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[PASS] {name}")
            if "analyze_discrepancies" in args[0] or "validate" in args[0]:
                for line in res.stdout.strip().splitlines()[-4:]:
                    print(f"       {line}")
        else:
            print(f"[FAIL] {name} (exit code {res.returncode})")
            print("--- STDOUT ---")
            print(res.stdout)
            print("--- STDERR ---")
            print(res.stderr)
            failed.append(name)

    print("\n" + "=" * 60)
    if not failed:
        print(f"ALL {len(TEST_SUITES)} TEST SUITES PASSED PERFECTLY (0 FAILURES)")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"TEST SUITE FAILED: {len(failed)} suites failed:")
        for f in failed:
            print(f"  - {f}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
