import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from code.tools.find_404_hits import main

# Let's inspect the exact lines
import csv, json
from code.loaders import DatasetLoader
from code.identity import IdentityResolver
from code.tools.oracle_scan import OracleScanner

loader = DatasetLoader()
requests = loader.load_deletion_requests()
identities = loader.load_identities()
audit_log = loader.load_audit_log()
resolver = IdentityResolver(identities, audit_log)
scanner = OracleScanner()

pipeline_out = {}
with open(REPO_ROOT / "output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        pipeline_out[r["case_id"]] = {
            "status": r["deletion_status"],
            "steps": json.loads(r["steps_json"])
        }

case_meta = []
case_map = {}
for req in requests:
    cid = req.case_id
    ident = resolver.resolve(req.email)
    terms = ident.all_search_terms()
    account_id = f"account_{ident.user_id.split('_')[1]:0>3}" if ident.user_id.startswith("user_") and ident.user_id.split("_")[1].isdigit() else f"account_{ident.user_id}"
    all_terms = list(set(terms + [account_id]))
    case_meta.append({
        "case_id": cid,
        "audit_at": req.audit_at,
        "terms": all_terms
    })
    case_map[cid] = (req, ident, all_terms)

all_hits = scanner.scan_all_cases(case_meta)

p404_list = []
for cid, raw_hits in all_hits.items():
    if pipeline_out.get(cid, {}).get("status") != "COMPLETE":
        continue
    pipe_covered = {s.get("resource_id") for s in pipeline_out[cid]["steps"] if s.get("resource_id")}
    pipe_cited = {s.get("evidence_id") for s in pipeline_out[cid]["steps"] if s.get("evidence_id")}

    for h in raw_hits:
        if h.get("type") == "system_activity":
            continue
        res_id = ""
        if "data" in h and isinstance(h["data"], dict):
            res_id = h["data"].get("resource_id") or h["data"].get("id") or ""
        if not res_id:
            res_id = h.get("resource_id", "")
        if res_id and res_id in pipe_covered:
            continue
        if h.get("evidence_id") in pipe_cited:
            continue

        h_str = json.dumps(h).lower()
        if "audit_record" in h_str or "security_service" in h_str:
            continue
        if any(k in h_str for k in ["rows=0", "rows=\\\"0\\\"", "404", "not_found", "lookup_started", "scan_started", "_started", "query_started"]):
            p404_list.append((cid, h))

for idx, (cid, h) in enumerate(p404_list, 1):
    print(f"[{idx:>2}] Case: {cid} | File: {h.get('evidence_id')} ({h.get('file')})")
    print(f"     Line: {h.get('line')}")
