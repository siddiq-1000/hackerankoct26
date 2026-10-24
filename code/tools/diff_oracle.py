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

def run_diff():
    loader = DatasetLoader()
    requests = loader.load_deletion_requests()
    identities = loader.load_identities()
    audit_log = loader.load_audit_log()
    rules = loader.load_deletion_rules()
    
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
            
    manifest_by_id = loader.load_evidence_manifest()

    print(f"Total requests to diff: {len(requests)}")
    
    # Prepare metadata for bulk scan
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

    print("Running bulk oracle scan across all evidence files...")
    all_hits = scanner.scan_all_cases(case_meta)
    print("Bulk oracle scan complete.")

    complete_discrepancies = []
    incomplete_discrepancies = []
    
    single_step_complete = []
    not_started_complete = []
    complete_and_complete = []

    for cid, raw_hits in all_hits.items():
        req, ident, terms = case_map[cid]
        pipe = pipeline_out.get(cid, {"status": "UNKNOWN", "steps": []})
        pipe_status = pipe["status"]
        pipe_steps = pipe["steps"]
        
        pipe_findings = [s for s in pipe_steps if s.get("phase") == "FINDING"]
        pipe_verifications = [s for s in pipe_steps if s.get("phase") == "VERIFICATION"]
        pipe_covered_resources = {s.get("resource_id") for s in pipe_steps if s.get("resource_id")}
        pipe_cited_evidence = {s.get("evidence_id") for s in pipe_steps if s.get("evidence_id")}
        
        if pipe_status == "COMPLETE":
            if len(pipe_steps) == 1:
                single_step_complete.append((cid, req.reported_status, pipe_steps[0]))
            if req.reported_status == "NOT_STARTED":
                not_started_complete.append((cid, pipe_steps))
            elif req.reported_status == "COMPLETE":
                complete_and_complete.append((cid, pipe_steps))
                
        unaccounted_hits = []
        for h in raw_hits:
            h_type = h.get("type")
            ev_id = h.get("evidence_id")
            
            if h_type == "system_activity":
                continue
                
            res_id = ""
            if "data" in h and isinstance(h["data"], dict):
                res_id = h["data"].get("resource_id") or h["data"].get("id") or h["data"].get("job_id") or ""
            if not res_id:
                res_id = h.get("resource_id", "")
                
            if res_id and res_id in pipe_covered_resources:
                continue
            if ev_id and ev_id in pipe_cited_evidence:
                continue
                
            unaccounted_hits.append(h)
            
        if pipe_status == "COMPLETE" and unaccounted_hits:
            complete_discrepancies.append({
                "case_id": cid,
                "email": req.email,
                "reported_status": req.reported_status,
                "audit_at": req.audit_at,
                "unaccounted_hits": unaccounted_hits
            })
        elif pipe_status == "INCOMPLETE" and unaccounted_hits:
            incomplete_discrepancies.append({
                "case_id": cid,
                "unaccounted_hits_count": len(unaccounted_hits)
            })

    print("\n=== DIFF RESULTS ===")
    print(f"COMPLETE discrepancies count: {len(complete_discrepancies)}")
    print(f"INCOMPLETE discrepancies count: {len(incomplete_discrepancies)}")
    print(f"Single-step COMPLETE cases: {len(single_step_complete)}")
    print(f"NOT_STARTED -> COMPLETE cases: {len(not_started_complete)}")
    print(f"COMPLETE -> COMPLETE cases: {len(complete_and_complete)}")
    
    if complete_discrepancies:
        print("\nSample COMPLETE discrepancies (first 5):")
        for cd in complete_discrepancies[:5]:
            print(f"- {cd['case_id']} ({cd['reported_status']}): {len(cd['unaccounted_hits'])} unaccounted hits")
            for h in cd['unaccounted_hits'][:3]:
                print(f"    hit: {h.get('evidence_id')} {h.get('type')} {h.get('matched_term')} {h.get('data') or h.get('line') or h.get('table')}")

if __name__ == "__main__":
    run_diff()
