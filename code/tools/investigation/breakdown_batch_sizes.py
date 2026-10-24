import sys
sys.path.insert(0, '.')
import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open('output.csv', 'r', encoding='utf-8') as f:
    full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    full_reqs = list(csv.DictReader(f))

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
anon_events.sort(key=lambda x: x['event_time'])

# Index anonymized evidence
from code.analytics_linker import AnalyticsLinker
from pathlib import Path
linker = AnalyticsLinker(Path('dataset'))

complete_cases = [r for r in full_reqs if full_out[r['case_id']][0] == 'COMPLETE']

# Group by reported_at rounded to hour
batches = defaultdict(list)
for r in complete_cases:
    rep_dt = parse_iso(r['reported_at'])
    if rep_dt:
        key = rep_dt.strftime('%Y-%m-%d %H')
        batches[key].append(r)

singleton_pairs = {}
multicase_pairs = {}
ambiguous_batches = 0
ambiguous_cases = 0

for bkey, b_reqs in batches.items():
    b_rep_dts = [parse_iso(r['reported_at']) for r in b_reqs]
    min_dt = min(b_rep_dts) - timedelta(minutes=60)
    max_dt = max(b_rep_dts) + timedelta(minutes=5)
    b_events = [a for a in anon_events if min_dt <= parse_iso(a['event_time']) <= max_dt]

    if len(b_reqs) == len(b_events):
        if len(b_reqs) == 1:
            # Singleton batch!
            r = b_reqs[0]
            ev = b_events[0]
            aud_dt = parse_iso(r['audit_at'])
            rid = ev['resource_id']
            cands = [(fid, cap) for fid, cap in linker.anon_evidence[rid] if cap <= aud_dt]
            if cands:
                cands.sort(key=lambda x: x[1], reverse=True)
                singleton_pairs[r['case_id']] = (rid, cands[0][0])
        else:
            # Multi-case batch!
            b_reqs.sort(key=lambda r: linker.users_by_email.get(r['email'], {}).get('user_id', r['case_id']))
            b_events.sort(key=lambda a: a['resource_id'])
            for r, ev in zip(b_reqs, b_events):
                aud_dt = parse_iso(r['audit_at'])
                rid = ev['resource_id']
                cands = [(fid, cap) for fid, cap in linker.anon_evidence[rid] if cap <= aud_dt]
                if cands:
                    cands.sort(key=lambda x: x[1], reverse=True)
                    multicase_pairs[r['case_id']] = (rid, cands[0][0])
    else:
        ambiguous_batches += 1
        ambiguous_cases += len(b_reqs)

print("=== BATCH BREAKDOWN (200 COMPLETE CASES) ===")
print(f"Total COMPLETE cases: {len(complete_cases)}")
print(f"Total batches: {len(batches)}")
print(f"Singleton batches (1 request, 1 event) with valid evidence: {len(singleton_pairs)} cases")
print(f"Multi-case batches (size >= 2, N_req == N_ev) with valid evidence: {len(multicase_pairs)} cases")
print(f"Total currently paired: {len(singleton_pairs) + len(multicase_pairs)} cases")
print(f"Ambiguous batches (N_req != N_ev): {ambiguous_batches} batches covering {ambiguous_cases} cases")

# Check sample performance under singleton-only + deterministic cross-evidence
sample_complete_cids = ['case_01', 'case_02', 'case_03', 'case_04', 'case_21', 'case_25', 'case_26', 'case_27', 'case_28', 'case_31']
print("\n=== SAMPLE PERFORMANCE (SINGLETON-ONLY + DETERMINISTIC) ===")
for cid in sample_complete_cids:
    in_singleton = cid in singleton_pairs
    in_multi = cid in multicase_pairs
    print(f"  {cid}: singleton={in_singleton}, multi={in_multi}")
