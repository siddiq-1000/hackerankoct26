import csv
import json

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_cases = list(csv.DictReader(f))

# Let's see all unique combinations of (system_id, operation, state, resource_id prefix) in sample_output.csv
combos = set()
for sc in sample_cases:
    for s in json.loads(sc['steps_json']):
        rid_prefix = s['resource_id'].split('_')[0] if '_' in s['resource_id'] else s['resource_id']
        combos.add((s['system_id'], rid_prefix, s['operation'], s['state']))

for c in sorted(combos):
    print(c)
