import csv
import json
import os
import re
import sqlite3
import zlib
import base64
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = REPO_ROOT / "dataset"
EVIDENCE_DIR = DATASET_DIR / "evidence"

class OracleScanner:
    """
    Independent Brute-Force Evidence Scanner.
    Shares NO gap logic, NO state reconstruction, and NO planning logic with the main pipeline.
    Scans every evidence file for ANY trace of a user's identifiers up to audit_at.
    Uses pre-inverted term indexing for blistering performance across 518 cases.
    """
    def __init__(self):
        # 1. Load evidence manifest
        self.manifest = {}
        with open(DATASET_DIR / "evidence_files.csv", "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.manifest[r["file_id"]] = {
                    "file_path": r["file_path"],
                    "origin": r["origin"],
                    "captured_at": r["captured_at"]
                }
        self.file_to_fid = {Path(m["file_path"]).name: fid for fid, m in self.manifest.items()}

        # 2. Pre-load all SQL databases in-memory
        self.sql_dbs = {}
        db_dir = EVIDENCE_DIR / "databases"
        for sql_path in db_dir.glob("*.sql"):
            conn = sqlite3.connect(":memory:")
            try:
                with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
                    conn.executescript(f.read())
                self.sql_dbs[sql_path.name] = conn
            except Exception:
                pass

        # 3. Pre-load all JSON records
        self.json_records = {}
        records_dir = EVIDENCE_DIR / "records"
        for jp in records_dir.glob("*.json"):
            try:
                with open(jp, "r", encoding="utf-8", errors="ignore") as f:
                    self.json_records[jp.name] = json.load(f)
            except Exception:
                pass

        # 4. Pre-load text files & logs
        self.text_files = {}
        for txt_path in records_dir.glob("*.txt"):
            try:
                with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                    self.text_files[txt_path.name] = f.readlines()
            except Exception:
                pass

        logs_dir = EVIDENCE_DIR / "logs"
        self.log_files = {}
        for lp in logs_dir.glob("*.log"):
            try:
                with open(lp, "r", encoding="utf-8", errors="ignore") as f:
                    self.log_files[lp.name] = f.readlines()
            except Exception:
                pass

        # 5. Pre-decode PDFs
        self.pdf_texts = {}
        docs_dir = EVIDENCE_DIR / "documents"
        for pp in docs_dir.glob("*.pdf"):
            self.pdf_texts[pp.name] = self._extract_pdf_text(pp)

        # 6. Pre-load image transcripts cache
        self.image_transcripts = {}
        img_cache = REPO_ROOT / "code" / "cache" / "image_transcripts.json"
        if img_cache.exists():
            try:
                with open(img_cache, "r", encoding="utf-8") as f:
                    self.image_transcripts = json.load(f)
            except Exception:
                pass

        # 7. Pre-load system_activity.csv
        self.activities = []
        with open(DATASET_DIR / "system_activity.csv", "r", encoding="utf-8") as f:
            self.activities = list(csv.DictReader(f))

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        with open(pdf_path, "rb") as f:
            content = f.read()
        extracted = []
        idx = 0
        while True:
            s_idx = content.find(b"stream", idx)
            if s_idx == -1:
                break
            e_idx = content.find(b"endstream", s_idx)
            if e_idx == -1:
                break
            stream_data = content[s_idx + 6:e_idx].strip()
            try:
                dec = base64.a85decode(stream_data, adobe=True)
                decomp = zlib.decompress(dec)
                texts = re.findall(rb"\((.*?)\)", decomp)
                for t in texts:
                    try:
                        extracted.append(t.decode("latin1"))
                    except Exception:
                        pass
            except Exception:
                try:
                    decomp = zlib.decompress(stream_data)
                    texts = re.findall(rb"\((.*?)\)", decomp)
                    for t in texts:
                        try:
                            extracted.append(t.decode("latin1"))
                        except Exception:
                            pass
                except Exception:
                    pass
            idx = e_idx + 9
        return " ".join(extracted)

    def scan_all_cases(self, case_meta: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fast bulk scan across all cases simultaneously.
        case_meta: list of dicts with keys: 'case_id', 'audit_at', 'terms'
        Returns dict: case_id -> list of raw hit records.
        """
        term_to_cases: Dict[str, List[Tuple[str, str]]] = {}
        case_hits: Dict[str, List[Dict[str, Any]]] = {c["case_id"]: [] for c in case_meta}
        
        for c in case_meta:
            cid = c["case_id"]
            aat = c["audit_at"]
            for t in c["terms"]:
                if not t or len(t.strip()) < 3:
                    continue
                clean_t = t.strip().lower()
                term_to_cases.setdefault(clean_t, []).append((cid, aat))

        # Helper to find matches in string
        def check_and_add(text: str, hit_base: Dict[str, Any]):
            text_lower = text.lower()
            for term, c_list in term_to_cases.items():
                if term in text_lower:
                    if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
                        for cid, aat in c_list:
                            cap_at = hit_base.get("captured_at") or hit_base.get("event_time", "")
                            if cap_at and cap_at <= aat:
                                h = dict(hit_base)
                                h["matched_term"] = term
                                case_hits[cid].append(h)

        # A. SQL Databases
        for fn, conn in self.sql_dbs.items():
            fid = self.file_to_fid.get(fn)
            if not fid:
                continue
            ef = self.manifest[fid]
            cap_at = ef["captured_at"]

            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall()]

            for tbl in tables:
                cursor.execute(f"PRAGMA table_info({tbl});")
                cols = [c[1] for c in cursor.fetchall()]
                cursor.execute(f"SELECT * FROM {tbl};")
                rows = cursor.fetchall()
                for row in rows:
                    row_dict = dict(zip(cols, row))
                    row_str = " ".join(str(v) for v in row if v is not None)
                    hit_base = {
                        "evidence_id": fid,
                        "file_name": fn,
                        "captured_at": cap_at,
                        "type": "sql",
                        "table": tbl,
                        "data": row_dict
                    }
                    check_and_add(row_str, hit_base)

        # B. JSON Records
        for fn, data in self.json_records.items():
            fid = self.file_to_fid.get(fn)
            if not fid:
                continue
            ef = self.manifest[fid]
            cap_at = ef["captured_at"]

            if "service_exports" in data:
                for sys_id, export_data in data["service_exports"].items():
                    for tbl, items in export_data.items():
                        for item in items:
                            item_str = json.dumps(item)
                            hit_base = {
                                "evidence_id": fid,
                                "file_name": fn,
                                "captured_at": cap_at,
                                "type": "json_service_export",
                                "system_id": sys_id,
                                "table": tbl,
                                "data": item
                            }
                            check_and_add(item_str, hit_base)

            elif "snapshots" in data:
                for snap in data.get("snapshots", []):
                    ds = snap.get("data_store")
                    for rec in snap.get("records", []):
                        rec_str = json.dumps(rec)
                        hit_base = {
                            "evidence_id": fid,
                            "file_name": fn,
                            "captured_at": cap_at,
                            "type": "json_snapshot_bundle",
                            "data_store": ds,
                            "data": rec
                        }
                        check_and_add(rec_str, hit_base)

            elif isinstance(data, list):
                for item in data:
                    item_str = json.dumps(item)
                    hit_base = {
                        "evidence_id": fid,
                        "file_name": fn,
                        "captured_at": cap_at,
                        "type": "json_list",
                        "data": item
                    }
                    check_and_add(item_str, hit_base)

        # C. Handover text files
        for fn, lines in self.text_files.items():
            fid = self.file_to_fid.get(fn)
            if not fid:
                continue
            ef = self.manifest[fid]
            cap_at = ef["captured_at"]

            for lno, line in enumerate(lines, 1):
                clean_l = line.strip()
                hit_base = {
                    "evidence_id": fid,
                    "file_name": fn,
                    "captured_at": cap_at,
                    "type": "text_line",
                    "line_no": lno,
                    "line": clean_l
                }
                check_and_add(clean_l, hit_base)

        # D. Logs
        for fn, lines in self.log_files.items():
            fid = self.file_to_fid.get(fn)
            if not fid:
                continue
            ef = self.manifest[fid]
            cap_at = ef["captured_at"]

            for lno, line in enumerate(lines, 1):
                clean_l = line.strip()
                hit_base = {
                    "evidence_id": fid,
                    "file_name": fn,
                    "captured_at": cap_at,
                    "type": "log_line",
                    "line_no": lno,
                    "line": clean_l
                }
                check_and_add(clean_l, hit_base)

        # E. PDFs
        for fn, text in self.pdf_texts.items():
            fid = self.file_to_fid.get(fn)
            if not fid:
                continue
            ef = self.manifest[fid]
            cap_at = ef["captured_at"]

            hit_base = {
                "evidence_id": fid,
                "file_name": fn,
                "captured_at": cap_at,
                "type": "pdf_document"
            }
            check_and_add(text, hit_base)

        # F. Image Transcripts
        for fid, entry in self.image_transcripts.items():
            ef = self.manifest.get(fid)
            if not ef:
                continue
            cap_at = ef["captured_at"]

            for rec in entry.get("records", []):
                rec_str = json.dumps(rec)
                hit_base = {
                    "evidence_id": fid,
                    "file_name": entry.get("file_name", ""),
                    "captured_at": cap_at,
                    "type": "image_transcript",
                    "system_id": entry.get("system_id"),
                    "data": rec
                }
                check_and_add(rec_str, hit_base)

        # G. System Activity
        for a in self.activities:
            act_str = f"{a['activity_id']} {a['resource_id']} {a['details']}"
            hit_base = {
                "activity_id": a["activity_id"],
                "event_time": a["event_time"],
                "type": "system_activity",
                "target_system": a["target_system"],
                "resource_id": a["resource_id"],
                "reported_result": a["reported_result"],
                "details": a["details"]
            }
            check_and_add(act_str, hit_base)

        return case_hits
