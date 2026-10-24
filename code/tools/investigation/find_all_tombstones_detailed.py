import os
import json
import re

print("=== ALL TOMBSTONE OCCURRENCES IN ENTIRE DATASET ===")
for root, dirs, files in os.walk('dataset'):
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'tombstone' in c.lower():
                    matches = set(re.findall(r'tombstone_\d+', c, re.IGNORECASE))
                    print(f"\n{p} -> {matches}")
                    for line in c.splitlines():
                        if 'tombstone' in line.lower():
                            print(f"  {line.strip()[:150]}")
        except:
            pass
