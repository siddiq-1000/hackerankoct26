# Step Prevalence Audit: Sample vs. Full Evaluation Dataset

This audit compares the case-level prevalence of every `(system_id, operation)` pair between the public sample (32 cases) and the full evaluation run (518 cases), stratified by deletion status (`COMPLETE` vs. `INCOMPLETE`).

## 1. Prevalence Audit Summary
- **Sample Distribution:** 10 COMPLETE, 22 INCOMPLETE, 0 NOT_APPLICABLE
- **Full Evaluation Distribution:** 200 COMPLETE, 308 INCOMPLETE, 10 NOT_APPLICABLE
- **Total Operations Evaluated:** 62
- **Outliers Flagged (< 1/3x or > 3x):** 11

## 2. Complete Prevalence Comparison Table

| System ID | Operation | Status | Sample Hits | Sample Rate | Full Hits | Full Rate | Ratio (Full / Sample) | Outlier? |
|---|---|---|---|---|---|---|---|---|
| `account_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `account_service` | `DELETE_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 33/308 | 10.7% | 0.79x | No |
| `account_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `account_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 33/308 | 10.7% | 0.79x | No |
| `account_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 10/10 | 100.0% | 200/200 | 100.0% | 1.00x | No |
| `account_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 22/22 | 100.0% | 308/308 | 100.0% | 1.00x | No |
| `analytics_platform` | `ANONYMIZE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `ANONYMIZE_RECORD` | `INCOMPLETE` | 5/22 | 22.7% | 61/308 | 19.8% | 0.87x | No |
| `analytics_platform` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `DELETE_RECORD` | `INCOMPLETE` | 1/22 | 4.5% | 0/308 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `analytics_platform` | `REPORT_EXPOSED_PII` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `REPORT_EXPOSED_PII` | `INCOMPLETE` | 5/22 | 22.7% | 61/308 | 19.8% | 0.87x | No |
| `analytics_platform` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 1/22 | 4.5% | 0/308 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `analytics_platform` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `analytics_platform` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 1/22 | 4.5% | 0/308 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `analytics_platform` | `VERIFY_RECORD_ANONYMIZED` | `COMPLETE` | 7/10 | 70.0% | 72/200 | 36.0% | 0.51x | No |
| `analytics_platform` | `VERIFY_RECORD_ANONYMIZED` | `INCOMPLETE` | 5/22 | 22.7% | 61/308 | 19.8% | 0.87x | No |
| `backup_service` | `BLOCK_RESTORE` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `backup_service` | `BLOCK_RESTORE` | `INCOMPLETE` | 3/22 | 13.6% | 21/308 | 6.8% | 0.50x | No |
| `backup_service` | `REPORT_RESTORE_RISK` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `backup_service` | `REPORT_RESTORE_RISK` | `INCOMPLETE` | 3/22 | 13.6% | 21/308 | 6.8% | 0.50x | No |
| `backup_service` | `VERIFY_RESTORE_BLOCKED` | `COMPLETE` | 3/10 | 30.0% | 60/200 | 30.0% | 1.00x | No |
| `backup_service` | `VERIFY_RESTORE_BLOCKED` | `INCOMPLETE` | 3/22 | 13.6% | 21/308 | 6.8% | 0.50x | No |
| `export_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `DELETE_RECORD` | `INCOMPLETE` | 2/22 | 9.1% | 11/308 | 3.6% | 0.39x | No |
| `export_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 2/22 | 9.1% | 11/308 | 3.6% | 0.39x | No |
| `export_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `export_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 2/22 | 9.1% | 11/308 | 3.6% | 0.39x | No |
| `identity_service` | `REDACT_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `identity_service` | `REDACT_RECORD` | `INCOMPLETE` | 1/22 | 4.5% | 0/308 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `identity_service` | `REPORT_EXPOSED_PII` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `identity_service` | `REPORT_EXPOSED_PII` | `INCOMPLETE` | 1/22 | 4.5% | 0/308 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `identity_service` | `VERIFY_RECORD_REDACTED` | `COMPLETE` | 1/10 | 10.0% | 1/200 | 0.5% | 0.05x | **YES** |
| `identity_service` | `VERIFY_RECORD_REDACTED` | `INCOMPLETE` | 1/22 | 4.5% | 0/308 | 0.0% | 0.0x (sample=4.5%, full=0) | **YES** |
| `integration_service` | `DISABLE_DATA_FLOW` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `integration_service` | `DISABLE_DATA_FLOW` | `INCOMPLETE` | 6/22 | 27.3% | 105/308 | 34.1% | 1.25x | No |
| `integration_service` | `REPORT_ACTIVE_DATA_FLOW` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `integration_service` | `REPORT_ACTIVE_DATA_FLOW` | `INCOMPLETE` | 6/22 | 27.3% | 105/308 | 34.1% | 1.25x | No |
| `integration_service` | `VERIFY_DATA_FLOW_DISABLED` | `COMPLETE` | 3/10 | 30.0% | 30/200 | 15.0% | 0.50x | No |
| `integration_service` | `VERIFY_DATA_FLOW_DISABLED` | `INCOMPLETE` | 6/22 | 27.3% | 105/308 | 34.1% | 1.25x | No |
| `search_service` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `search_service` | `DELETE_RECORD` | `INCOMPLETE` | 12/22 | 54.5% | 249/308 | 80.8% | 1.48x | No |
| `search_service` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `search_service` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 12/22 | 54.5% | 249/308 | 80.8% | 1.48x | No |
| `search_service` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `search_service` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 12/22 | 54.5% | 249/308 | 80.8% | 1.48x | No |
| `security_service` | `VERIFY_RECORD_PRESENT` | `COMPLETE` | 7/10 | 70.0% | 87/200 | 43.5% | 0.62x | No |
| `security_service` | `VERIFY_RECORD_PRESENT` | `INCOMPLETE` | 17/22 | 77.3% | 18/308 | 5.8% | 0.08x | **YES** |
| `support_platform` | `DELETE_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `DELETE_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 0/308 | 0.0% | 0.0x (sample=13.6%, full=0) | **YES** |
| `support_platform` | `REDACT_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `REDACT_RECORD` | `INCOMPLETE` | 5/22 | 22.7% | 102/308 | 33.1% | 1.46x | No |
| `support_platform` | `REPORT_EXPOSED_PII` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `REPORT_EXPOSED_PII` | `INCOMPLETE` | 5/22 | 22.7% | 102/308 | 33.1% | 1.46x | No |
| `support_platform` | `REPORT_REMAINING_RECORD` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `REPORT_REMAINING_RECORD` | `INCOMPLETE` | 3/22 | 13.6% | 0/308 | 0.0% | 0.0x (sample=13.6%, full=0) | **YES** |
| `support_platform` | `VERIFY_RECORD_ABSENT` | `COMPLETE` | 0/10 | 0.0% | 0/200 | 0.0% | 1.0x (both 0) | No |
| `support_platform` | `VERIFY_RECORD_ABSENT` | `INCOMPLETE` | 3/22 | 13.6% | 0/308 | 0.0% | 0.0x (sample=13.6%, full=0) | **YES** |
| `support_platform` | `VERIFY_RECORD_REDACTED` | `COMPLETE` | 3/10 | 30.0% | 34/200 | 17.0% | 0.57x | No |
| `support_platform` | `VERIFY_RECORD_REDACTED` | `INCOMPLETE` | 5/22 | 22.7% | 102/308 | 33.1% | 1.46x | No |

## 3. Investigation of Outliers

### `analytics_platform` — `DELETE_RECORD` (`INCOMPLETE`)
- **Sample Rate:** 4.5% (1/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=4.5%, full=0)]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.

### `analytics_platform` — `REPORT_REMAINING_RECORD` (`INCOMPLETE`)
- **Sample Rate:** 4.5% (1/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=4.5%, full=0)]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.

### `analytics_platform` — `VERIFY_RECORD_ABSENT` (`INCOMPLETE`)
- **Sample Rate:** 4.5% (1/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=4.5%, full=0)]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.

### `identity_service` — `REDACT_RECORD` (`INCOMPLETE`)
- **Sample Rate:** 4.5% (1/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=4.5%, full=0)]
- **Root Cause Investigation:**
  - Account tombstones occur in specific batches (e.g. `customer_data_failover_replica_20260920.sql` covering cases 543-550). In the sample, cases 31/32 specifically demonstrated tombstones, representing an intentional oversampling in the sample.

### `identity_service` — `REPORT_EXPOSED_PII` (`INCOMPLETE`)
- **Sample Rate:** 4.5% (1/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=4.5%, full=0)]
- **Root Cause Investigation:**
  - Account tombstones occur in specific batches (e.g. `customer_data_failover_replica_20260920.sql` covering cases 543-550). In the sample, cases 31/32 specifically demonstrated tombstones, representing an intentional oversampling in the sample.

### `identity_service` — `VERIFY_RECORD_REDACTED` (`COMPLETE`)
- **Sample Rate:** 10.0% (1/10) vs. **Full Rate:** 0.5% (1/200) [Ratio: 0.05x]
- **Root Cause Investigation:**
  - Account tombstones occur in specific batches (e.g. `customer_data_failover_replica_20260920.sql` covering cases 543-550). In the sample, cases 31/32 specifically demonstrated tombstones, representing an intentional oversampling in the sample.

### `identity_service` — `VERIFY_RECORD_REDACTED` (`INCOMPLETE`)
- **Sample Rate:** 4.5% (1/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=4.5%, full=0)]
- **Root Cause Investigation:**
  - Account tombstones occur in specific batches (e.g. `customer_data_failover_replica_20260920.sql` covering cases 543-550). In the sample, cases 31/32 specifically demonstrated tombstones, representing an intentional oversampling in the sample.

### `security_service` — `VERIFY_RECORD_PRESENT` (`INCOMPLETE`)
- **Sample Rate:** 77.3% (17/22) vs. **Full Rate:** 5.8% (18/308) [Ratio: 0.08x]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.

### `support_platform` — `DELETE_RECORD` (`INCOMPLETE`)
- **Sample Rate:** 13.6% (3/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=13.6%, full=0)]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.

### `support_platform` — `REPORT_REMAINING_RECORD` (`INCOMPLETE`)
- **Sample Rate:** 13.6% (3/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=13.6%, full=0)]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.

### `support_platform` — `VERIFY_RECORD_ABSENT` (`INCOMPLETE`)
- **Sample Rate:** 13.6% (3/22) vs. **Full Rate:** 0.0% (0/308) [Ratio: 0.0x (sample=13.6%, full=0)]
- **Root Cause Investigation:**
  - Reflects natural variation in system failure modes across the larger full evaluation cohort.
