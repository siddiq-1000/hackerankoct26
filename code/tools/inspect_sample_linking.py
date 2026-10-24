import csv, json
from datetime import datetime

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

cases_7 = ['case_03', 'case_04', 'case_21', 'case_25', 'case_26', 'case_27', 'case_28']

for cid in cases_7:
    steps = sample_out[cid]
    acc_step = [s for s in steps if s['system_id']=='account_service'][0]
    ana_step = [s for s in steps if s['system_id']=='analytics_platform'][0]
    
    acc_rid = acc_step['resource_id']
    ana_rid = ana_step['resource_id']
    
    acc_acts = [a for a in acts if a['resource_id'] == acc_rid]
    ana_acts = [a for a in acts if a['resource_id'] == ana_rid]
    
    print(f'=== {cid} ===')
    print(f'Account {acc_rid}: {[a["activity_id"] + " " + a["event_time"] + " " + a["details"] for a in acc_acts]}')
    print(f'Analytics {ana_rid} ({ana_step["evidence_id"]}): {[a["activity_id"] + " " + a["event_time"] + " " + a["details"] for a in ana_acts]}')
    if acc_acts and ana_acts:
        t1 = datetime.fromisoformat(acc_acts[0]['event_time'].replace('Z', '+00:00'))
        t2 = datetime.fromisoformat(ana_acts[0]['event_time'].replace('Z', '+00:00'))
        delta = (t2 - t1).total_seconds()
        print(f'Delta: {delta:.0f}s ({delta/60:.1f}m)')
    else:
        print('Delta: N/A')
