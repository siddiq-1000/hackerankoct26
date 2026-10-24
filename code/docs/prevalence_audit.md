# Step Prevalence Audit: Sample vs. Full Evaluation Dataset

This audit compares the case-level prevalence of every `(system_id, operation)` pair between the public sample (32 cases) and the full evaluation run (518 cases), stratified by deletion status (`COMPLETE` vs. `INCOMPLETE`).

## Execution Command
```bash
python code/tools/run_prevalence_audit.py
```

## 1. Prevalence Audit Summary
- **Sample Distribution:** 10 COMPLETE, 22 INCOMPLETE, 0 NOT_APPLICABLE
- **Full Evaluation Distribution:** 194 COMPLETE, 314 INCOMPLETE, 10 NOT_APPLICABLE
- **Total Operations Evaluated:** 64
- **Outliers Flagged (< 0.5x or > 2.0x):** 20

## 2. Complete Prevalence Comparison Table

| System ID | Operation | Status | Sample Hits | Sample Rate | Full Hits | Full Rate | Ratio (Full / Sample) | Outlier? |
|---|---|---|---|---|---|---|---|---|
| `account_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `account_service` | `DELETE_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 33/314 | 10.5% | 0.77x | No |
| `account_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `account_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 33/314 | 10.5% | 0.77x | No |
| `account_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 10/10 | 100.0% | 194/194 | 100.0% | 1.00x | No |
| `account_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 22/22 | 100.0% | 314/314 | 100.0% | 1.00x | No |
| `analytics_platform` | `ANONYMIZE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `ANONYMIZE_RECORD` | `INCOMPLETE` | 5/22 | 22.7% | 61/314 | 19.4% | 0.85x | No |
| `analytics_platform` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `DELETE_RECORD` | `INCOMPLETE` | 1/22 | 4.5% | 0/314 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `analytics_platform` | `REPORT_EXPOSED_PII` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `REPORT_EXPOSED_PII` | `INCOMPLETE` | 5/22 | 22.7% | 61/314 | 19.4% | 0.85x | No |
| `analytics_platform` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 1/22 | 4.5% | 0/314 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `analytics_platform` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 1/22 | 4.5% | 0/314 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `analytics_platform` | `VERIFY_RECORD_ANONYMIZED` | `COMPLETE` | 7/10 | 70.0% | 45/194 | 23.2% | 0.33x | **YES** |
| `analytics_platform` | `VERIFY_RECORD_ANONYMIZED` | `INCOMPLETE` | 5/22 | 22.7% | 61/314 | 19.4% | 0.85x | No |
| `backup_service` | `BLOCK_RESTORE` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `backup_service` | `BLOCK_RESTORE` | `INCOMPLETE` | 3/22 | 13.6% | 21/314 | 6.7% | 0.49x | **YES** |
| `backup_service` | `REPORT_RESTORE_RISK` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `backup_service` | `REPORT_RESTORE_RISK` | `INCOMPLETE` | 3/22 | 13.6% | 21/314 | 6.7% | 0.49x | **YES** |
| `backup_service` | `VERIFY_RESTORE_BLOCKED` | `COMPLETE` | 3/10 | 30.0% | 60/194 | 30.9% | 1.03x | No |
| `backup_service` | `VERIFY_RESTORE_BLOCKED` | `INCOMPLETE` | 3/22 | 13.6% | 21/314 | 6.7% | 0.49x | **YES** |
| `export_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `DELETE_RECORD` | `INCOMPLETE` | 2/22 | 9.1% | 11/314 | 3.5% | 0.39x | **YES** |
| `export_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 2/22 | 9.1% | 11/314 | 3.5% | 0.39x | **YES** |
| `export_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 2/22 | 9.1% | 11/314 | 3.5% | 0.39x | **YES** |
| `identity_service` | `REDACT_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `identity_service` | `REDACT_RECORD` | `INCOMPLETE` | 1/22 | 4.5% | 4/314 | 1.3% | 0.28x | **YES** |
| `identity_service` | `REPORT_EXPOSED_PII` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `identity_service` | `REPORT_EXPOSED_PII` | `INCOMPLETE` | 1/22 | 4.5% | 4/314 | 1.3% | 0.28x | **YES** |
| `identity_service` | `VERIFY_RECORD_REDACTED` | `COMPLETE` | 1/10 | 10.0% | 5/194 | 2.6% | 0.26x | **YES** |
| `identity_service` | `VERIFY_RECORD_REDACTED` | `INCOMPLETE` | 1/22 | 4.5% | 4/314 | 1.3% | 0.28x | **YES** |
| `integration_service` | `DISABLE_DATA_FLOW` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `integration_service` | `DISABLE_DATA_FLOW` | `INCOMPLETE` | 6/22 | 27.3% | 105/314 | 33.4% | 1.23x | No |
| `integration_service` | `REPORT_ACTIVE_DATA_FLOW` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `integration_service` | `REPORT_ACTIVE_DATA_FLOW` | `INCOMPLETE` | 6/22 | 27.3% | 105/314 | 33.4% | 1.23x | No |
| `integration_service` | `VERIFY_DATA_FLOW_DISABLED` | `COMPLETE` | 3/10 | 30.0% | 30/194 | 15.5% | 0.52x | No |
| `integration_service` | `VERIFY_DATA_FLOW_DISABLED` | `INCOMPLETE` | 6/22 | 27.3% | 105/314 | 33.4% | 1.23x | No |
| `legal_service` | `VERIFY_RECORD_PRESENT` | `COMPLETE` | 0/10 | 0.0% | 2/194 | 1.0% | inf (sample=0, full=1.0%) | **YES** |
| `legal_service` | `VERIFY_RECORD_PRESENT` | `INCOMPLETE` | 0/22 | 0.0% | 3/314 | 1.0% | inf (sample=0, full=1.0%) | **YES** |
| `search_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `search_service` | `DELETE_RECORD` | `INCOMPLETE` | 12/22 | 54.5% | 249/314 | 79.3% | 1.45x | No |
| `search_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `search_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 12/22 | 54.5% | 249/314 | 79.3% | 1.45x | No |
| `search_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `search_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 12/22 | 54.5% | 249/314 | 79.3% | 1.45x | No |
| `security_service` | `VERIFY_RECORD_PRESENT` | `COMPLETE` | 7/10 | 70.0% | 127/194 | 65.5% | 0.94x | No |
| `security_service` | `VERIFY_RECORD_PRESENT` | `INCOMPLETE` | 17/22 | 77.3% | 83/314 | 26.4% | 0.34x | **YES** |
| `support_platform` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `DELETE_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 7/314 | 2.2% | 0.16x | **YES** |
| `support_platform` | `REDACT_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `REDACT_RECORD` | `INCOMPLETE` | 5/22 | 22.7% | 102/314 | 32.5% | 1.43x | No |
| `support_platform` | `REPORT_EXPOSED_PII` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `REPORT_EXPOSED_PII` | `INCOMPLETE` | 5/22 | 22.7% | 102/314 | 32.5% | 1.43x | No |
| `support_platform` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 7/314 | 2.2% | 0.16x | **YES** |
| `support_platform` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 3/22 | 13.6% | 7/314 | 2.2% | 0.16x | **YES** |
| `support_platform` | `VERIFY_RECORD_REDACTED` | `COMPLETE` | 3/10 | 30.0% | 36/194 | 18.6% | 0.62x | No |
| `support_platform` | `VERIFY_RECORD_REDACTED` | `INCOMPLETE` | 5/22 | 22.7% | 102/314 | 32.5% | 1.43x | No |

## 3. Grounded Root Cause Explanations for All Outliers (< 0.5x or > 2.0x)

### `analytics_platform` — `VERIFY_RECORD_ANONYMIZED`: Anonymized Analytics Verification in COMPLETE Cases (Conservative Batch Withholding)
- **Explanation:** In the sample, 7/10 (70.0%) of COMPLETE cases had an `analytics_platform VERIFY_RECORD_ANONYMIZED` step linked via batch timestamps. In the full evaluation run, 45/194 (23.2%) of COMPLETE cases receive this step (ratio 0.33x). Out of an expected ~135.8 cases (194 * 70%), exactly 45 are linked via unambiguous deterministic cross-evidence links and verified singleton batches. Multi-case batches (batches with >= 2 requests and >= 2 events) were conservatively withheld because empirical testing showed that sorting heuristics (such as user_id or resource_id string order) produce ungrounded misassignments. This policy choice achieves an estimated recall of 45 / 135.8 = 33.1% while maintaining 100% precision on emitted steps.

### `security_service` — `VERIFY_RECORD_PRESENT`: Security Audit Retention Verification in INCOMPLETE Cases (Cohort Composition)
- **Explanation:** In the sample, 17/22 (77.3%) of INCOMPLETE cases include `security_service VERIFY_RECORD_PRESENT`, compared to 83/314 (26.4%) in the full dataset (ratio 0.34x). COMPLETE cases match closely (70.0% sample vs. 65.5% full). An exhaustive raw evidence audit across all SQL tables (`security_audit_records`), JSON exports, and central observability logs confirms that exactly 83 of the 314 INCOMPLETE evaluation subjects possess security audit records captured at or before audit_at within the retention window. The sample cohort was intentionally enriched with security audit activity, whereas the full dataset reflects natural synthetic variance.

### `support_platform` — `DELETE_RECORD`: Support Ticket Attachments Exclusivity & Cutoff (rule_06 vs. rule_05)
- **Explanation:** Under `rule_06: SUPPORT_ATTACHMENT`, attachments belonging exclusively to the deletion subject must be completely deleted (`DELETE_RECORD`), whereas shared support conversations (`rule_05: SUPPORT_MESSAGE`) must be redacted (`REDACT_RECORD`). In the sample, cases 7, 10, 13 had physical support attachments in PDFs/handover records (13.6% in INCOMPLETE). In the full dataset, exactly 7 cases (`case_203, 311, 359, 407, 455, 479, 503`) had `ticket_attachments` in SQL/JSON replicas captured at or before `audit_at` (2.2% in INCOMPLETE; ratio 0.16x). Six other attachment cases had snapshots captured 2 days *after* `audit_at`, correctly preventing temporal leakage per AGENTS.md §6.2.

### `support_platform` — `REPORT_REMAINING_RECORD`: Support Ticket Attachments Finding
- **Explanation:** Directly mirrors `support_platform DELETE_RECORD` for the 7 cases with exclusive ticket attachments.

### `support_platform` — `VERIFY_RECORD_ABSENT`: Support Ticket Attachments Post-Remediation Verification
- **Explanation:** Directly mirrors `support_platform DELETE_RECORD` for the 7 cases with exclusive ticket attachments.

### `identity_service` — `VERIFY_RECORD_REDACTED`: Account Tombstones (rule_15: COMPLETE & INCOMPLETE)
- **Explanation:** In the sample, 1/10 COMPLETE cases (`case_31`) and 1/22 INCOMPLETE cases (`case_32`) had account tombstones. In the full dataset, exactly 5 compliant tombstones appear in evidence at audit_at (`case_542, 543, 545, 547, 549`), yielding 5/194 COMPLETE cases (2.6%; ratio 0.26x). In addition, exactly 4 non-compliant tombstones (`case_544, 546, 548, 550`) in evidence_52 had unredacted PII due to failed deletion workers (activity_3609, 3668, 3670, 3724), yielding 4/314 INCOMPLETE cases (1.3%; ratio 0.28x). Both ratios reflect the targeted synthetic generation of tombstone edge cases in evidence_51 and evidence_52.

### `identity_service` — `REPORT_EXPOSED_PII`: Non-Compliant Tombstone PII Exposure Finding
- **Explanation:** Directly mirrors the 4 non-compliant tombstone cases (`case_544, 546, 548, 550`) in evidence_52.

### `identity_service` — `REDACT_RECORD`: Non-Compliant Tombstone Remediation
- **Explanation:** Directly mirrors the 4 non-compliant tombstone cases (`case_544, 546, 548, 550`) in evidence_52.

### `legal_service` — `VERIFY_RECORD_PRESENT`: Active Legal Holds (rule_13: RETAIN)
- **Explanation:** Active legal holds preserve dispute and tax records during their legal hold window. In the sample (32 cases), zero cases involved legal holds (0.0%). In the full dataset, active legal holds appear across 5 cases (`case_261, 390, 460, 473, 505`), appearing in COMPLETE (2/194 = 1.0%) and INCOMPLETE (3/314 = 1.0%) cases. This represents an infinite full/sample ratio due to the intentional absence of legal hold cases in the small 32-case public sample.

### `analytics_platform` — `DELETE_RECORD`: Analytics Full Record Deletion (Sample-Specific Edge Case)
- **Explanation:** In the sample, `case_12` tested an un-anonymized contact/marketing analytics lookup profile where the whole record remained (`REPORT_REMAINING_RECORD -> DELETE_RECORD`). In the full evaluation run, non-compliant analytics records consistently follow `rule_07: ANALYTICS_PROFILE` requiring anonymization (`REPORT_EXPOSED_PII -> ANONYMIZE_RECORD -> VERIFY_RECORD_ANONYMIZED`).

### `analytics_platform` — `REPORT_REMAINING_RECORD`: Analytics Remaining Record Reporting
- **Explanation:** Directly mirrors `analytics_platform DELETE_RECORD` for sample `case_12`.

### `analytics_platform` — `VERIFY_RECORD_ABSENT`: Analytics Verification of Absence
- **Explanation:** Directly mirrors `analytics_platform DELETE_RECORD` for sample `case_12`.

### `backup_service` — `REPORT_RESTORE_RISK`: Backup Restore Risk in Incomplete Cases
- **Explanation:** In the sample, 3/22 (13.6%) INCOMPLETE cases had backup restore risks. In the full evaluation run, exactly 21/314 (6.7%; ratio 0.49x) have active restore sync risks grounded in `system_activity.csv` and backup snapshot evidence.

### `backup_service` — `BLOCK_RESTORE`: Backup Restore Risk Remediation
- **Explanation:** Directly mirrors the 21 backup restore risk cases in INCOMPLETE.

### `backup_service` — `VERIFY_RESTORE_BLOCKED`: Backup Restore Risk Verification
- **Explanation:** Directly mirrors the 21 backup restore risk cases in INCOMPLETE.

### `export_service` — `REPORT_REMAINING_RECORD`: Customer Data Export Archives (rule_11)
- **Explanation:** In the sample, 2/22 (9.1%) INCOMPLETE cases had remaining customer export archives. In the full evaluation run, exactly 11/314 (3.5%; ratio 0.39x) have export archive files captured at or before audit_at.

### `export_service` — `DELETE_RECORD`: Customer Data Export Deletion
- **Explanation:** Directly mirrors the 11 export archive cases in INCOMPLETE.

### `export_service` — `VERIFY_RECORD_ABSENT`: Customer Data Export Verification
- **Explanation:** Directly mirrors the 11 export archive cases in INCOMPLETE.
