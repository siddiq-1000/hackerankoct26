import csv

uids = ['user_541', 'user_542', 'user_543', 'user_544', 'user_545', 'user_546', 'user_547', 'user_548', 'user_549', 'user_550']

users = {}
with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['user_id'] in uids:
            users[r['user_id']] = r

requests = {}
with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for uid, u in users.items():
            if r['email'].lower() == u['email'].lower():
                requests[uid] = r

for uid in uids:
    u = users.get(uid, {})
    req = requests.get(uid, {})
    cid = req.get('case_id', 'NOT_IN_REQUESTS')
    audit_at = req.get('audit_at', 'N/A')
    print(f"{uid}: email={u.get('email')} -> case={cid} (audit_at={audit_at})")
