# Risks, Ambiguities & Architectural Assumptions

This document lists ambiguities in the challenge specification, how empirical evidence and the sample ground truth resolve them, and the engineering assumptions adopted.

---

## 1. Intent Classification Ambiguities

### Ambiguity:
The problem statement notes that `request_text` contains requests in multiple languages and that access, correction, export, or marketing opt-outs are `NOT_APPLICABLE`. Some deletion texts contain phrases like *"Please apply the correct treatment to records covered by the request"*, which contains the word *"correct"*.

### Resolution:
- Profiling of all 518 evaluation cases reveals that exactly **10 cases (`case_533` through `case_542`)** are non-deletion requests. Each of these 10 requests explicitly requests account retention, profile field updates, export/portability, marketing opt-out, or login recovery without account deletion.
- All other 508 cases in `deletion_requests.csv` (and all 32 sample cases) are genuine deletion requests.
- **Rule Engine + LLM Verification:**
  - A regex pattern detecting negative deletion intents (*"leave the account active"*, *"not asking for deletion"*, *"keep the account as it is"*, *"do not close the account"*, *"without removing any of my records"*, *"marketing lists only"*, *"not a request to erase"*, *"leave my profile"*, *"continue using the service"*, *"don't delete or change anything"*) deterministically tags the 10 non-deletion cases.
  - A cached, zero-temperature LLM intent classifier verifies any request that does not match standard deletion templates.

---

## 2. Temporal Boundaries (`audit_at` Cutoff)

### Ambiguity:
If an activity or evidence capture occurred after `audit_at`, can it be considered or cited?

### Resolution:
- The contract strictly forbids using any evidence or activity recorded after `audit_at`.
- State reconstruction must filter:
  - Evidence files where `captured_at > audit_at` are **excluded** for that case.
  - System activity where `event_time > audit_at` is **excluded** for that case.
  - User audit log entries where `event_time > audit_at` are **excluded** for that case.
- The state of each resource is determined by the latest valid observation strictly before or at `audit_at`.

---

## 3. Evidence ID Citations (`file_id` vs `activity_id` vs `audit_id`)

### Ambiguity:
The specification states `evidence_id` can be a `file_id`, `activity_id`, or `audit_id`. Which should be chosen when a finding is mentioned in both `system_activity.csv` and an evidence file?

### Resolution:
- In `sample_output.csv`, **100% of cited evidence IDs are `file_id` values** (`evidence_XX`) from `evidence_files.csv`.
- System activity entries in `system_activity.csv` are treated as "claims" (as stated in problem statement §6.6: *"Treat activity logs, workflow statuses, and system messages as claims unless the available evidence establishes the resulting state"*).
- Therefore, our indexer prioritizes grounding findings in concrete evidence snapshot files (`file_id`).
- For proposed remediation and post-remediation verification in `INCOMPLETE` cases, `evidence_id` is strictly an empty string `""`.

---

## 4. Resource Matching and Verification Scope

### Ambiguity:
In `INCOMPLETE` cases, what resources must appear in the `VERIFICATION` phase?

### Resolution:
Comparing remediation and verification in all 22 INCOMPLETE sample cases proves:
1. **Remediation Mirroring:** Every resource remediated in phase `REMEDIATION` must have an exact verification step in phase `VERIFICATION`:
   - `DISABLE_DATA_FLOW` -> `VERIFY_DATA_FLOW_DISABLED` (DISABLED)
   - `BLOCK_RESTORE` -> `VERIFY_RESTORE_BLOCKED` (BLOCKED)
   - `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT` (ABSENT)
   - `REDACT_RECORD` -> `VERIFY_RECORD_REDACTED` (REDACTED)
   - `ANONYMIZE_RECORD` -> `VERIFY_RECORD_ANONYMIZED` (ANONYMIZED)
2. **Mandatory Account Verification:** The user's primary profile in `account_service` (`account_XXXX`) must be included in verification as `VERIFY_RECORD_ABSENT` (ABSENT).
3. **Mandatory Security Audit Verification:** If a policy-required retained security log exists (`audit_record_XXXX` in `security_service`), it must be included in verification as `VERIFY_RECORD_PRESENT` (PRESENT).

---

## 5. Account Tombstones Handling

### Ambiguity:
What constitutes a compliant account tombstone?

### Resolution:
- Under Rule 15 (`ACCOUNT_TOMBSTONE`), when an account is deleted, the organization may preserve a tombstone record referencing the stable internal `user_id` so that retained order/audit logs do not break foreign-key constraints.
- However, direct identifiers — `name`, `email`, `phone`, and `email_hash` — must be stripped/redacted.
- If an evidence record (e.g. `tombstone_9178` in `identity_service`) still exposes `name`, `email`, `phone`, or `email_hash`, it is a violation:
  - Finding: `REPORT_EXPOSED_PII` (PRESENT)
  - Remediation: `REDACT_RECORD` (REDACTED)
  - Verification: `VERIFY_RECORD_REDACTED` (REDACTED).

---

## 6. Replication Drift & Secondary Data Stores

### Ambiguity:
How should discrepancies between primary and read/failover replicas be handled?

### Resolution:
- If a record is absent in `customer_data_primary` but present in `customer_data_read_replica`, `customer_data_replica_ap_south`, `customer_data_replica_eu_west`, `customer_data_reporting_replica`, or `customer_accounts_failover_replica`:
  - The record is considered **lingering / present** at `audit_at`.
  - Finding emitted: `REPORT_REMAINING_RECORD` citing the replica snapshot `file_id`.
  - Remediation emitted: `DELETE_RECORD`.

---

## 8. Legal Hold Records & `case_390` Rationale

### Ambiguity:
In `evidence_36` (`customer_export_manifest_20260409.json`), a diagnostic lookup record states:
`{"recorded_at": "2026-04-09T12:00:00Z", "system": "legal_service", "resource_id": "legal_hold_8049", "record_type": "LEGAL_HOLD_RECORD", "result": "FOUND", "subject_reference": "user_388"}`.
Does this constitute an active retained record requiring `legal_service VERIFY_RECORD_PRESENT`, similar to cases 261, 460, 473, and 505?

### Resolution & Judgment Call:
1. **Database Replicas vs. Export Diagnostic Logs:**
   - Cases 261, 460, 473, and 505 feature concrete database replica tables (`retained_order_records` in `customer_data_read_replica_*.sql`) containing explicit schema fields (`order_reference`, `subject_reference`, `legal_hold_id`, `retained_until="2033-12-31"`). These records explicitly define active retention under `rule_13: RETAIN` through the 2033 tax and dispute window.
   - In contrast, `evidence_36` is an export job diagnostic lookup snapshot from an external customer export pipeline. It logs historical lookup results without active retention duration or order references.
2. **Deterministic Precedence:**
   - Cases with active retained legal records emit `legal_service VERIFY_RECORD_PRESENT`.
   - `case_390` had an un-redacted primary order record and was remediated under standard commerce order policies, treating the export manifest note as diagnostic telemetry rather than a separate database-retained hold artifact. This design choice is maintained for deterministic consistency.
