"""
Determinism Test: Verifies byte-identical output across consecutive clean runs.
"""

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.main import run_deletion_audit
from code.config import OUTPUT_CSV_PATH

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_determinism():
    print("Testing pipeline determinism...")
    # First run
    run_deletion_audit()
    hash1 = sha256_file(OUTPUT_CSV_PATH)
    print(f"Run 1 SHA-256: {hash1}")

    # Second run
    run_deletion_audit()
    hash2 = sha256_file(OUTPUT_CSV_PATH)
    print(f"Run 2 SHA-256: {hash2}")

    assert hash1 == hash2, f"Pipeline is non-deterministic! {hash1} != {hash2}"
    print("[PASS] Determinism verified: byte-identical SHA-256 hash.")

if __name__ == "__main__":
    test_determinism()
