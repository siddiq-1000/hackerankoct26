import csv
import json

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = list(csv.DictReader(f))

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_reqs = {r['case_id']: r for r in csv.DictReader(f)}

print("=== ALL SUPPORT STEPS IN SAMPLE GROUND TRUTH ===")
support_cases = []
for r in sample_out:
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    sup_steps = [s for s in steps if s['system_id'] == 'support_platform']
    if sup_steps:
        support_cases.append((cid, r['deletion_status'], sup_steps))
        print(f"\nCase {cid} ({r['deletion_status']}) [email={sample_reqs[cid]['email']}]:")
        for s in sup_steps:
            print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
