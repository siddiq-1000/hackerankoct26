import csv
import json
import re
import os
import glob
from pathlib import Path
from datetime import datetime

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

repo = Path(".")
users = list(csv.DictReader(open("dataset/user_identities.csv", "r", encoding="utf-8")))
user_by_id = {u["user_id"]: u for u in users}
user_by_email = {u["email"].lower(): u for u in users}

audit_log = list(csv.DictReader(open("dataset/user_audit_log.csv", "r", encoding="utf-8")))
hist_emails = {}
for a in audit_log:
    if a["field_name"] == "email":
        hist_emails[a["old_value"].lower()] = a["user_id"]
        hist_emails[a["new_value"].lower()] = a["user_id"]

eval_reqs = list(csv.DictReader(open("dataset/deletion_requests.csv", "r", encoding="utf-8")))
ev_files = {r["file_id"]: r for r in csv.DictReader(open("dataset/evidence_files.csv", "r", encoding="utf-8"))}

# Load current output
with open("output.csv", "r", encoding="utf-8") as f:
    eval_output = {r["case_id"]: r for r in csv.DictReader(f)}

# Find all occurrences of security records across all files in dataset/evidence
# A security record line/object contains 'audit_record_\d+' and an identifier (user_..., email, etc.)
all_sec_evidence = [] # (file_id, captured_at, audit_record_id, matched_user_id, matched_email)

manifest_by_path = {r["file_path"].replace("\\", "/"): r for r in ev_files.values()}

for fpath in glob.glob("dataset/evidence/**/*.*", recursive=True):
    rel_p = str(Path(fpath).relative_to(repo / "dataset")).replace("\\", "/")
    ef = manifest_by_path.get(rel_p)
    if not ef: continue
    fid = ef["file_id"]
    cap_dt = parse_iso(ef["captured_at"])
    
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    if "audit_record_" not in content:
        continue
        
    for line in content.splitlines():
        if "audit_record_" in line:
            m_aud = re.search(r"(audit_record_\d+)", line)
            if not m_aud: continue
            aud_id = m_aud.group(1)
            
            # Check user_id
            m_uid = re.search(r"\b(user_\d+)\b", line)
            m_em = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line)
            
            uid = m_uid.group(1) if m_uid else None
            em = m_em.group(0).lower() if m_em else None
            
            if uid or em:
                all_sec_evidence.append((fid, cap_dt, aud_id, uid, em))

print(f"Total raw security record matches found: {len(all_sec_evidence)}")

# Now for each evaluation request, check if any match is valid (cap_dt <= audit_dt)
case_matches = {}
for req in eval_reqs:
    cid = req["case_id"]
    aud_dt = parse_iso(req["audit_at"])
    em = req["email"].lower()
    u = user_by_email.get(em)
    uid = u["user_id"] if u else hist_emails.get(em)
    
    hits = []
    for fid, cap_dt, aud_id, r_uid, r_em in all_sec_evidence:
        if cap_dt <= aud_dt:
            is_match = False
            if uid and r_uid and uid.lower() == r_uid.lower():
                is_match = True
            elif em and r_em and em == r_em:
                is_match = True
            if is_match:
                hits.append((fid, aud_id))
    case_matches[cid] = list(set(hits))

complete_cases = [r for r in eval_reqs if eval_output[r["case_id"]]["deletion_status"] == "COMPLETE"]
incomplete_cases = [r for r in eval_reqs if eval_output[r["case_id"]]["deletion_status"] == "INCOMPLETE"]

print("\n--- INDEPENDENT RAW EVIDENCE COUNT ---")
complete_has = sum(1 for r in complete_cases if len(case_matches[r["case_id"]]) > 0)
incomplete_has = sum(1 for r in incomplete_cases if len(case_matches[r["case_id"]]) > 0)

print(f"COMPLETE:   {complete_has} / {len(complete_cases)} ({complete_has/len(complete_cases):.1%}) have security audit records <= audit_at")
print(f"INCOMPLETE: {incomplete_has} / {len(incomplete_cases)} ({incomplete_has/len(incomplete_cases):.1%}) have security audit records <= audit_at")

# Check emitted in output.csv
complete_emitted = 0
for r in complete_cases:
    steps = json.loads(eval_output[r["case_id"]]["steps_json"])
    if any(s.get("system_id") == "security_service" for s in steps):
        complete_emitted += 1

incomplete_emitted = 0
for r in incomplete_cases:
    steps = json.loads(eval_output[r["case_id"]]["steps_json"])
    if any(s.get("system_id") == "security_service" for s in steps):
        incomplete_emitted += 1

print(f"COMPLETE emitted:   {complete_emitted} / {len(complete_cases)}")
print(f"INCOMPLETE emitted: {incomplete_emitted} / {len(incomplete_cases)}")

# Differences
diffs = []
for r in eval_reqs:
    cid = r["case_id"]
    st = eval_output[cid]["deletion_status"]
    if st == "NOT_APPLICABLE": continue
    has_raw = len(case_matches[cid]) > 0
    steps = json.loads(eval_output[cid]["steps_json"])
    has_out = any(s.get("system_id") == "security_service" for s in steps)
    if has_raw != has_out:
        diffs.append((cid, st, has_raw, has_out, case_matches[cid]))

print(f"\nTotal differences between raw evidence scan and output: {len(diffs)}")
for d in diffs[:10]:
    print(" ", d)
