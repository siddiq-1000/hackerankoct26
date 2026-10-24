import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

def parse_iso(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

# Load datasets
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    users_list = list(csv.DictReader(f))
    users_by_email = {r['email']: r for r in users_list}
    users_by_uid = {r['user_id']: r for r in users_list}

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_reqs = list(csv.DictReader(f))

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    full_reqs = list(csv.DictReader(f))

with open('output.csv', 'r', encoding='utf-8') as f:
    full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

# All ANONYMIZE_RECORD events
anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
all_anon_rids = set(a['resource_id'] for a in anon_events)

# Index evidence where analytics records appear and have PII
rid_to_user = {}

for fid, ef in ev_files.items():
    p = Path('dataset') / ef['file_path']
    if not p.exists():
        continue
    if p.suffix == '.json':
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            def search_json(o):
                if isinstance(o, dict):
                    rid = o.get('resource_id')
                    if rid in all_anon_rids:
                        email = o.get('email')
                        uid = o.get('user_id')
                        if email or uid:
                            rid_to_user[rid] = (email, uid, fid)
                    for v in o.values():
                        search_json(v)
                elif isinstance(o, list):
                    for it in o:
                        search_json(it)
            search_json(data)
        except Exception:
            pass
    elif p.suffix == '.sql':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                for rid in all_anon_rids:
                    if rid in line:
                        m_email = re.search(r"'([^\s,']+@[^\s,']+)'", line)
                        m_user = re.search(r"'(user_\d+)'", line)
                        if m_email or m_user:
                            rid_to_user[rid] = (m_email.group(1) if m_email else None, m_user.group(1) if m_user else None, fid)
        except Exception:
            pass
    elif p.suffix == '.log':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                for rid in all_anon_rids:
                    if rid in line:
                        m_email = re.search(r'email="?([^\s,"]+@[^\s,"]+)"?', line)
                        m_user = re.search(r'user_id="?(user_\d+)"?', line)
                        if m_email or m_user:
                            rid_to_user[rid] = (m_email.group(1) if m_email else None, m_user.group(1) if m_user else None, fid)
        except Exception:
            pass

print(f"Total distinct RIDs with direct PII mappings from evidence: {len(rid_to_user)}")

# Index anonymized evidence files for each RID
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
                    m = re.search(r'(analytics_\d+)', l)
                    if m:
                        anon_evidence[m.group(1)].append((fid, cap))
        except Exception:
            pass
    elif p.suffix == '.sql':
        try:
            for l in open(p, 'r', encoding='utf-8', errors='ignore'):
                if 'customer_analytics_profiles' in l and 'NULL, NULL, NULL' in l:
                    m = re.search(r"'(analytics_\d+)'", l)
                    if m:
                        anon_evidence[m.group(1)].append((fid, cap))
        except Exception:
            pass

# Test deterministic link on sample cases
print("\n=== SAMPLE EVALUATION WITH DETERMINISTIC CROSS-EVIDENCE + BATCH LINK ===")
# Build email/user_id to RID index from rid_to_user
user_to_rid = {}
for rid, (em, uid, fid) in rid_to_user.items():
    if em:
        user_to_rid[em.lower()] = rid
    if uid:
        user_to_rid[uid] = rid

# Check 32 sample cases
sample_complete_cids = [r['case_id'] for r in sample_reqs if sample_out[r['case_id']][0] == 'COMPLETE']
sample_det_links = {}
for r in sample_reqs:
    cid = r['case_id']
    if cid not in sample_complete_cids:
        continue
    email = r['email'].lower()
    u = users_by_email.get(r['email'], {})
    uid = u.get('user_id')
    rid = user_to_rid.get(email) or (user_to_rid.get(uid) if uid else None)
    if rid:
        # Check if anonymized evidence exists <= audit_at
        aud_dt = parse_iso(r['audit_at'])
        cands = [(fid, cap) for fid, cap in anon_evidence[rid] if cap <= aud_dt]
        if cands:
            cands.sort(key=lambda x: x[1], reverse=True)
            sample_det_links[cid] = (rid, cands[0][0])

print(f"Sample COMPLETE cases deterministically linked via cross-evidence: {len(sample_det_links)}")
for cid, (rid, fid) in sorted(sample_det_links.items()):
    gt_step = [s for s in sample_out[cid][1] if s['system_id'] == 'analytics_platform']
    print(f"  {cid}: det_linked=({rid}, {fid}) | gt={[(s['resource_id'], s['evidence_id']) for s in gt_step]}")
