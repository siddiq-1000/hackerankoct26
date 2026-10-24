import csv
import json

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_cases = list(csv.DictReader(f))

for sc in sample_cases:
    steps = json.loads(sc['steps_json'])
    if steps:
        print(f"\nCase {sc['case_id']} ({sc['deletion_status']}):")
        for s in steps:
            print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']}")
