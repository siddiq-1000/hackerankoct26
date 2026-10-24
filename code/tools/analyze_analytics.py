#!/usr/bin/env python3
"""
Deep investigation into analytics records across sample and full dataset.
Answers Section A2 of Brief 3B.
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.loaders import DatasetLoader
from code.identity import IdentityResolver
DATASET_DIR = REPO_ROOT / "dataset"

def main():
    loader = DatasetLoader(DATASET_DIR)
    identities = loader.load_identities()
    audit_logs = loader.load_audit_log()
    resolver = IdentityResolver(identities, audit_logs)

    sample_reqs = loader.load_deletion_requests("sample_deletion_requests.csv")
    full_reqs = loader.load_deletion_requests("deletion_requests.csv")
    manifest = loader.load_evidence_manifest()

    print("=" * 60)
    print("ANALYTICS RECORDS INVESTIGATION (SECTION A2)")
    print("=" * 60)

    # 1. Inspect SQL databases
    sql_files = sorted((DATASET_DIR / "evidence" / "databases").glob("*.sql"))
    sql_analytics = []
    for sf in sql_files:
        fid = None
        for f_id, ef in manifest.items():
            if Path(ef.file_path).name == sf.name:
                fid = f_id
                break
        captured_dt = manifest[fid].captured_dt if fid else None

        conn = sqlite3.connect(":memory:")
        with open(sf, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_analytics_profiles';")
        if cur.fetchone():
            cur.execute("SELECT * FROM customer_analytics_profiles;")
            cols = [c[0] for c in cur.description]
            for row in cur.fetchall():
                d = dict(zip(cols, row))
                sql_analytics.append({
                    "source": "sql",
                    "file": sf.name,
                    "file_id": fid,
                    "captured_dt": captured_dt,
                    "data": d
                })

    print(f"[*] Found {len(sql_analytics)} total customer_analytics_profiles in SQL databases.")

    # 2. Inspect JSON evidence files
    json_analytics = []
    for jf in sorted((DATASET_DIR / "evidence" / "records").glob("*.json")):
        fid = None
        for f_id, ef in manifest.items():
            if Path(ef.file_path).name == jf.name:
                fid = f_id
                break
        captured_dt = manifest[fid].captured_dt if fid else None

        try:
            with open(jf, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception:
            continue

        # Check export format
        if "service_exports" in content and "analytics_platform" in content["service_exports"]:
            profiles = content["service_exports"]["analytics_platform"].get("profiles", [])
            for p in profiles:
                json_analytics.append({
                    "source": "json_service_export",
                    "file": jf.name,
                    "file_id": fid,
                    "captured_dt": captured_dt,
                    "data": p
                })
        # Check snapshot bundle format
        elif "snapshots" in content:
            for s in content["snapshots"]:
                if s.get("data_store") == "analytics_platform":
                    for r in s.get("records", []):
                        json_analytics.append({
                            "source": "json_snapshot_bundle",
                            "file": jf.name,
                            "file_id": fid,
                            "captured_dt": captured_dt,
                            "data": r
                        })
        # Check customer_analytics_report format
        elif "customer_analytics_report" in jf.name:
            for r in content.get("records", []):
                json_analytics.append({
                    "source": "json_analytics_report",
                    "file": jf.name,
                    "file_id": fid,
                    "captured_dt": captured_dt,
                    "data": r
                })

    print(f"[*] Found {len(json_analytics)} total analytics profiles in JSON files.")

    # 3. Inspect Log trace files
    log_analytics = []
    for lf in sorted((DATASET_DIR / "evidence" / "logs").glob("resource_lookup_trace_*.log")):
        fid = None
        for f_id, ef in manifest.items():
            if Path(ef.file_path).name == lf.name:
                fid = f_id
                break
        captured_dt = manifest[fid].captured_dt if fid else None

        with open(lf, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "service=analytics_platform" in line and "event=analytics_profile_read_completed" in line:
                    # extract fields
                    parts = line.strip().split()
                    d = {}
                    for p in parts:
                        if "=" in p:
                            k, v = p.split("=", 1)
                            d[k] = None if v == "null" else v
                    log_analytics.append({
                        "source": "log_trace",
                        "file": lf.name,
                        "file_id": fid,
                        "captured_dt": captured_dt,
                        "data": d,
                        "line": line.strip()
                    })

    print(f"[*] Found {len(log_analytics)} total analytics profiles in resource lookup trace logs.")

    all_analytics_evidence = sql_analytics + json_analytics + log_analytics
    print(f"[*] Total analytics records across all evidence: {len(all_analytics_evidence)}")

    # Load system activity for linking
    activities = loader.load_system_activity()

    def analyze_dataset_cases(requests_list, label="Full Dataset"):
        print(f"\n--- Analyzing Analytics for {label} ({len(requests_list)} cases) ---")
        cases_with_analytics = 0
        cases_anonymized = 0
        cases_exposed = 0
        cases_both = 0

        case_details = []

        for req in requests_list:
            ident = resolver.resolve(req.email)
            if not ident:
                continue

            audit_dt = req.audit_dt
            search_terms = {t.lower() for t in ident.all_search_terms() if t}

            # Find linked resource_ids from system activity up to audit_dt
            linked_res_ids = set()
            for act in activities:
                if act.event_dt <= audit_dt:
                    # check if activity matches user
                    if act.resource_id in search_terms or any(t in act.details.lower() for t in search_terms):
                        if "analytics" in act.resource_id or act.target_system == "analytics_platform":
                            linked_res_ids.add(act.resource_id)

            # Match analytics records
            matched_records = []
            for item in all_analytics_evidence:
                if item["captured_dt"] and item["captured_dt"] > audit_dt:
                    continue

                d = item["data"]
                res_id = d.get("resource_id") or ""
                
                # Check direct match on PII
                has_user_pii = False
                for val in [d.get("email"), d.get("phone"), d.get("customer_reference"), d.get("user_id"), d.get("email_hash"), d.get("requester_email")]:
                    if val and str(val).lower().strip() in search_terms:
                        has_user_pii = True
                        break

                # Check if linked by resource_id
                is_linked_resource = res_id in linked_res_ids

                if has_user_pii or is_linked_resource:
                    # Check if this record is anonymized or holds PII
                    direct_pii_present = bool(d.get("email") or d.get("phone") or d.get("customer_reference") or d.get("user_id") or d.get("email_hash"))
                    matched_records.append((item, direct_pii_present, res_id))

            if matched_records:
                cases_with_analytics += 1
                any_exposed = any(r[1] for r in matched_records)
                all_anon = all(not r[1] for r in matched_records)

                if all_anon:
                    cases_anonymized += 1
                elif any_exposed and not all_anon:
                    cases_both += 1
                else:
                    cases_exposed += 1

                case_details.append({
                    "case_id": req.case_id,
                    "reported_status": req.reported_status,
                    "records_count": len(matched_records),
                    "exposed_count": sum(1 for r in matched_records if r[1]),
                    "anonymized_count": sum(1 for r in matched_records if not r[1]),
                    "records": matched_records
                })

        print(f"Total cases with analytics records at audit_at: {cases_with_analytics}")
        print(f"  Cases with ONLY ANONYMIZED analytics records: {cases_anonymized}")
        print(f"  Cases with EXPOSED PII analytics records:     {cases_exposed + cases_both}")
        return case_details

    sample_res = analyze_dataset_cases(sample_reqs, "Sample (32 cases)")
    full_res = analyze_dataset_cases(full_reqs, "Full Run (518 cases)")

    # Inspect the cases in full run with analytics
    print(f"\n[*] Sample cases with analytics details:")
    for cd in sample_res:
        print(f"  {cd['case_id']} ({cd['reported_status']}): {cd['records_count']} records (anon={cd['anonymized_count']}, exposed={cd['exposed_count']})")

    print(f"\n[*] Full run cases with analytics details:")
    for cd in full_res:
        print(f"  {cd['case_id']} ({cd['reported_status']}): {cd['records_count']} records (anon={cd['anonymized_count']}, exposed={cd['exposed_count']})")

if __name__ == "__main__":
    main()
