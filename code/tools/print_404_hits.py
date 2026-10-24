import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.tools.diff_oracle import diff_oracle_against_pipeline

def main():
    discrepancies, hits = diff_oracle_against_pipeline()
    p404_hits = [h for h in hits if h.get("classification") == "PROOF_OF_ABSENCE_LOG_404"]
    print(f"Total PROOF_OF_ABSENCE_LOG_404 hits: {len(p404_hits)}")
    for idx, h in enumerate(p404_hits, 1):
        print(f"[{idx:>2}] Case: {h.get('case_id'):<10} File: {h.get('file'):<45} Matched: {h.get('term')}")
        print(f"     Excerpt: {h.get('line', '').strip()[:140]}")

if __name__ == "__main__":
    main()
