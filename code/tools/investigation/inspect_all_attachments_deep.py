import sqlite3
import glob
import json
import csv
from pathlib import Path

repo = Path(".")
ev_files = list(csv.DictReader(open("dataset/evidence_files.csv", "r", encoding="utf-8")))
ev_map = {r["file_path"]: r for r in ev_files}

users = list(csv.DictReader(open("dataset/user_identities.csv", "r", encoding="utf-8")))
user_by_id = {u["user_id"]: u for u in users}
user_by_email = {u["email"].lower(): u for u in users}

eval_reqs = list(csv.DictReader(open("dataset/deletion_requests.csv", "r", encoding="utf-8")))
eval_by_email = {r["email"].lower(): r for r in eval_reqs}
eval_by_uid = {user_by_email[r["email"].lower()]["user_id"]: r for r in eval_reqs if r["email"].lower() in user_by_email}

sample_reqs = list(csv.DictReader(open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8")))
sample_by_email = {r["email"].lower(): r for r in sample_reqs}
sample_by_uid = {user_by_email[r["email"].lower()]["user_id"]: r for r in sample_reqs if r["email"].lower() in user_by_email}

found = []

# 1. SQL evidence
for f in sorted(glob.glob("dataset/evidence/databases/*.sql")):
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(open(f, "r", encoding="utf-8", errors="ignore").read())
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in tables:
            # check if collection_name exists
            cols = [col[1] for col in conn.execute(f"PRAGMA table_info('{t}')").fetchall()]
            if "collection_name" in cols:
                rows = conn.execute(f"SELECT * FROM '{t}' WHERE collection_name = 'ticket_attachments'").fetchall()
                for r in rows:
                    rel_p = str(Path(f).relative_to(repo / "dataset")).replace("\\", "/")
                    fid = ev_map.get(rel_p, {}).get("file_id", "unknown")
                    payload = json.loads(r[3])
                    found.append((fid, f, t, r[0], payload))
    except Exception as e:
        pass

# 2. JSON evidence
for f in sorted(glob.glob("dataset/evidence/documents/*.json") + glob.glob("dataset/evidence/records/*.json")):
    try:
        data = json.loads(open(f, "r", encoding="utf-8", errors="ignore").read())
        rel_p = str(Path(f).relative_to(repo / "dataset")).replace("\\", "/")
        fid = ev_map.get(rel_p, {}).get("file_id", "unknown")
        def walk(o):
            if isinstance(o, dict):
                if o.get("collection") == "ticket_attachments" or o.get("collection_name") == "ticket_attachments":
                    # Check if there is a 'records' list
                    recs = o.get("records")
                    if isinstance(recs, list):
                        for rec in recs:
                            found.append((fid, f, "json", rec.get("resource_id"), rec))
                    else:
                        found.append((fid, f, "json", o.get("resource_id"), o))
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for it in o: walk(it)
        walk(data)
    except Exception:
        pass

print(f"Total ticket_attachments found: {len(found)}")
unique_rids = {}
for fid, fpath, tbl, rid, pay in found:
    if rid not in unique_rids:
        unique_rids[rid] = (fid, fpath, tbl, pay)

# Also load user_audit_log for historical emails
audit_log = list(csv.DictReader(open("dataset/user_audit_log.csv", "r", encoding="utf-8")))
hist_to_current_user = {}
for a in audit_log:
    uid = a["user_id"]
    if a["field_name"] == "email":
        hist_to_current_user[a["old_value"].lower()] = uid
        hist_to_current_user[a["new_value"].lower()] = uid

print(f"Unique ticket_attachments resources: {len(unique_rids)}")
for rid, (fid, fpath, tbl, pay) in unique_rids.items():
    fn = Path(fpath).name
    up_by = (pay.get("uploaded_by") or "").lower()
    
    # Resolve user
    u = user_by_email.get(up_by)
    uid = u["user_id"] if u else hist_to_current_user.get(up_by)
    curr_em = user_by_id[uid]["email"].lower() if uid and uid in user_by_id else up_by
    
    s_c = sample_by_email.get(curr_em) or sample_by_email.get(up_by) or (sample_by_uid.get(uid) if uid else None)
    e_c = eval_by_email.get(curr_em) or eval_by_email.get(up_by) or (eval_by_uid.get(uid) if uid else None)
    target = f"SAMPLE:{s_c['case_id']}" if s_c else (f"EVAL:{e_c['case_id']}" if e_c else "UNRELATED")
    print(f"RID: {rid} | File: {fid} ({fn}) | UploadedBy: {up_by} | UserID: {uid} | Target: {target} | Ticket: {pay.get('ticket_id')}")

