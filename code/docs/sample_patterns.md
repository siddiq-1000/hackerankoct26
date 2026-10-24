# Reverse-Engineering the Sample Dataset

This document analyzes the 32 reference cases in `dataset/sample_deletion_requests.csv` against canonical answers in `dataset/sample_output.csv` to establish ground-truth behavior, ordering rules, and edge-case resolution.

---

## 1. How NOT_APPLICABLE Cases Are Phrased & Text Signals

In `sample_deletion_requests.csv`, all 32 requests are legitimate deletion requests (status is either `COMPLETE` or `INCOMPLETE`). 
However, profiling the full 518 evaluation requests in `dataset/deletion_requests.csv` reveals exactly **10 NOT_APPLICABLE cases** (`case_533` through `case_542`).

### Text Signals for `NOT_APPLICABLE`:
1. **Account retention with profile update:**
   - *"The mobile number on my profile is out of date. Please replace it with the new one and leave the account active."* (`case_533`)
   - *"My surname is misspelled on the account. Can you correct it without removing any of my records?"* (`case_537`)
   - *"Please change the email address used for this account. I want to continue using the service."* (`case_541`)
2. **Access / Data Export (portability):**
   - *"I'd like to download my account information in a portable format. Please keep the account as it is."* (`case_535`)
   - *"Can you tell me what personal information you hold about me? This is an information request, not a request to erase it."* (`case_539`)
   - *"I need a copy of last year's invoices for my records. Please leave my profile and purchase history in place."* (`case_540`)
   - *"Could you send me a copy of the information held on my account? I still use it, so please don't delete or change anything."* (`case_542`)
3. **Marketing opt-out / Unsubscribe only:**
   - *"Please stop the promotional emails. I still need the account and my order history, so I am not asking for deletion."* (`case_534`)
   - *"Please remove me from marketing lists only. I still want receipts and service messages for this account."* (`case_538`)
4. **Login / Account recovery:**
   - *"I can't access my profile and need help resetting the login. Do not close the account."* (`case_536`)

**Contract Requirement for `NOT_APPLICABLE`:**
- `deletion_status`: `NOT_APPLICABLE`
- `steps_json`: `[]` (exact empty JSON array).

---

## 2. In INCOMPLETE Cases: Verification Scope & Retained Records

Analysis of the 22 `INCOMPLETE` cases in `sample_output.csv` reveals strict structural symmetry:

1. **Every Remediated Resource is Verified Post-Remediation:**
   - In 100% of cases, every `(system_id, resource_id)` appearing in `REMEDIATION` has an exact counterpart in `VERIFICATION`:
     - `DISABLE_DATA_FLOW` -> `VERIFY_DATA_FLOW_DISABLED`
     - `BLOCK_RESTORE` -> `VERIFY_RESTORE_BLOCKED`
     - `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`
     - `REDACT_RECORD` -> `VERIFY_RECORD_REDACTED`
     - `ANONYMIZE_RECORD` -> `VERIFY_RECORD_ANONYMIZED`
   - In proposed remediation and future verification steps for `INCOMPLETE` cases, `evidence_id` is **always `""` (empty string)**.

2. **Mandatory Retained Records in Verification:**
   - When a security audit log exists for the user (`SECURITY_AUDIT_LOG`), policy rule 12 requires it to be retained.
   - In `INCOMPLETE` cases, this audit log appears in the verification phase as:
     `{"phase": "VERIFICATION", "system_id": "security_service", "resource_id": "audit_record_XXXX", "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": ""}`
   - Similarly, the primary user profile appears in verification as:
     `{"phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_XXXX", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""}`

---

## 3. Representation of Replicas, Backups, and Search Indexes

- **Replicas (Failover, Regional, Reporting):**
  - When data lingers in a replica (e.g. `customer_accounts_failover_replica_20260902.sql`), the system is identified as `account_service` (or the owning service), and the resource is the entity `resource_id` (e.g. `account_005`).
  - The finding is `REPORT_REMAINING_RECORD` citing the replica snapshot file (`evidence_54`).
- **Backups & Restore Risks:**
  - System: `backup_service`
  - Resource ID prefix: `backup_` (e.g. `backup_4978`, `backup_3870`, `backup_3245`)
  - Finding: `REPORT_RESTORE_RISK` with state `ACTIVE`
  - Remediation: `BLOCK_RESTORE` with state `BLOCKED`
  - Verification: `VERIFY_RESTORE_BLOCKED` with state `BLOCKED`.
- **Search Indexes:**
  - System: `search_service`
  - Resource ID prefix: `search_` (e.g. `search_001`, `search_052`, `search_1308`)
  - Finding: `REPORT_REMAINING_RECORD` with state `PRESENT`
  - Remediation: `DELETE_RECORD` with state `ABSENT`
  - Verification: `VERIFY_RECORD_ABSENT` with state `ABSENT`.
- **Integration Flows / Sync:**
  - System: `integration_service`
  - Resource ID prefix: `data_flow_` (e.g. `data_flow_9522`, `data_flow_3827`)
  - Finding: `REPORT_ACTIVE_DATA_FLOW` with state `ACTIVE`
  - Remediation: `DISABLE_DATA_FLOW` with state `DISABLED`
  - Verification: `VERIFY_DATA_FLOW_DISABLED` with state `DISABLED`.

---

## 4. Evidence IDs Cited for Findings

- In `sample_output.csv`, **all cited evidence IDs are file IDs (`evidence_XX`)** from `evidence_files.csv`.
- Each finding cites the concrete manifest file where the evidence was captured:
  - `evidence_54`: `customer_accounts_failover_replica_20260902.sql` (failover replica containing remaining account)
  - `evidence_57`: `customer_search_primary_20260910.sql` (primary search index containing unpurged profile)
  - `evidence_58`: `delivery_correction_attachment.pdf` (support document containing customer identity attachment)
  - `evidence_59`: `customer_export_jobs_20260914.json` (unexpired customer export file)
  - `evidence_93`: `customer_data_snapshot_bundle_20260925.json` (unblocked backup restore entry)
  - `evidence_01`: `service_events_ap_south_20260915.log` (observability log showing active data flow / historical correlation key)
  - `evidence_03`: `customer_account_handover_20261001.txt` (shift handover log documenting unredacted support tickets, unpurged search records, and enabled connector flows)
  - `evidence_92`: `records_assurance_report_20260924.json` (bulk audit report identifying lingering data across services)
  - `evidence_51`: `customer_data_snapshot_bundle_20260915.json` (identity tombstone containing unredacted name, phone, email, and email hash).

---

## 5. Historical Email Handling & Correlation Keys

- In `case_12`, user `user_12` submitted deletion request under `minjun.kim@gmail.com`.
- Inspecting `dataset/user_audit_log.csv` reveals `audit_282` and `audit_283`:
  - Former email: `minjun.kim90@gmail.com`
  - Former SHA-256 hash: `44a65154bfd8e408852578fbd76813d094d1944f255ac1769ee81ba90492f10e`.
- Searching `evidence/logs/service_events_ap_south_20260915.log` (`evidence_01`) reveals:
  `resource_id=analytics_9914 event=contact_lookup_completed rows=1 correlation_key="44a65154bfd8e408852578fbd76813d094d1944f255ac1769ee81ba90492f10e"`
- Because `analytics_9914` was correlated only via the **historical email hash**, standard lookup on current email would have completely missed it.
- Ground truth `sample_output.csv` flags this as:
  `{"step_no": 1, "phase": "FINDING", "system_id": "analytics_platform", "resource_id": "analytics_9914", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_01"}`

---

## 6. What Gave Away `INCOMPLETE` When `reported_status=COMPLETE`

17 sample cases claimed `reported_status = COMPLETE`. However, **10 of them were actually INCOMPLETE**:
1. **Replication Drift:** Primary DB processed deletion, but read or failover replica snapshot still contained the user's record (`case_05`).
2. **Support Attachments:** Profile was deleted, but identity documents uploaded during support interactions were never purged (`case_07`, Rule 06).
3. **Active Connectors / Sync:** Background sync connector (`connector_subscriptions`) was still enabled, risking automatic re-ingestion (`case_11`, `case_15`, `case_18`).
4. **Restore Risks:** Backup created before deletion remained available with `restore_allowed = 1` (`case_09`, `case_14`, `case_17`).
5. **Historical Identifiers in Analytics / Logs:** Secondary systems still logged or keyed records by former email addresses or old hashes (`case_12`).
6. **Account Tombstones Retaining Forbidden PII:** Tombstone preserved internal `user_id` but failed to redact name, phone, email, and email hash (`case_32`).

---

## 7. Canonical Ordering Rules & Grader Contract

Every step in `steps_json` must follow the lexicographical sort order specified in the problem statement:
1. **Phase Rank (1st):**
   - `FINDING` (Rank 1)
   - `REMEDIATION` (Rank 2)
   - `VERIFICATION` (Rank 3)
2. **Operation Rank within Phase (2nd):**
   - In `FINDING`:
     1. `REPORT_REMAINING_RECORD`
     2. `REPORT_EXPOSED_PII`
     3. `REPORT_ACTIVE_DATA_FLOW`
     4. `REPORT_RESTORE_RISK`
   - In `REMEDIATION`:
     1. `DISABLE_DATA_FLOW`
     2. `BLOCK_RESTORE`
     3. `DELETE_RECORD`
     4. `REDACT_RECORD`
     5. `ANONYMIZE_RECORD`
   - In `VERIFICATION`:
     1. `VERIFY_RECORD_ABSENT`
     2. `VERIFY_RECORD_PRESENT`
     3. `VERIFY_RECORD_REDACTED`
     4. `VERIFY_RECORD_ANONYMIZED`
     5. `VERIFY_DATA_FLOW_DISABLED`
     6. `VERIFY_RESTORE_BLOCKED`
3. **`system_id` Ascending (3rd):** Alphabetical string comparison.
4. **`resource_id` Ascending (4th):** Alphabetical string comparison.
5. **Sequential Step Numbering:** `step_no` must strictly be 1, 2, 3... consecutive integers.
