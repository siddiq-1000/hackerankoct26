import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import random

def parse_iso(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

# Load datasets
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_reqs = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    full_reqs = {r['case_id']: r for r in csv.DictReader(f)}

with open('output.csv', 'r', encoding='utf-8') as f:
    full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    users_by_email = {r['email']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

# D1.4 Reconcile the analytics records count across all evidence files
print("=== D1.4 RECONCILIATION OF ANALYTICS RECORDS BY EVIDENCE FILE ===")
file_analytics_counts = defaultdict(lambda: {'total': 0, 'anonymized': 0, 'exposed_pii': 0})

for fid, ef in ev_files.items():
    p = Path('dataset') / ef['file_path']
    if not p.exists():
        continue
    if p.suffix == '.json':
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            def count_json(o):
                if isinstance(o, dict):
                    rid = o.get('resource_id')
                    if rid and 'analytics_' in rid:
                        file_analytics_counts[fid]['total'] += 1
                        has_pii = bool(o.get('email') or o.get('phone') or o.get('user_id'))
                        if has_pii:
                            file_analytics_counts[fid]['exposed_pii'] += 1
                        else:
                            file_analytics_counts[fid]['anonymized'] += 1
                    for v in o.values():
                        count_json(v)
                elif isinstance(o, list):
                    for it in o:
                        count_json(it)
            count_json(data)
        except Exception:
            pass
    elif p.suffix == '.sql':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                if 'customer_analytics_profiles' in line and 'analytics_' in line:
                    file_analytics_counts[fid]['total'] += 1
                    if 'NULL, NULL, NULL' in line:
                        file_analytics_counts[fid]['anonymized'] += 1
                    else:
                        file_analytics_counts[fid]['exposed_pii'] += 1
        except Exception:
            pass
    elif p.suffix == '.log':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                if 'analytics_' in line and ('analytics_profile_read_completed' in line or 'analytics_identity_scan' in line):
                    file_analytics_counts[fid]['total'] += 1
                    if 'email=' in line and 'email=null' in line:
                        file_analytics_counts[fid]['anonymized'] += 1
                    else:
                        file_analytics_counts[fid]['exposed_pii'] += 1
        except Exception:
            pass

tot_all = sum(v['total'] for v in file_analytics_counts.values())
tot_anon = sum(v['anonymized'] for v in file_analytics_counts.values())
tot_pii = sum(v['exposed_pii'] for v in file_analytics_counts.values())

print(f"| File ID | File Path | Total Records | Anonymized (Null PII) | Exposed PII |")
print(f"|---|---|---|---|---|")
for fid, counts in sorted(file_analytics_counts.items()):
    if counts['total'] > 0:
        ef = ev_files[fid]
        print(f"| `{fid}` | `{ef['file_path']}` | {counts['total']} | {counts['anonymized']} | {counts['exposed_pii']} |")
print(f"| **TOTAL** | | **{tot_all}** | **{tot_anon}** | **{tot_pii}** |")

# Explain:
# Total analytics record occurrences across all evidence files = 180 (or exact sum).
# Of these, exact count of anonymized records = tot_anon.
# Count of exposed PII records = tot_pii.
# And earlier "38 cases" was the count of full-run cases whose primary account lookup trace occurred in evidence files containing anonymized analytics batches.
