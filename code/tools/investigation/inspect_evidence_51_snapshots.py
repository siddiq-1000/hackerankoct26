import json

with open('dataset/evidence/records/customer_data_snapshot_bundle_20260915.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

for idx, s in enumerate(d.get('snapshots', [])):
    print(f"Snapshot {idx}: data_store={s.get('data_store')}, collection={s.get('collection')}, records_len={len(s.get('records', []))}")
    for r in s.get('records', [])[:2]:
        print("  sample record:", r)
