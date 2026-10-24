import csv
import json

with open('candidate_final_output.csv', 'r', encoding='utf-8') as f:
    cand = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('output.csv', 'r', encoding='utf-8') as f:
    curr = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

for cid in ['case_479', 'case_503']:
    print(f"\n{cid}:")
    print(f"  Old: {curr[cid][0]} ({len(curr[cid][1])} steps)")
    for s in curr[cid][1]:
        print(f"    {s['phase']} | {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")
    print(f"  New: {cand[cid][0]} ({len(cand[cid][1])} steps)")
    for s in cand[cid][1]:
        print(f"    {s['phase']} | {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")
