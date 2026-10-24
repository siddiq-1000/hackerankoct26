import csv

del_reqs = {r['email'].lower(): r['case_id'] for r in csv.DictReader(open('dataset/deletion_requests.csv', 'r', encoding='utf-8'))}
for a in csv.DictReader(open('dataset/user_audit_log.csv', 'r', encoding='utf-8')):
    if a['field_name'] == 'email' and a['old_value'].lower() in del_reqs:
        cid = del_reqs[a['old_value'].lower()]
        print(f"Case {cid}: requested under old_email={a['old_value']}, current_email={a['new_value']}, user_id={a['user_id']}")
