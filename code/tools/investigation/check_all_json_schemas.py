import json
import glob
from pathlib import Path

records = list(Path('dataset/evidence/records').glob('*.json'))
print(f"Total json records: {len(records)}")
has_snapshots = []
has_service_exports = []
other = []
for p in records:
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
        if 'snapshots' in d: has_snapshots.append(p.name)
        elif 'service_exports' in d: has_service_exports.append(p.name)
        else: other.append((p.name, list(d.keys())))

print(f"Files with 'snapshots': {len(has_snapshots)}")
print(f"Files with 'service_exports': {len(has_service_exports)}")
print(f"Other files: {len(other)} -> {other}")
