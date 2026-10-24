import zipfile
import subprocess
import hashlib
from pathlib import Path

repo = Path(".")
zip_path = repo / "code.zip"

zf = zipfile.ZipFile(zip_path, "r")
names = zf.namelist()
print(f"Total entries in code.zip: {len(names)}")
print("\n--- ZIP LISTING (PATHS ONLY) ---")
for n in sorted(names):
    print(n)

# Check dual evaluation copies
top_eval = zf.read("evaluation/evaluation_report.md")
code_eval = zf.read("code/evaluation/evaluation_report.md")
top_usage = zf.read("evaluation/usage_report.md")
code_usage = zf.read("code/evaluation/usage_report.md")

print("\n--- DUAL EVALUATION COPIES VERIFICATION ---")
print("evaluation_report.md matches:", top_eval == code_eval, f"({len(top_eval)} bytes)")
print("usage_report.md matches:", top_usage == code_usage, f"({len(top_usage)} bytes)")
