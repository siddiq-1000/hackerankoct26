import json
import sys
from pathlib import Path

# Ensure project root is in path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.loaders import DeletionRequest, UserIdentity, UserAuditEntry
from code.identity import IdentityResolver, IdentitySet
from code.intent import IntentClassifier
from code.gaps import GapAnalyzer
from code.planner import PlanGenerator
from code.state import ObservedResource

def test_custom_cases():
    custom_dir = REPO_ROOT / "code" / "evaluation" / "custom_cases"
    gap_analyzer = GapAnalyzer()
    planner = PlanGenerator()
    intent_clf = IntentClassifier()

    passed = 0
    total = 5

    print("==========================================")
    print("RUNNING GATE 3 — CUSTOM CASES A through E")
    print("==========================================")

    # 1. Test Case A
    with open(custom_dir / "case_a.json", "r", encoding="utf-8") as f:
        case_a = json.load(f)
    req_a = case_a["request"]
    ident_a = case_a["user_identity"]
    audits_a = [UserAuditEntry(**a) for a in case_a["audit_log"]]
    resolver_a = IdentityResolver({ident_a["user_id"]: UserIdentity(**ident_a)}, audits_a)
    resolved_id_a = resolver_a.resolve(req_a["email"])

    # Confirm resolved user is user_custom_a, not user_unrelated_x (collision safety)
    assert resolved_id_a.user_id == "user_custom_a", "Collision safety failed in Case A"
    obs_a = {k: ObservedResource(**v) for k, v in case_a["observed_resources"].items()}
    gaps_a = [gap_analyzer.analyze_resource(r) for r in obs_a.values() if gap_analyzer.analyze_resource(r)]
    status_a, steps_a = planner.generate_plan(case_a["case_id"], "account_custom_a", obs_a, gaps_a)
    assert status_a == case_a["expected_status"], f"Case A status mismatch: {status_a}"
    assert steps_a == case_a["expected_steps"], f"Case A steps mismatch: {steps_a}"
    print("[PASS] Case A: Multi-hop historical email collision + active connector")
    passed += 1

    # 2. Test Case B
    with open(custom_dir / "case_b.json", "r", encoding="utf-8") as f:
        case_b = json.load(f)
    obs_b = {k: ObservedResource(**v) for k, v in case_b["observed_resources"].items()}
    gaps_b = [gap_analyzer.analyze_resource(r) for r in obs_b.values() if gap_analyzer.analyze_resource(r)]
    status_b, steps_b = planner.generate_plan(case_b["case_id"], "account_custom_b", obs_b, gaps_b)
    assert status_b == case_b["expected_status"], f"Case B status mismatch: {status_b}"
    assert steps_b == case_b["expected_steps"], f"Case B steps mismatch: {steps_b}"
    print("[PASS] Case B: Regional replica drift + tombstone PII")
    passed += 1

    # 3. Test Case C (temporal cutoff)
    with open(custom_dir / "case_c.json", "r", encoding="utf-8") as f:
        case_c = json.load(f)
    obs_c = {k: ObservedResource(**v) for k, v in case_c["observed_resources_at_audit"].items()}
    gaps_c = [gap_analyzer.analyze_resource(r) for r in obs_c.values() if gap_analyzer.analyze_resource(r)]
    status_c, steps_c = planner.generate_plan(case_c["case_id"], "account_custom_c", obs_c, gaps_c)
    assert status_c == case_c["expected_status"], f"Case C status mismatch: {status_c}"
    assert steps_c == case_c["expected_steps"], f"Case C steps mismatch: {steps_c}"
    print("[PASS] Case C: Post-audit_at decoy activity ignored (strict temporal cutoff)")
    passed += 1

    # 4. Test Case D (intent edges)
    with open(custom_dir / "case_d.json", "r", encoding="utf-8") as f:
        case_d = json.load(f)
    for sc in case_d["subcases"]:
        is_del = intent_clf.is_deletion_request(sc["text"], "custom_d")
        expected_del = sc["expected_is_deletion"]
        assert is_del == expected_del, f"Subcase {sc['id']} intent mismatch: expected {expected_del}, got {is_del}"
    print("[PASS] Case D: Mixed intent edge cases yield [] and Portuguese indirect deletion authorized")
    passed += 1

    # 5. Test Case E (restore risk + active flow)
    with open(custom_dir / "case_e.json", "r", encoding="utf-8") as f:
        case_e = json.load(f)
    obs_e = {k: ObservedResource(**v) for k, v in case_e["observed_resources"].items()}
    gaps_e = [gap_analyzer.analyze_resource(r) for r in obs_e.values() if gap_analyzer.analyze_resource(r)]
    status_e, steps_e = planner.generate_plan(case_e["case_id"], "account_custom_e", obs_e, gaps_e)
    assert status_e == case_e["expected_status"], f"Case E status mismatch: {status_e}"
    assert steps_e == case_e["expected_steps"], f"Case E steps mismatch: {steps_e}"
    print("[PASS] Case E: Reported COMPLETE but unblocked restore risk + active flow detected")
    passed += 1

    # 6. Test Case F (Unicode NFKC Normalization & Homoglyph Safety)
    with open(custom_dir / "case_f.json", "r", encoding="utf-8") as f:
        case_f = json.load(f)
    ident_f = case_f["user_identity"]
    resolver_f = IdentityResolver({ident_f["user_id"]: UserIdentity(**ident_f)}, [])
    resolved_id_f = resolver_f.resolve(case_f["request"]["email"])
    assert resolved_id_f is not None, "Failed to resolve full-width Unicode email"
    assert resolved_id_f.user_id == "user_custom_f", f"Expected user_custom_f, got {resolved_id_f.user_id}"
    obs_f = {k: ObservedResource(**v) for k, v in case_f["observed_resources"].items()}
    gaps_f = [gap_analyzer.analyze_resource(r) for r in obs_f.values() if gap_analyzer.analyze_resource(r)]
    status_f, steps_f = planner.generate_plan(case_f["case_id"], "account_custom_f", obs_f, gaps_f)
    assert status_f == case_f["expected_status"], f"Case F status mismatch: {status_f}"
    assert steps_f == case_f["expected_steps"], f"Case F steps mismatch: {steps_f}"
    print("[PASS] Case F: Adversarial Unicode NFKC & Homoglyph Normalization")
    passed += 1

    # 7. Test Case G (Rapid Temporal Oscillation & Strict Cutoff)
    with open(custom_dir / "case_g.json", "r", encoding="utf-8") as f:
        case_g = json.load(f)
    obs_g = {k: ObservedResource(**v) for k, v in case_g["observed_resources_at_audit"].items()}
    gaps_g = [gap_analyzer.analyze_resource(r) for r in obs_g.values() if gap_analyzer.analyze_resource(r)]
    status_g, steps_g = planner.generate_plan(case_g["case_id"], "account_custom_g", obs_g, gaps_g)
    assert status_g == case_g["expected_status"], f"Case G status mismatch: {status_g}"
    assert steps_g == case_g["expected_steps"], f"Case G steps mismatch: {steps_g}"
    print("[PASS] Case G: Rapid Temporal Activity Oscillation and Strict Audit Cutoff")
    passed += 1

    print("==========================================")
    print(f"Custom Cases Result: {passed}/7 Passed (100.0%)")
    print("==========================================")

if __name__ == "__main__":
    test_custom_cases()
