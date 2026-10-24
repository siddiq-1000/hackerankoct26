import csv
import json
import re
import glob
from pathlib import Path
from datetime import datetime

repo = Path(".")
users = list(csv.DictReader(open("dataset/user_identities.csv", "r", encoding="utf-8")))
user_by_id = {u["user_id"]: u for u in users}
user_by_email = {u["email"].lower(): u for u in users}

audit_log = list(csv.DictReader(open("dataset/user_audit_log.csv", "r", encoding="utf-8")))
hist_emails = {}
hist_phones = {}
for a in audit_log:
    uid = a["user_id"]
    if a["field_name"] == "email":
        hist_emails[a["old_value"].lower()] = uid
    elif a["field_name"] == "phone":
        hist_phones[a["old_value"]] = uid

eval_reqs = list(csv.DictReader(open("dataset/deletion_requests.csv", "r", encoding="utf-8")))
eval_uids = {user_by_email[r["email"].lower()]["user_id"]: r["case_id"] for r in eval_reqs if r["email"].lower() in user_by_email}
# Also map historical emails in requests
for r in eval_reqs:
    em = r["email"].lower()
    if em in hist_emails:
        eval_uids[hist_emails[em]] = r["case_id"]

ev_files = {r["file_id"]: r for r in csv.DictReader(open("dataset/evidence_files.csv", "r", encoding="utf-8"))}
manifest_by_path = {r["file_path"].replace("\\", "/"): r for r in ev_files.values()}

# Find analytics records matching historical-only identifiers
hist_analytics = []

for fpath in glob.glob("dataset/evidence/**/*.*", recursive=True):
    rel_p = str(Path(fpath).relative_to(repo / "dataset")).replace("\\", "/")
    ef = manifest_by_path.get(rel_p)
    if not ef: continue
    fid = ef["file_id"]
    cap_dt = datetime.fromisoformat(ef["captured_at"].replace("Z", "+00:00"))
    
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    if "analytics_" not in content:
        continue
        
    for line in content.splitlines():
        if "analytics_" in line:
            m_res = re.search(r"(analytics_\d+)", line)
            if not m_res: continue
            rid = m_res.group(1)
            
            # Check if line matches any historical email or phone
            for hem, uid in hist_emails.items():
                if hem in line.lower():
                    # check current email is NOT in line
                    curr_em = user_by_id[uid]["email"].lower()
                    if curr_em not in line.lower():
                        cid = eval_uids.get(uid)
                        hist_analytics.append((cid, uid, hem, rid, fid, line.strip()))
                        
            for hph, uid in hist_phones.items():
                if hph in line:
                    curr_ph = user_by_id[uid]["phone"]
                    if curr_ph not in line:
                        cid = eval_uids.get(uid)
                        hist_analytics.append((cid, uid, hph, rid, fid, line.strip()))

print(f"Total historical-only analytics records found: {len(hist_analytics)}")
for h in hist_analytics:
    print(f"Case: {h[0]} | User: {h[1]} | Hist Ident: {h[2]} | RID: {h[3]} | File: {h[4]}")
    print(f"  Line: {h[5][:120]}")
