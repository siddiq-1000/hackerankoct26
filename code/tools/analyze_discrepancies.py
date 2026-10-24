import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from code.loaders import DatasetLoader
from code.identity import IdentityResolver
from code.tools.oracle_scan import OracleScanner

def analyze():
    loader = DatasetLoader()
    requests = loader.load_deletion_requests()
    identities = loader.load_identities()
    audit_log = loader.load_audit_log()
    resolver = IdentityResolver(identities, audit_log)
    scanner = OracleScanner()
    
    # Load pipeline output
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

    # Classify all discrepancies on COMPLETE cases
    justified_exclusions = {
        "RETAINED_SECURITY_AUDIT_LOG": 0,
        "PROOF_OF_ABSENCE_LOG_404": 0,
        "COMPLIANT_TOMBSTONE_REFERENCE": 0,
        "ANONYMIZED_TELEMETRY": 0,
        "OTHER_UNEXPLAINED": 0
    }
    
    unexplained_list = []

    for cid, raw_hits in all_hits.items():
        req, ident, terms = case_map[cid]
        pipe = pipeline_out.get(cid, {"status": "UNKNOWN", "steps": []})
        pipe_status = pipe["status"]
        pipe_steps = pipe["steps"]
        
        if pipe_status != "COMPLETE":
            continue

        pipe_covered_resources = {s.get("resource_id") for s in pipe_steps if s.get("resource_id")}
        pipe_cited_evidence = {s.get("evidence_id") for s in pipe_steps if s.get("evidence_id")}

        for h in raw_hits:
            if h.get("type") == "system_activity":
                continue
            
            res_id = ""
            if "data" in h and isinstance(h["data"], dict):
                res_id = h["data"].get("resource_id") or h["data"].get("id") or h["data"].get("job_id") or ""
            if not res_id:
                res_id = h.get("resource_id", "")
                
            if res_id and res_id in pipe_covered_resources:
                continue
            if h.get("evidence_id") in pipe_cited_evidence:
                continue

            # Analyze what this hit actually is:
            h_str = json.dumps(h).lower()
            if "audit_record" in h_str or "security_service" in h_str or "security_audit" in h_str:
                justified_exclusions["RETAINED_SECURITY_AUDIT_LOG"] += 1
            elif "rows=0" in h_str or "rows=\\\"0\\\"" in h_str or "rows=\\0" in h_str or "404" in h_str or "not_found" in h_str or "lookup_started" in h_str or "scan_started" in h_str or "_started" in h_str or "query_started" in h_str:
                justified_exclusions["PROOF_OF_ABSENCE_LOG_404"] += 1
            elif "tombstone" in h_str or "pii_removed" in h_str:
                justified_exclusions["COMPLIANT_TOMBSTONE_REFERENCE"] += 1
            elif "general_shopper" in h_str or "anonymized" in h_str:
                justified_exclusions["ANONYMIZED_TELEMETRY"] += 1
            else:
                justified_exclusions["OTHER_UNEXPLAINED"] += 1
                unexplained_list.append((cid, h))

    print("=== ORACLE vs PIPELINE EXCLUSION ANALYSIS ON COMPLETE CASES ===")
    for k, v in justified_exclusions.items():
        print(f"  {k}: {v}")
    print(f"Total unexplained discrepancies on COMPLETE cases: {justified_exclusions['OTHER_UNEXPLAINED']}")
    if unexplained_list:
        print("Sample unexplained hits:")
        for cid, h in unexplained_list[:5]:
            print(f"  [{cid}] {h.get('evidence_id')} {h.get('type')}: {h}")

if __name__ == "__main__":
    analyze()
