#!/usr/bin/env python3
"""
Packaging and Verification Tool for Ghost Data Still Exists.
Implements Gate 6 requirements from HackerRank Orchestrate (October 2026) Brief 3.

Creates code.zip with exact allowed files and tests extracted execution
against repo output.csv for byte-identical determinism.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_ZIP = REPO_ROOT / "code.zip"
REFERENCE_CSV = REPO_ROOT / "output.csv"
DATASET_DIR = REPO_ROOT / "dataset"

EXCLUDED_DIRS = {
    ".git", ".github", "__pycache__", "venv", ".venv", "env",
    "dataset", ".pytest_cache", ".mypy_cache", ".idea", ".vscode"
}
EXCLUDED_FILES = {
    "output.csv", "log.txt", ".env", "code.zip", ".DS_Store", "Thumbs.db",
    "sample_pred.csv"
}
EXCLUDED_EXTS = {".pyc", ".pyo", ".pyd", ".zip", ".tar", ".gz"}


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_submission_zip():
    print("=" * 60)
    print("CREATING SUBMISSION PACKAGE: code.zip")
    print("=" * 60)

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    included_entries = []

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Package code/
        code_dir = REPO_ROOT / "code"
        for root, dirs, files in os.walk(code_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                fpath = Path(root) / file
                if file in EXCLUDED_FILES or fpath.suffix.lower() in EXCLUDED_EXTS:
                    continue
                rel_path = fpath.relative_to(REPO_ROOT).as_posix()
                zf.write(fpath, arcname=rel_path)
                included_entries.append(rel_path)

        # 2. Package evaluation reports at top-level evaluation/ to satisfy AGENTS.md §6.8
        for rep_name in ["evaluation_report.md", "usage_report.md"]:
            src = REPO_ROOT / "code" / "evaluation" / rep_name
            if src.exists():
                arc_name = f"evaluation/{rep_name}"
                zf.write(src, arcname=arc_name)
                included_entries.append(arc_name)

        # 3. Package root markdown and requirements
        root_files = ["README.md", "requirements.txt"]
        for rf_name in root_files:
            rf = REPO_ROOT / rf_name
            if rf.exists():
                rel_path = rf.name
                zf.write(rf, arcname=rel_path)
                included_entries.append(rel_path)

    # Verify both copies are present and identical in the closed archive
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
        for rep_name in ["evaluation_report.md", "usage_report.md"]:
            top_bytes = zf.read(f"evaluation/{rep_name}")
            code_bytes = zf.read(f"code/evaluation/{rep_name}")
            assert top_bytes == code_bytes, f"Mismatch between code/evaluation/{rep_name} and evaluation/{rep_name}"
    print("[*] Verified: evaluation/ and code/evaluation/ reports are byte-identical in code.zip")

    zip_size = OUTPUT_ZIP.stat().st_size
    print(f"[*] Packaged {len(included_entries)} files into {OUTPUT_ZIP.name}")
    print(f"[*] Package size: {zip_size:,} bytes ({zip_size / 1024:.2f} KB)")
    return included_entries


def verify_extracted_run():
    print("\n" + "=" * 60)
    print("VERIFYING CLEAN EXTRACTED RUN (GATE 6)")
    print("=" * 60)

    if not REFERENCE_CSV.exists():
        print(f"[FAIL] Reference output.csv not found at {REFERENCE_CSV}")
        return False

    ref_hash = compute_sha256(REFERENCE_CSV)
    print(f"[*] Reference output.csv SHA-256: {ref_hash}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"[*] Extracting package to isolated sandbox: {temp_path}")
        with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
            zf.extractall(temp_path)

        # Confirm expected structure
        required_items = [
            temp_path / "code" / "main.py",
            temp_path / "README.md",
            temp_path / "evaluation" / "evaluation_report.md",
            temp_path / "evaluation" / "usage_report.md"
        ]
        for ri in required_items:
            if not ri.exists():
                print(f"[FAIL] Missing required artifact in archive: {ri.relative_to(temp_path)}")
                return False

        # Run pipeline from extracted directory
        target_output = temp_path / "output.csv"
        cmd = [
            sys.executable,
            str(temp_path / "code" / "main.py"),
            "--dataset-dir", str(DATASET_DIR),
            "--output", str(target_output)
        ]

        print("[*] Executing extraction test: python code/main.py ...")
        test_env = os.environ.copy()
        test_env["DATASET_DIR"] = str(DATASET_DIR)
        proc = subprocess.run(cmd, cwd=str(temp_path), env=test_env, capture_output=True, text=True)

        if proc.returncode != 0:
            print("[FAIL] Extracted execution failed with non-zero exit code:")
            print(proc.stderr)
            return False

        if not target_output.exists():
            print("[FAIL] Extracted execution did not produce output.csv")
            return False

        test_hash = compute_sha256(target_output)
        print(f"[*] Generated output.csv SHA-256: {test_hash}")

        if test_hash != ref_hash:
            print("[FAIL] Generated output.csv SHA-256 differs from reference output.csv!")
            return False

        print("[PASS] Byte-for-byte SHA-256 identity verified against root output.csv.")
        return True


def main():
    entries = create_submission_zip()
    ok = verify_extracted_run()

    print("\n" + "=" * 60)
    if ok:
        print("GATE 6 RESULT: PASS")
        print(f"Total files in code.zip: {len(entries)}")
        print(f"Archive Size: {OUTPUT_ZIP.stat().st_size:,} bytes")
        print("=" * 60)
        sys.exit(0)
    else:
        print("GATE 6 RESULT: FAIL")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
