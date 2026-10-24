import csv
import json
from collections import defaultdict

# Real rules from dataset/deletion_rules.csv
with open('dataset/deletion_rules.csv', 'r', encoding='utf-8') as f:
    rules = list(csv.DictReader(f))

with open('output.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# Mapping from system/category/operation to rule
# rule_01: USER_PROFILE -> account_service DELETE
# rule_02: SECONDARY_IDENTIFIER -> DELETE
# rule_03: SEARCH_INDEX_ENTRY -> search_service DELETE
# rule_04: CACHE_ENTRY -> session_cache DELETE
# rule_05: SUPPORT_MESSAGE -> support_platform REDACT
# rule_06: SUPPORT_ATTACHMENT -> support_platform DELETE
# rule_07: ANALYTICS_PROFILE -> analytics_platform ANONYMIZE
# rule_08: PRODUCT_TELEMETRY -> telemetry_service ANONYMIZE
# rule_09: USER_EXPORT -> export_service DELETE
# rule_10: MARKETING_PROFILE -> marketing_platform DELETE
# rule_11: EMAIL_DELIVERY_LOG -> email_delivery REDACT
# rule_12: SECURITY_AUDIT_LOG -> security_service RETAIN
# rule_13: LEGAL_HOLD_RECORD -> legal_service RETAIN
# rule_14: BACKUP_ARCHIVE -> backup_service RETAIN / BLOCK
# rule_15: ACCOUNT_TOMBSTONE -> identity_service / account_service REDACT

rule_stats = defaultdict(lambda: {'COMPLETE_cases': set(), 'INCOMPLETE_cases': set(), 'total_steps': 0})

for r in rows:
    cid = r['case_id']
    st = r['deletion_status']
    steps = json.loads(r['steps_json'])
    for s in steps:
        sys_id = s.get('system_id', '')
        op = s.get('operation', '')
        rid = s.get('resource_id', '')

        # Classify by rule
        matched_rule = None
        if sys_id == 'account_service':
            matched_rule = 'rule_01'
        elif sys_id == 'search_service':
            matched_rule = 'rule_03'
        elif sys_id == 'support_platform':
            matched_rule = 'rule_05'
        elif sys_id == 'analytics_platform':
            matched_rule = 'rule_07'
        elif sys_id == 'export_service':
            matched_rule = 'rule_09'
        elif sys_id == 'security_service':
            matched_rule = 'rule_12'
        elif 'legal' in rid or sys_id == 'legal_service':
            matched_rule = 'rule_13'
        elif sys_id == 'backup_service':
            matched_rule = 'rule_14'
        elif sys_id == 'identity_service':
            matched_rule = 'rule_15'
        elif sys_id == 'integration_service':
            # Connector / active flow
            pass

        if matched_rule:
            rule_stats[matched_rule]['total_steps'] += 1
            if st == 'COMPLETE':
                rule_stats[matched_rule]['COMPLETE_cases'].add(cid)
            elif st == 'INCOMPLETE':
                rule_stats[matched_rule]['INCOMPLETE_cases'].add(cid)

print("=== RULE COVERAGE TABLE (518 EVALUATION CASES) ===")
print("| Rule ID | Data Category | Required Action | Condition | Complete Cases | Incomplete Cases | Total Output Steps |")
print("|---|---|---|---|---|---|---|")
for r in rules:
    rid = r['rule_id']
    cat = r['data_category']
    act = r['required_action']
    cond = r['condition']
    st = rule_stats[rid]
    c_cnt = len(st['COMPLETE_cases'])
    i_cnt = len(st['INCOMPLETE_cases'])
    tot = st['total_steps']
    print(f"| `{rid}` | `{cat}` | `{act}` | {cond} | {c_cnt} | {i_cnt} | {tot} |")
