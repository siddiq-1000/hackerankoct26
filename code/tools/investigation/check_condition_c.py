import csv
import json
import re
from datetime import datetime

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

manifest = {}
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        manifest[r['file_id']] = r

user_identities = {}
with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        user_identities[r['user_id']] = r

deletion_requests = {}
with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        deletion_requests[r['email'].lower()] = r

legal_files = [
    ('evidence_24', 'dataset/evidence/databases/customer_data_read_replica_20260613.sql'),
    ('evidence_36', 'dataset/evidence/records/customer_export_manifest_20260409.json'),
    ('evidence_40', 'dataset/evidence/records/customer_data_snapshot_bundle_20260322.json'),
    ('evidence_43', 'dataset/evidence/databases/customer_data_reporting_replica_20260305.sql'),
    ('evidence_45', 'dataset/evidence/records/customer_data_snapshot_bundle_20260223.json'),
    ('evidence_47', 'dataset/evidence/databases/customer_data_reporting_replica_20260208.sql')
]

found_holds = []
for fid, fpath in legal_files:
    finfo = manifest[fid]
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
        for m in re.finditer(r'\{[^{}]*"legal_hold_\d+"[^}]*\}', c):
            try:
                data = json.loads(m.group(0))
                rid = data.get('resource_id')
                sub = data.get('subject_reference')
                uinfo = user_identities.get(sub, {})
                em = uinfo.get('email', '').lower()
                req = deletion_requests.get(em, {})
                cid = req.get('case_id', 'NOT_IN_REQUESTS')
                audit_at = req.get('audit_at')
                found_holds.append({
                    'file_id': fid,
                    'file_captured_at': finfo['captured_at'],
                    'resource_id': rid,
                    'subject': sub,
                    'email': em,
                    'case_id': cid,
                    'audit_at': audit_at,
                    'data': data
                })
            except:
                pass

# De-duplicate by resource_id
unique_holds = {}
for h in found_holds:
    rid = h['resource_id']
    if rid not in unique_holds:
        unique_holds[rid] = h

# Also load current output.csv to see their current output rows
current_output = {}
with open('output.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        current_output[r['case_id']] = (r['deletion_status'], json.loads(r['steps_json']))

print("=== DETAILED ANALYSIS OF THE 6 LEGAL HOLDS ===")
for rid, h in sorted(unique_holds.items()):
    d = h['data']
    cid = h['case_id']
    print(f"\nResource: {rid} in [{h['file_id']}] (captured_at={h['file_captured_at']})")
    print(f"  Subject: {h['subject']} | Email: {h['email']} | Case: {cid}")
    print(f"  Audit at: {h['audit_at']}")
    print(f"  Order reference: {d.get('order_reference')}")
    print(f"  Retention reason: {d.get('retention_reason')}")
    print(f"  Retained until: {d.get('retained_until')}")
    
    if h['audit_at']:
        aud_dt = parse_iso(h['audit_at'])
        cap_dt = parse_iso(h['file_captured_at'])
        ret_until = parse_iso(d.get('retained_until'))
        is_le = cap_dt <= aud_dt
        is_active = (cap_dt <= aud_dt <= ret_until) if ret_until else is_le
        print(f"  Hold active at audit_at: {is_active} (cap_dt <= audit_at: {is_le}, ret_until: {d.get('retained_until')})")
        if cid in current_output:
            st, steps = current_output[cid]
            print(f"  Current output status: {st} ({len(steps)} steps)")
            for s in steps:
                print(f"    {s['phase']} | {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")
