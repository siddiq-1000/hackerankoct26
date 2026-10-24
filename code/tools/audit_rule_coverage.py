import csv
import json
from pathlib import Path
from collections import defaultdict

# Load deletion_rules.csv
rules = list(csv.DictReader(open('dataset/deletion_rules.csv', 'r', encoding='utf-8')))

# Load output.csv
with open('output.csv', 'r', encoding='utf-8') as f:
    outputs = list(csv.DictReader(f))

# Count operations and system_ids in output.csv
step_counts_by_system = defaultdict(int)
step_counts_by_op = defaultdict(int)
for r in outputs:
    steps = json.loads(r['steps_json'])
    for s in steps:
        step_counts_by_system[s['system_id']] += 1
        step_counts_by_op[(s['system_id'], s['operation'])] += 1

print("=== RULE COVERAGE AUDIT (15 RULES) ===")
# Map each rule to system_id and category
# rule_01: USER_PROFILE -> account_service
# rule_02: SECONDARY_IDENTIFIER -> identity_service
# rule_03: SEARCH_INDEX_ENTRY -> search_service
# rule_04: CACHE_ENTRY -> cache
# rule_05: SUPPORT_MESSAGE -> support_platform
# rule_06: SUPPORT_ATTACHMENT -> support_platform (attachment)
# rule_07: ANALYTICS_PROFILE -> analytics_platform
# rule_08: PRODUCT_TELEMETRY -> telemetry
# rule_09: USER_EXPORT -> export_service
# rule_10: MARKETING_PROFILE -> marketing
# rule_11: EMAIL_DELIVERY_LOG -> notification_delivery
# rule_12: SECURITY_AUDIT_LOG -> security_service
# rule_13: LEGAL_HOLD_RECORD -> legal
# rule_14: BACKUP_ARCHIVE -> backup_service
# rule_15: ACCOUNT_TOMBSTONE -> identity_service

rule_system_map = {
    'rule_01': ('USER_PROFILE', 'account_service', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_02': ('SECONDARY_IDENTIFIER', 'identity_service', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_03': ('SEARCH_INDEX_ENTRY', 'search_service', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_04': ('CACHE_ENTRY', 'cache_service', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_05': ('SUPPORT_MESSAGE', 'support_platform', ['REDACT_RECORD', 'VERIFY_RECORD_REDACTED', 'REPORT_EXPOSED_PII']),
    'rule_06': ('SUPPORT_ATTACHMENT', 'support_platform', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_07': ('ANALYTICS_PROFILE', 'analytics_platform', ['ANONYMIZE_RECORD', 'VERIFY_RECORD_ANONYMIZED', 'REPORT_EXPOSED_PII']),
    'rule_08': ('PRODUCT_TELEMETRY', 'telemetry_service', ['ANONYMIZE_RECORD', 'VERIFY_RECORD_ANONYMIZED']),
    'rule_09': ('USER_EXPORT', 'export_service', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_10': ('MARKETING_PROFILE', 'marketing_platform', ['DELETE_RECORD', 'VERIFY_RECORD_ABSENT']),
    'rule_11': ('EMAIL_DELIVERY_LOG', 'notification_service', ['REDACT_RECORD', 'VERIFY_RECORD_REDACTED']),
    'rule_12': ('SECURITY_AUDIT_LOG', 'security_service', ['VERIFY_RECORD_PRESENT']),
    'rule_13': ('LEGAL_HOLD_RECORD', 'legal_service', ['VERIFY_RECORD_PRESENT']),
    'rule_14': ('BACKUP_ARCHIVE', 'backup_service', ['BLOCK_RESTORE', 'VERIFY_RESTORE_BLOCKED', 'REPORT_RESTORE_RISK']),
    'rule_15': ('ACCOUNT_TOMBSTONE', 'identity_service', ['REDACT_RECORD', 'VERIFY_RECORD_REDACTED'])
}

# Scan raw evidence for mentions of each category
evidence_mentions = defaultdict(int)
for p in Path('dataset/evidence').rglob('*'):
    if p.is_file():
        txt = p.read_text(encoding='utf-8', errors='ignore').lower()
        if 'search_' in txt or 'search_index' in txt:
            evidence_mentions['SEARCH_INDEX_ENTRY'] += 1
        if 'cache_' in txt:
            evidence_mentions['CACHE_ENTRY'] += 1
        if 'support_' in txt:
            evidence_mentions['SUPPORT_MESSAGE'] += 1
        if 'attachment' in txt:
            evidence_mentions['SUPPORT_ATTACHMENT'] += 1
        if 'analytics_' in txt:
            evidence_mentions['ANALYTICS_PROFILE'] += 1
        if 'telemetry' in txt:
            evidence_mentions['PRODUCT_TELEMETRY'] += 1
        if 'export_' in txt:
            evidence_mentions['USER_EXPORT'] += 1
        if 'marketing' in txt:
            evidence_mentions['MARKETING_PROFILE'] += 1
        if 'notification_delivery' in txt or 'email_delivery' in txt:
            evidence_mentions['EMAIL_DELIVERY_LOG'] += 1
        if 'audit_record' in txt:
            evidence_mentions['SECURITY_AUDIT_LOG'] += 1
        if 'legal_hold' in txt:
            evidence_mentions['LEGAL_HOLD_RECORD'] += 1
        if 'backup_' in txt:
            evidence_mentions['BACKUP_ARCHIVE'] += 1
        if 'tombstone' in txt:
            evidence_mentions['ACCOUNT_TOMBSTONE'] += 1

print(f"| Rule ID | Category | Evidence Files Present | Output Steps Emitted | Status |")
print(f"|---|---|---|---|---|")
for r in rules:
    rid = r['rule_id']
    cat = r['data_category']
    info = rule_system_map.get(rid, (cat, '', []))
    sys_name = info[1]
    steps_count = step_counts_by_system.get(sys_name, 0)
    ev_count = evidence_mentions.get(cat, 0)
    status = "Active" if steps_count > 0 else "0 Steps Emitted"
    print(f"| `{rid}` | `{cat}` | {ev_count} files | {steps_count} steps (`{sys_name}`) | {status} |")

# Specific check for rule_11 (email delivery log)
print("\n=== RULE_11 SPECIFIC CHECK ===")
deliv_files = list(Path('dataset/evidence/logs').glob('*notification_delivery*'))
print(f"Notification delivery log files: {len(deliv_files)}")
has_subject_email = False
for f in deliv_files:
    for line in open(f, 'r', encoding='utf-8', errors='ignore'):
        if '@' in line:
            print(f"Found email in {f.name}: {line.strip()[:120]}")
            has_subject_email = True
            break
if not has_subject_email:
    print("Zero email addresses found in any notification delivery log.")
