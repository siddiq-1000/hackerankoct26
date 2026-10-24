import json

with open('dataset/evidence/records/customer_data_snapshot_bundle_20260915.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print("Top-level keys in evidence_51:", list(d.keys()))
for k, v in d.items():
    if isinstance(v, dict):
        print(f"  {k} keys:", list(v.keys()))
    elif isinstance(v, list):
        print(f"  {k} list length:", len(v))
