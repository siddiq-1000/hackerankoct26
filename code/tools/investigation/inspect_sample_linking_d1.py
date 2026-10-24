import csv
import json
from pathlib import Path

# Load data
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_reqs = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    users = {r['email']: r for r in csv.DictReader(f)}
    user_by_id = {r['user_id']: r for r in users.values()}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

sample_complete_cids = ['case_03', 'case_04', 'case_21', 'case_25', 'case_26', 'case_27', 'case_28']

print("=" * 80)
print("D1.1: SYSTEM_ACTIVITY & EVIDENCE INSPECTION FOR 7 SAMPLE COMPLETE CASES")
print("=" * 80)

for cid in sample_complete_cids:
    req = sample_reqs[cid]
    u = users.get(req['email'])
    uid = u['user_id'] if u else 'unknown'
    uname = u['name'] if u else 'unknown'
    st, steps = sample_out[cid]

    acc_step = [s for s in steps if s['system_id'] == 'account_service'][0]
    ana_step = [s for s in steps if s['system_id'] == 'analytics_platform'][0]

    acc_res = acc_step['resource_id']
    ana_res = ana_step['resource_id']
    ana_evid = ana_step['evidence_id']

    print(f"\n------------------------------------------------------------")
    print(f"CASE: {cid} | User: {uid} ({uname}) | Email: {req['email']}")
    print(f"Requested: {req['requested_at']} | Reported: {req['reported_at']} | Audit: {req['audit_at']}")
    print(f"Target Account: {acc_res} (ev: {acc_step['evidence_id']})")
    print(f"Target Analytics: {ana_res} (ev: {ana_evid})")

    # Find account deletion event in system_activity
    acc_acts = [a for a in activity if a['resource_id'] == acc_res or acc_res in a['details']]
    print(f"Account Activity Events ({len(acc_acts)}):")
    for a in acc_acts:
        print(f"  act_id={a['activity_id']} time={a['event_time']} src={a['source_system']} tgt={a['target_system']} type={a['event_type']} res={a['resource_id']} reslt={a['reported_result']} details='{a['details']}'")

    # Find analytics anonymize event in system_activity
    ana_acts = [a for a in activity if a['resource_id'] == ana_res or ana_res in a['details']]
    print(f"Analytics Activity Events ({len(ana_acts)}):")
    for a in ana_acts:
        print(f"  act_id={a['activity_id']} time={a['event_time']} src={a['source_system']} tgt={a['target_system']} type={a['event_type']} res={a['resource_id']} reslt={a['reported_result']} details='{a['details']}'")

    # Find the evidence content in cited file
    ef = ev_files.get(ana_evid)
    if ef:
        ef_path = Path('dataset') / ef['file_path']
        print(f"Evidence File: {ana_evid} ({ef['file_path']}, origin={ef['origin']}, captured={ef['captured_at']})")
        # Find lines mentioning ana_res
        if ef_path.exists():
            text = ef_path.read_text(encoding='utf-8', errors='ignore')
            lines = [l.strip() for l in text.splitlines() if ana_res in l]
            for l in lines[:3]:
                print(f"  Evidence line: {l[:150]}")
