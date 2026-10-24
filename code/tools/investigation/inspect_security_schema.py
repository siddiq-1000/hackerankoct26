import sqlite3
import glob

for f in sorted(glob.glob("dataset/evidence/databases/*.sql")):
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(open(f, "r", encoding="utf-8", errors="ignore").read())
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "security_audit_records" in tables:
            cols = [c[1] for c in conn.execute("PRAGMA table_info('security_audit_records')").fetchall()]
            rows = conn.execute("SELECT * FROM security_audit_records LIMIT 3").fetchall()
            print(f, "COLS:", cols)
            for r in rows:
                print("  ", r)
            break
    except Exception as e:
        pass
