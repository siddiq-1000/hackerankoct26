import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from code.config import DATASET_DIR

class SqlDatabaseManager:
    def __init__(self, databases_dir: Optional[Path] = None):
        self.databases_dir = databases_dir or (DATASET_DIR / "evidence" / "databases")
        self.databases: Dict[str, sqlite3.Connection] = {}
        self.metadata: Dict[str, dict] = {}
        self._load_all_databases()

    def _determine_role_and_system(self, filename: str) -> dict:
        fn = filename.lower()
        if "failover" in fn:
            role = "failover_replica"
        elif "regional" in fn:
            role = "regional_replica"
        elif "reporting" in fn:
            role = "reporting_replica"
        elif "read_replica" in fn:
            role = "read_replica"
        elif "search" in fn:
            role = "search_primary"
        else:
            role = "inventory"

        system_id = "account_service"
        if "search" in fn:
            system_id = "search_service"
        return {"role": role, "system_id": system_id}

    def _load_all_databases(self):
        sql_files = list(self.databases_dir.glob("*.sql"))
        for sf in sql_files:
            conn = sqlite3.connect(":memory:")
            with open(sf, "r", encoding="utf-8") as f:
                sql_script = f.read()
            try:
                conn.executescript(sql_script)
                self.databases[sf.name] = conn
                self.metadata[sf.name] = self._determine_role_and_system(sf.name)
            except Exception as e:
                print(f"[ERROR] Failed to load SQL {sf.name}: {e}")

    def search_database(self, filename: str, search_terms: List[str]) -> List[dict]:
        conn = self.databases.get(filename)
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        hits = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            cols = [c[1] for c in cursor.fetchall()]
            
            # Fetch all rows from table
            cursor.execute(f"SELECT * FROM {table};")
            rows = cursor.fetchall()

            for row in rows:
                row_dict = dict(zip(cols, row))
                
                matched = []
                for term in search_terms:
                    if not term:
                        continue
                    t_lower = term.lower().strip()
                    # Check exact value in any column first
                    term_matched = False
                    for k, v in row_dict.items():
                        if v is None:
                            continue
                        v_str = str(v).lower().strip()
                        if v_str == t_lower:
                            term_matched = True
                            break
                        # Word boundary match
                        if re.search(r"\b" + re.escape(t_lower) + r"\b", v_str):
                            term_matched = True
                            break
                    if term_matched:
                        matched.append(term)

                if matched:
                    hits.append({
                        "file_name": filename,
                        "table": table,
                        "data": row_dict,
                        "matched_terms": matched,
                        "system_id": self._infer_system(table, filename),
                        "resource_id": row_dict.get("resource_id", "")
                    })
        return hits

    def _infer_system(self, table: str, filename: str) -> str:
        t = table.lower()
        if "search" in t:
            return "search_service"
        if "analytics" in t:
            return "analytics_platform"
        if "support" in t:
            return "support_platform"
        if "connector" in t:
            return "integration_service"
        if "backup" in t:
            return "backup_service"
        if "export" in t:
            return "export_service"
        if "audit" in t:
            return "security_service"
        if "tombstone" in t:
            return "identity_service"
        return "account_service"
