import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.config import DATASET_DIR, OUTPUT_CSV_PATH
from code.loaders import DatasetLoader, DeletionRequest
from code.identity import IdentityResolver
from code.intent import IntentClassifier
from code.state import StateReconstructor
from code.gaps import GapAnalyzer
from code.planner import PlanGenerator
from code.validate import validate_csv
from code.usage import global_usage_ledger

def run_deletion_audit(
    dataset_dir: Path = DATASET_DIR,
    output_path: Path = OUTPUT_CSV_PATH,
    filename: str = "deletion_requests.csv"
) -> Tuple[int, Dict[str, int]]:
    import code.config as cfg
    cfg.DATASET_DIR = Path(dataset_dir).resolve()
    cfg.EVIDENCE_DIR = cfg.DATASET_DIR / "evidence"
    os.environ["DATASET_DIR"] = str(cfg.DATASET_DIR)

    print(f"[*] Starting Ghost Data Still Exists deletion audit pipeline...")
    print(f"[*] Dataset: {dataset_dir / filename}")
    print(f"[*] Destination: {output_path}")

    loader = DatasetLoader(dataset_dir)
    requests = loader.load_deletion_requests(filename)
    print(f"[*] Loaded {len(requests)} deletion requests.")

    # Sort requests strictly by case_id ascending (lexicographical string sort)
    requests.sort(key=lambda r: r.case_id)

    identities = loader.load_identities()
    audit_logs = loader.load_audit_log()
    resolver = IdentityResolver(identities, audit_logs)
    intent_clf = IntentClassifier()
    state_recon = StateReconstructor(loader=loader)
    gap_analyzer = GapAnalyzer()
    planner = PlanGenerator()

    counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
    output_rows = []

    for idx, req in enumerate(requests, 1):
        if idx % 50 == 0 or idx == len(requests):
            print(f"[*] Processed {idx}/{len(requests)} cases...")

        # 1. Intent Check
        if not intent_clf.is_deletion_request(req.request_text, req.case_id):
            status = "NOT_APPLICABLE"
            steps = []
        else:
            # 2. Identity Resolution
            ident = resolver.resolve(req.email)
            if not ident:
                # Fallback if email has no identity profile
                account_id = f"account_{req.case_id.split('_')[1]}"
                observed = {}
                gaps = []
            else:
                account_id = state_recon.find_user_account_id(ident, req.audit_dt)
                observed = state_recon.reconstruct_state(req, ident)
                gaps = []
                for res_id, res in observed.items():
                    gap = gap_analyzer.analyze_resource(res)
                    if gap:
                        gaps.append(gap)

            # 3. Planning & canonical step ordering
            status, steps = planner.generate_plan(req.case_id, account_id, observed, gaps)

        counts[status] = counts.get(status, 0) + 1
        output_rows.append({
            "case_id": req.case_id,
            "deletion_status": status,
            "steps_json": json.dumps(steps, separators=(",", ":"))
        })

    # 4. Optional compliant analytics linking for COMPLETE cases (Brief 3D Option A)
    from code.config import LINK_NULL_IDENTIFIER_ANALYTICS
    if LINK_NULL_IDENTIFIER_ANALYTICS:
        from code.analytics_linker import AnalyticsLinker
        complete_reqs = [
            {"case_id": r.case_id, "email": r.email, "reported_at": r.reported_at, "audit_at": r.audit_at}
            for r, row in zip(requests, output_rows)
            if row["deletion_status"] == "COMPLETE"
        ]
        linker = AnalyticsLinker(dataset_dir)
        pairs = linker.build_batch_pairs(complete_reqs)
        for row in output_rows:
            cid = row["case_id"]
            if cid in pairs:
                rid, fid = pairs[cid]
                steps = json.loads(row["steps_json"])
                has_s = any(s.get("system_id") == "analytics_platform" for s in steps)
                if not has_s:
                    steps.append({
                        "step_no": len(steps) + 1,
                        "phase": "VERIFICATION",
                        "system_id": "analytics_platform",
                        "resource_id": rid,
                        "operation": "VERIFY_RECORD_ANONYMIZED",
                        "state": "ANONYMIZED",
                        "evidence_id": fid
                    })
                    sys_priority = {
                        "account_service": 1,
                        "security_service": 2,
                        "support_platform": 3,
                        "analytics_platform": 4,
                        "integration_service": 5,
                        "backup_service": 6,
                        "identity_service": 7
                    }
                    steps.sort(key=lambda s: sys_priority.get(s["system_id"], 99))
                    for i, s in enumerate(steps, 1):
                        s["step_no"] = i
                    row["steps_json"] = json.dumps(steps, separators=(",", ":"))

    # Write output.csv with exact headers and UTF-8 encoding
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"[+] Successfully wrote {len(output_rows)} rows to {output_path}")
    print(f"[+] Status distribution: {counts}")

    # Validate generated CSV
    errs = validate_csv(output_path, expected_rows=len(requests))
    if errs:
        print(f"[!] Validation FAILED with {len(errs)} errors:")
        for e in errs[:10]:
            print(f"    - {e}")
        raise ValueError(f"Output validation failed with {len(errs)} errors")
    else:
        print(f"[+] Validation PASSED: 0 errors across {len(output_rows)} rows.")

    return len(output_rows), counts

def main():
    parser = argparse.ArgumentParser(description="Ghost Data Still Exists Deletion Audit Agent")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR, help="Path to dataset directory")
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV_PATH, help="Path to output CSV")
    parser.add_argument("--input-file", type=str, default="deletion_requests.csv", help="Input deletion requests file")
    args = parser.parse_args()

    run_deletion_audit(
        dataset_dir=args.dataset_dir,
        output_path=args.output,
        filename=args.input_file
    )

if __name__ == "__main__":
    main()
