import glob
import re

for f in glob.glob("dataset/evidence/**/*.*", recursive=True):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        c = fp.read()
        if "IDENTIFIABLE" in c:
            lines = [l.strip() for l in c.splitlines() if "IDENTIFIABLE" in l]
            print(f, f"-> {len(lines)} lines with IDENTIFIABLE")
            for l in lines[:3]:
                print("  ", l[:120])
