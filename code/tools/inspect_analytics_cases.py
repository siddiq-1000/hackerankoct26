import sqlite3
import json

# 1. case_161
conn = sqlite3.connect(':memory:')
with open('dataset/evidence/databases/customer_data_read_replica_20260802.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
cur = conn.cursor()
cur.execute("SELECT * FROM customer_data_primary WHERE resource_id='analytics_2008';")
print('case_161 customer_data_primary row:', cur.fetchone())

# 2. case_377
with open('dataset/evidence/logs/resource_lookup_trace_20260414_054007.log', encoding='utf-8') as f:
    for l in f:
        if 'analytics_3651' in l:
            print('case_377 trace line:', l.strip())

# 3. case_413
with open('dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', encoding='utf-8') as f:
    for l in f:
        if 'analytics_4523' in l:
            print('case_413 syslog line:', l.strip())

# 4. case_50
trans = json.load(open('code/cache/ocr_transcripts.json', encoding='utf-8'))
print('case_50 ocr transcript:', trans.get('evidence/images/analytics_profile_view_20260713.png'))
