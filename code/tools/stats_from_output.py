#!/usr/bin/env python3
"""
Independent Statistics and Reconciler Tool for Ghost Data Still Exists.
Implements Section A1 requirements from HackerRank Orchestrate (October 2026) Brief 3B.

Reads ONLY output.csv and dataset/deletion_requests.csv (and sample files) to compute
status counts, step distributions, (system_id, operation) frequency tables, and reconciliations.
"""

import csv
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_CSV = REPO_ROOT / "output.csv"
FULL_REQS_CSV = REPO_ROOT / "dataset" / "deletion_requests.csv"
SAMPLE_OUTPUT_CSV = REPO_ROOT / "dataset" / "sample_output.csv"
SAMPLE_REQS_CSV = REPO_ROOT / "dataset" / "sample_deletion_requests.csv"


def analyze_dataset(output_path: Path, requests_path: Path, label: str):
    print("=" * 70)
    print(f"DATASET ANALYSIS: {label}")
    print(f"Output File:   {output_path.relative_to(REPO_ROOT) if output_path.is_relative_to(REPO_ROOT) else output_path}")
    print(f"Requests File: {requests_path.relative_to(REPO_ROOT) if requests_path.is_relative_to(REPO_ROOT) else requests_path}")
    print("=" * 70)

    # 1. Load requests map: case_id -> reported_status
    req_status_map = {}
    with open(requests_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            req_status_map[r["case_id"]] = r["reported_status"]

    total_requests = len(req_status_map)

    # 2. Load output rows
    status_counts = Counter()
    complete_step_counts = Counter()
    complete_sys_op_counts = Counter()
    complete_by_reported_status = Counter()

    complete_cases = []

    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cid = r["case_id"]
            del_status = r["deletion_status"]
            status_counts[del_status] += 1

            if del_status == "COMPLETE":
                steps = json.loads(r["steps_json"])
                num_steps = len(steps)
                complete_step_counts[num_steps] += 1
                rep_stat = req_status_map.get(cid, "UNKNOWN")
                complete_by_reported_status[rep_stat] += 1
                complete_cases.append((cid, rep_stat, num_steps, steps))

                for s in steps:
                    sys_id = s.get("system_id", "")
                    op = s.get("operation", "")
                    complete_sys_op_counts[(sys_id, op)] += 1

    total_output_rows = sum(status_counts.values())
    total_complete = status_counts["COMPLETE"]

    # 3. Print Status Counts
    print(f"\n[1] Overall Deletion Status Distribution ({total_output_rows} rows):")
    for st, cnt in sorted(status_counts.items()):
        pct = (cnt / total_output_rows) * 100 if total_output_rows else 0
        print(f"    {st:<15}: {cnt:>4} ({pct:>6.2f}%)")

    # 4. Print Step Count Distribution for COMPLETE rows
    print(f"\n[2] Distribution of Step Counts for COMPLETE Cases ({total_complete} cases):")
    sum_steps_from_counts = 0
    for num_steps, cnt in sorted(complete_step_counts.items()):
        total_for_bin = num_steps * cnt
        sum_steps_from_counts += total_for_bin
        print(f"    {cnt:>4} cases with {num_steps} step(s) -> {total_for_bin:>4} steps")
    print(f"    ------------------------------------")
    print(f"    Total Steps Across Complete Cases: {sum_steps_from_counts}")

    # 5. Print (system_id, operation) table for COMPLETE rows
    print(f"\n[3] (system_id, operation) Step Counts for COMPLETE Cases:")
    print(f"    {'System ID':<25} {'Operation':<28} {'Count':>6}")
    print(f"    {'-'*25} {'-'*28} {'-'*6}")
    total_sys_op_steps = sum(complete_sys_op_counts.values())
    for (sys_id, op), cnt in sorted(complete_sys_op_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"    {sys_id:<25} {op:<28} {cnt:>6}")
    print(f"    {'-'*25} {'-'*28} {'-'*6}")
    print(f"    {'TOTAL STEPS':<25} {'':<28} {total_sys_op_steps:>6}")

    # Check reconciliation
    reconciled = (sum_steps_from_counts == total_sys_op_steps)
    print(f"\n[*] Reconciliation Check: sum(step_counts) == sum(sys_op_counts): {sum_steps_from_counts} == {total_sys_op_steps} -> {'PASS' if reconciled else 'FAIL'}")

    # 6. Print COMPLETE by reported_status
    print(f"\n[4] COMPLETE Cases by reported_status (Sum = {total_complete}):")
    for rep_st in ["NOT_STARTED", "PARTIALLY_COMPLETE", "COMPLETE"]:
        cnt = complete_by_reported_status[rep_st]
        pct = (cnt / total_complete) * 100 if total_complete else 0
        print(f"    {rep_st:<20}: {cnt:>4} ({pct:>6.2f}%)")
    print(f"    ------------------------------------")
    sum_reported = sum(complete_by_reported_status.values())
    print(f"    {'TOTAL COMPLETE':<20}: {sum_reported:>4} (Check == {total_complete}: {'PASS' if sum_reported == total_complete else 'FAIL'})")

    return {
        "status_counts": status_counts,
        "complete_step_counts": complete_step_counts,
        "complete_sys_op_counts": complete_sys_op_counts,
        "complete_by_reported_status": complete_by_reported_status,
        "reconciled": reconciled
    }


def main():
    print("=" * 70)
    print("HACKERRANK ORCHESTRATE - RECONCILIATION & STATS FROM OUTPUT.CSV")
    print("Command: python code/tools/stats_from_output.py")
    print("=" * 70)

    # 1. Full Dataset Run
    full_stats = analyze_dataset(OUTPUT_CSV, FULL_REQS_CSV, "Full Evaluation Dataset (518 cases)")

    # 2. Public Sample Ground Truth
    sample_stats = analyze_dataset(SAMPLE_OUTPUT_CSV, SAMPLE_REQS_CSV, "Public Sample Ground Truth (32 cases)")

    print("\n" + "=" * 70)
    print("STATISTICS RUN COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    main()
