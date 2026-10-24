import sys
sys.path.insert(0, '.')
import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

with open('output.csv', 'r', encoding='utf-8') as f:
    full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    full_reqs = list(csv.DictReader(f))

# Direct inline extraction of rid_to_user
ev_files = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', 'r', encoding='utf-8'))}
activity = list(csv.DictReader(open('dataset/system_activity.csv', 'r', encoding='utf-8')))
anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
all_anon_rids = set(a['resource_id'] for a in anon_events)

rid_to_user = {}
for fid, ef in ev_files.items():
    p = Path('dataset') / ef['file_path']
    if not p.exists(): continue
    if p.suffix == '.json':
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            def s_json(o):
                if isinstance(o, dict):
                    rid = o.get('resource_id')
                    if rid in all_anon_rids:
                        email = o.get('email')
                        uid = o.get('user_id')
                        if email or uid:
                            rid_to_user[rid] = (email, uid, fid)
                    for v in o.values(): s_json(v)
                elif isinstance(o, list):
                    for it in o: s_json(it)
            s_json(data)
        except Exception: pass
    elif p.suffix == '.sql':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                for rid in all_anon_rids:
                    if rid in line:
                        m_email = re.search(r"'([^\s,']+@[^\s,']+)'", line)
                        m_user = re.search(r"'(user_\d+)'", line)
                        if m_email or m_user:
                            rid_to_user[rid] = (m_email.group(1) if m_email else None, m_user.group(1) if m_user else None, fid)
        except Exception: pass

print(f"Total direct PII RIDs: {len(rid_to_user)}")
cids_matched = []
for r in full_reqs:
    cid = r['case_id']
    st = full_out[cid][0]
    em = r['email'].lower()
    for rid, (re_em, re_uid, fid) in rid_to_user.items():
        if (re_em and re_em.lower() == em):
            cids_matched.append((cid, st, rid, re_em, fid))

print(f"Matched full cases: {len(cids_matched)}")
for c in cids_matched[:15]:
    print(' ', c)
