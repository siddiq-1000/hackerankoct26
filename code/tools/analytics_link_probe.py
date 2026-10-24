"""Comprehensive Analytics Linking Probe and Ground Truth Analysis for D1/D2."""

import csv
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def parse_iso(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def run_probe():
    with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
        sample_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

    with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
        sample_reqs = list(csv.DictReader(f))

    with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
        full_reqs = list(csv.DictReader(f))

    with open('output.csv', 'r', encoding='utf-8') as f:
        full_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

    with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
        users_by_email = {r['email']: r for r in csv.DictReader(f)}

    with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
        activity = list(csv.DictReader(f))

    with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
        ev_files = {r['file_id']: r for r in csv.DictReader(f)}

    # D1.1 Seven sample COMPLETE cases
    cases_7 = ['case_03', 'case_04', 'case_21', 'case_25', 'case_26', 'case_27', 'case_28']
    
    print("=" * 80)
    print("D1.1 THE 7 SAMPLE COMPLETE CASES WITH ANALYTICS VERIFICATION")
    print("=" * 80)

    for cid in cases_7:
        steps = sample_out[cid][1]
        acc_step = [s for s in steps if s['system_id'] == 'account_service'][0]
        ana_step = [s for s in steps if s['system_id'] == 'analytics_platform'][0]
        acc_rid = acc_step['resource_id']
        ana_rid = ana_step['resource_id']

        acc_acts = [a for a in activity if a['resource_id'] == acc_rid]
        ana_acts = [a for a in activity if a['resource_id'] == ana_rid]

        print(f"\n--- {cid} ---")
        print(f"  Account: {acc_rid}")
        if acc_acts:
            print(f"    Event: {acc_acts[0]['activity_id']} | {acc_acts[0]['event_time']} | {acc_acts[0]['details']}")
        else:
            print("    Event: (Direct evidence in snapshot)")
        print(f"  Analytics: {ana_rid} ({ana_step['evidence_id']})")
        if ana_acts:
            print(f"    Event: {ana_acts[0]['activity_id']} | {ana_acts[0]['event_time']} | {ana_acts[0]['details']}")
        if acc_acts and ana_acts:
            t1 = parse_iso(acc_acts[0]['event_time'])
            t2 = parse_iso(ana_acts[0]['event_time'])
            delta = abs((t2 - t1).total_seconds())
            print(f"    Timestamp Delta: {delta:.0f}s ({delta/60:.1f} min)")

    # Index anonymized evidence records
    anon_evidence = defaultdict(list)
    file_analytics_counts = defaultdict(lambda: {'total': 0, 'anonymized': 0, 'exposed_pii': 0})
    for fid, ef in ev_files.items():
        p = Path('dataset') / ef['file_path']
        if not p.exists():
            continue
        cap = parse_iso(ef['captured_at'])
        if p.suffix == '.json':
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                def extract(o):
                    if isinstance(o, dict):
                        rid = o.get('resource_id')
                        if rid and 'analytics_' in rid:
                            file_analytics_counts[fid]['total'] += 1
                            if not (o.get('email') or o.get('phone') or o.get('user_id')):
                                anon_evidence[rid].append((fid, cap))
                                file_analytics_counts[fid]['anonymized'] += 1
                            else:
                                file_analytics_counts[fid]['exposed_pii'] += 1
                        for v in o.values():
                            extract(v)
                    elif isinstance(o, list):
                        for it in o:
                            extract(it)
                extract(data)
            except Exception:
                pass
        elif p.suffix == '.log':
            try:
                for l in open(p, 'r', encoding='utf-8', errors='ignore'):
                    if 'analytics_' in l and ('analytics_profile_read_completed' in l or 'analytics_identity_scan' in l):
                        m = re.search(r'(analytics_\d+)', l)
                        if m:
                            file_analytics_counts[fid]['total'] += 1
                            if 'email=null' in l:
                                anon_evidence[m.group(1)].append((fid, cap))
                                file_analytics_counts[fid]['anonymized'] += 1
                            else:
                                file_analytics_counts[fid]['exposed_pii'] += 1
            except Exception:
                pass
        elif p.suffix == '.sql':
            try:
                for l in open(p, 'r', encoding='utf-8', errors='ignore'):
                    if 'customer_analytics_profiles' in l and 'analytics_' in l:
                        m = re.search(r"'(analytics_\d+)'", l)
                        if m:
                            file_analytics_counts[fid]['total'] += 1
                            if 'NULL, NULL, NULL' in l:
                                anon_evidence[m.group(1)].append((fid, cap))
                                file_analytics_counts[fid]['anonymized'] += 1
                            else:
                                file_analytics_counts[fid]['exposed_pii'] += 1
            except Exception:
                pass

    anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
    anon_events.sort(key=lambda x: x['event_time'])

    # D1.2 Probe on 32 sample cases
    print("\n" + "=" * 80)
    print("D1.2 PROBE ON 32 SAMPLE CASES (PRECISION / RECALL)")
    print("=" * 80)

    # Let's test the strict 1-to-1 batch linking on sample cases
    sample_complete = [r for r in sample_reqs if sample_out[r['case_id']][0] == 'COMPLETE']
    batches = defaultdict(list)
    for r in sample_complete:
        rep_dt = parse_iso(r['reported_at'])
        if rep_dt:
            key = rep_dt.strftime('%Y-%m-%d %H')
            batches[key].append(r)

    paired_sample = {}
    for bkey, b_reqs in batches.items():
        b_rep_dts = [parse_iso(r['reported_at']) for r in b_reqs]
        min_dt = min(b_rep_dts) - timedelta(minutes=60)
        max_dt = max(b_rep_dts) + timedelta(minutes=5)
        b_events = [a for a in anon_events if min_dt <= parse_iso(a['event_time']) <= max_dt]
        if len(b_reqs) == len(b_events):
            b_reqs.sort(key=lambda r: users_by_email.get(r['email'], {}).get('user_id', r['case_id']))
            b_events.sort(key=lambda a: a['resource_id'])
            for r, ev in zip(b_reqs, b_events):
                aud_dt = parse_iso(r['audit_at'])
                rid = ev['resource_id']
                cands = [(fid, cap) for fid, cap in anon_evidence[rid] if cap <= aud_dt]
                if cands:
                    cands.sort(key=lambda x: x[1], reverse=True)
                    paired_sample[r['case_id']] = (rid, cands[0][0])

    print(f"Sample COMPLETE cases: 10 total (7 ground-truth positive, 3 ground-truth negative)")
    print(f"Sample cases paired by 1-to-1 batch link: {len(paired_sample)}")
    for cid, (rid, fid) in sorted(paired_sample.items()):
        gt_steps = [s for s in sample_out[cid][1] if s['system_id'] == 'analytics_platform']
        gt_str = f"({gt_steps[0]['resource_id']}, {gt_steps[0]['evidence_id']})" if gt_steps else "None"
        exact_match = (gt_steps and gt_steps[0]['resource_id'] == rid and gt_steps[0]['evidence_id'] == fid)
        print(f"  {cid}: predicted=({rid}, {fid}) | ground_truth={gt_str} | exact_match={exact_match}")

    # Check false positives on other 3 COMPLETE cases
    neg_complete = ['case_01', 'case_02', 'case_31']
    fp_complete = [cid for cid in neg_complete if cid in paired_sample]
    print(f"False positives on other 3 sample COMPLETE cases: {len(fp_complete)} {fp_complete}")

    # Check false positives on 22 INCOMPLETE cases
    sample_incomplete = [r for r in sample_reqs if sample_out[r['case_id']][0] != 'COMPLETE']
    fp_incomplete = [r['case_id'] for r in sample_incomplete if r['case_id'] in paired_sample]
    print(f"False positives on 22 sample INCOMPLETE cases: {len(fp_incomplete)} {fp_incomplete}")

    # D1.3 Probe on full 518 cases
    print("\n" + "=" * 80)
    print("D1.3 PROBE ON FULL 518 CASES (READ-ONLY ANALYSIS)")
    print("=" * 80)

    complete_cases = [r for r in full_reqs if full_out[r['case_id']][0] == 'COMPLETE']
    full_batches = defaultdict(list)
    for r in complete_cases:
        rep_dt = parse_iso(r['reported_at'])
        if rep_dt:
            key = rep_dt.strftime('%Y-%m-%d %H')
            full_batches[key].append(r)

    paired_full = {}
    ambiguous_batches = 0
    unpaired_cases = 0

    for bkey, b_reqs in full_batches.items():
        b_rep_dts = [parse_iso(r['reported_at']) for r in b_reqs]
        min_dt = min(b_rep_dts) - timedelta(minutes=60)
        max_dt = max(b_rep_dts) + timedelta(minutes=5)
        b_events = [a for a in anon_events if min_dt <= parse_iso(a['event_time']) <= max_dt]

        if len(b_reqs) == len(b_events):
            b_reqs.sort(key=lambda r: users_by_email.get(r['email'], {}).get('user_id', r['case_id']))
            b_events.sort(key=lambda a: a['resource_id'])
            for r, ev in zip(b_reqs, b_events):
                aud_dt = parse_iso(r['audit_at'])
                rid = ev['resource_id']
                cands = [(fid, cap) for fid, cap in anon_evidence[rid] if cap <= aud_dt]
                if cands:
                    cands.sort(key=lambda x: x[1], reverse=True)
                    paired_full[r['case_id']] = (rid, cands[0][0], ev)
        else:
            ambiguous_batches += 1
            unpaired_cases += len(b_reqs)

    print(f"Total COMPLETE cases: {len(complete_cases)}")
    print(f"Cases in PERFECT 1-to-1 batches with valid evidence: {len(paired_full)}")
    print(f"Ambiguous batches (case count != event count): {ambiguous_batches} (covering {unpaired_cases} cases)")

    print("\n10 Representative Examples of Linked COMPLETE cases:")
    for cid, (rid, fid, ev) in list(paired_full.items())[:10]:
        print(f"  {cid}: linked_resource={rid}, evidence={fid}, activity={ev['activity_id']} ({ev['event_time']})")

    # D1.4 Reconciliation
    print("\n" + "=" * 80)
    print("D1.4 RECONCILIATION OF ANALYTICS COUNTS")
    print("=" * 80)
    tot_all = sum(v['total'] for v in file_analytics_counts.values())
    tot_anon = sum(v['anonymized'] for v in file_analytics_counts.values())
    tot_pii = sum(v['exposed_pii'] for v in file_analytics_counts.values())
    print(f"Total appearances across all evidence files: {tot_all}")
    print(f"  - Anonymized records (all PII null):     {tot_anon}")
    print(f"  - Exposed PII records:                   {tot_pii}")
    print(f"Total evidence files with analytics records: {sum(1 for v in file_analytics_counts.values() if v['total'] > 0)}")

if __name__ == '__main__':
    run_probe()
