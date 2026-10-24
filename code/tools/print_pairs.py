import csv, json

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

cases = ['case_21', 'case_25', 'case_26', 'case_27', 'case_28']
for cid in cases:
    steps = sample_out[cid]
    acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service'][0]
    ana = [s['resource_id'] for s in steps if s['system_id'] == 'analytics_platform'][0]
    print(f"{cid}: account={acc} -> analytics={ana}")
