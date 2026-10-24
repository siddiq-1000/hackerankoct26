import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def parse_iso(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open('output.csv', 'r', encoding='utf-8') as f:
    full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    full_reqs = list(csv.DictReader(f))

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    users_by_email = {r['email']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
anon_events.sort(key=lambda x: x['event_time'])

# Index anonymized evidence records
anon_evidence = defaultdict(list)
for fid, ef in ev_files.items():
    p = Path('dataset') / ef['file_path']
    if not p.exists():
        continue
    cap = parse_iso(ef['captured_at'])
    if p.suffix == '.json':
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            def extract(o):
                if isinstance(o, dict):
                    rid = o.get('resource_id')
                    if rid and 'analytics_' in rid:
                        if not (o.get('email') or o.get('phone') or o.get('user_id')):
                            anon_evidence[rid].append((fid, cap))
                    for v in o.values():
                        extract(v)
                elif isinstance(o, list):
                    for it in o:
                        extract(it)
            extract(data)
        except Exception:
            pass
    elif p.suffix == '.log':
        try:
            for l in open(p, 'r', encoding='utf-8', errors='ignore'):
                if 'analytics_' in l and 'email=null' in l:
                    import re
                    m = re.search(r'(analytics_\d+)', l)
                    if m:
                        anon_evidence[m.group(1)].append((fid, cap))
        except Exception:
            pass
    elif p.suffix == '.sql':
        try:
            for l in open(p, 'r', encoding='utf-8', errors='ignore'):
                if 'customer_analytics_profiles' in l and 'NULL, NULL, NULL' in l:
                    import re
                    m = re.search(r"'(analytics_\d+)'", l)
                    if m:
                        anon_evidence[m.group(1)].append((fid, cap))
        except Exception:
            pass

# Group COMPLETE cases by reported_at rounded to 1 hour
complete_cases = [r for r in full_reqs if full_out[r['case_id']][0] == 'COMPLETE']
batches = defaultdict(list)

for r in complete_cases:
    rep_dt = parse_iso(r['reported_at'])
    if rep_dt:
        key = rep_dt.strftime('%Y-%m-%d %H')
        batches[key].append(r)

batch_paired = {}
ambiguous_batches = 0
unpaired_cases = 0

for bkey, b_reqs in batches.items():
    b_rep_dts = [parse_iso(r['reported_at']) for r in b_reqs]
    min_dt = min(b_rep_dts) - timedelta(minutes=60)
    max_dt = max(b_rep_dts) + timedelta(minutes=5)

    b_events = [a for a in anon_events if min_dt <= parse_iso(a['event_time']) <= max_dt]

    if len(b_reqs) == len(b_events):
        # Perfect 1-to-1 batch!
        # Sort reqs by user_id
        b_reqs.sort(key=lambda r: users_by_email.get(r['email'], {}).get('user_id', r['case_id']))
        # Sort events by resource_id
        b_events.sort(key=lambda a: a['resource_id'])
        for r, ev in zip(b_reqs, b_events):
            aud_dt = parse_iso(r['audit_at'])
            rid = ev['resource_id']
            cands = [(fid, cap) for fid, cap in anon_evidence[rid] if cap <= aud_dt]
            if cands:
                cands.sort(key=lambda x: x[1], reverse=True)
                batch_paired[r['case_id']] = (rid, cands[0][0])
    else:
        ambiguous_batches += 1
        unpaired_cases += len(b_reqs)

print(f"Total COMPLETE cases: {len(complete_cases)}")
print(f"Cases in PERFECT 1-to-1 batches with valid evidence: {len(batch_paired)}")
print(f"Ambiguous batches where case count != event count: {ambiguous_batches} (covering {unpaired_cases} cases)")
