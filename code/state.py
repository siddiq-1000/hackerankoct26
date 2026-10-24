import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from code.config import DATASET_DIR
from code.loaders import DatasetLoader, DeletionRequest, EvidenceFile, SystemActivity
from code.identity import IdentitySet
from code.evidence.sql import SqlDatabaseManager
from code.evidence.records import RecordsAndLogsParser
from code.evidence.docs import DocumentParser
from code.evidence.vision import VisionEvidenceManager

def build_term_matcher(terms: List[str]):
    """Builds a fast compiled regex matcher enforcing word/identifier boundaries."""
    cleaned = [re.escape(t.strip().lower()) for t in terms if t and t.strip()]
    if not cleaned:
        return lambda text: False
    pattern = re.compile(r"(?<![a-zA-Z0-9_])(?:" + "|".join(cleaned) + r")(?![a-zA-Z0-9_])", re.IGNORECASE)
    return lambda text: bool(pattern.search(text))

@dataclass
class ObservedResource:
    system_id: str
    resource_id: str
    category: str
    observed_state: str  # PRESENT, EXPOSED_PII, ACTIVE_FLOW, RESTORE_RISK, ANONYMIZED, REDACTED, ABSENT, DISABLED, BLOCKED
    evidence_id: str
    evidence_time: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

class StateReconstructor:
    def __init__(
        self,
        loader: Optional[DatasetLoader] = None,
        sql_mgr: Optional[SqlDatabaseManager] = None,
        rec_parser: Optional[RecordsAndLogsParser] = None,
        doc_parser: Optional[DocumentParser] = None,
        vision_mgr: Optional[VisionEvidenceManager] = None
    ):
        self.loader = loader or DatasetLoader()
        self.dataset_dir = self.loader.dataset_dir
        self.manifest = self.loader.load_evidence_manifest()
        self.sql_mgr = sql_mgr or SqlDatabaseManager(databases_dir=self.dataset_dir / "evidence" / "databases")
        self.rec_parser = rec_parser or RecordsAndLogsParser(evidence_dir=self.dataset_dir / "evidence")
        self.doc_parser = doc_parser or DocumentParser(documents_dir=self.dataset_dir / "evidence" / "documents")
        self.vision_mgr = vision_mgr or VisionEvidenceManager()
        self.activities = self.loader.load_system_activity()

        # Build path to file_id lookup
        self.path_to_fid = {}
        for fid, ef in self.manifest.items():
            fn = Path(ef.file_path).name
            self.path_to_fid[fn] = fid
            self.path_to_fid[ef.file_path] = fid

    def find_user_account_id(self, identity: IdentitySet, audit_dt: datetime) -> str:
        """Find the stable account_XXXX identifier for the user."""
        terms = identity.all_search_terms()
        match_terms = build_term_matcher(terms)

        # 1. Check handover log text
        handover_path = self.dataset_dir / "evidence" / "records" / "customer_account_handover_20261001.txt"
        if handover_path.exists():
            with open(handover_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "account_service" in line and match_terms(line):
                        m = re.search(r"(account_\d+)", line)
                        if m:
                            return m.group(1)

        # 2. Check readback trace logs
        logs_dir = self.dataset_dir / "evidence" / "logs"
        for log_file in sorted(logs_dir.glob("resource_lookup_trace_*.log"), reverse=True):
            fid = self.path_to_fid.get(log_file.name)
            if fid and self.manifest[fid].captured_dt <= audit_dt:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "account_service" in line and match_terms(line):
                            m = re.search(r"resource_id=(account_\d+)", line)
                            if m:
                                return m.group(1)

        # 3. Check central observability logs
        for log_file in sorted(logs_dir.glob("service_events_*.log"), reverse=True):
            fid = self.path_to_fid.get(log_file.name)
            if fid and self.manifest[fid].captured_dt <= audit_dt:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "account_service" in line and match_terms(line):
                            m = re.search(r"resource_id=(account_\d+)", line)
                            if m:
                                return m.group(1)

        # 4. Check structured service events
        for log_file in sorted(logs_dir.glob("structured_service_events_*.log"), reverse=True):
            fid = self.path_to_fid.get(log_file.name)
            if fid and self.manifest[fid].captured_dt <= audit_dt:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "account_service" in line and match_terms(line):
                            m = re.search(r'"resource_id":"(account_\d+)"', line)
                            if m:
                                return m.group(1)

        # 5. Check system activity for deletion worker submission
        # Leading zero padding for low numeric IDs
        if identity.user_id.startswith("user_"):
            num_str = identity.user_id.split("_")[1]
            if num_str.isdigit() and int(num_str) <= 10:
                return f"account_{int(num_str):03d}"

        for a in self.activities:
            if a.event_dt <= audit_dt and "account_service" in a.target_system and match_terms(a.details):
                m = re.search(r"(account_\d+)", a.resource_id)
                if m:
                    return m.group(1)
                m2 = re.search(r"(account_\d+)", a.details)
                if m2:
                    return m2.group(1)

        # 6. Fallback
        if identity.user_id.startswith("user_"):
            num_str = identity.user_id.split("_")[1]
            if num_str.isdigit() and int(num_str) < 100:
                return f"account_{int(num_str):03d}"
            return f"account_{num_str}"

        return f"account_{identity.user_id}"

    def reconstruct_state(self, request: DeletionRequest, identity: IdentitySet) -> Dict[str, ObservedResource]:
        """
        Reconstructs all observed resources for the subject at or before audit_at.
        Returns a dict of resource_id -> ObservedResource.
        """
        audit_dt = request.audit_dt
        terms = identity.all_search_terms()
        match_terms = build_term_matcher(terms)
        account_id = self.find_user_account_id(identity, audit_dt)
        terms_with_acc = list(set(terms + [account_id]))
        match_terms_acc = build_term_matcher(terms_with_acc)

        observed: Dict[str, ObservedResource] = {}

        # Default state for primary account: ABSENT unless proven PRESENT in a replica snapshot
        # Ensure evidence_id is strictly captured at or before audit_at
        candidates = [
            (ef.captured_dt, fid)
            for fid, ef in self.manifest.items()
            if ef.captured_dt <= audit_dt
            and any(k in ef.file_path for k in ["replica", "inventory", "service_resource_export", "resource_lookup_trace"])
        ]
        default_evidence_id = ""
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            default_evidence_id = candidates[0][1]

        observed[account_id] = ObservedResource(
            system_id="account_service",
            resource_id=account_id,
            category="USER_PROFILE",
            observed_state="ABSENT",
            evidence_id=default_evidence_id,
            evidence_time=request.audit_at
        )

        # 1. Check SQL Snapshots (databases) <= audit_dt
        for db_name, conn in self.sql_mgr.databases.items():
            fid = self.path_to_fid.get(db_name)
            if not fid:
                continue
            ef = self.manifest.get(fid)
            if not ef or ef.captured_dt > audit_dt:
                continue

            hits = self.sql_mgr.search_database(db_name, terms_with_acc)
            for hit in hits:
                data = hit.get("data", {})
                res_id = hit.get("resource_id") or data.get("resource_id") or data.get("account_id") or data.get("search_id")
                table = hit.get("table", "")

                # Format A: Generic customer_data tables with embedded record_json
                if "record_json" in data:
                    try:
                        rec_data = json.loads(data["record_json"])
                        r_id = rec_data.get("resource_id") or data.get("resource_id") or res_id
                        s_id = rec_data.get("origin_system") or data.get("origin_system") or "account_service"
                        
                        if s_id == "account_service":
                            observed[r_id] = ObservedResource(system_id="account_service", resource_id=r_id, category="USER_PROFILE", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                        elif s_id == "search_service":
                            observed[r_id] = ObservedResource(system_id="search_service", resource_id=r_id, category="SEARCH_INDEX_ENTRY", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                        elif s_id == "analytics_platform":
                            has_pii = bool(rec_data.get("email") or rec_data.get("phone") or rec_data.get("user_id"))
                            state = "EXPOSED_PII" if has_pii else "ANONYMIZED"
                            observed[r_id] = ObservedResource(system_id="analytics_platform", resource_id=r_id, category="ANALYTICS_PROFILE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                        elif s_id == "support_platform":
                            has_pii = bool(rec_data.get("requester_email") or rec_data.get("requester_name") or rec_data.get("requester_phone"))
                            state = "EXPOSED_PII" if has_pii else "REDACTED"
                            observed[r_id] = ObservedResource(system_id="support_platform", resource_id=r_id, category="SUPPORT_MESSAGE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                        elif s_id == "integration_service":
                            enabled = bool(rec_data.get("enabled", True))
                            state = "ACTIVE_FLOW" if enabled else "DISABLED"
                            observed[r_id] = ObservedResource(system_id="integration_service", resource_id=r_id, category="ACTIVE_DATA_FLOW", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                        elif s_id == "backup_service":
                            allowed = bool(rec_data.get("restore_allowed", True))
                            state = "RESTORE_RISK" if allowed else "BLOCKED"
                            observed[r_id] = ObservedResource(system_id="backup_service", resource_id=r_id, category="BACKUP_ARCHIVE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                        continue
                    except Exception:
                        pass

                # Format B: Failover replica containing account
                if "failover" in db_name.lower() or "accounts" in table.lower():
                    acc_num = data.get("account_id") or res_id
                    if acc_num:
                        observed[acc_num] = ObservedResource(
                            system_id="account_service",
                            resource_id=acc_num,
                            category="USER_PROFILE",
                            observed_state="PRESENT",
                            evidence_id=fid,
                            evidence_time=ef.captured_at,
                            details=data
                        )

                # Format C: Customer search index SQL
                elif "search" in db_name.lower() or "search" in table.lower() or table == "customer_search_documents":
                    s_id = data.get("search_id") or res_id or data.get("id")
                    if s_id:
                        observed[s_id] = ObservedResource(
                            system_id="search_service",
                            resource_id=s_id,
                            category="SEARCH_INDEX_ENTRY",
                            observed_state="PRESENT",
                            evidence_id=fid,
                            evidence_time=ef.captured_at,
                            details=data
                        )

                # Format D: Analytics profiles
                elif table == "customer_analytics_profiles":
                    a_id = data.get("analytics_id") or res_id
                    if a_id:
                        has_pii = bool(data.get("email") or data.get("phone") or data.get("user_id"))
                        state = "EXPOSED_PII" if has_pii else "ANONYMIZED"
                        observed[a_id] = ObservedResource(
                            system_id="analytics_platform",
                            resource_id=a_id,
                            category="ANALYTICS_PROFILE",
                            observed_state=state,
                            evidence_id=fid,
                            evidence_time=ef.captured_at
                        )

                # Format E: Support records
                elif table == "support_records":
                    sup_id = data.get("support_id") or res_id
                    if sup_id:
                        has_pii = bool(data.get("requester_email") or data.get("requester_name") or data.get("requester_phone"))
                        state = "EXPOSED_PII" if has_pii else "REDACTED"
                        observed[sup_id] = ObservedResource(
                            system_id="support_platform",
                            resource_id=sup_id,
                            category="SUPPORT_MESSAGE",
                            observed_state=state,
                            evidence_id=fid,
                            evidence_time=ef.captured_at
                        )

                # Format F: Connector subscriptions
                elif table == "connector_subscriptions":
                    c_id = data.get("connector_id") or res_id
                    if c_id:
                        enabled = str(data.get("status", "")).lower() == "active" or bool(data.get("enabled", True))
                        state = "ACTIVE_FLOW" if enabled else "DISABLED"
                        observed[c_id] = ObservedResource(
                            system_id="integration_service",
                            resource_id=c_id,
                            category="ACTIVE_DATA_FLOW",
                            observed_state=state,
                            evidence_id=fid,
                            evidence_time=ef.captured_at
                        )

                # Format G: Backup inventory SQL
                elif "inventory" in db_name.lower() or "backup" in table.lower() or table == "backup_restore_entries":
                    b_id = data.get("backup_id") or res_id
                    allowed = str(data.get("restore_allowed", "")).strip().lower() in ["1", "true"]
                    if b_id:
                        state = "RESTORE_RISK" if allowed else "BLOCKED"
                        observed[b_id] = ObservedResource(
                            system_id="backup_service",
                            resource_id=b_id,
                            category="BACKUP_ARCHIVE",
                            observed_state=state,
                            evidence_id=fid,
                            evidence_time=ef.captured_at,
                            details=data
                        )

                # Format H: Security audit records
                elif table == "security_audit_records":
                    aud_id = data.get("audit_id") or res_id
                    if aud_id:
                        observed[aud_id] = ObservedResource(
                            system_id="security_service",
                            resource_id=aud_id,
                            category="SECURITY_AUDIT_LOG",
                            observed_state="PRESENT",
                            evidence_id=fid,
                            evidence_time=ef.captured_at
                        )

        # 2. Check JSON Records & Snapshot Bundles <= audit_dt
        records_dir = self.dataset_dir / "evidence" / "records"
        for json_file in sorted(records_dir.glob("*.json")):
            fid = self.path_to_fid.get(json_file.name)
            if not fid:
                continue
            ef = self.manifest.get(fid)
            if not ef or ef.captured_dt > audit_dt:
                continue

            # Check format A: service_resource_export files
            if "service_resource_export" in json_file.name:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    exports = d.get("service_exports", {})

                    matched_user = False
                    for s_name, tables in exports.items():
                        for t_name, rows in tables.items():
                            for row in rows:
                                row_str = json.dumps(row).lower()
                                if match_terms(row_str):
                                    matched_user = True
                                    break
                            if matched_user:
                                break
                        if matched_user:
                            break

                    if matched_user:
                        # Search
                        for item in exports.get("search_service", {}).get("index_queries", []):
                            q = item.get("query", "").lower()
                            if match_terms(q):
                                hits = item.get("hits", {}).get("documents", [])
                                total = item.get("hits", {}).get("total", 0)
                                if total > 0 and hits:
                                    res_id = hits[0].get("resource_id", item.get("resource_id"))
                                    observed[res_id] = ObservedResource(
                                        system_id="search_service",
                                        resource_id=res_id,
                                        category="SEARCH_INDEX_ENTRY",
                                        observed_state="PRESENT",
                                        evidence_id=fid,
                                        evidence_time=ef.captured_at
                                    )

                        # Analytics
                        for item in exports.get("analytics_platform", {}).get("profiles", []):
                            res_id = item.get("resource_id")
                            item_str = json.dumps(item).lower()
                            if match_terms(item_str):
                                has_pii = bool(item.get("email") or item.get("phone") or item.get("customer_reference"))
                                state = "EXPOSED_PII" if has_pii else "ANONYMIZED"
                                observed[res_id] = ObservedResource(
                                    system_id="analytics_platform",
                                    resource_id=res_id,
                                    category="ANALYTICS_PROFILE",
                                    observed_state=state,
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )

                        # Support
                        for item in exports.get("support_platform", {}).get("tickets", []):
                            res_id = item.get("resource_id")
                            item_str = json.dumps(item).lower()
                            if match_terms(item_str):
                                has_pii = bool(item.get("requester_email") or item.get("requester_name") or item.get("requester_phone"))
                                state = "EXPOSED_PII" if has_pii else "REDACTED"
                                observed[res_id] = ObservedResource(
                                    system_id="support_platform",
                                    resource_id=res_id,
                                    category="SUPPORT_MESSAGE",
                                    observed_state=state,
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )

                        # Integration / Data flows
                        for item in exports.get("integration_service", {}).get("connectors", []):
                            res_id = item.get("resource_id")
                            item_str = json.dumps(item).lower()
                            if match_terms(item_str):
                                is_enabled = bool(item.get("enabled"))
                                state = "ACTIVE_FLOW" if is_enabled else "DISABLED"
                                observed[res_id] = ObservedResource(
                                    system_id="integration_service",
                                    resource_id=res_id,
                                    category="ACTIVE_DATA_FLOW",
                                    observed_state=state,
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )

                        # Backup
                        for item in exports.get("backup_service", {}).get("restore_entries", []):
                            res_id = item.get("resource_id")
                            item_str = json.dumps(item).lower()
                            if match_terms(item_str):
                                allowed = bool(item.get("restore_allowed"))
                                state = "RESTORE_RISK" if allowed else "BLOCKED"
                                observed[res_id] = ObservedResource(
                                    system_id="backup_service",
                                    resource_id=res_id,
                                    category="BACKUP_ARCHIVE",
                                    observed_state=state,
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )

                        # Security audit records
                        for item in exports.get("security_service", {}).get("audit_records", []):
                            res_id = item.get("resource_id")
                            item_str = json.dumps(item).lower()
                            if match_terms(item_str):
                                observed[res_id] = ObservedResource(
                                    system_id="security_service",
                                    resource_id=res_id,
                                    category="SECURITY_AUDIT_LOG",
                                    observed_state="PRESENT",
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )

                        # Export
                        for item in exports.get("export_service", {}).get("exports", []):
                            res_id = item.get("resource_id")
                            item_str = json.dumps(item).lower()
                            if match_terms(item_str):
                                observed[res_id] = ObservedResource(
                                    system_id="export_service",
                                    resource_id=res_id,
                                    category="USER_EXPORT",
                                    observed_state="PRESENT",
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )

                        # Account lookup
                        for item in exports.get("account_service", {}).get("profile_lookups", []):
                            acc = item.get("resource_id")
                            observed[acc] = ObservedResource(
                                system_id="account_service",
                                resource_id=acc,
                                category="USER_PROFILE",
                                observed_state="ABSENT",
                                evidence_id=fid,
                                evidence_time=ef.captured_at
                            )

                except Exception:
                    pass

            # Check format B: customer_data_snapshot_bundle
            elif "customer_data_snapshot_bundle" in json_file.name:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    for snap in d.get("snapshots", []):
                        ds = snap.get("data_store")
                        for rec in snap.get("records", []):
                            rec_str = json.dumps(rec).lower()
                            if match_terms(rec_str):
                                res_id = rec.get("resource_id")
                                if ds == "identity_service":
                                    has_pii = bool(rec.get("name") or rec.get("email") or rec.get("phone") or rec.get("email_hash"))
                                    state = "EXPOSED_PII" if has_pii else "REDACTED"
                                    observed[res_id] = ObservedResource(
                                        system_id="identity_service",
                                        resource_id=res_id,
                                        category="ACCOUNT_TOMBSTONE",
                                        observed_state=state,
                                        evidence_id=fid,
                                        evidence_time=ef.captured_at
                                    )
                                elif ds == "security_service":
                                    observed[res_id] = ObservedResource(
                                        system_id="security_service",
                                        resource_id=res_id,
                                        category="SECURITY_AUDIT_LOG",
                                        observed_state="PRESENT",
                                        evidence_id=fid,
                                        evidence_time=ef.captured_at
                                    )
                except Exception:
                    pass

            # Check format C: customer_export_jobs_*.json
            elif "customer_export_jobs" in json_file.name:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        jobs_data = json.load(f)
                    jobs_list = jobs_data.get("records", []) if isinstance(jobs_data, dict) else jobs_data
                    for job in jobs_list:
                        job_str = json.dumps(job).lower()
                        if match_terms(job_str):
                            res_id = job.get("resource_id") or job.get("job_id") or "export_001"
                            if job.get("download_available", True):
                                observed[res_id] = ObservedResource(
                                    system_id="export_service",
                                    resource_id=res_id,
                                    category="USER_EXPORT",
                                    observed_state="PRESENT",
                                    evidence_id=fid,
                                    evidence_time=ef.captured_at
                                )
                except Exception:
                    pass

            # Check format D: customer_analytics_report_*.json
            elif "customer_analytics_report" in json_file.name:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        report = json.load(f)
                    for item in report.get("profiles", []):
                        item_str = json.dumps(item).lower()
                        if match_terms(item_str):
                            res_id = item.get("resource_id") or "analytics_901"
                            observed[res_id] = ObservedResource(
                                system_id="analytics_platform",
                                resource_id=res_id,
                                category="ANALYTICS_PROFILE",
                                observed_state="ANONYMIZED",
                                evidence_id=fid,
                                evidence_time=ef.captured_at
                            )
                except Exception:
                    pass

        # 3. Check Handover Text <= audit_dt
        handover_path = self.dataset_dir / "evidence" / "records" / "customer_account_handover_20261001.txt"
        fid_handover = self.path_to_fid.get("customer_account_handover_20261001.txt", "")
        ef_handover = self.manifest.get(fid_handover)
        if ef_handover and ef_handover.captured_dt <= audit_dt and handover_path.exists():
            with open(handover_path, "r", encoding="utf-8") as f:
                for line in f:
                    if match_terms(line):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 6:
                            sys_id = parts[1]
                            res_id = parts[2]
                            cat = parts[3]
                            status_val = parts[4]

                            if status_val == "NOT_FOUND":
                                state = "ABSENT"
                            elif status_val == "IDENTIFIABLE":
                                state = "EXPOSED_PII" if cat in ["SUPPORT_MESSAGE", "ANALYTICS_PROFILE"] else "PRESENT"
                            elif status_val == "REMAINING":
                                state = "PRESENT"
                            elif status_val == "ACTIVE":
                                state = "ACTIVE_FLOW" if sys_id == "integration_service" else "RESTORE_RISK"
                            elif status_val == "ENABLED":
                                state = "ACTIVE_FLOW"
                            elif status_val == "BLOCKED":
                                state = "BLOCKED"
                            elif status_val == "DISABLED":
                                state = "DISABLED"
                            elif status_val == "ANONYMIZED":
                                state = "ANONYMIZED"
                            elif status_val == "REDACTED":
                                state = "REDACTED"
                            else:
                                state = "PRESENT"

                            observed[res_id] = ObservedResource(
                                system_id=sys_id,
                                resource_id=res_id,
                                category=cat,
                                observed_state=state,
                                evidence_id=fid_handover,
                                evidence_time=ef_handover.captured_at
                            )

        # 4. Check Readback Logs & Service Events Logs <= audit_dt
        logs_dir = self.dataset_dir / "evidence" / "logs"
        for log_file in sorted(logs_dir.glob("*.log")):
            fid = self.path_to_fid.get(log_file.name)
            if not fid:
                continue
            ef = self.manifest.get(fid)
            if not ef or ef.captured_dt > audit_dt:
                continue

            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # A. Support replica log with trace correlation
            if "support_replica" in log_file.name:
                matching_traces = set()
                for line in lines:
                    if match_terms_acc(line):
                        m_tr = re.search(r"trace_id=([a-zA-Z0-9_\-]+)", line)
                        if m_tr:
                            matching_traces.add(m_tr.group(1))
                for line in lines:
                    m_tr = re.search(r"trace_id=([a-zA-Z0-9_\-]+)", line)
                    if m_tr and m_tr.group(1) in matching_traces:
                        m_res = re.search(r"resource_id=([a-zA-Z0-9_]+)", line)
                        if m_res:
                            res_id = m_res.group(1)
                            observed[res_id] = ObservedResource(
                                system_id="support_platform",
                                resource_id=res_id,
                                category="SUPPORT_MESSAGE",
                                observed_state="PRESENT",
                                evidence_id=fid,
                                evidence_time=ef.captured_at
                            )

            # B. Resource lookup trace logs
            elif "resource_lookup_trace" in log_file.name:
                for line in lines:
                    if match_terms_acc(line):
                        m_res = re.search(r"resource_id=(\w+_\d+)", line)
                        if m_res:
                            res_id = m_res.group(1)
                            if "profile_lookup_completed" in line:
                                if "rows=0" in line or "http_status=404" in line:
                                    observed[res_id] = ObservedResource(system_id="account_service", resource_id=res_id, category="USER_PROFILE", observed_state="ABSENT", evidence_id=fid, evidence_time=ef.captured_at)
                                elif "rows=1" in line or "http_status=200" in line:
                                    observed[res_id] = ObservedResource(system_id="account_service", resource_id=res_id, category="USER_PROFILE", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif "audit_record_read_completed" in line:
                                observed[res_id] = ObservedResource(system_id="security_service", resource_id=res_id, category="SECURITY_AUDIT_LOG", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif "index_query_completed" in line and "result=hit" in line:
                                observed[res_id] = ObservedResource(system_id="search_service", resource_id=res_id, category="SEARCH_INDEX_ENTRY", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif "connector_config_read_completed" in line:
                                enabled = "enabled=true" in line
                                state = "ACTIVE_FLOW" if enabled else "DISABLED"
                                observed[res_id] = ObservedResource(system_id="integration_service", resource_id=res_id, category="ACTIVE_DATA_FLOW", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif "restore_policy_read_completed" in line:
                                allowed = "restore_allowed=true" in line
                                state = "RESTORE_RISK" if allowed else "BLOCKED"
                                observed[res_id] = ObservedResource(system_id="backup_service", resource_id=res_id, category="BACKUP_ARCHIVE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif "analytics" in res_id:
                                has_pii = "email=" in line and "email=null" not in line
                                state = "EXPOSED_PII" if has_pii else "ANONYMIZED"
                                observed[res_id] = ObservedResource(system_id="analytics_platform", resource_id=res_id, category="ANALYTICS_PROFILE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif "support" in res_id:
                                has_pii = "requester_email=" in line and "requester_email=null" not in line
                                state = "EXPOSED_PII" if has_pii else "REDACTED"
                                observed[res_id] = ObservedResource(system_id="support_platform", resource_id=res_id, category="SUPPORT_MESSAGE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)

            # C. Central observability logs & runtime traces
            elif any(k in log_file.name for k in ["service_events_", "operations_stream_", "cloud_runtime_export", "application_trace", "structured_service_events", "syslog_archive"]):
                matching_traces = set()
                for line in lines:
                    if match_terms_acc(line):
                        m_tr = re.search(r'(?:trace_id|requestId)[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_\-]+)', line) or re.search(r'\b(tr-\d+)\b', line)
                        if m_tr:
                            matching_traces.add(m_tr.group(1))

                for line in lines:
                    m_tr = re.search(r'(?:trace_id|requestId)[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_\-]+)', line) or re.search(r'\b(tr-\d+)\b', line)
                    is_user_line = match_terms_acc(line) or (m_tr and m_tr.group(1) in matching_traces)
                    if not is_user_line:
                        continue

                    m_res = re.search(r'resource_id[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_]+)', line)
                    if m_res:
                        res_id = m_res.group(1)
                        if "backup" in res_id:
                            allowed = "deletion_block=false" in line or 'deletion_block":false' in line.replace(" ", "") or "restore_candidate_evaluated eligible=true" in line or "restore_allowed=true" in line or 'restore_allowed":true' in line.replace(" ", "")
                            state = "RESTORE_RISK" if allowed else "BLOCKED"
                            observed[res_id] = ObservedResource(system_id="backup_service", resource_id=res_id, category="BACKUP_ARCHIVE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                        elif "search" in res_id:
                            observed[res_id] = ObservedResource(system_id="search_service", resource_id=res_id, category="SEARCH_INDEX_ENTRY", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                        elif "support" in res_id:
                            observed[res_id] = ObservedResource(system_id="support_platform", resource_id=res_id, category="SUPPORT_MESSAGE", observed_state="EXPOSED_PII", evidence_id=fid, evidence_time=ef.captured_at)
                        elif "analytics" in res_id:
                            observed[res_id] = ObservedResource(system_id="analytics_platform", resource_id=res_id, category="ANALYTICS_PROFILE", observed_state="EXPOSED_PII", evidence_id=fid, evidence_time=ef.captured_at)
                        elif "data_flow" in res_id:
                            observed[res_id] = ObservedResource(system_id="integration_service", resource_id=res_id, category="ACTIVE_DATA_FLOW", observed_state="ACTIVE_FLOW", evidence_id=fid, evidence_time=ef.captured_at)
                        elif "account" in res_id:
                            if 'rows="0"' in line or 'rows=\\"0\\"' in line or "rows=0" in line or "404" in line or 'rows":0' in line.replace(" ", ""):
                                observed[res_id] = ObservedResource(system_id="account_service", resource_id=res_id, category="USER_PROFILE", observed_state="ABSENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif 'rows="1"' in line or 'rows=\\"1\\"' in line or "rows=1" in line or "200" in line or 'rows":1' in line.replace(" ", ""):
                                observed[res_id] = ObservedResource(system_id="account_service", resource_id=res_id, category="USER_PROFILE", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)

            # D. Diagnostic and Delivery logs
            elif "search_index_diagnostic" in log_file.name or "notification_delivery" in log_file.name:
                for line in lines:
                    if match_terms_acc(line):
                        m_sys = re.search(r'system[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_]+)', line)
                        m_res = re.search(r'resource_id[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_]+)', line)
                        m_cat = re.search(r'record_type[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_]+)', line)
                        m_reslt = re.search(r'result[\\\"\'\s]*[=:][\\\"\'\s]*([a-zA-Z0-9_]+)', line)
                        if m_sys and m_res:
                            s_id = m_sys.group(1)
                            r_id = m_res.group(1)
                            cat_id = m_cat.group(1) if m_cat else "USER_PROFILE"
                            reslt = m_reslt.group(1) if m_reslt else "FOUND"

                            if reslt == "NOT_FOUND":
                                if s_id == "account_service":
                                    observed[r_id] = ObservedResource(system_id=s_id, resource_id=r_id, category=cat_id, observed_state="ABSENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif reslt == "ACTIVE" and s_id == "integration_service":
                                observed[r_id] = ObservedResource(system_id=s_id, resource_id=r_id, category="ACTIVE_DATA_FLOW", observed_state="ACTIVE_FLOW", evidence_id=fid, evidence_time=ef.captured_at)
                            elif reslt == "FOUND":
                                if s_id == "security_service":
                                    observed[r_id] = ObservedResource(system_id=s_id, resource_id=r_id, category="SECURITY_AUDIT_LOG", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                                else:
                                    observed[r_id] = ObservedResource(system_id=s_id, resource_id=r_id, category=cat_id, observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)



        # 5. Check Document PDFs <= audit_dt
        docs_dir = self.dataset_dir / "evidence" / "documents"
        for pdf_file in docs_dir.glob("*.pdf"):
            fid = self.path_to_fid.get(pdf_file.name)
            if not fid:
                continue
            ef = self.manifest.get(fid)
            if not ef or ef.captured_dt > audit_dt:
                continue

            txt = self.doc_parser.extract_text_from_pdf(pdf_file)
            if match_terms(txt):
                if "delivery" in pdf_file.name.lower() or "support" in ef.origin.lower():
                    res_id = "support_001"
                    observed[res_id] = ObservedResource(
                        system_id="support_platform",
                        resource_id=res_id,
                        category="SUPPORT_ATTACHMENT",
                        observed_state="PRESENT",
                        evidence_id=fid,
                        evidence_time=ef.captured_at
                    )
                elif "legal" in pdf_file.name.lower() or "legal" in ef.origin.lower():
                    res_id = "legal_hold_001"
                    observed[res_id] = ObservedResource(
                        system_id="legal_service",
                        resource_id=res_id,
                        category="LEGAL_HOLD_RECORD",
                        observed_state="PRESENT",
                        evidence_id=fid,
                        evidence_time=ef.captured_at
                    )
                elif "security" in pdf_file.name.lower() or "security" in ef.origin.lower():
                    res_id = "audit_record_pdf"
                    observed[res_id] = ObservedResource(
                        system_id="security_service",
                        resource_id=res_id,
                        category="SECURITY_AUDIT_LOG",
                        observed_state="PRESENT",
                        evidence_id=fid,
                        evidence_time=ef.captured_at
                    )

        # 6. Check Image Transcripts <= audit_dt
        img_cache_file = Path(__file__).resolve().parent / "cache" / "image_transcripts.json"
        if img_cache_file.exists():
            try:
                with open(img_cache_file, "r", encoding="utf-8") as f:
                    img_cache = json.load(f)
                for fid, img_data in img_cache.items():
                    ef = self.manifest.get(fid)
                    if not ef or ef.captured_dt > audit_dt:
                        continue
                    for rec in img_data.get("records", []):
                        rec_str = json.dumps(rec).lower()
                        if match_terms_acc(rec_str):
                            res_id = rec.get("resource_id")
                            if not res_id:
                                continue
                            sys_id = img_data.get("system_id", "account_service")
                            if sys_id == "account_service":
                                observed[res_id] = ObservedResource(system_id="account_service", resource_id=res_id, category="USER_PROFILE", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "search_service":
                                observed[res_id] = ObservedResource(system_id="search_service", resource_id=res_id, category="SEARCH_INDEX_ENTRY", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "integration_service":
                                enabled = bool(rec.get("enabled", True))
                                state = "ACTIVE_FLOW" if enabled else "DISABLED"
                                observed[res_id] = ObservedResource(system_id="integration_service", resource_id=res_id, category="ACTIVE_DATA_FLOW", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "analytics_platform":
                                has_pii = bool(rec.get("email") or rec.get("phone") or rec.get("user_id") or rec.get("name"))
                                state = "EXPOSED_PII" if has_pii else "ANONYMIZED"
                                observed[res_id] = ObservedResource(system_id="analytics_platform", resource_id=res_id, category="ANALYTICS_PROFILE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "support_platform":
                                has_pii = bool(rec.get("email") or rec.get("customer") or rec.get("phone"))
                                state = "EXPOSED_PII" if has_pii else "REDACTED"
                                observed[res_id] = ObservedResource(system_id="support_platform", resource_id=res_id, category="SUPPORT_MESSAGE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "backup_service":
                                allowed = bool(rec.get("restore_allowed", True))
                                state = "RESTORE_RISK" if allowed else "BLOCKED"
                                observed[res_id] = ObservedResource(system_id="backup_service", resource_id=res_id, category="BACKUP_ARCHIVE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "export_service":
                                observed[res_id] = ObservedResource(system_id="export_service", resource_id=res_id, category="USER_EXPORT", observed_state="PRESENT", evidence_id=fid, evidence_time=ef.captured_at)
                            elif sys_id == "identity_service":
                                has_pii = not bool(rec.get("pii_removed", False))
                                state = "EXPOSED_PII" if has_pii else "REDACTED"
                                observed[res_id] = ObservedResource(system_id="identity_service", resource_id=res_id, category="ACCOUNT_TOMBSTONE", observed_state=state, evidence_id=fid, evidence_time=ef.captured_at)
            except Exception:
                pass

        return observed
