import csv
import json
from datetime import datetime, timedelta

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_reqs = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    users = {r['email']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

# Look at Batch 2026-08-30: case_27, case_28
# Look at Batch 2026-09-02: case_25, case_26
for batch_name, cids, t_start, t_end in [
    ("2026-08-30", ["case_27", "case_28"], "2026-08-30T10:00:00Z", "2026-08-30T12:00:00Z"),
    ("2026-09-02", ["case_25", "case_26"], "2026-09-02T10:00:00Z", "2026-09-02T12:00:00Z")
]:
    print(f"\n=== BATCH {batch_name} ({cids}) ===")
    for cid in cids:
        r = sample_reqs[cid]
        u = users.get(r['email'], {})
        gt_ana = [s for s in sample_out[cid] if s['system_id'] == 'analytics_platform'][0]
        gt_acc = [s for s in sample_out[cid] if s['system_id'] == 'account_service'][0]
        acc_acts = [a for a in activity if a['resource_id'] == gt_acc['resource_id']]
        ana_acts = [a for a in activity if a['resource_id'] == gt_ana['resource_id']]
        print(f"Case {cid}: user_id={u.get('user_id')}, email={r['email']}")
        print(f"  Account {gt_acc['resource_id']}: act_time={[a['event_time'] for a in acc_acts]}")
        print(f"  Analytics {gt_ana['resource_id']}: act_time={[a['event_time'] for a in ana_acts]}")

    # Let's inspect all ANONYMIZE_RECORD events in this window
    evs = [a for a in activity if a['target_system'] == 'analytics_platform' and a['event_type'] == 'ANONYMIZE_RECORD' and t_start <= a['event_time'] <= t_end]
    print(f"ANONYMIZE_RECORD events in window:")
    for e in evs:
        print(f"  {e['activity_id']} | {e['event_time']} | {e['resource_id']}")
