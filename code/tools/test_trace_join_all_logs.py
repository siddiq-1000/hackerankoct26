import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    reqs = list(csv.DictReader(f))

with open('output.csv', 'r', encoding='utf-8') as f:
    full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    ev_files = {r['file_id']: r for r in csv.DictReader(f)}

# Let's inspect all log files
log_files = {fid: ef for fid, ef in ev_files.items() if ef['file_path'].endswith('.log')}
print(f"Total log files: {len(log_files)}")

# Map trace_id -> all lines in log
trace_map = defaultdict(list)
for fid, ef in log_files.items():
    p = Path('dataset') / ef['file_path']
    if not p.exists(): continue
    for line in open(p, 'r', encoding='utf-8', errors='ignore'):
        m_tr = re.search(r'tr-\d+', line)
        if m_tr:
            trace_map[(fid, m_tr.group(0))].append(line.strip())

print(f"Total unique (file_id, trace_id) groups: {len(trace_map)}")

# Now for each case, find all traces where user's email or user_id or account appears
status_changes = []
step_changes = []

for r in reqs:
    cid = r['case_id']
    curr_status, curr_steps = full_out[cid]
    email = r['email'].lower()
    aud_dt = parse_iso(r['audit_at'])

    # Find traces for this user
    user_traces = []
    for (fid, tr), lines in trace_map.items():
        ef = ev_files[fid]
        cap_dt = parse_iso(ef['captured_at'])
        if cap_dt > aud_dt:
            continue
        has_user = any(email in l.lower() for l in lines)
        if has_user:
            user_traces.append((fid, tr, lines))

    # Evaluate outcomes in user_traces
    for fid, tr, lines in user_traces:
        # Check if there is an outcome line
        for l in lines:
            if 'http_status="404"' in l or 'rows="0"' in l or 'result="not_found"' in l:
                # Proven absent
                pass
            elif 'http_status="200"' in l or 'result="hit"' in l or 'rows="1"' in l or 'enabled="true"' in l or 'restore_allowed="true"' in l:
                # Proven present or active
                # Check if currently complete
                if curr_status == 'COMPLETE':
                    status_changes.append((cid, curr_status, fid, tr, l))

print(f"\nTrace-join results:")
print(f"Total cases with potential status changes from trace-join: {len(status_changes)}")
for sc in status_changes[:15]:
    print(" ", sc)
