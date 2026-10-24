import csv
import json

# Let's inspect git history to compare the baseline output.csv (commit 5af6321) vs current output.csv (commit 8e55f90)
# Or read git show 5af6321:output.csv
import subprocess

p = subprocess.run(['git', 'show', '5af6321:output.csv'], capture_output=True, text=True)
base_rows = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(p.stdout.splitlines())}

with open('output.csv', 'r', encoding='utf-8') as f:
    curr_rows = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

# Find all COMPLETE cases in curr_rows where steps changed
changed_complete = []
for cid, (st, steps) in curr_rows.items():
    if st == 'COMPLETE':
        b_st, b_steps = base_rows[cid]
        if steps != b_steps:
            has_ana_new = any(s['system_id'] == 'analytics_platform' for s in steps)
            has_ana_old = any(s['system_id'] == 'analytics_platform' for s in b_steps)
            changed_complete.append((cid, len(b_steps), len(steps), has_ana_old, has_ana_new, b_steps, steps))

print(f"Total COMPLETE cases in current output.csv: {sum(1 for st, _ in curr_rows.values() if st == 'COMPLETE')}")
print(f"Total COMPLETE cases with changed steps: {len(changed_complete)}")

gained_analytics = [c for c in changed_complete if not c[3] and c[4]]
other_changed = [c for c in changed_complete if not (not c[3] and c[4])]

print(f"Cases that gained analytics steps: {len(gained_analytics)}")
print(f"Other COMPLETE cases with changed steps: {len(other_changed)}")

print("\n=== LIST OF THE OTHER CHANGED COMPLETE ROWS ===")
for c in other_changed:
    cid, b_len, c_len, h_old, h_new, b_s, c_s = c
    print(f"\nCase {cid}: baseline_len={b_len}, current_len={c_len}, had_ana={h_old}->{h_new}")
    print("  Baseline steps:")
    for s in b_s:
        print(f"    {s['step_no']}: {s['system_id']} {s['resource_id']} {s['operation']} {s['evidence_id']}")
    print("  Current steps:")
    for s in c_s:
        print(f"    {s['step_no']}: {s['system_id']} {s['resource_id']} {s['operation']} {s['evidence_id']}")
