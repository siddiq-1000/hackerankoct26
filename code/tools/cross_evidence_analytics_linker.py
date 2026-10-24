import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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
    users_by_email = {r['email']: r for r in csv.DictReader(f)}
    users_by_uid = {r['user_id']: r for r in csv.DictReader(f)}

# Find all 144 anonymized analytics resource_ids from system_activity.csv ANONYMIZE_RECORD
anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
all_anon_rids = sorted(list(set(a['resource_id'] for a in anon_events)))
print(f"Total distinct anonymized analytics resource_ids in system_activity.csv: {len(all_anon_rids)}")

# Cross-search ALL evidence for appearances of these 144 resource_ids
# We want to check if ANY evidence file (earlier snapshot, export, log, PDF, transcript)
# associates this resource_id with an email, phone, user_id, or customer_reference.
rid_to_pii_links = defaultdict(list)

# 1. Search JSON files
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
                        phone = o.get('phone')
                        cust_ref = o.get('customer_reference') or o.get('customer_id') or o.get('subject_id')
                        if email or uid or phone or cust_ref:
                            rid_to_pii_links[rid].append({
                                'file_id': fid,
                                'file_path': ef['file_path'],
                                'captured_at': ef['captured_at'],
                                'email': email,
                                'user_id': uid,
                                'phone': phone,
                                'cust_ref': cust_ref
                            })
                    for v in o.values():
                        search_json(v)
                elif isinstance(o, list):
                    for it in o:
                        search_json(it)
            search_json(data)
        except Exception:
            pass

    # 2. Search SQL files
    elif p.suffix == '.sql':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                for rid in all_anon_rids:
                    if rid in line:
                        # Check if line has email or customer reference
                        # Format in customer_analytics_profiles: (resource_id, customer_reference, email, phone, ...)
                        m = re.findall(r"'([^']+)'", line)
                        # Find strings in insert line
                        if len(m) >= 4:
                            # if rid is among strings
                            if rid in m:
                                idx = m.index(rid)
                                # check subsequent fields
                                for item in m:
                                    if item != rid and ('@' in item or item.startswith('user_') or item.startswith('cust_')):
                                        rid_to_pii_links[rid].append({
                                            'file_id': fid,
                                            'file_path': ef['file_path'],
                                            'captured_at': ef['captured_at'],
                                            'val': item
                                        })
        except Exception:
            pass

    # 3. Search Log files
    elif p.suffix == '.log':
        try:
            for line in open(p, 'r', encoding='utf-8', errors='ignore'):
                for rid in all_anon_rids:
                    if rid in line:
                        # Check if line has email or user_id
                        email_m = re.search(r'email="?([^\s,"]+@[^\s,"]+)"?', line)
                        user_m = re.search(r'user_id="?(user_\d+)"?', line)
                        matched_m = re.search(r'matched_value="?([^\s,"]+)"?', line)
                        if email_m or user_m or matched_m:
                            rid_to_pii_links[rid].append({
                                'file_id': fid,
                                'file_path': ef['file_path'],
                                'captured_at': ef['captured_at'],
                                'email': email_m.group(1) if email_m else None,
                                'user_id': user_m.group(1) if user_m else None,
                                'matched': matched_m.group(1) if matched_m else None
                            })
        except Exception:
            pass

# 4. Search system_activity.csv
for a in activity:
    for rid in all_anon_rids:
        if rid in a['resource_id'] or rid in a['details']:
            # check if activity details or target has email or user_id
            m_email = re.search(r'([^\s,]+@[^\s,]+)', a['details'])
            m_user = re.search(r'(user_\d+)', a['details'])
            m_acc = re.search(r'(account_\d+)', a['details'])
            if m_email or m_user or m_acc:
                rid_to_pii_links[rid].append({
                    'system_activity': a['activity_id'],
                    'event_time': a['event_time'],
                    'email': m_email.group(1) if m_email else None,
                    'user_id': m_user.group(1) if m_user else None,
                    'acc': m_acc.group(1) if m_acc else None
                })

print(f"\nResults of cross-evidence search:")
print(f"Total anonymized rids searched: {len(all_anon_rids)}")
print(f"RIDs with deterministic cross-evidence PII links found: {len(rid_to_pii_links)}")

for rid, links in sorted(rid_to_pii_links.items()):
    print(f"\nRID: {rid} has {len(links)} cross-evidence link(s):")
    for l in links[:3]:
        print(f"  {l}")
