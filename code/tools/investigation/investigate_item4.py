import sys
sys.path.insert(0, '.')
import csv
import json
import re

flips = ['case_416', 'case_417', 'case_420', 'case_517']

requests = {}
with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in flips:
            requests[r['case_id']] = r

manifest = {}
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        manifest[r['file_id']] = r

identities = {}
with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        identities[r['email']] = r

audit_logs = []
with open('dataset/user_audit_log.csv', 'r', encoding='utf-8') as f:
    audit_logs = list(csv.DictReader(f))

# Also read current output.csv
curr_outs = {}
with open('output.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in flips:
            curr_outs[r['case_id']] = (r['deletion_status'], json.loads(r['steps_json']))

import subprocess
p = subprocess.run(['git', 'show', '5af6321:output.csv'], capture_output=True, text=True)
base_outs = {}
for r in csv.DictReader(p.stdout.splitlines()):
    if r['case_id'] in flips:
        base_outs[r['case_id']] = (r['deletion_status'], json.loads(r['steps_json']))

print("=== 4 STATUS FLIP TIMELINES AND EVIDENCE ===")
for cid in flips:
    req = requests[cid]
    audit_at = req['audit_at']
    email = req['email']
    user = identities.get(email, {})
    uid = user.get('user_id', '')
    
    # Check historical identifiers
    hist_emails = [email]
    hist_uids = [uid] if uid else []
    for al in audit_logs:
        if al['user_id'] == uid or al['old_value'] == email or al['new_value'] == email:
            if al['field_name'] == 'email':
                if al['old_value'] and al['old_value'] not in hist_emails: hist_emails.append(al['old_value'])
                if al['new_value'] and al['new_value'] not in hist_emails: hist_emails.append(al['new_value'])
            if al['user_id'] and al['user_id'] not in hist_uids: hist_uids.append(al['user_id'])
            
    print(f"\n============================================================")
    print(f"CASE: {cid} | Email: {email} | User ID: {uid} | audit_at: {audit_at}")
    print(f"All emails: {hist_emails} | All user_ids: {hist_uids}")
    print(f"Baseline: {base_outs[cid][0]} ({len(base_outs[cid][1])} steps)")
    for s in base_outs[cid][1]:
        print(f"  BASE: {s['phase']} | {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")
    print(f"Candidate: {curr_outs[cid][0]} ({len(curr_outs[cid][1])} steps)")
    for s in curr_outs[cid][1]:
        print(f"  CAND: {s['phase']} | {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")

    # Let's inspect all evidence files mentioning any of the emails or user_ids or findings
    print("\n  Evidence mentions (captured_at <= audit_at?):")
    # Search in syslog or other evidence files
    for fid, finfo in manifest.items():
        fpath = "dataset/" + finfo['file_path']
        captured_at = finfo['captured_at']
        if any(fpath.endswith(ext) for ext in ['.log', '.json', '.txt', '.sql']):
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as ef:
                    content = ef.read()
                    matched_items = []
                    for em in hist_emails:
                        if em in content: matched_items.append(em)
                    for u in hist_uids:
                        if re.search(rf"\b{u}\b", content): matched_items.append(u)
                    
                    for s in curr_outs[cid][1]:
                        rid = s['resource_id']
                        if re.search(rf"\b{rid}\b", content):
                            matched_items.append(rid)
                            
                    if matched_items:
                        is_le = (captured_at <= audit_at)
                        print(f"    [{fid}] captured_at={captured_at} (<= audit_at: {is_le}) {finfo['file_path']}")
                        print(f"      Matched tokens: {set(matched_items)}")
                        count = 0
                        for line in content.splitlines():
                            if any(m in line for m in matched_items):
                                if count < 5:
                                    print(f"        LINE: {line.strip()[:140]}")
                                    count += 1
            except Exception as e:
                pass
