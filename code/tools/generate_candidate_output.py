import csv
import json
import shutil
from pathlib import Path

# Load current output.csv
with open('output.csv', 'r', encoding='utf-8') as f:
    orig_rows = list(csv.DictReader(f))

# Run candidate generation by taking the unique 1-to-1 batch links found in test_batch_1to1.py
# and injecting the VERIFY_RECORD_ANONYMIZED step into steps_json for those COMPLETE cases.
from test_batch_1to1 import batch_paired

print("=== GENERATING output_candidate.csv ===")
print(f"Injecting analytics verification steps for {len(batch_paired)} uniquely linked COMPLETE cases...")

candidate_rows = []
changed_rows_by_status = {'COMPLETE': 0, 'INCOMPLETE': 0, 'NOT_APPLICABLE': 0}
status_changes = 0

for r in orig_rows:
    cid = r['case_id']
    st = r['deletion_status']
    steps = json.loads(r['steps_json'])

    if cid in batch_paired:
        rid, fid = batch_paired[cid]
        # Check if already present
        has_step = any(s['system_id'] == 'analytics_platform' and s['operation'] == 'VERIFY_RECORD_ANONYMIZED' for s in steps)
        if not has_step:
            new_step = {
                "step_no": len(steps) + 1,
                "phase": "VERIFICATION",
                "system_id": "analytics_platform",
                "resource_id": rid,
                "operation": "VERIFY_RECORD_ANONYMIZED",
                "state": "ANONYMIZED",
                "evidence_id": fid
            }
            steps.append(new_step)
            # Re-sort steps canonically
            # Priority: account_service -> security_service -> support_platform -> analytics_platform -> integration_service -> backup_service
            sys_priority = {
                "account_service": 1,
                "security_service": 2,
                "support_platform": 3,
                "analytics_platform": 4,
                "integration_service": 5,
                "backup_service": 6,
                "identity_service": 7
            }
            steps.sort(key=lambda s: sys_priority.get(s['system_id'], 99))
            for i, s in enumerate(steps, 1):
                s['step_no'] = i

            changed_rows_by_status[st] += 1

    candidate_rows.append({
        'case_id': cid,
        'deletion_status': st,
        'steps_json': json.dumps(steps)
    })

# Write candidate output (untracked)
with open('output_candidate.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['case_id', 'deletion_status', 'steps_json'])
    writer.writeheader()
    writer.writerows(candidate_rows)

print(f"Successfully generated output_candidate.csv ({len(candidate_rows)} rows).")
print(f"Rows changed by status: {changed_rows_by_status}")
print(f"Total status changes:   {status_changes}")

# Diff summary against output.csv
diff_count = sum(1 for o, c in zip(orig_rows, candidate_rows) if o != c)
print(f"Total row diff count:   {diff_count}")
