import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

ALLOWED_TRIPLES = {
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
    ("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED"),

    # Verification
    ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT"),
    ("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT"),
    ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED"),
    ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"),
    ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED"),
    ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED")
}

PHASE_RANK = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
OP_RANK = {
    "REPORT_REMAINING_RECORD": 1, "REPORT_EXPOSED_PII": 2, "REPORT_ACTIVE_DATA_FLOW": 3, "REPORT_RESTORE_RISK": 4,
    "DISABLE_DATA_FLOW": 1, "BLOCK_RESTORE": 2, "DELETE_RECORD": 3, "REDACT_RECORD": 4, "ANONYMIZE_RECORD": 5,
    "VERIFY_RECORD_ABSENT": 1, "VERIFY_RECORD_PRESENT": 2, "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4, "VERIFY_DATA_FLOW_DISABLED": 5, "VERIFY_RESTORE_BLOCKED": 6
}

def validate_row(row_idx: int, case_id: str, status: str, steps_json_str: str) -> List[str]:
    errors = []
    if status not in ["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"]:
        errors.append(f"Row {row_idx} ({case_id}): invalid deletion_status '{status}'")

    try:
        steps = json.loads(steps_json_str)
    except Exception as e:
        errors.append(f"Row {row_idx} ({case_id}): JSON decode error: {e}")
        return errors

    if not isinstance(steps, list):
        errors.append(f"Row {row_idx} ({case_id}): steps_json is not an array")
        return errors

    if status == "NOT_APPLICABLE":
        if steps != []:
            errors.append(f"Row {row_idx} ({case_id}): NOT_APPLICABLE must have empty steps_json [], got {len(steps)} items")
        return errors

    required_fields = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
    last_key = None

    for idx, s in enumerate(steps, 1):
        if not isinstance(s, dict):
            errors.append(f"Row {row_idx} ({case_id}) step {idx}: not a JSON object")
            continue

        missing = required_fields - set(s.keys())
        if missing:
            errors.append(f"Row {row_idx} ({case_id}) step {idx}: missing fields {missing}")

        step_no = s.get("step_no")
        if step_no != idx:
            errors.append(f"Row {row_idx} ({case_id}) step {idx}: expected step_no {idx}, got {step_no}")

        phase = s.get("phase")
        op = s.get("operation")
        state = s.get("state")
        ev_id = s.get("evidence_id")

        if (phase, op, state) not in ALLOWED_TRIPLES:
            errors.append(f"Row {row_idx} ({case_id}) step {idx}: invalid triple ({phase}, {op}, {state})")

        # Ordering check
        curr_key = (PHASE_RANK.get(phase, 99), OP_RANK.get(op, 99), s.get("system_id", ""), s.get("resource_id", ""))
        if last_key is not None and curr_key < last_key:
            errors.append(f"Row {row_idx} ({case_id}) step {idx}: out of canonical order ({curr_key} < {last_key})")
        last_key = curr_key

        # Evidence ID check
        if status == "COMPLETE":
            if not ev_id:
                errors.append(f"Row {row_idx} ({case_id}) step {idx}: COMPLETE case verification step must cite evidence_id")
        elif status == "INCOMPLETE":
            if phase == "FINDING" and not ev_id:
                errors.append(f"Row {row_idx} ({case_id}) step {idx}: FINDING must cite evidence_id")
            elif phase in ["REMEDIATION", "VERIFICATION"] and ev_id != "":
                errors.append(f"Row {row_idx} ({case_id}) step {idx}: proposed {phase} must have empty evidence_id, got '{ev_id}'")

    return errors

def validate_csv(csv_path: Path, expected_rows: Optional[int] = None) -> List[str]:
    errors = []
    if not csv_path.exists():
        return [f"File not found: {csv_path}"]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        expected_header = ["case_id", "deletion_status", "steps_json"]
        if header != expected_header:
            errors.append(f"Header mismatch: expected {expected_header}, got {header}")

        rows = list(reader)

    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"Row count mismatch: expected {expected_rows}, got {len(rows)}")

    last_case_id = ""
    for idx, r in enumerate(rows, 1):
        if len(r) != 3:
            errors.append(f"Row {idx}: expected 3 columns, got {len(r)}")
            continue

        cid, status, steps_str = r[0], r[1], r[2]
        if cid <= last_case_id:
            errors.append(f"Row {idx}: case_id '{cid}' not sorted after '{last_case_id}'")
        last_case_id = cid

        row_errs = validate_row(idx, cid, status, steps_str)
        errors.extend(row_errs)

    return errors
