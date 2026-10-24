import csv
import os
import json
import re

manifest = {}
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        manifest[r['file_id']] = r

users = {}
with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        users[r['user_id']] = r

print("=== SCANNING ALL EVIDENCE FOR LEGAL HOLDS ===")
legal_records = []
for fid, finfo in manifest.items():
    p = os.path.join('dataset', finfo['file_path'])
    if not os.path.exists(p): continue
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            c = fp.read()
            if 'legal_hold' in c:
                # Find all occurrences of legal_hold_...
                matches = re.findall(r'legal_hold_\d+', c)
                print(f"File {fid} ({finfo['file_path']}) mentions: {set(matches)}")
                for line in c.splitlines():
                    if 'legal_hold' in line:
                        print(f"   LINE: {line.strip()[:140]}")
    except:
        pass
