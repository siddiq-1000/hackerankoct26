import json
from pathlib import Path
from typing import Dict, List, Optional
from code.config import CACHE_DIR

class VisionEvidenceManager:
    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or (CACHE_DIR / "image_transcripts.json")
        self.transcripts: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def search_images(self, search_terms: List[str]) -> List[dict]:
        hits = []
        for evidence_id, entry in self.transcripts.items():
            records = entry.get("records", [])
            for rec in records:
                rec_str = json.dumps(rec).lower()
                matched = [t for t in search_terms if t and t.lower() in rec_str]
                if matched:
                    hits.append({
                        "evidence_id": evidence_id,
                        "file_name": entry.get("file_name", ""),
                        "system_id": entry.get("system_id", "account_service"),
                        "resource_id": rec.get("resource_id", ""),
                        "data": rec,
                        "matched_terms": matched
                    })
        return hits
