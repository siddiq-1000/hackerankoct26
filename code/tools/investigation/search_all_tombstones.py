import csv
import os
import re
import json

manifest = {}
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        manifest[r['file_id']] = r

print("=== SEARCHING ALL EVIDENCE FOR TOMBSTONES ===")
tombstone_occurrences = []

for fid, finfo in manifest.items():
    p = os.path.join('dataset', finfo['file_path'])
    if not os.path.exists(p): continue
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            c = fp.read()
            if 'tombstone' in c.lower():
                matches = re.findall(r'(tombstone_\d+)', c)
                print(f"[{fid}] {finfo['file_path']} (captured_at={finfo['captured_at']}):")
                print(f"  RIDs: {set(matches)}")
                for line in c.splitlines():
                    if 'tombstone' in line.lower():
                        print(f"    LINE: {line.strip()[:140]}")
    except:
        pass
