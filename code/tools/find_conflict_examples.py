import csv
import json

# Load data
with open('output.csv', 'r', encoding='utf-8') as f:
    outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    requests = {r['case_id']: r for r in csv.DictReader(f)}

# 1. reported_status vs evidence (reported COMPLETE, but true output is INCOMPLETE)
rep_complete_but_inc = []
for cid, r in requests.items():
    if r['reported_status'] == 'COMPLETE' and outputs[cid][0] == 'INCOMPLETE':
        st, steps = outputs[cid]
        evids = [s['evidence_id'] for s in steps if s['phase'] == 'FINDING']
        rep_complete_but_inc.append((cid, r['email'], evids))

print("1. reported_status COMPLETE vs True INCOMPLETE:")
for c in rep_complete_but_inc[:3]:
    print(f"   Case: {c[0]} ({c[1]}) | Evidence: {c[2]}")

# 2. primary vs replica/failover
# Look for cases where failover or replica had remaining record
replica_cases = []
for cid, (st, steps) in outputs.items():
    for s in steps:
        if s['phase'] == 'FINDING' and s['system_id'] == 'account_service':
            replica_cases.append((cid, s['resource_id'], s['evidence_id']))

print("\n2. primary vs replica drift:")
for c in replica_cases[:3]:
    print(f"   Case: {c[0]} | Resource: {c[1]} | Evidence: {c[2]}")

# 3. current vs historical identity
with open('dataset/user_audit_log.csv', 'r', encoding='utf-8') as f:
    audit_log = list(csv.DictReader(f))

historical_cases = []
for a in audit_log:
    old_em = a.get('old_email')
    if old_em:
        for cid, r in requests.items():
            if r['email'].lower() == old_em.lower():
                historical_cases.append((cid, r['email'], a['new_email'], a['user_id']))

print("\n3. Current vs Historical Identity:")
for c in historical_cases[:3]:
    print(f"   Case: {c[0]} | Requested with historical email: {c[1]} | Current email: {c[2]} | User: {c[3]}")
