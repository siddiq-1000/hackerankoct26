import csv
import json

print("=== SAMPLE COMPLETE ACCOUNT ABSENCE CITATIONS ===")
sample_out = {}
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['deletion_status'] == 'COMPLETE':
            steps = json.loads(r['steps_json'])
            acc_steps = [s for s in steps if s['system_id'] == 'account_service' and s['operation'] == 'VERIFY_RECORD_ABSENT']
            print(f"{r['case_id']}: {acc_steps[0]['resource_id']} -> cited {acc_steps[0]['evidence_id']}")

print("\n=== THE 20 CHANGED COMPLETE ROWS (CITED EVIDENCE REFINEMENT) ===")
# Cases:
cases_52 = ['case_543', 'case_544', 'case_545', 'case_546', 'case_547', 'case_548']
cases_05 = ['case_57', 'case_58', 'case_59', 'case_60']
cases_90 = ['case_45', 'case_84', 'case_86', 'case_87', 'case_88']
cases_93 = ['case_63', 'case_67', 'case_69', 'case_70', 'case_72']

manifest = {}
with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    manifest = {r['file_id']: r for r in csv.DictReader(f)}

for fid in ['evidence_54', 'evidence_52', 'evidence_05', 'evidence_90', 'evidence_93']:
    print(f"[{fid}] {manifest[fid]['origin']} | captured_at={manifest[fid]['captured_at']} | path={manifest[fid]['file_path']}")
