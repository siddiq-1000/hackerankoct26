import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict

def parse_iso(ts):
    if not ts: return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    sample_out = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_reqs = list(csv.DictReader(f))

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activity = list(csv.DictReader(f))

anon_events = [a for a in activity if a['event_type'] == 'ANONYMIZE_RECORD' and a['target_system'] == 'analytics_platform']
anon_events.sort(key=lambda x: x['event_time'])

sample_complete = [r for r in sample_reqs if sample_out[r['case_id']][0] == 'COMPLETE']
batches = defaultdict(list)
for r in sample_complete:
    rep_dt = parse_iso(r['reported_at'])
    if rep_dt:
        key = rep_dt.strftime('%Y-%m-%d %H')
        batches[key].append(r)

print("=== SAMPLE COMPLETE BATCHES ===")
size_counts = defaultdict(int)
for bkey, b_reqs in sorted(batches.items()):
    b_rep_dts = [parse_iso(r['reported_at']) for r in b_reqs]
    min_dt = min(b_rep_dts) - timedelta(minutes=60)
    max_dt = max(b_rep_dts) + timedelta(minutes=5)
    b_events = [a for a in anon_events if min_dt <= parse_iso(a['event_time']) <= max_dt]
    cids = [r['case_id'] for r in b_reqs]
    size_counts[len(b_reqs)] += 1
    print(f"Batch {bkey}: {len(b_reqs)} request(s), {len(b_events)} event(s) | Cases: {cids}")

print(f"\nSample batch size distribution: {dict(size_counts)}")
print(f"Number of multi-case sample batches (size >= 2): {sum(v for k, v in size_counts.items() if k >= 2)}")
