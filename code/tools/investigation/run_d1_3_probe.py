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

# Group full-run cases by reported_at window (1 hour)
complete_cases = [r for r in full_reqs if full_out[r['case_id']][0] == 'COMPLETE']

# Map each event to cases whose [requested_at, reported_at] overlaps it
event_to_cases = defaultdict(list)
case_to_events = defaultdict(list)

for r in complete_cases:
    cid = r['case_id']
    req_dt = parse_iso(r['requested_at'])
    rep_dt = parse_iso(r['reported_at'])
    aud_dt = parse_iso(r['audit_at'])

    for a in anon_events:
        a_dt = parse_iso(a['event_time'])
        # Workflow window: 60 minutes before reported_at up to reported_at
        if rep_dt and (rep_dt - timedelta(minutes=60)) <= a_dt <= (rep_dt + timedelta(minutes=5)):
            if a_dt <= aud_dt:
                event_to_cases[a['activity_id']].append(cid)
                case_to_events[cid].append(a)

print("=== D1.3 PROBE ON FULL 518 CASES (READ-ONLY) ===")
print(f"Total COMPLETE cases: {len(complete_cases)}")

# Analyze ambiguity:
ambiguous_events = {aid: cids for aid, cids in event_to_cases.items() if len(cids) > 1}
unique_events = {aid: cids[0] for aid, cids in event_to_cases.items() if len(cids) == 1}
orphan_events = [a['activity_id'] for a in anon_events if a['activity_id'] not in event_to_cases]

print(f"Total ANONYMIZE_RECORD events in activity: {len(anon_events)}")
print(f"Events matching EXACTLY ONE COMPLETE case:  {len(unique_events)}")
print(f"Events matching MULTIPLE cases (AMBIGUOUS): {len(ambiguous_events)}")
print(f"Events matching ZERO cases (ORPHANS):       {len(orphan_events)}")

# How many COMPLETE cases would receive a step?
cases_with_unique = set(unique_events.values())
cases_with_any = set(c for cids in event_to_cases.values() for c in cids)

print(f"COMPLETE cases with unique link:            {len(cases_with_unique)}")
print(f"COMPLETE cases with any link (incl ambig): {len(cases_with_any)}")

# Check evidence presence for unique matches
valid_evidence_matches = []
for aid, cid in sorted(unique_events.items()):
    ev = next(a for a in anon_events if a['activity_id'] == aid)
    rid = ev['resource_id']
    req = full_reqs_dict = next(r for r in full_reqs if r['case_id'] == cid)
    aud_dt = parse_iso(req['audit_at'])
    ev_cands = [(fid, cap) for fid, cap in anon_evidence[rid] if cap <= aud_dt]
    if ev_cands:
        ev_cands.sort(key=lambda x: x[1], reverse=True)
        valid_evidence_matches.append((cid, aid, ev['event_time'], rid, ev_cands[0][0]))

print(f"Cases with unique activity link AND valid evidence before audit_at: {len(valid_evidence_matches)}")

# Print 10 examples
print("\n--- 10 EXAMPLES OF GROUNDED FULL-RUN LINKS ---")
random.seed(42)
sample_10 = random.sample(valid_evidence_matches, min(10, len(valid_evidence_matches)))
for cid, aid, ev_time, rid, fid in sample_10:
    req = next(r for r in full_reqs if r['case_id'] == cid)
    print(f"Case: {cid:8s} | Email: {req['email']:25s} | Activity: {aid} ({ev_time}) -> {rid} | Evidence: {fid}")
