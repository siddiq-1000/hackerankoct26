import csv

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

# Check columns of system_activity.csv
print("Activity columns:", list(acts[0].keys()))

# Check if there is any shared token or ID between:
# account_3866 and analytics_4574
# account_5482 and analytics_6077
for a in acts:
    if a['resource_id'] in ['analytics_4574', 'analytics_6077', 'analytics_1895', 'analytics_4566', 'analytics_5335', 'analytics_9406', 'analytics_901']:
        print(a)
