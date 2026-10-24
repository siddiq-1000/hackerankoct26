import csv
import json
import sqlite3
import glob
from pathlib import Path
from datetime import datetime

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

repo = Path(".")

# Load users and requests
users = list(csv.DictReader(open("dataset/user_identities.csv", "r", encoding="utf-8")))
user_by_id = {u["user_id"]: u for u in users}
user_by_email = {u["email"].lower(): u for u in users}

eval_reqs = list(csv.DictReader(open("dataset/deletion_requests.csv", "r", encoding="utf-8")))
eval_by_email = {r["email"].lower(): r for r in eval_reqs}
eval_by_uid = {}
for r in eval_reqs:
    u = user_by_email.get(r["email"].lower())
    if u: eval_by_uid[u["user_id"]] = r

# Load current output.csv
with open("output.csv", "r", encoding="utf-8") as f:
    eval_output = {r["case_id"]: r for r in csv.DictReader(f)}

ev_files = {r["file_id"]: r for r in csv.DictReader(open("dataset/evidence_files.csv", "r", encoding="utf-8"))}
ev_by_path = {r["file_path"]: r for r in ev_files.values()}

# Let's search all evidence for security audit records
# A security record maps to a user via user_id, email, or subject_reference
sec_records = [] # (fid, file_path, cap_time, res_id, user_ref, email_ref)

# 1. SQL evidence
for fpath in sorted(glob.glob("dataset/evidence/databases/*.sql")):
    rel_p = str(Path(fpath).relative_to(repo / "dataset")).replace("\\", "/")
    ef = ev_by_path.get(rel_p)
    if not ef: continue
    fid = ef["file_id"]
    cap = parse_iso(ef["captured_at"])
    
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(open(fpath, "r", encoding="utf-8", errors="ignore").read())
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        
        # Check security_audit_records table
        if "security_audit_records" in tables:
            cols = [c[1] for c in conn.execute("PRAGMA table_info('security_audit_records')").fetchall()]
            for r in conn.execute("SELECT * FROM security_audit_records").fetchall():
                row_dict = dict(zip(cols, r))
                res_id = row_dict.get("audit_id") or row_dict.get("resource_id") or r[0]
                uid = row_dict.get("user_id")
                em = row_dict.get("email")
                sec_records.append((fid, fpath, cap, res_id, uid, em))
                
        # Check collection tables like customer_data_primary
        for t in tables:
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info('{t}')").fetchall()]
            if "collection_name" in cols and "payload" in cols:
                for r in conn.execute(f"SELECT * FROM '{t}' WHERE collection_name = 'security_audit_records'").fetchall():
                    pay = json.loads(r[3])
                    res_id = pay.get("resource_id") or r[0]
                    uid = pay.get("user_id") or pay.get("subject_reference")
                    em = pay.get("email")
                    sec_records.append((fid, fpath, cap, res_id, uid, em))
    except Exception:
        pass

# 2. JSON evidence
for fpath in sorted(glob.glob("dataset/evidence/records/*.json")):
    rel_p = str(Path(fpath).relative_to(repo / "dataset")).replace("\\", "/")
    ef = ev_by_path.get(rel_p)
    if not ef: continue
    fid = ef["file_id"]
    cap = parse_iso(ef["captured_at"])
    
    try:
        data = json.load(open(fpath, "r", encoding="utf-8", errors="ignore"))
        # Check customer_data_snapshot_bundle
        for snap in data.get("snapshots", []):
            if snap.get("data_store") == "security_service":
                for rec in snap.get("records", []):
                    res_id = rec.get("resource_id")
                    uid = rec.get("user_id")
                    em = rec.get("email")
                    sec_records.append((fid, fpath, cap, res_id, uid, em))
                    
        # Check service_resource_export
        for rec in data.get("exports", {}).get("security_service", {}).get("audit_records", []):
            res_id = rec.get("resource_id")
            uid = rec.get("user_id")
            em = rec.get("email")
            sec_records.append((fid, fpath, cap, res_id, uid, em))
            
        # Check customer_export_manifest
        for rec in data.get("records", []):
            if rec.get("system") == "security_service":
                res_id = rec.get("resource_id")
                sub = rec.get("subject_reference")
                uid = sub if (sub and sub.startswith("user_")) else None
                em = sub if (sub and "@" in sub) else None
                sec_records.append((fid, fpath, cap, res_id, uid, em))
                
        # Check security_audit_ledger
        for rec in data.get("audit_entries", []):
            res_id = rec.get("audit_id") or rec.get("resource_id")
            uid = rec.get("user_id")
            em = rec.get("email")
            sec_records.append((fid, fpath, cap, res_id, uid, em))
    except Exception:
        pass

print(f"Total raw security records indexed: {len(sec_records)}")

# Map each evaluation case to security records captured <= audit_at
case_valid_sec = {}
for req in eval_reqs:
    cid = req["case_id"]
    aud_dt = parse_iso(req["audit_at"])
    em = req["email"].lower()
    u = user_by_email.get(em)
    uid = u["user_id"] if u else None
    
    valid_recs = []
    for fid, fpath, cap, res_id, r_uid, r_em in sec_records:
        if cap <= aud_dt:
            match = False
            if r_uid and uid and r_uid.lower() == uid.lower():
                match = True
            elif r_em and r_em.lower() == em:
                match = True
            if match:
                valid_recs.append((fid, res_id, cap))
    case_valid_sec[cid] = valid_recs

# Compare with output.csv
has_valid_sec_count = {'COMPLETE': 0, 'INCOMPLETE': 0}
emitted_sec_count = {'COMPLETE': 0, 'INCOMPLETE': 0}
mismatches = []

for req in eval_reqs:
    cid = req["case_id"]
    st = eval_output[cid]["deletion_status"]
    if st == "NOT_APPLICABLE": continue
    
    has_valid = len(case_valid_sec[cid]) > 0
    if has_valid:
        has_valid_sec_count[st] += 1
        
    steps = json.loads(eval_output[cid]["steps_json"])
    emitted = any(s.get("system_id") == "security_service" and s.get("operation") == "VERIFY_RECORD_PRESENT" for s in steps)
    if emitted:
        emitted_sec_count[st] += 1
        
    if has_valid != emitted:
        mismatches.append((cid, st, has_valid, emitted, case_valid_sec[cid]))

print("\n--- RESULTS ---")
print("COMPLETE Cases:")
print(f"  Has Valid Security Record in Evidence (<= audit_at): {has_valid_sec_count['COMPLETE']} / 194 ({has_valid_sec_count['COMPLETE']/194:.1%})")
print(f"  Emitted security_service VERIFY_RECORD_PRESENT:       {emitted_sec_count['COMPLETE']} / 194 ({emitted_sec_count['COMPLETE']/194:.1%})")

print("\nINCOMPLETE Cases:")
print(f"  Has Valid Security Record in Evidence (<= audit_at): {has_valid_sec_count['INCOMPLETE']} / 314 ({has_valid_sec_count['INCOMPLETE']/314:.1%})")
print(f"  Emitted security_service VERIFY_RECORD_PRESENT:       {emitted_sec_count['INCOMPLETE']} / 314 ({emitted_sec_count['INCOMPLETE']/314:.1%})")

print(f"\nTotal Mismatches (has_valid != emitted): {len(mismatches)}")
for m in mismatches[:10]:
    print(" ", m)
