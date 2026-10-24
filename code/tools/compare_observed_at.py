import json

data = json.load(open('dataset/evidence/records/service_resource_export_20260915_114455.json', 'r', encoding='utf-8'))

accs = [a for a in data['service_exports']['account_service']['profile_lookups'] if a['status_code'] == 404]
accs.sort(key=lambda x: x['observed_at'])

anas = [a for a in data['service_exports']['analytics_platform']['profiles'] if a['email'] is None]
anas.sort(key=lambda x: x['observed_at'])

print("ACCOUNTS (sorted by observed_at):")
for a in accs:
    print(f"  {a['resource_id']:15s} | {a['observed_at']}")

print("\nANALYTICS (sorted by observed_at):")
for a in anas:
    print(f"  {a['resource_id']:15s} | {a['observed_at']}")
