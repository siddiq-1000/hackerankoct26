import csv
import json
import re

files = [
    'dataset/evidence/databases/customer_data_read_replica_20260613.sql',
    'dataset/evidence/records/customer_export_manifest_20260409.json',
    'dataset/evidence/records/customer_data_snapshot_bundle_20260322.json',
    'dataset/evidence/databases/customer_data_reporting_replica_20260305.sql',
    'dataset/evidence/records/customer_data_snapshot_bundle_20260223.json',
    'dataset/evidence/databases/customer_data_reporting_replica_20260208.sql'
]

# Map user_id to case_id
user_to_case = {}
with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    uid_email = {r['user_id']: r['email'] for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    email_case = {r['email']: (r['case_id'], r['audit_at']) for r in csv.DictReader(f)}

for uid, em in uid_email.items():
    if em in email_case:
        user_to_case[uid] = email_case[em]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
        for m in re.finditer(r'\{[^{}]*"legal_hold_[^}]*\}', c):
            try:
                data = json.loads(m.group(0))
                sub = data.get('subject_reference')
                rid = data.get('resource_id')
                cid, a_at = user_to_case.get(sub, ('UNKNOWN', 'UNKNOWN'))
                print(f"{rid} -> subject={sub} -> case={cid} (audit_at={a_at}) in {fpath.split('/')[-1]}")
            except:
                pass
