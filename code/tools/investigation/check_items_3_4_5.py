import csv
import json
from pathlib import Path

repo = Path(".")

# Load outputs
with open("output.csv", "r", encoding="utf-8") as f:
    eval_rows = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_rows = {r["case_id"]: r for r in csv.DictReader(f)}

# Load requests
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    eval_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

print("="*60)
print("ITEM 4: COMPLIANT TOMBSTONES")
print("="*60)
tombstone_cases = ["case_543", "case_545", "case_547", "case_549"]
for cid in tombstone_cases:
    r = eval_rows.get(cid)
    print(f"\n--- {cid} ({r['deletion_status']}) ---")
    steps = json.loads(r["steps_json"])
    for s in steps:
        print(" ", s)

print("\n--- SAMPLE CASE_24 (Tombstone Comparison) ---")
s24 = sample_rows.get("case_24")
print(f"case_24 status: {s24['deletion_status']}")
for s in json.loads(s24["steps_json"]):
    print(" ", s)

print("\n--- SAMPLE CASE_31 & CASE_32 (Tombstone Comparison) ---")
for scid in ["case_31", "case_32"]:
    sr = sample_rows.get(scid)
    print(f"{scid} status: {sr['deletion_status']}")
    for s in json.loads(sr["steps_json"]):
        print(" ", s)

print("\n" + "="*60)
print("ITEM 5: LEGAL HOLDS (5 ACTIVE HOLDS)")
print("="*60)
active_hold_cases = ["case_261", "case_390", "case_460", "case_473", "case_505"]
for cid in active_hold_cases:
    r = eval_rows.get(cid)
    print(f"\n--- {cid} ({r['deletion_status']}) ---")
    steps = json.loads(r["steps_json"])
    for s in steps:
        print(" ", s)

print("\n" + "="*60)
print("ITEM 3: CASE_131 AND TARGET ATTACHMENT CASES IN OUTPUT.CSV")
print("="*60)
att_cases = ["case_131", "case_179", "case_203", "case_227", "case_275", "case_311", "case_359", "case_407", "case_431", "case_455", "case_479", "case_503", "case_527"]
for cid in att_cases:
    r = eval_rows.get(cid)
    steps = json.loads(r["steps_json"])
    supp_steps = [s for s in steps if s.get("system_id") == "support_platform"]
    print(f"{cid}: status={r['deletion_status']}, support_steps={len(supp_steps)}")
    for s in supp_steps:
        print("  ", s)
