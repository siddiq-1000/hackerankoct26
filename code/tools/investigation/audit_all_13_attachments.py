import csv
import json
from pathlib import Path
from datetime import datetime

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

repo = Path(".")
ev_files = {r["file_id"]: r for r in csv.DictReader(open("dataset/evidence_files.csv", "r", encoding="utf-8"))}
eval_reqs = {r["case_id"]: r for r in csv.DictReader(open("dataset/deletion_requests.csv", "r", encoding="utf-8"))}
output_rows = {r["case_id"]: r for r in csv.DictReader(open("output.csv", "r", encoding="utf-8"))}

# 13 attachment resources and their files
att_info = [
    ("case_203", "support_8903", "evidence_20"),
    ("case_407", "support_3802", "evidence_38"),
    ("case_359", "support_2537", "evidence_33"),
    ("case_311", "support_4952", "evidence_29"),
    ("case_503", "support_2295", "evidence_47"),
    ("case_455", "support_2055", "evidence_43"),
    ("case_527", "support_3896", "evidence_49"),
    ("case_479", "support_4665", "evidence_45"),
    ("case_431", "support_3615", "evidence_40"),
    ("case_275", "support_3684", "evidence_26"),
    ("case_227", "support_5830", "evidence_22"),
    ("case_179", "support_2283", "evidence_17"),
    ("case_131", "support_2315", "evidence_12"),
]

print(f"{'Case ID':<10} {'Resource ID':<14} {'File ID':<12} {'File Captured':<22} {'Audit At':<22} {'<= Audit?':<10} {'Output Status':<12} {'Support Op'}")
print("-" * 115)

for cid, rid, fid in att_info:
    ef = ev_files[fid]
    req = eval_reqs[cid]
    out = output_rows[cid]
    
    cap_dt = parse_iso(ef["captured_at"])
    aud_dt = parse_iso(req["audit_at"])
    is_valid = cap_dt <= aud_dt
    
    steps = json.loads(out["steps_json"])
    supp_ops = [s["operation"] for s in steps if s.get("resource_id") == rid and s["phase"] == "REMEDIATION"]
    op_str = supp_ops[0] if supp_ops else "NONE"
    
    print(f"{cid:<10} {rid:<14} {fid:<12} {ef['captured_at']:<22} {req['audit_at']:<22} {str(is_valid):<10} {out['deletion_status']:<12} {op_str}")
