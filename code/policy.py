from typing import Dict, Optional
from code.loaders import DeletionRule

class PolicyEngine:
    def __init__(self, rules: Optional[Dict[str, DeletionRule]] = None):
        self.rules = rules or {}

    def get_required_action(self, data_category: str) -> str:
        # Defaults based on deletion_rules.csv
        defaults = {
            "USER_PROFILE": "DELETE",
            "SECONDARY_IDENTIFIER": "DELETE",
            "SEARCH_INDEX_ENTRY": "DELETE",
            "CACHE_ENTRY": "DELETE",
            "SUPPORT_MESSAGE": "REDACT",
            "SUPPORT_ATTACHMENT": "DELETE",
            "ANALYTICS_PROFILE": "ANONYMIZE",
            "PRODUCT_TELEMETRY": "ANONYMIZE",
            "USER_EXPORT": "DELETE",
            "MARKETING_PROFILE": "DELETE",
            "EMAIL_DELIVERY_LOG": "REDACT",
            "SECURITY_AUDIT_LOG": "RETAIN",
            "LEGAL_HOLD_RECORD": "RETAIN",
            "BACKUP_ARCHIVE": "RETAIN",
            "ACCOUNT_TOMBSTONE": "REDACT"
        }
        if data_category in self.rules:
            return self.rules[data_category].required_action
        return defaults.get(data_category, "DELETE")

    def infer_category(self, system_id: str, resource_id: str, data: dict = None) -> str:
        res = resource_id.lower()
        sys = system_id.lower()

        if "tombstone" in res or sys == "identity_service":
            return "ACCOUNT_TOMBSTONE"
        if "audit" in res or sys == "security_service":
            return "SECURITY_AUDIT_LOG"
        if "backup" in res or sys == "backup_service":
            return "BACKUP_ARCHIVE"
        if "data_flow" in res or sys == "integration_service":
            return "ACTIVE_DATA_FLOW"
        if "search" in res or sys == "search_service":
            return "SEARCH_INDEX_ENTRY"
        if "export" in res or sys == "export_service":
            return "USER_EXPORT"
        if "analytics" in res or sys == "analytics_platform":
            return "ANALYTICS_PROFILE"
        if "marketing" in res or sys == "marketing_platform":
            return "MARKETING_PROFILE"
        if "support" in res or sys == "support_platform":
            if data and (data.get("has_shared_context") or "conversation" in data or "message" in data):
                return "SUPPORT_MESSAGE"
            if data and ("attachment" in res or "filename" in data or "pdf" in str(data)):
                return "SUPPORT_ATTACHMENT"
            return "SUPPORT_MESSAGE"
        return "USER_PROFILE"
