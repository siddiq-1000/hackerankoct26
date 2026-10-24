import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from code.config import DATASET_DIR

def parse_iso(ts_str: str) -> datetime:
    if not ts_str:
        return datetime.min
    # Strip Z and parse UTC
    clean = ts_str.rstrip("Z")
    return datetime.fromisoformat(clean)

@dataclass
class DeletionRequest:
    case_id: str
    email: str
    requested_at: str
    reported_status: str
    reported_at: str
    audit_at: str
    request_text: str

    @property
    def audit_dt(self) -> datetime:
        return parse_iso(self.audit_at)

    @property
    def requested_dt(self) -> datetime:
        return parse_iso(self.requested_at)

@dataclass
class UserIdentity:
    user_id: str
    name: str
    email: str
    phone: str
    email_hash: str
    updated_at: str

@dataclass
class UserAuditEntry:
    audit_id: str
    user_id: str
    event_time: str
    field_name: str
    old_value: str
    new_value: str

    @property
    def event_dt(self) -> datetime:
        return parse_iso(self.event_time)

@dataclass
class SystemActivity:
    activity_id: str
    event_time: str
    event_type: str
    source_system: str
    target_system: str
    resource_id: str
    reported_result: str
    details: str

    @property
    def event_dt(self) -> datetime:
        return parse_iso(self.event_time)

@dataclass
class DeletionRule:
    rule_id: str
    data_category: str
    condition: str
    required_action: str

@dataclass
class EvidenceFile:
    file_id: str
    file_path: str
    origin: str
    captured_at: str

    @property
    def captured_dt(self) -> datetime:
        return parse_iso(self.captured_at)

class DatasetLoader:
    def __init__(self, dataset_dir: Optional[Path] = None):
        self.dataset_dir = dataset_dir or DATASET_DIR

    def load_deletion_requests(self, filename: str = "deletion_requests.csv") -> List[DeletionRequest]:
        path = self.dataset_dir / filename
        requests = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                requests.append(DeletionRequest(
                    case_id=r["case_id"],
                    email=r["email"],
                    requested_at=r["requested_at"],
                    reported_status=r["reported_status"],
                    reported_at=r["reported_at"],
                    audit_at=r["audit_at"],
                    request_text=r["request_text"]
                ))
        return requests

    def load_identities(self) -> Dict[str, UserIdentity]:
        path = self.dataset_dir / "user_identities.csv"
        identities = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                identities[r["user_id"]] = UserIdentity(
                    user_id=r["user_id"],
                    name=r["name"],
                    email=r["email"],
                    phone=r["phone"],
                    email_hash=r["email_hash"],
                    updated_at=r["updated_at"]
                )
        return identities

    def load_audit_log(self) -> List[UserAuditEntry]:
        path = self.dataset_dir / "user_audit_log.csv"
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                entries.append(UserAuditEntry(
                    audit_id=r["audit_id"],
                    user_id=r["user_id"],
                    event_time=r["event_time"],
                    field_name=r["field_name"],
                    old_value=r["old_value"],
                    new_value=r["new_value"]
                ))
        return entries

    def load_system_activity(self) -> List[SystemActivity]:
        path = self.dataset_dir / "system_activity.csv"
        activities = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                activities.append(SystemActivity(
                    activity_id=r["activity_id"],
                    event_time=r["event_time"],
                    event_type=r["event_type"],
                    source_system=r["source_system"],
                    target_system=r["target_system"],
                    resource_id=r["resource_id"],
                    reported_result=r["reported_result"],
                    details=r["details"]
                ))
        return activities

    def load_deletion_rules(self) -> Dict[str, DeletionRule]:
        path = self.dataset_dir / "deletion_rules.csv"
        rules = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rules[r["data_category"]] = DeletionRule(
                    rule_id=r["rule_id"],
                    data_category=r["data_category"],
                    condition=r["condition"],
                    required_action=r["required_action"]
                )
        return rules

    def load_evidence_manifest(self) -> Dict[str, EvidenceFile]:
        path = self.dataset_dir / "evidence_files.csv"
        manifest = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                manifest[r["file_id"]] = EvidenceFile(
                    file_id=r["file_id"],
                    file_path=r["file_path"],
                    origin=r["origin"],
                    captured_at=r["captured_at"]
                )
        return manifest
