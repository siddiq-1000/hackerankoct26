import sys
sys.path.insert(0, '.')
import csv
import json
from pathlib import Path
from code.main import run_deletion_audit

cand_path = Path('candidate_final_output.csv')

print("[*] Running candidate full evaluation run...")
num_rows, counts = run_deletion_audit(
    dataset_dir=Path('dataset'),
    output_path=cand_path,
    filename='deletion_requests.csv'
)

print(f"[+] Candidate run finished: {num_rows} rows, distribution: {counts}")

# Now compare candidate_final_output.csv against output.csv
with open('output.csv', 'r', encoding='utf-8') as f:
    curr_rows = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open(cand_path, 'r', encoding='utf-8') as f:
    cand_rows = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

status_changes = []
step_changes = []

for cid, (c_st, c_steps) in curr_rows.items():
    new_st, new_steps = cand_rows[cid]
    if new_st != c_st:
        status_changes.append((cid, c_st, new_st))
    if new_steps != c_steps:
        step_changes.append((cid, len(c_steps), len(new_steps), c_st, new_st))

print(f"\n==========================================")
print(f"DIAGNOSTIC COMPARISON VS CURRENT output.csv:")
print(f"Total cases: {len(curr_rows)}")
print(f"Total status changes: {len(status_changes)}")
if status_changes:
    print("Status changes detail:")
    for cid, old_st, new_st in status_changes:
        print(f"  {cid}: {old_st} -> {new_st}")
print(f"Total rows with step changes: {len(step_changes)}")
print(f"==========================================")
