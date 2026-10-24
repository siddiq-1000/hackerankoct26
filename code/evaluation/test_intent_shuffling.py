import random
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.loaders import DatasetLoader
from code.intent import IntentClassifier

def test_intent_shuffling():
    loader = DatasetLoader()
    requests = loader.load_deletion_requests("deletion_requests.csv")
    clf = IntentClassifier()

    # Original run
    orig_results = {}
    for r in requests:
        orig_results[r.request_text] = clf.is_deletion_request(r.request_text, r.case_id)

    # Shuffled run with dummy case IDs
    shuffled_requests = list(requests)
    random.seed(42)
    random.shuffle(shuffled_requests)

    mismatches = 0
    for idx, r in enumerate(shuffled_requests):
        dummy_cid = f"dummy_case_{idx:04d}"
        shuffled_res = clf.is_deletion_request(r.request_text, dummy_cid)
        if shuffled_res != orig_results[r.request_text]:
            mismatches += 1

    print("==========================================")
    print("INTENT CLASSIFIER CASE-ID INDEPENDENCE TEST")
    print("==========================================")
    print(f"Total requests tested: {len(requests)}")
    print(f"Mismatches on shuffled dummy case IDs: {mismatches}")
    assert mismatches == 0, f"Classifier depends on case_id! {mismatches} mismatches found."
    print("[PASS] Intent classification is 100% case-id independent (decided from request_text only).")
    print("==========================================")

if __name__ == "__main__":
    test_intent_shuffling()
