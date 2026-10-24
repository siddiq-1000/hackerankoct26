import json

data = json.load(open('dataset/evidence/records/service_resource_export_20260915_114455.json', 'r', encoding='utf-8'))
for sys_id, content in data['service_exports'].items():
    for subk, items in content.items():
        for it in items:
            rid = it.get('resource_id', '')
            cref = str(it.get('customer_reference', ''))
            obs = it.get('observed_at', '')
            print(f"{sys_id:20s} | {rid:15s} | {cref:10s} | {obs}")
