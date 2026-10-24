from dataclasses import dataclass
from typing import Dict, List, Optional
from code.state import ObservedResource

@dataclass
class PolicyGap:
    resource_id: str
    system_id: str
    category: str
    finding_op: str
    finding_state: str
    remediation_op: str
    remediation_state: str
    verification_op: str
    verification_state: str
    evidence_id: str

class GapAnalyzer:
    def analyze_resource(self, res: ObservedResource) -> Optional[PolicyGap]:
        sys_id = res.system_id
        res_id = res.resource_id
        cat = res.category
        obs = res.observed_state
        ev_id = res.evidence_id

        # 1. Integration Service / Data Flows
        if sys_id == "integration_service" or cat == "ACTIVE_DATA_FLOW":
            if obs == "ACTIVE_FLOW":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="integration_service",
                    category="ACTIVE_DATA_FLOW",
                    finding_op="REPORT_ACTIVE_DATA_FLOW",
                    finding_state="ACTIVE",
                    remediation_op="DISABLE_DATA_FLOW",
                    remediation_state="DISABLED",
                    verification_op="VERIFY_DATA_FLOW_DISABLED",
                    verification_state="DISABLED",
                    evidence_id=ev_id
                )

        # 2. Backup Service / Restore Risks
        elif sys_id == "backup_service" or cat == "BACKUP_ARCHIVE":
            if obs == "RESTORE_RISK":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="backup_service",
                    category="BACKUP_ARCHIVE",
                    finding_op="REPORT_RESTORE_RISK",
                    finding_state="ACTIVE",
                    remediation_op="BLOCK_RESTORE",
                    remediation_state="BLOCKED",
                    verification_op="VERIFY_RESTORE_BLOCKED",
                    verification_state="BLOCKED",
                    evidence_id=ev_id
                )

        # 3. Search Service
        elif sys_id == "search_service" or cat == "SEARCH_INDEX_ENTRY":
            if obs == "PRESENT":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="search_service",
                    category="SEARCH_INDEX_ENTRY",
                    finding_op="REPORT_REMAINING_RECORD",
                    finding_state="PRESENT",
                    remediation_op="DELETE_RECORD",
                    remediation_state="ABSENT",
                    verification_op="VERIFY_RECORD_ABSENT",
                    verification_state="ABSENT",
                    evidence_id=ev_id
                )

        # 4. Export Service
        elif sys_id == "export_service" or cat == "USER_EXPORT":
            if obs == "PRESENT":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="export_service",
                    category="USER_EXPORT",
                    finding_op="REPORT_REMAINING_RECORD",
                    finding_state="PRESENT",
                    remediation_op="DELETE_RECORD",
                    remediation_state="ABSENT",
                    verification_op="VERIFY_RECORD_ABSENT",
                    verification_state="ABSENT",
                    evidence_id=ev_id
                )

        # 5. Support Platform
        elif sys_id == "support_platform" or "support" in cat:
            if obs == "PRESENT":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="support_platform",
                    category=cat,
                    finding_op="REPORT_REMAINING_RECORD",
                    finding_state="PRESENT",
                    remediation_op="DELETE_RECORD",
                    remediation_state="ABSENT",
                    verification_op="VERIFY_RECORD_ABSENT",
                    verification_state="ABSENT",
                    evidence_id=ev_id
                )
            elif obs == "EXPOSED_PII":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="support_platform",
                    category=cat,
                    finding_op="REPORT_EXPOSED_PII",
                    finding_state="PRESENT",
                    remediation_op="REDACT_RECORD",
                    remediation_state="REDACTED",
                    verification_op="VERIFY_RECORD_REDACTED",
                    verification_state="REDACTED",
                    evidence_id=ev_id
                )

        # 6. Analytics Platform
        elif sys_id == "analytics_platform" or cat == "ANALYTICS_PROFILE":
            if obs == "PRESENT":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="analytics_platform",
                    category="ANALYTICS_PROFILE",
                    finding_op="REPORT_REMAINING_RECORD",
                    finding_state="PRESENT",
                    remediation_op="DELETE_RECORD",
                    remediation_state="ABSENT",
                    verification_op="VERIFY_RECORD_ABSENT",
                    verification_state="ABSENT",
                    evidence_id=ev_id
                )
            elif obs == "EXPOSED_PII":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="analytics_platform",
                    category="ANALYTICS_PROFILE",
                    finding_op="REPORT_EXPOSED_PII",
                    finding_state="PRESENT",
                    remediation_op="ANONYMIZE_RECORD",
                    remediation_state="ANONYMIZED",
                    verification_op="VERIFY_RECORD_ANONYMIZED",
                    verification_state="ANONYMIZED",
                    evidence_id=ev_id
                )

        # 7. Identity Service / Account Tombstone
        elif sys_id == "identity_service" or cat == "ACCOUNT_TOMBSTONE":
            if obs in ["EXPOSED_PII", "PRESENT"]:
                return PolicyGap(
                    resource_id=res_id,
                    system_id="identity_service",
                    category="ACCOUNT_TOMBSTONE",
                    finding_op="REPORT_EXPOSED_PII",
                    finding_state="PRESENT",
                    remediation_op="REDACT_RECORD",
                    remediation_state="REDACTED",
                    verification_op="VERIFY_RECORD_REDACTED",
                    verification_state="REDACTED",
                    evidence_id=ev_id
                )

        # 8. Account Service
        elif sys_id == "account_service":
            if obs == "PRESENT":
                return PolicyGap(
                    resource_id=res_id,
                    system_id="account_service",
                    category="USER_PROFILE",
                    finding_op="REPORT_REMAINING_RECORD",
                    finding_state="PRESENT",
                    remediation_op="DELETE_RECORD",
                    remediation_state="ABSENT",
                    verification_op="VERIFY_RECORD_ABSENT",
                    verification_state="ABSENT",
                    evidence_id=ev_id
                )

        return None
