import json

data = json.load(open('dataset/evidence/records/customer_data_snapshot_bundle_20260917.json', 'r', encoding='utf-8'))
for k, v in data.items():
    s = json.dumps(v)
    if 'analytics_4574' in s:
        print(f"In bundle under '{k}':")
        if isinstance(v, list):
            for it in v:
                if 'analytics_4574' in json.dumps(it):
                    print(" ", it)
        elif isinstance(v, dict):
            for subk, subv in v.items():
                if 'analytics_4574' in json.dumps(subv):
                    print(f"  under subkey '{subk}':", subv)
