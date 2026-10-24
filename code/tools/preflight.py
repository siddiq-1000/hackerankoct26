"""
Independent Preflight Verifier for HackerRank Orchestrate output.csv.

Shares ZERO code with the main pipeline. Reads solely output.csv and
dataset/deletion_requests.csv to enforce all grader submission contracts.
"""

import csv
import json
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_CSV = REPO_ROOT / "output.csv"
INPUT_CSV = REPO_ROOT / "dataset" / "deletion_requests.csv"

# Contract vocabulary
VALID_TRIPLES = {
    # Findings
    ("FINDING", "REPORT_REMAINING_RECORD", "PRESENT"),
    ("FINDING", "REPORT_EXPOSED_PII", "PRESENT"),
    ("FINDING", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE"),
    ("FINDING", "REPORT_RESTORE_RISK", "ACTIVE"),
    # Remediation
    ("REMEDIATION", "DISABLE_DATA_FLOW", "DISABLED"),
    ("REMEDIATION", "BLOCK_RESTORE", "BLOCKED"),
    ("REMEDIATION", "DELETE_RECORD", "ABSENT"),
    ("REMEDIATION", "REDACT_RECORD", "REDACTED"),
    ("REMEDIATION", "ANONYMIZED_RECORD", "ANONYMIZED"),  # alias if any
    ("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED"),
    # Verification
    ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT"),
    ("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT"),
    ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED"),
    ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"),
    ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED"),
    ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED"),
}

VALID_STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_preflight() -> bool:
    print("=" * 60)
    print("INDEPENDENT PREFLIGHT VERIFICATION: output.csv")
    print(f"Target File: {OUTPUT_CSV}")
    print("=" * 60)

    errors = []

    # 1. File existence & basic checks
    if not OUTPUT_CSV.exists():
        print(f"[FATAL] output.csv does not exist at {OUTPUT_CSV}")
        return False

    size = OUTPUT_CSV.stat().st_size
    if size == 0:
        print("[FATAL] output.csv is empty")
        return False
    print(f"[*] File Size: {size:,} bytes")

    # 2. SHA-256
    file_sha256 = compute_sha256(OUTPUT_CSV)
    print(f"[*] SHA-256 Hash: {file_sha256}")

    # 3. Read input case_ids and sort by case_id (contract requirement)
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        input_cases = sorted([r["case_id"] for r in csv.DictReader(f)])

    if len(input_cases) != 518:
        errors.append(f"Expected 518 input cases in {INPUT_CSV}, got {len(input_cases)}")

    # 4. Read output.csv
    try:
        with open(OUTPUT_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != ["case_id", "deletion_status", "steps_json"]:
                errors.append(f"Header mismatch: expected ['case_id', 'deletion_status', 'steps_json'], got {header}")

            rows = list(reader)
    except UnicodeDecodeError as e:
        errors.append(f"UTF-8 decode failure: {e}")
        return False

    print(f"[*] Row Count: {len(rows)} data rows")
    if len(rows) != 518:
        errors.append(f"Row count mismatch: expected exactly 518 rows, got {len(rows)}")

    # 5. Row-by-row validation
    prev_case_id = ""
    status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

    for idx, row in enumerate(rows, start=1):
        if len(row) != 3:
            errors.append(f"Row {idx} has {len(row)} columns instead of 3")
            continue

        cid, status, steps_raw = row[0], row[1], row[2]

        # Strict lexicographical ordering by case_id
        if cid <= prev_case_id:
            errors.append(f"Row {idx} out of order: '{cid}' not strictly greater than '{prev_case_id}'")
        prev_case_id = cid

        # Matching input case_id in exact position
        if idx <= len(input_cases) and cid != input_cases[idx - 1]:
            errors.append(f"Row {idx} case_id mismatch: expected {input_cases[idx-1]}, got {cid}")

        # Status validation
        if status not in VALID_STATUSES:
            errors.append(f"Row {idx} [{cid}] invalid status: {status}")
        else:
            status_counts[status] += 1

        # Parse steps_json
        try:
            steps = json.loads(steps_raw)
        except Exception as e:
            errors.append(f"Row {idx} [{cid}] JSON parse error: {e}")
            continue

        if not isinstance(steps, list):
            errors.append(f"Row {idx} [{cid}] steps_json is not an array")
            continue

        # Status specific rules
        if status == "NOT_APPLICABLE":
            if steps != []:
                errors.append(f"Row {idx} [{cid}] NOT_APPLICABLE must have empty steps_json [], got {len(steps)} steps")
            continue

        if status == "COMPLETE":
            for s in steps:
                if s.get("phase") != "VERIFICATION":
                    errors.append(f"Row {idx} [{cid}] COMPLETE case contains non-VERIFICATION step: {s.get('phase')}")
                if not s.get("evidence_id"):
                    errors.append(f"Row {idx} [{cid}] COMPLETE case verification step missing evidence_id: {s}")

        if status == "INCOMPLETE":
            phases = [s.get("phase") for s in steps]
            phase_set = set(phases)
            if "FINDING" not in phase_set:
                errors.append(f"Row {idx} [{cid}] INCOMPLETE case missing FINDING phase")

        # Step numbering & triple validity
        expected_step_no = 1
        for s in steps:
            s_no = s.get("step_no")
            if s_no != expected_step_no:
                errors.append(f"Row {idx} [{cid}] step_no non-consecutive: expected {expected_step_no}, got {s_no}")
            expected_step_no += 1

            triple = (s.get("phase"), s.get("operation"), s.get("state"))
            if triple not in VALID_TRIPLES:
                errors.append(f"Row {idx} [{cid}] invalid (phase, operation, state) triple: {triple}")

            if s.get("phase") in ["REMEDIATION"] and s.get("evidence_id") != "":
                errors.append(f"Row {idx} [{cid}] REMEDIATION step must have empty evidence_id, got '{s.get('evidence_id')}'")

    print("\n[*] Deletion Status Distribution:")
    for k, v in status_counts.items():
        pct = (v / len(rows) * 100) if rows else 0
        print(f"    {k:15}: {v:3d} ({pct:5.2f}%)")

    print("\n" + "=" * 60)
    if not errors:
        print("PREFLIGHT CHECK PASSED: 0 ERRORS DETECTED.")
        print(f"FINAL SUBMISSION SHA-256: {file_sha256}")
        print("=" * 60)
        return True
    else:
        print(f"PREFLIGHT CHECK FAILED: {len(errors)} ERRORS:")
        for err in errors[:20]:
            print(f"  [ERROR] {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_preflight()
    sys.exit(0 if success else 1)
