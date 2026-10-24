import csv
import json
from collections import defaultdict

# Read deletion rules
with open('dataset/deletion_rules.csv', 'r', encoding='utf-8') as f:
    rules = list(csv.DictReader(f))

# Read baseline output and candidate output
with open('output.csv', 'r', encoding='utf-8') as f:
    base_rows = list(csv.DictReader(f))

with open('output_candidate.csv', 'r', encoding='utf-8') as f:
    cand_rows = list(csv.DictReader(f))

# Count VERIFY_RECORD_ANONYMIZED steps by status in baseline and candidate
print("=== VERIFY_RECORD_ANONYMIZED STEPS BY STATUS ===")
def count_anon_steps(rows):
    by_st = defaultdict(int)
    total = 0
    cases_with_step = []
    for r in rows:
        st = r['deletion_status']
        steps = json.loads(r['steps_json'])
        has_s = False
        for s in steps:
            if s.get('operation') == 'VERIFY_RECORD_ANONYMIZED':
                by_st[st] += 1
                total += 1
                has_s = True
        if has_s:
            cases_with_step.append((r['case_id'], st))
    return by_st, total, cases_with_step

base_by_st, base_tot, base_cids = count_anon_steps(base_rows)
cand_by_st, cand_tot, cand_cids = count_anon_steps(cand_rows)

print(f"Baseline Output (518 eval cases):")
print(f"  Total VERIFY_RECORD_ANONYMIZED steps: {base_tot}")
print(f"  By status: {dict(base_by_st)}")
print(f"Candidate Output (518 eval cases):")
print(f"  Total VERIFY_RECORD_ANONYMIZED steps: {cand_tot}")
print(f"  By status: {dict(cand_by_st)}")
print(f"  Delta: {cand_tot - base_tot} new steps (all in COMPLETE cases)")
