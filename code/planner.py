import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from code.state import ObservedResource
from code.gaps import PolicyGap

PHASE_RANK = {
    "FINDING": 1,
    "REMEDIATION": 2,
    "VERIFICATION": 3
}

OP_RANK = {
    # Finding
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,

    # Remediation
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,

    # Verification
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6
}

def canonical_step_sort_key(step: dict) -> Tuple[int, int, str, str]:
    p_rank = PHASE_RANK.get(step["phase"], 99)
    o_rank = OP_RANK.get(step["operation"], 99)
    sys_id = step.get("system_id", "")
    res_id = step.get("resource_id", "")
    return (p_rank, o_rank, sys_id, res_id)

class PlanGenerator:
    def generate_plan(
        self,
        case_id: str,
        account_id: str,
        observed: Dict[str, ObservedResource],
        gaps: List[PolicyGap]
    ) -> Tuple[str, List[dict]]:
        raw_steps = []

        if gaps:
            deletion_status = "INCOMPLETE"
            # 1. Findings
            for g in gaps:
                raw_steps.append({
                    "phase": "FINDING",
                    "system_id": g.system_id,
                    "resource_id": g.resource_id,
                    "operation": g.finding_op,
                    "state": g.finding_state,
                    "evidence_id": g.evidence_id
                })

            # 2. Remediation
            for g in gaps:
                raw_steps.append({
                    "phase": "REMEDIATION",
                    "system_id": g.system_id,
                    "resource_id": g.resource_id,
                    "operation": g.remediation_op,
                    "state": g.remediation_state,
                    "evidence_id": ""
                })

            # 3. Verification
            # Remediated resources
            verified_resources = set()
            for g in gaps:
                raw_steps.append({
                    "phase": "VERIFICATION",
                    "system_id": g.system_id,
                    "resource_id": g.resource_id,
                    "operation": g.verification_op,
                    "state": g.verification_state,
                    "evidence_id": ""
                })
                verified_resources.add((g.system_id, g.resource_id))

            # Mandatory account verification if not already verified
            if ("account_service", account_id) not in verified_resources:
                raw_steps.append({
                    "phase": "VERIFICATION",
                    "system_id": "account_service",
                    "resource_id": account_id,
                    "operation": "VERIFY_RECORD_ABSENT",
                    "state": "ABSENT",
                    "evidence_id": ""
                })

            # Mandatory security audit log verification if security record exists
            for res_id, res in observed.items():
                if res.system_id == "security_service" and ("security_service", res_id) not in verified_resources:
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": "security_service",
                        "resource_id": res_id,
                        "operation": "VERIFY_RECORD_PRESENT",
                        "state": "PRESENT",
                        "evidence_id": ""
                    })

        else:
            deletion_status = "COMPLETE"
            # Only verification steps with evidence_id citing the evidence
            seen_verifs = set()
            for res_id, res in observed.items():
                pair = (res.system_id, res.resource_id)
                if pair in seen_verifs:
                    continue

                if res.system_id == "account_service" and res.observed_state == "ABSENT":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

                elif res.system_id == "security_service" and res.observed_state == "PRESENT":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_RECORD_PRESENT",
                        "state": "PRESENT",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

                elif res.system_id == "identity_service" and res.observed_state == "REDACTED":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_RECORD_REDACTED",
                        "state": "REDACTED",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

                elif res.system_id == "analytics_platform" and res.observed_state == "ANONYMIZED":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_RECORD_ANONYMIZED",
                        "state": "ANONYMIZED",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

                elif res.system_id == "support_platform" and res.observed_state == "REDACTED":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_RECORD_REDACTED",
                        "state": "REDACTED",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

                elif res.system_id == "integration_service" and res.observed_state == "DISABLED":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_DATA_FLOW_DISABLED",
                        "state": "DISABLED",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

                elif res.system_id == "backup_service" and res.observed_state == "BLOCKED":
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": "VERIFY_RESTORE_BLOCKED",
                        "state": "BLOCKED",
                        "evidence_id": res.evidence_id
                    })
                    seen_verifs.add(pair)

        # Sort canonically
        raw_steps.sort(key=canonical_step_sort_key)

        # Assign consecutive step numbers starting from 1
        final_steps = []
        for i, s in enumerate(raw_steps, 1):
            final_steps.append({
                "step_no": i,
                "phase": s["phase"],
                "system_id": s["system_id"],
                "resource_id": s["resource_id"],
                "operation": s["operation"],
                "state": s["state"],
                "evidence_id": s["evidence_id"]
            })

        return deletion_status, final_steps
