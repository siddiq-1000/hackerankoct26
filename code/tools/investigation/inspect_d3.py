import csv
import json
from pathlib import Path

# Load output.csv
with open('output.csv', 'r', encoding='utf-8') as f:
    outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    requests = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

# The 13 probe lines identified in complete_rate_investigation.md
# 1-2 in evidence_88:
# 3-7 in evidence_39:
# 8-13 in evidence_48:

print("=" * 80)
print("D3: MATCHING COMPLETION / OUTCOME LINES FOR THE 13 PROBE LOG ENTRIES")
print("=" * 80)

# 1. evidence_88
e88_lines = open('dataset/evidence/logs/resource_lookup_trace_20260822_103910.log', 'r', encoding='utf-8', errors='ignore').readlines()
# 2. evidence_39
e39_lines = open('dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', 'r', encoding='utf-8', errors='ignore').readlines()
# 3. evidence_48
e48_lines = open('dataset/evidence/logs/operations_stream_me_central_20260203.log', 'r', encoding='utf-8', errors='ignore').readlines()

def search_matching(lines, search_key, fname):
    print(f"\n--- Searching in {fname} for '{search_key}' ---")
    hits = [l.strip() for l in lines if search_key.lower() in l.lower()]
    for h in hits:
        print("  ", h)
    if not hits:
        print("   [NONE FOUND]")

# Case 121 (nicolas.n7090@zoho.com) on evidence_88
search_matching(e88_lines, 'nicolas.n7090@zoho.com', 'evidence_88')
# Case 416 (keiko.sato@outlook.com) on evidence_39
search_matching(e39_lines, 'keiko.sato@outlook.com', 'evidence_39')
# Case 417 (s.kim14@yahoo.com) on evidence_39
search_matching(e39_lines, 's.kim14@yahoo.com', 'evidence_39')
# Case 517 (yetunde.a3014@zoho.com) on evidence_48
search_matching(e48_lines, 'yetunde.a3014@zoho.com', 'evidence_48')
# Case 519 (s.dlamini52@gmail.com) on evidence_48
search_matching(e48_lines, 's.dlamini52@gmail.com', 'evidence_48')
# Case 521 (yuna-lee@gmail.com) on evidence_48
search_matching(e48_lines, 'yuna-lee@gmail.com', 'evidence_48')

print("\n" + "=" * 80)
print("OUTPUT.CSV STEPS FOR THE CASES INVOLVED")
print("=" * 80)
target_cases = ['case_83', 'case_121', 'case_416', 'case_417', 'case_517', 'case_519', 'case_521']
for cid in target_cases:
    if cid in outputs:
        st, steps = outputs[cid]
        req = requests.get(cid, {})
        print(f"\n{cid} ({st}) | Email: {req.get('email')} | Audit: {req.get('audit_at')}")
        for s in steps:
            print(f"  Step {s['step_no']}: {s['system_id']:20s} | {s['resource_id']:15s} | {s['operation']:25s} | {s['state']:10s} | ev={s['evidence_id']}")
