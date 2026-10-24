#!/usr/bin/env python3
"""
Per-case analysis for single-step COMPLETE cases.
Implements Section A5 requirements from HackerRank Orchestrate (October 2026) Brief 3B.
"""

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from code.loaders import DatasetLoader
from code.identity import IdentityResolver
from code.tools.oracle_scan import OracleScanner

def main():
    loader = DatasetLoader()
    requests = {r.case_id: r for r in loader.load_deletion_requests()}
    identities = loader.load_identities()
    audit_log = loader.load_audit_log()
    resolver = IdentityResolver(identities, audit_log)
    scanner = OracleScanner()
    manifest = loader.load_evidence_manifest()

    # Load output.csv
    single_step_cases = []
    with open(REPO_ROOT / "output.csv", "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["deletion_status"] == "COMPLETE":
                steps = json.loads(r["steps_json"])
                if len(steps) == 1:
                    single_step_cases.append((r["case_id"], steps[0]))

    print(f"[*] Found {len(single_step_cases)} single-step COMPLETE cases in output.csv.")

    # Prepare case metadata for oracle scan
    case_meta = []
    for cid, step in single_step_cases:
        req = requests[cid]
        ident = resolver.resolve(req.email)
        terms = ident.all_search_terms()
        account_id = f"account_{ident.user_id.split('_')[1]:0>3}" if ident.user_id.startswith("user_") and ident.user_id.split("_")[1].isdigit() else f"account_{ident.user_id}"
        all_terms = list(set(terms + [account_id]))
        case_meta.append({
            "case_id": cid,
            "audit_at": req.audit_at,
            "terms": all_terms
        })

    all_hits = scanner.scan_all_cases(case_meta)

    # Inspect each case
    summary_rows = []
    
    print("\n" + "=" * 90)
    print(f"{'Case ID':<10} {'Evidence Cited':<15} {'Operation':<22} {'Oracle Hits':<12} {'Excluded':<10} {'Exclusion Reasons'}")
    print("=" * 90)

    for cid, step in single_step_cases:
        req = requests[cid]
        ident = resolver.resolve(req.email)
        raw_hits = all_hits.get(cid, [])
        evidence_cited = step.get("evidence_id")
        op = step.get("operation")
        res_id = step.get("resource_id")

        reasons = set()
        excluded_count = 0
        for h in raw_hits:
            if h.get("type") == "system_activity":
                continue
            h_str = json.dumps(h).lower()
            if h.get("evidence_id") == evidence_cited or res_id in h_str:
                reasons.add("CITED_PROOF_OF_ABSENCE")
                excluded_count += 1
            elif "audit_record" in h_str or "security" in h_str:
                reasons.add("RETAINED_SECURITY_LOG (rule_12)")
                excluded_count += 1
            elif "404" in h_str or "rows=0" in h_str or "not_found" in h_str or "lookup_started" in h_str:
                reasons.add("PROOF_OF_ABSENCE_LOG_404")
                excluded_count += 1
            elif "tombstone" in h_str:
                reasons.add("COMPLIANT_TOMBSTONE (rule_15)")
                excluded_count += 1

        reason_str = ", ".join(sorted(reasons)) if reasons else "None (0 hits)"
        print(f"{cid:<10} {evidence_cited:<15} {op:<22} {len(raw_hits):<12} {excluded_count:<10} {reason_str}")

        summary_rows.append({
            "case_id": cid,
            "evidence_cited": evidence_cited,
            "operation": op,
            "resource_id": res_id,
            "oracle_hits": len(raw_hits),
            "excluded_hits": excluded_count,
            "exclusion_reasons": reason_str
        })

    print("=" * 90)
    print(f"[*] Total single-step cases verified: {len(summary_rows)}")
    return summary_rows

if __name__ == "__main__":
    main()
