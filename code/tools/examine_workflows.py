import csv
import json

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

# Let's inspect all events for:
# user_21 (account_6440, analytics_5335)
# user_25 (account_3136, analytics_1895)
# user_26 (account_5684, analytics_4566, support_4715, data_flow_6244, backup_3120)
# user_27 (account_3866, analytics_4574, support_4707, data_flow_2295, backup_5970)
# user_28 (account_5482, analytics_6077, support_2351, data_flow_2337, backup_838)
# user_43 (account_7566, analytics_9406)
# user_04 (account_004, analytics_901)

cases_resources = {
    'case_03': ['account_7566', 'analytics_9406'],
    'case_04': ['account_004', 'analytics_901'],
    'case_21': ['account_6440', 'analytics_5335'],
    'case_25': ['account_3136', 'analytics_1895'],
    'case_26': ['account_5684', 'analytics_4566', 'support_4715', 'data_flow_6244', 'backup_3120'],
    'case_27': ['account_3866', 'analytics_4574', 'support_4707', 'data_flow_2295', 'backup_5970'],
    'case_28': ['account_5482', 'analytics_6077', 'support_2351', 'data_flow_2337', 'backup_838'],
}

for cid, rlist in cases_resources.items():
    print(f"\n==================== {cid} ====================")
    case_acts = [a for a in activity if a['resource_id'] in rlist or any(r in a['details'] for r in rlist)]
    case_acts.sort(key=lambda x: x['event_time'])
    for a in case_acts:
        print(f"  {a['event_time']} | {a['target_system']:18s} | {a['event_type']:18s} | {a['resource_id']:15s} | {a['reported_result']:7s} | {a['details']}")
