import csv
import os
import re

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    uids = {r['user_id']: r['email'] for r in csv.DictReader(f)}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    req_emails = {r['email']: r['case_id'] for r in csv.DictReader(f)}

print("=== CHECKING SUPPORT ATTACHMENTS ACROSS EVIDENCE ===")
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'attachment' in c.lower():
                    # check if any email or user_id is near attachment
                    for uid in uids:
                        if uid in c and 'attachment' in c:
                            print(f"File {f}: mentions {uid} and attachment!")
        except:
            pass
