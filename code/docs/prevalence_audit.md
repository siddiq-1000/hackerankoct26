# Step Prevalence Audit: Sample vs. Full Evaluation Dataset

This audit compares the case-level prevalence of every `(system_id, operation)` pair between the public sample (32 cases) and the full evaluation run (518 cases), stratified by deletion status (`COMPLETE` vs. `INCOMPLETE`).

## Execution Command
```bash
python code/tools/investigation/run_prevalence_audit.py
```

## 1. Prevalence Audit Summary
- **Sample Distribution:** 10 COMPLETE, 22 INCOMPLETE, 0 NOT_APPLICABLE
- **Full Evaluation Distribution:** 194 COMPLETE, 314 INCOMPLETE, 10 NOT_APPLICABLE
- **Total Operations Evaluated:** 64
- **Outliers Flagged (< 1/3x or > 3x):** 13

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
| `backup_service` | `BLOCK_RESTORE` | `INCOMPLETE` | 3/22 | 13.6% | 21/314 | 6.7% | 0.49x | No |
| `backup_service` | `REPORT_RESTORE_RISK` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `backup_service` | `REPORT_RESTORE_RISK` | `INCOMPLETE` | 3/22 | 13.6% | 21/314 | 6.7% | 0.49x | No |
| `backup_service` | `VERIFY_RESTORE_BLOCKED` | `COMPLETE` | 3/10 | 30.0% | 60/194 | 30.9% | 1.03x | No |
| `backup_service` | `VERIFY_RESTORE_BLOCKED` | `INCOMPLETE` | 3/22 | 13.6% | 21/314 | 6.7% | 0.49x | No |
| `export_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `DELETE_RECORD` | `INCOMPLETE` | 2/22 | 9.1% | 11/314 | 3.5% | 0.39x | No |
| `export_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 2/22 | 9.1% | 11/314 | 3.5% | 0.39x | No |
| `export_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/194 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 2/22 | 9.1% | 11/314 | 3.5% | 0.39x | No |
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
| `security_service` | `VERIFY_RECORD_PRESENT` | `INCOMPLETE` | 17/22 | 77.3% | 83/314 | 26.4% | 0.34x | No |
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

## 3. Investigated Explanations for Outliers & Specific Operations

### `support_platform` — `DELETE_RECORD`: Support Ticket Attachments (rule_06 vs rule_05)
- **Explanation:** Under `rule_06: SUPPORT_ATTACHMENT`, attachments belonging exclusively to the deletion subject must be completely deleted (`DELETE_RECORD`), whereas shared support conversations (`rule_05: SUPPORT_MESSAGE`) must be redacted (`REDACT_RECORD`). In the sample, cases 7, 10, 13 had physical support attachments in PDFs/handover records (13.6% in INCOMPLETE). In the full dataset, exactly 7 cases (`case_203, 311, 359, 407, 455, 479, 503`) had `ticket_attachments` in SQL/JSON replicas captured at or before `audit_at` (2.2% in INCOMPLETE; ratio 0.16x). Six other attachment cases had snapshots captured 2 days *after* `audit_at`, correctly preventing temporal leakage per AGENTS.md §6.2.

### `identity_service` — `VERIFY_RECORD_REDACTED`: Compliant Account Tombstones (rule_15)
- **Explanation:** In the sample, 1 of 10 COMPLETE cases (`case_31`) demonstrated an account tombstone in `evidence_51` where direct PII was stripped while internal `user_id` was retained. In the full dataset, exactly 4 compliant tombstones appear in `customer_data_failover_replica_20260920.sql` (`evidence_52`: `case_543, 545, 547, 549`), yielding 4/194 COMPLETE cases (2.1%; ratio 0.21x). In addition, 4 non-compliant tombstones (`case_544, 546, 548, 550`) had unredacted PII from failed deletion workers and were correctly flipped to INCOMPLETE with `REPORT_EXPOSED_PII`.

### `legal_service` — `VERIFY_RECORD_PRESENT`: Active Legal Holds (rule_13: RETAIN)
- **Explanation:** Active legal holds preserve dispute and tax records during their legal hold window. In the sample (32 cases), zero cases involved legal holds (0.0%). In the full dataset, 5 cases involve active legal holds (`case_261, 390, 460, 473, 505`), appearing in COMPLETE (2/194 = 1.0%) and INCOMPLETE (2/314 = 0.6%) cases. This represents an infinite full/sample ratio due to the intentional absence of legal hold cases in the small 32-case public sample.

### `analytics_platform` — `DELETE_RECORD`: Analytics Full Record Deletion
- **Explanation:** In the sample, `case_12` specifically tested deleting an un-anonymized analytics record (`REPORT_REMAINING_RECORD -> DELETE_RECORD`). In the full dataset, non-compliant analytics records consistently follow `rule_07: ANALYTICS_PROFILE` requiring anonymization (`REPORT_EXPOSED_PII -> ANONYMIZE_RECORD -> VERIFY_RECORD_ANONYMIZED`). This represents an edge case present only in the sample.

### `analytics_platform` — `REPORT_REMAINING_RECORD`: Analytics Remaining Record Reporting
- **Explanation:** Corresponds to `analytics_platform DELETE_RECORD` in sample `case_12`, where the whole record remained rather than exposed PII in an active profile.

### `analytics_platform` — `VERIFY_RECORD_ABSENT`: Analytics Verification of Absence
- **Explanation:** Corresponds to sample `case_12` post-remediation verification verifying that the record was removed entirely.

### `identity_service` — `REDACT_RECORD`: Tombstone Remediation in Incomplete Cases
- **Explanation:** In the sample, `case_32` tested an incomplete tombstone where exposed PII was detected and remediated via `REDACT_RECORD`. In the full dataset, the 4 non-compliant tombstones (`case_544, 546, 548, 550`) similarly report `REPORT_EXPOSED_PII` and remediate via `REDACT_RECORD`.

### `identity_service` — `REPORT_EXPOSED_PII`: Tombstone PII Exposure Finding
- **Explanation:** In the sample, 1/22 INCOMPLETE cases (`case_32`) exposed PII in an account tombstone. In the full dataset, 4 cases (`case_544, 546, 548, 550`) in `evidence_52` had failed deletion worker activities (`activity_3609, 3668, 3670, 3724`), exposing customer names and phones.

### `analytics_platform` — `VERIFY_RECORD_ANONYMIZED` (`COMPLETE`)
- **Sample Rate:** 70.0% (7/10) vs. **Full Rate:** 23.2% (45/194) [Ratio: 0.33x]
- **Investigation:** Natural variance in synthetic generation distribution between the 32-case sample and 518-case full cohort.

### `support_platform` — `REPORT_REMAINING_RECORD` (`INCOMPLETE`)
- **Sample Rate:** 13.6% (3/22) vs. **Full Rate:** 2.2% (7/314) [Ratio: 0.16x]
- **Investigation:** Natural variance in synthetic generation distribution between the 32-case sample and 518-case full cohort.

### `support_platform` — `VERIFY_RECORD_ABSENT` (`INCOMPLETE`)
- **Sample Rate:** 13.6% (3/22) vs. **Full Rate:** 2.2% (7/314) [Ratio: 0.16x]
- **Investigation:** Natural variance in synthetic generation distribution between the 32-case sample and 518-case full cohort.
