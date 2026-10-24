import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from code.config import DATASET_DIR

def match_terms_in_dict(d: dict, search_terms: List[str]) -> List[str]:
    matched = []
    for term in search_terms:
        if not term:
            continue
        t_lower = term.lower().strip()
        found = False
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float)):
                v_str = str(v).lower().strip()
                if v_str == t_lower or re.search(r"\b" + re.escape(t_lower) + r"\b", v_str):
                    found = True
                    break
            elif isinstance(v, dict):
                sub_matched = match_terms_in_dict(v, [term])
                if sub_matched:
                    found = True
                    break
            elif isinstance(v, list):
                for elem in v:
                    if isinstance(elem, dict):
                        if match_terms_in_dict(elem, [term]):
                            found = True
                            break
                    elif isinstance(elem, (str, int, float)):
                        elem_str = str(elem).lower().strip()
                        if elem_str == t_lower or re.search(r"\b" + re.escape(t_lower) + r"\b", elem_str):
                            found = True
                            break
                if found:
                    break
        if found:
            matched.append(term)
    return matched

class RecordsAndLogsParser:
    def __init__(self, evidence_dir: Optional[Path] = None):
        self.evidence_dir = evidence_dir or (DATASET_DIR / "evidence")
        self.records_dir = self.evidence_dir / "records"
        self.logs_dir = self.evidence_dir / "logs"
        self._json_cache: Dict[str, dict] = {}

    def search_json_file(self, filename: str, search_terms: List[str]) -> List[dict]:
        path = self.records_dir / filename
        if not path.exists():
            return []

        if filename not in self._json_cache:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._json_cache[filename] = json.load(f)
            except Exception:
                return []

        data = self._json_cache[filename]
        hits = []

        # Format A: service_resource_export files
        if "service_exports" in data:
            for sys_id, export_data in data["service_exports"].items():
                for coll_name, items in export_data.items():
                    for item in items:
                        matched = match_terms_in_dict(item, search_terms)
                        if matched:
                            hits.append({
                                "file_name": filename,
                                "system_id": self._map_system_id(sys_id),
                                "resource_id": item.get("resource_id", ""),
                                "data": item,
                                "matched_terms": matched
                            })

        # Format B: snapshot bundle files
        elif "snapshots" in data:
            for sn in data.get("snapshots", []):
                sys_id = sn.get("data_store", "account_service")
                for rec in sn.get("records", []):
                    matched = match_terms_in_dict(rec, search_terms)
                    if matched:
                        hits.append({
                            "file_name": filename,
                            "system_id": self._map_system_id(sys_id),
                            "resource_id": rec.get("resource_id", ""),
                            "data": rec,
                            "matched_terms": matched
                        })

        # Format C: direct records list (e.g. connector_configurations, customer_analytics_report)
        elif "records" in data:
            origin = data.get("origin", "")
            sys_id = self._map_origin_to_system(origin)
            for rec in data.get("records", []):
                rec_str = json.dumps(rec).lower()
                matched = [t for t in search_terms if t and t.lower() in rec_str]
                if matched:
                    hits.append({
                        "file_name": filename,
                        "system_id": self._map_system_id(rec.get("system") or sys_id),
                        "resource_id": rec.get("resource_id", ""),
                        "data": rec,
                        "matched_terms": matched
                    })
        return hits

    def search_text_or_log_file(self, file_path_rel: str, search_terms: List[str]) -> List[dict]:
        path = self.evidence_dir.parent / file_path_rel
        if not path.exists():
            path = self.evidence_dir / file_path_rel
        if not path.exists():
            return []

        hits = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue

                line_lower = clean_line.lower()
                matched = [t for t in search_terms if t and t.lower() in line_lower]
                if not matched:
                    continue

                # Check if pipe-separated format (e.g. customer_account_handover.txt)
                if "|" in clean_line:
                    parts = [p.strip() for p in clean_line.lstrip("- ").split("|")]
                    if len(parts) >= 6:
                        ts, sys_id, res_id, rec_type, state, ident = parts[:6]
                        hits.append({
                            "file_name": path.name,
                            "line_no": line_no,
                            "system_id": self._map_system_id(sys_id),
                            "resource_id": res_id,
                            "state": state,
                            "record_type": rec_type,
                            "data": clean_line,
                            "matched_terms": matched
                        })
                        continue

                # Standard log line with key=value attributes
                res_match = re.search(r"resource_id=([a-zA-Z0-9_]+)", clean_line) or re.search(r"\b([a-z]+_\d+)\b", clean_line)
                sys_match = re.search(r"service=([a-zA-Z0-9_]+)", clean_line) or re.search(r"system=[\"\']?([a-zA-Z0-9_]+)[\"\']?", clean_line)
                
                resource_id = res_match.group(1) if res_match else ""
                system_id = sys_match.group(1) if sys_match else self._infer_system_from_path(file_path_rel)
                
                hits.append({
                    "file_name": path.name,
                    "line_no": line_no,
                    "system_id": self._map_system_id(system_id),
                    "resource_id": resource_id,
                    "data": clean_line,
                    "matched_terms": matched
                })
        return hits

    def _map_origin_to_system(self, origin: str) -> str:
        orig = origin.lower()
        if "integration" in orig: return "integration_service"
        if "export" in orig: return "export_service"
        if "analytics" in orig: return "analytics_platform"
        if "support" in orig: return "support_platform"
        if "search" in orig: return "search_service"
        if "security" in orig: return "security_service"
        if "identity" in orig: return "identity_service"
        return "account_service"

    def _infer_system_from_path(self, path_str: str) -> str:
        p = path_str.lower()
        if "analytics" in p: return "analytics_platform"
        if "support" in p: return "support_platform"
        if "search" in p: return "search_service"
        if "delivery" in p or "connector" in p or "integration" in p: return "integration_service"
        if "security" in p or "compliance" in p: return "security_service"
        if "backup" in p: return "backup_service"
        if "export" in p: return "export_service"
        if "identity" in p or "tombstone" in p: return "identity_service"
        return "account_service"

    def _map_system_id(self, sys_id: str) -> str:
        s = sys_id.lower()
        if "analytics" in s: return "analytics_platform"
        if "support" in s: return "support_platform"
        if "search" in s: return "search_service"
        if "integration" in s or "connector" in s or "delivery" in s: return "integration_service"
        if "security" in s: return "security_service"
        if "backup" in s: return "backup_service"
        if "export" in s: return "export_service"
        if "identity" in s: return "identity_service"
        return "account_service"
