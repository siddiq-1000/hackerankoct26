import csv
import json

sample_out = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))
sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
req_map = {r['case_id']: r for r in sample_reqs}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

for so in sample_out:
    cid = so['case_id']
    steps = json.loads(so['steps_json'])
    anon_steps = [s for s in steps if s.get('operation') == 'VERIFY_RECORD_ANONYMIZED']
    if anon_steps:
        req = req_map[cid]
        target_res = anon_steps[0]['resource_id']
        ev_id = anon_steps[0]['evidence_id']
        print(f"=== {cid} (req={req['requested_at']}, rep={req['reported_at']}): target={target_res} in {ev_id} ===")
        matching_acts = [a for a in activities if a['resource_id'] == target_res]
        for ma in matching_acts:
            print(f"   Act {ma['activity_id']} at {ma['event_time']}: {ma['event_type']} {ma['source_system']}->{ma['target_system']} {ma['details']}")
