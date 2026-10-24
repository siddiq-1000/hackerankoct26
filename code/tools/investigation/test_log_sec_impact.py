import glob
import re
import csv
from datetime import datetime
from pathlib import Path

repo = Path(".")
eval_reqs = list(csv.DictReader(open("dataset/deletion_requests.csv", "r", encoding="utf-8")))
users = {u["email"].lower(): u for u in csv.DictReader(open("dataset/user_identities.csv", "r", encoding="utf-8"))}
manifest = {r["file_id"]: r for r in csv.DictReader(open("dataset/evidence_files.csv", "r", encoding="utf-8"))}
manifest_by_path = {r["file_path"].replace("\\", "/"): r for r in manifest.values()}

log_sec_hits = []
for p in glob.glob("dataset/evidence/logs/*.*"):
    rel_p = str(Path(p).relative_to(repo / "dataset")).replace("\\", "/")
    ef = manifest_by_path.get(rel_p)
    if not ef: continue
    fid = ef["file_id"]
    cap = datetime.fromisoformat(ef["captured_at"].replace("Z", "+00:00"))
    
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "audit_record_" in line:
                m_res = re.search(r"resource_id[\"'=\s:]+(audit_record_\d+)", line)
                m_user = re.search(r"\b(user_\d+)\b", line)
                m_em = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line)
                if m_res and (m_user or m_em):
                    log_sec_hits.append((fid, cap, m_res.group(1), m_user.group(1) if m_user else None, m_em.group(0).lower() if m_em else None))

print(f"Total log security hits: {len(log_sec_hits)}")

# How many eval cases match a log security record <= audit_at?
case_hits = set()
for req in eval_reqs:
    cid = req["case_id"]
    aud_dt = datetime.fromisoformat(req["audit_at"].replace("Z", "+00:00"))
    em = req["email"].lower()
    u = users.get(em)
    uid = u["user_id"] if u else None
    
    for fid, cap, rid, r_uid, r_em in log_sec_hits:
        if cap <= aud_dt:
            if (uid and r_uid and uid == r_uid) or (em and r_em and em == r_em):
                case_hits.add(cid)

print(f"Eval cases with log security record <= audit_at: {len(case_hits)}")
