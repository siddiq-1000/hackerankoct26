import csv
import json

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

# Let's inspect all activities on 2026-08-30 between 10:00 and 12:00
print("=== ACTIVITIES ON 2026-08-30 10:40 to 11:50 ===")
for a in acts:
    if '2026-08-30T10:4' in a['event_time'] or '2026-08-30T10:5' in a['event_time'] or '2026-08-30T11:' in a['event_time']:
        print(f"{a['activity_id']} | {a['event_time']} | {a['target_system']:20s} | {a['event_type']:18s} | {a['resource_id']:15s} | {a['details']}")

print("\n=== CASE_27 STEPS ===")
for s in sample_out['case_27'][1]:
    print(' ', s['system_id'], s['resource_id'], s['operation'])

print("\n=== CASE_28 STEPS ===")
for s in sample_out['case_28'][1]:
    print(' ', s['system_id'], s['resource_id'], s['operation'])
