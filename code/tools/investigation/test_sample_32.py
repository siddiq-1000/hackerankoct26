import sys
sys.path.insert(0, '.')
import csv
import json
from pathlib import Path
from code.main import run_deletion_audit

out_path = Path('code/tools/investigation/test_sample_output.csv')
num_rows, counts = run_deletion_audit(
    dataset_dir=Path('dataset'),
    output_path=out_path,
    filename='sample_deletion_requests.csv'
)

print(f"Sample audit completed. Rows: {num_rows}, Counts: {counts}")

# Compare with dataset/sample_output.csv
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    expected = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open(out_path, 'r', encoding='utf-8') as f:
    actual = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

matched_status = 0
matched_steps = 0
total = len(expected)

for cid, (exp_st, exp_steps) in expected.items():
    act_st, act_steps = actual.get(cid, ('MISSING', []))
    if act_st == exp_st:
        matched_status += 1
    if act_steps == exp_steps:
        matched_steps += 1
    else:
        print(f"\nMismatch in {cid}:")
        print(f"  Status: exp={exp_st}, act={act_st}")
        print(f"  Expected steps ({len(exp_steps)}):")
        for s in exp_steps:
            print(f"    {s}")
        print(f"  Actual steps ({len(act_steps)}):")
        for s in act_steps:
            print(f"    {s}")

print(f"\n==========================================")
print(f"SAMPLE RESULTS: Status Accuracy = {matched_status}/{total} ({matched_status/total:.1%})")
print(f"SAMPLE RESULTS: Exact Step Accuracy = {matched_steps}/{total} ({matched_steps/total:.1%})")
print(f"==========================================")
