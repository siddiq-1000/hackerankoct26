import sys
sys.path.insert(0, '.')
import csv
import json
import re

print("=== RULE COVERAGE VS SAMPLE AUDIT ===")

# 1. Read deletion_rules.csv
rules = {}
with open('dataset/deletion_rules.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rules[r['rule_id']] = r

print(f"Total rules in dataset/deletion_rules.csv: {len(rules)}")

# 2. Inspect sample_output.csv steps
sample_steps = []
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for s in json.loads(r['steps_json']):
            sample_steps.append((r['case_id'], r['deletion_status'], s))

print(f"Total sample steps: {len(sample_steps)}")

# Categorize sample steps by system_id and resource_id prefix/type
sample_systems = {}
for cid, st, s in sample_steps:
    sys_id = s['system_id']
    rid = s['resource_id']
    op = s['operation']
    sample_systems[sys_id] = sample_systems.get(sys_id, 0) + 1

print(f"Sample step systems: {sample_systems}")

# 3. Read current full output.csv steps
full_steps = []
with open('output.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for s in json.loads(r['steps_json']):
            full_steps.append((r['case_id'], r['deletion_status'], s))

full_systems = {}
for cid, st, s in full_steps:
    sys_id = s['system_id']
    full_systems[sys_id] = full_systems.get(sys_id, 0) + 1

print(f"Full step systems: {full_systems}")

# 4. Check rule_06 (support attachments), rule_09 (exports), rule_13 (legal hold), rule_02 (secondary identifiers)
# Specifically check legal_hold_8017
print("\n--- Investigating legal_hold_8017 ---")
with open('output.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if 'legal_hold' in r['steps_json']:
            print(f"Found legal_hold in output.csv: {r['case_id']} -> {r['steps_json']}")

# Search evidence files for legal_hold, attachment, export, and secondary identifiers
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    manifest = list(csv.DictReader(f))

print("\n--- Searching Evidence Files for legal_hold, attachment, export ---")
legal_hold_hits = []
attachment_hits = []
export_hits = []

for finfo in manifest:
    fid = finfo['file_id']
    fpath = "dataset/" + finfo['file_path']
    if any(fpath.endswith(ext) for ext in ['.log', '.json', '.txt', '.sql', '.csv']):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as ef:
                c = ef.read()
                if 'legal_hold' in c:
                    legal_hold_hits.append((fid, finfo['file_path']))
                if 'attachment' in c or 'support_attachment' in c:
                    attachment_hits.append((fid, finfo['file_path']))
                if 'export' in c:
                    export_hits.append((fid, finfo['file_path']))
        except Exception:
            pass

print(f"Evidence files with 'legal_hold': {len(legal_hold_hits)} -> {legal_hold_hits}")
print(f"Evidence files with 'attachment': {len(attachment_hits)} -> {attachment_hits[:5]}")
print(f"Evidence files with 'export': {len(export_hits)} -> {len(export_hits)} files")
