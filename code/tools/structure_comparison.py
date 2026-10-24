import csv
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 1. Load sample_output.csv COMPLETE rows
sample_complete_step_sets = {}
sample_step_tuples = Counter()
with open(REPO_ROOT / "dataset" / "sample_output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["deletion_status"] == "COMPLETE":
            steps = json.loads(r["steps_json"])
            tuple_set = frozenset((s["system_id"], s["operation"]) for s in steps)
            sample_complete_step_sets[r["case_id"]] = tuple_set
            for s in steps:
                sample_step_tuples[(s["system_id"], s["operation"])] += 1

# 2. Load full-run output.csv COMPLETE rows
full_complete_step_sets = {}
full_step_tuples = Counter()
full_complete_requests = {}
with open(REPO_ROOT / "dataset" / "deletion_requests.csv", "r", encoding="utf-8") as f:
    requests = {r["case_id"]: r for r in csv.DictReader(f)}

with open(REPO_ROOT / "output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["deletion_status"] == "COMPLETE":
            steps = json.loads(r["steps_json"])
            tuple_set = frozenset((s["system_id"], s["operation"]) for s in steps)
            full_complete_step_sets[r["case_id"]] = tuple_set
            full_complete_requests[r["case_id"]] = requests.get(r["case_id"])
            for s in steps:
                full_step_tuples[(s["system_id"], s["operation"])] += 1

print(f"Sample COMPLETE count: {len(sample_complete_step_sets)}")
print(f"Full-run COMPLETE count: {len(full_complete_step_sets)}")

print("\n--- Step types in Sample COMPLETE ---")
for k, v in sample_step_tuples.items():
    print(f"  {k}: {v}")

print("\n--- Step types in Full-Run COMPLETE ---")
for k, v in full_step_tuples.items():
    print(f"  {k}: {v}")

# Distinct set patterns in sample
sample_patterns = set(sample_complete_step_sets.values())
print(f"\nDistinct step-set patterns in sample: {len(sample_patterns)}")
for p in sample_patterns:
    print(f"  Pattern: {sorted(list(p))}")

# Check full-run cases against sample patterns
differing = {}
for cid, p in full_complete_step_sets.items():
    if p not in sample_patterns:
        differing[cid] = (p, full_complete_requests[cid])

print(f"\nFull-run COMPLETE rows whose step-set differs from every sample COMPLETE pattern: {len(differing)}")
step_counts = Counter(len(p) for p in full_complete_step_sets.values())
print(f"Step count distribution in full-run COMPLETE: {step_counts}")

# Check single-step COMPLETE cases
single_step_cases = [cid for cid, p in full_complete_step_sets.items() if len(p) == 1]
print(f"Single-step COMPLETE cases count: {len(single_step_cases)}")

# Check reported_status of full-run COMPLETE rows
rep_status_dist = Counter(req["reported_status"] for req in full_complete_requests.values() if req)
print(f"Reported status distribution of full-run COMPLETE rows: {rep_status_dist}")
