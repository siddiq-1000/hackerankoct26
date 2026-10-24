import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Ensure project root is in path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.loaders import DatasetLoader, DeletionRequest
from code.identity import IdentityResolver
from code.intent import IntentClassifier
from code.state import StateReconstructor
from code.gaps import GapAnalyzer
from code.planner import PlanGenerator
from code.validate import validate_row

def evaluate_predictions(
    predictions: Dict[str, Tuple[str, List[dict]]],
    ground_truth: Dict[str, Tuple[str, List[dict]]]
) -> Dict[str, Any]:
    total_cases = len(ground_truth)
    status_matches = 0
    row_matches = 0
    total_expected_steps = 0
    total_predicted_steps = 0
    matched_steps = 0
    field_matches = 0
    total_fields = 0
    sequence_matches = 0

    fields_to_check = ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

    mismatches = []

    for cid, (exp_status, exp_steps) in ground_truth.items():
        if cid not in predictions:
            mismatches.append({"case_id": cid, "error": "Missing prediction"})
            continue

        pred_status, pred_steps = predictions[cid]

        # 1. Status Accuracy
        status_correct = (pred_status == exp_status)
        if status_correct:
            status_matches += 1

        # 2. Row Accuracy (exact match of status and steps)
        row_correct = (pred_status == exp_status and pred_steps == exp_steps)
        if row_correct:
            row_matches += 1

        # 3. Sequence Accuracy (sequence of (phase, operation, system_id, resource_id) matches)
        exp_seq = [(s["phase"], s["operation"], s["system_id"], s["resource_id"]) for s in exp_steps]
        pred_seq = [(s["phase"], s["operation"], s["system_id"], s["resource_id"]) for s in pred_steps]
        seq_correct = (exp_seq == pred_seq)
        if seq_correct:
            sequence_matches += 1

        # 4. Step-level and Field-level Accuracy
        total_expected_steps += len(exp_steps)
        total_predicted_steps += len(pred_steps)

        # Compare step by step up to min length
        min_len = min(len(exp_steps), len(pred_steps))
        for i in range(min_len):
            es = exp_steps[i]
            ps = pred_steps[i]
            step_field_matches = 0
            for f in fields_to_check:
                total_fields += 1
                if es.get(f) == ps.get(f):
                    field_matches += 1
                    step_field_matches += 1
            if step_field_matches == len(fields_to_check):
                matched_steps += 1

        # Account for missing / extra steps in field counts
        diff_len = abs(len(exp_steps) - len(pred_steps))
        total_fields += diff_len * len(fields_to_check)

        if not row_correct:
            mismatches.append({
                "case_id": cid,
                "expected_status": exp_status,
                "pred_status": pred_status,
                "expected_steps_count": len(exp_steps),
                "pred_steps_count": len(pred_steps)
            })

    metrics = {
        "total_cases": total_cases,
        "status_accuracy": status_matches / total_cases if total_cases else 0.0,
        "row_accuracy": row_matches / total_cases if total_cases else 0.0,
        "sequence_accuracy": sequence_matches / total_cases if total_cases else 0.0,
        "step_accuracy": matched_steps / total_expected_steps if total_expected_steps else 1.0,
        "field_accuracy": field_matches / total_fields if total_fields else 1.0,
        "status_matches": status_matches,
        "row_matches": row_matches,
        "sequence_matches": sequence_matches,
        "total_expected_steps": total_expected_steps,
        "total_predicted_steps": total_predicted_steps,
        "matched_steps": matched_steps,
        "mismatches": mismatches
    }

    return metrics

def run_sample_evaluation() -> Dict[str, Any]:
    loader = DatasetLoader()
    sample_reqs = loader.load_deletion_requests("sample_deletion_requests.csv")
    identities = loader.load_identities()
    audit_logs = loader.load_audit_log()
    resolver = IdentityResolver(identities, audit_logs)
    intent_clf = IntentClassifier()
    state_recon = StateReconstructor(loader=loader)
    gap_analyzer = GapAnalyzer()
    planner = PlanGenerator()

    # Load ground truth
    with open(REPO_ROOT / "dataset" / "sample_output.csv", "r", encoding="utf-8") as f:
        ground_truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

    predictions = {}
    for req in sample_reqs:
        # 1. Intent Check
        if not intent_clf.is_deletion_request(req.request_text, req.case_id):
            pred_status = "NOT_APPLICABLE"
            pred_steps = []
        else:
            # 2. Identity Resolution
            ident = resolver.resolve(req.email)
            account_id = state_recon.find_user_account_id(ident, req.audit_dt)

            # 3. State Reconstruction
            observed = state_recon.reconstruct_state(req, ident)

            # 4. Gap Analysis
            gaps = []
            for res_id, res in observed.items():
                gap = gap_analyzer.analyze_resource(res)
                if gap:
                    gaps.append(gap)

            # 5. Planning
            pred_status, pred_steps = planner.generate_plan(req.case_id, account_id, observed, gaps)

        predictions[req.case_id] = (pred_status, pred_steps)

    metrics = evaluate_predictions(predictions, ground_truth)
    return metrics

if __name__ == "__main__":
    metrics = run_sample_evaluation()
    print("==========================================")
    print("HACKERRANK ORCHESTRATE — GATE 2 SAMPLE EVALUATION")
    print("==========================================")
    print(f"Total Sample Cases:     {metrics['total_cases']}")
    print(f"Status Accuracy:        {metrics['status_accuracy']*100:.2f}% ({metrics['status_matches']}/{metrics['total_cases']})")
    print(f"Row Accuracy:           {metrics['row_accuracy']*100:.2f}% ({metrics['row_matches']}/{metrics['total_cases']})")
    print(f"Sequence Accuracy:      {metrics['sequence_accuracy']*100:.2f}% ({metrics['sequence_matches']}/{metrics['total_cases']})")
    print(f"Step-Level Accuracy:    {metrics['step_accuracy']*100:.2f}% ({metrics['matched_steps']}/{metrics['total_expected_steps']})")
    print(f"Field-Level Accuracy:   {metrics['field_accuracy']*100:.2f}%")
    print("==========================================")
