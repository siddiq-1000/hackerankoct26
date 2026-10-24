import csv
import json
import re

print("=== PARSING ALL TOMBSTONE RECORDS ===")

# 1. In customer_data_failover_replica_20260920.sql
with open('dataset/evidence/databases/customer_data_failover_replica_20260920.sql', 'r', encoding='utf-8') as f:
    for line in f:
        if 'tombstone' in line and 'customer_data_failover_replica' in line:
            # Extract JSON string
            m = re.search(r"'(\{.*\})'", line)
            if m:
                data = json.loads(m.group(1))
                print(f"SQL Tombstone: {data.get('resource_id')} -> subject_reference={data.get('subject_reference')}, name={data.get('name')}, email={data.get('email')}, phone={data.get('phone')}")

# 2. In customer_data_snapshot_bundle_20260915.json
with open('dataset/evidence/records/customer_data_snapshot_bundle_20260915.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)
    def search_bundle(o):
        if isinstance(o, dict):
            if 'tombstone' in str(o.get('resource_id', '')):
                print(f"JSON Tombstone: {o.get('resource_id')} -> subject_reference={o.get('subject_reference') or o.get('user_id')}, name={o.get('name')}, email={o.get('email')}, phone={o.get('phone')}")
            for v in o.values(): search_bundle(v)
        elif isinstance(o, list):
            for it in o: search_bundle(it)
    search_bundle(bundle)
