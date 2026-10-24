import os
import json
import csv
import re

manifest = {}
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        manifest[r['file_id']] = r

print("=== ALL TICKET ATTACHMENTS ACROSS ALL EVIDENCE ===")
for fid, finfo in manifest.items():
    p = os.path.join('dataset', finfo['file_path'])
    if not os.path.exists(p): continue
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            c = fp.read()
            if 'ticket_attachment' in c:
                for line in c.splitlines():
                    if 'ticket_attachment' in line:
                        print(f"[{fid}] {finfo['file_path']}: {line.strip()[:140]}")
    except:
        pass
