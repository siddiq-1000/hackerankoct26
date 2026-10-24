# Dataset Schema Profile & Evidence Census

This document profiles all dataset files and evidence files in `dataset/` for HackerRank Orchestrate (October 2026) — **Ghost Data Still Exists**.

---

## 1. Dataset Files Schema & Profiles

All timestamps across all files follow the strict ISO-8601 UTC format: `YYYY-MM-DDTHH:MM:SSZ`. There are zero missing values or null fields across any columns in the dataset tables.

### 1.1 `dataset/deletion_requests.csv`
- **Purpose:** Primary evaluation requests (518 evaluation cases). Exactly one output row per `case_id` must be generated.
- **Row count:** 518 data rows (+ header). `case_33` through `case_550`.
- **Columns:** `case_id, email, requested_at, reported_status, reported_at, audit_at, request_text`
- **Sample Rows:**
  1. `case_33,ingrid.dahl@outlook.com,2026-07-16T08:00:00Z,COMPLETE,2026-07-18T02:00:00Z,2026-07-19T13:00:00Z,"Please close my account and process the associated personal-data deletion. Please handle any copies that fall within the scope of the deletion request. Please confirm when the review is complete."`
  2. `case_34,haruka.s1838@zoho.com,2026-09-24T08:00:00Z,COMPLETE,2026-09-26T02:00:00Z,2026-09-27T13:00:00Z,"I would like the account associated with this address to be erased. Please handle any copies that fall within the scope of the deletion request. Please contact me if you need information to verify the request."`
  3. `case_533,elena.v4728@gmail.com,2026-09-23T12:00:00Z,NOT_STARTED,2026-09-24T12:00:00Z,2026-10-01T12:00:00Z,"The mobile number on my profile is out of date. Please replace it with the new one and leave the account active."`
- **Value Ranges / Enums:**
  - `reported_status`: `COMPLETE` (254, 49.0%), `PARTIALLY_COMPLETE` (152, 29.3%), `NOT_STARTED` (112, 21.6%)
  - `requested_at`: `2026-01-05T06:00:00Z` to `2026-09-24T08:00:00Z`
  - `reported_at`: `2026-01-06T06:00:00Z` to `2026-09-26T02:00:00Z`
  - `audit_at`: `2026-01-29T12:00:00Z` to `2026-10-01T12:00:00Z`
  - `request_text`: Multilingual (English, Spanish, French, German, Portuguese, Italian, Dutch, Swedish, Polish, Japanese, Korean, Arabic). Includes 10 specific non-deletion requests (`case_533` to `case_542`) where user explicitly asks to keep account / update profile / export data / opt out of marketing only.

### 1.2 `dataset/sample_deletion_requests.csv`
- **Purpose:** Public reference sample set (32 sample cases).
- **Row count:** 32 data rows (+ header). `case_01` through `case_32`.
- **Columns:** `case_id, email, requested_at, reported_status, reported_at, audit_at, request_text`
- **Sample Rows:**
  1. `case_01,amina.elmasri@gmail.com,2026-08-18T09:14:00Z,COMPLETE,2026-08-20T16:42:00Z,2026-09-03T11:30:00Z,"Hi, I haven’t used this account in years and would like it closed. Please remove the profile and the personal details attached to it."`
  2. `case_02,mateo.rios@outlook.com,2026-08-21T18:06:00Z,PARTIALLY_COMPLETE,2026-08-22T07:25:00Z,2026-09-04T15:00:00Z,"Intenté eliminar mi cuenta ayer, pero la página terminó mostrando un error. ¿Pueden comprobar si todavía queda algún dato y completar la eliminación si hace falta?"`
  3. `case_32,addo.kofi@gmail.com,2026-09-03T12:00:00Z,PARTIALLY_COMPLETE,2026-09-06T12:00:00Z,2026-09-15T12:00:00Z,"The account itself is gone, but an internal deleted-account record still shows my personal details. Please keep only the reference needed for retained records and remove the rest."`
- **Value Ranges / Enums:**
  - `reported_status`: `COMPLETE` (17), `PARTIALLY_COMPLETE` (5), `NOT_STARTED` (10)

### 1.3 `dataset/sample_output.csv`
- **Purpose:** Canonical ground truth for the 32 sample requests.
- **Row count:** 32 rows.
- **Columns:** `case_id, deletion_status, steps_json`
- **Status Breakdown:**
  - `COMPLETE`: 10 cases (31.25%)
  - `INCOMPLETE`: 22 cases (68.75%)
  - `NOT_APPLICABLE`: 0 in sample (sample only features valid deletion requests).

### 1.4 `dataset/user_identities.csv`
- **Purpose:** Current identity snapshot for platform users.
- **Row count:** 850 rows.
- **Columns:** `user_id, name, email, phone, email_hash, updated_at`
- **Sample Rows:**
  1. `user_01,Amina El-Masri,amina.elmasri@gmail.com,+971 50 482 7316,d4e1f59abcf9a1e0cfdc7c27ad6c07ed4ff88b326a16ed5eed5ec6bc31618c93,2026-05-28T04:03:00Z`
  2. `user_02,Mateo Ríos,mateo.rios@outlook.com,+34 612 34 56 78,3f8b051ba28de6da436d4f6cbf1014e38c9285744cb80c7ad222d4fef947fa85,2026-06-11T14:22:00Z`
  3. `user_850,Astrid Nyström,anystrom5879@fastmail.com,+46 70 331 83 69,cc7a9b3c2f4bdfc65c1fae92cfe5a7184a12fca0318a24e233e34de23b1c2669,2025-09-15T13:50:00Z`
- **Email Hash Discovery:**
  All 850 rows strictly match SHA-256 over lowercase, whitespace-trimmed email:
  `hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()`.

### 1.5 `dataset/user_audit_log.csv`
- **Purpose:** Historical changelog of identity fields (`email`, `phone`, `email_hash`). Essential for historical identity resolution.
- **Row count:** 306 rows.
- **Columns:** `audit_id, user_id, event_time, field_name, old_value, new_value`
- **Sample Rows:**
  1. `audit_01,user_485,2024-12-14T16:31:44Z,phone,+33 6 24 34 80 16,+33 6 63 29 68 28`
  2. `audit_02,user_548,2025-01-09T09:12:03Z,email,c.dubois@free.fr,claire.dubois@orange.fr`
  3. `audit_03,user_548,2025-01-09T09:12:03Z,email_hash,1a5e...,4f2b...`
- **Value Ranges / Enums:**
  - `field_name` (3 unique): `email` (102), `email_hash` (102), `phone` (102). Exactly 102 identity change events where email, email_hash, and phone were modified.

### 1.6 `dataset/system_activity.csv`
- **Purpose:** Audit trail of events across internal microservices. Contains claims of deletion, synchronization, cache invalidation, indexing, and backup/restore jobs.
- **Row count:** 4011 rows.
- **Columns:** `activity_id, event_time, event_type, source_system, target_system, resource_id, reported_result, details`
- **Sample Rows:**
  1. `activity_01,2026-01-04T14:56:29Z,INDEX_RECORD,account_service,search_service,search_9729,SUCCESS,Customer search-index refresh processed search_9729.`
  2. `activity_02,2026-01-04T15:20:11Z,UPDATE_RECORD,account_service,account_service,account_9729,SUCCESS,Profile preference update processed account_9729.`
  3. `activity_4011,2026-03-10T06:07:01Z,LINK_RESOURCE_IDENTITY,data_catalog,identity_service,tombstone_17,SUCCESS,Data catalog linked tombstone_17 (user_17) to leonie.g9352@outlook.com and user_17.`
- **Value Ranges / Enums:**
  - `reported_result` (3 unique): `SUCCESS` (2914), `FAILED` (721), `PARTIAL` (376).
  - `event_type` (17 unique): `DELETE_RECORD` (890), `UPDATE_RECORD` (672), `SYNC_RECORD` (447), `INDEX_RECORD` (400), `SEND_EMAIL` (368), `REFRESH_CACHE` (284), `RETAIN_RECORD` (206), `ANONYMIZE_RECORD` (204), `REDACT_RECORD` (173), `CREATE_EXPORT` (155), `CHECK_DATA_FLOW` (89), `DISABLE_DATA_FLOW` (36), `BLOCK_RESTORE` (36), `CHECK_RESTORE_ACCESS` (28), `LINK_RESOURCE_IDENTITY` (12), `CLASSIFY_REQUEST` (10), `RESTORE_BACKUP` (1).
  - `source_system` (11 unique): `deletion_worker` (1466), `account_service` (1100), `profile_service` (440), `notification_service` (368), `support_platform` (232), `security_service` (196), `export_service` (155), `integration_service` (31), `data_catalog` (12), `privacy_intake` (10), `backup_service` (1).
  - `target_system` (19 unique): `account_service` (980), `search_service` (954), `analytics_platform` (566), `email_delivery_service` (368), `cache_service` (284), `archive_service` (196), `support_platform` (193), `object_store` (155), `integration_service` (126), `backup_service` (65), `account_replication_cluster` (55), `export_service` (34), `identity_service` (11), `legal_service` (10), `privacy_case_management` (10), `account_failover_replica` (1), `marketing_platform` (1), `object_storage` (1), `security_service` (1).

### 1.7 `dataset/deletion_rules.csv`
- **Purpose:** Enterprise retention & deletion policy defining treatment per data category.
- **Row count:** 15 rows.
- **Columns:** `rule_id, data_category, condition, required_action`
- Fully documented in Section 3 of this file.

### 1.8 `dataset/evidence_files.csv`
- **Purpose:** Manifest of external artifacts located in `dataset/evidence/`.
- **Row count:** 94 rows.
- **Columns:** `file_id, file_path, origin, captured_at`
- **Extensions:** `.json` (28), `.log` (26), `.sql` (24), `.png` (11), `.pdf` (4), `.txt` (1).

---

## 2. Evidence Census & Systems Profile

### 2.1 File Type Breakdown
| Format | Subdirectory | Count | Role |
|---|---|---|---|
| `.json` | `evidence/records/` | 28 | Structured snapshot bundles from records assurance service, connector configs, and service exports. |
| `.log` | `evidence/logs/` | 26 | Service event traces, readback logs, observability exports, and lookup audit trails. |
| `.sql` | `evidence/databases/` | 24 | SQLite-compatible database dump snapshots covering primary databases and replicas. |
| `.png` | `evidence/images/` | 11 | Administrative console screenshots (Admin portal, Analytics, Search Inspector, Storage browser, Support ticket, etc.). |
| `.pdf` | `evidence/documents/` | 4 | Generated customer statements, legal retention registers, security retention extracts, delivery attachments. |
| `.txt` | `evidence/records/` | 1 | Shift handover log (`customer_account_handover_20261001.txt`). |
| **Total** | | **94** | |

### 2.2 System IDs and Resource ID Naming Patterns
From `sample_output.csv`, `system_activity.csv`, and evidence artifacts:
| `system_id` | Canonical Resource Prefix | Example `resource_id` | Data Category |
|---|---|---|---|
| `account_service` | `account_` | `account_001`, `account_4248` | `USER_PROFILE` |
| `search_service` | `search_` | `search_001`, `search_052` | `SEARCH_INDEX_ENTRY` |
| `support_platform` | `support_` | `support_001`, `support_864` | `SUPPORT_MESSAGE`, `SUPPORT_ATTACHMENT` |
| `analytics_platform` | `analytics_` | `analytics_901`, `analytics_2034` | `ANALYTICS_PROFILE`, `PRODUCT_TELEMETRY` |
| `security_service` | `audit_record_` | `audit_record_2016`, `audit_record_9394` | `SECURITY_AUDIT_LOG` |
| `integration_service` | `data_flow_` | `data_flow_9522`, `data_flow_3827` | Active data flow connector |
| `backup_service` | `backup_` | `backup_001`, `backup_7749` | `BACKUP_ARCHIVE` (Restore risk) |
| `export_service` | `export_` | `export_001`, `export_381` | `USER_EXPORT` |
| `identity_service` | `tombstone_` | `tombstone_440`, `tombstone_9178` | `ACCOUNT_TOMBSTONE` |

### 2.3 SQL Files Deep Dive (24 Snapshot Files)
All 24 SQL files execute cleanly into SQLite. They represent two major snapshot families:
1. **Inventory Snapshots (`customer_data_inventory_YYYYMMDD.sql` - 11 files):**
   - Tables:
     - `snapshot_scope` (`origin_system`, `captured_at`)
     - `customer_profiles` (`resource_id`, `customer_reference`, `full_name`, `email`, `phone`, `email_hash`, `account_status`, `updated_at`) — **Holds PII**
     - `customer_search_documents` (`resource_id`, `customer_reference`, `display_name`, `email`, `phone`, `email_hash`, `index_name`, `updated_at`) — **Holds PII**
     - `customer_analytics_profiles` (`resource_id`, `customer_reference`, `email`, `phone`, `email_hash`, `audience_cohort`, `updated_at`) — **Holds PII**
     - `support_records` (`resource_id`, `customer_reference`, `requester_name`, `requester_email`, `requester_phone`, `message_excerpt`, `updated_at`) — **Holds PII**
     - `customer_exports` (`resource_id`, `customer_reference`, `owner_email`, `owner_phone`, `object_key`, `updated_at`) — **Holds PII**
     - `connector_subscriptions` (`resource_id`, `customer_reference`, `customer_email`, `connector_name`, `enabled`, `last_delivery_status`, `updated_at`) — **Active Flow Risk**
     - `backup_restore_entries` (`resource_id`, `customer_reference`, `customer_email`, `archive_key`, `restore_allowed`, `updated_at`) — **Restore Risk**
     - `security_audit_records` (`resource_id`, `subject_reference`, `event_code`, `retention_until`, `updated_at`) — **Mandatory Retention**

2. **Replication & Drift Snapshots (13 files):**
   - Files: `customer_data_read_replica_*.sql` (5), `customer_data_regional_replicas_*.sql` (3), `customer_data_reporting_replica_*.sql` (2), `customer_data_failover_replica_*.sql` (1), `customer_accounts_failover_replica_*.sql` (1), `customer_search_primary_*.sql` (1).
   - Tables: `customer_data_primary`, `customer_data_read_replica`, `customer_data_replica_ap_south`, `customer_data_replica_eu_west`, `customer_data_reporting_replica`, `customer_data_failover_replica`.
   - Columns: `resource_id, origin_system, collection_name, record_json, updated_at`.
   - `record_json` stores raw serialized records containing customer identity attributes and statuses. Replication drift occurs when a record is deleted in `primary` (`record_json` absent or marked deleted) but remains present in read, regional, reporting, or failover replicas.

---

## 3. Deletion Rules Decision Digest

The platform policy defined in `dataset/deletion_rules.csv` dictates the required action and operational steps:

| Rule ID | Data Category | Condition / Scope | Required Action | Permitted Retained Fields | Operations Implied | Verification Implied |
|---|---|---|---|---|---|---|
| `rule_01` | `USER_PROFILE` | Always | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_02` | `SECONDARY_IDENTIFIER` | Always | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_03` | `SEARCH_INDEX_ENTRY` | Always | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_04` | `CACHE_ENTRY` | Always | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_05` | `SUPPORT_MESSAGE` | Contains shared context | `REDACT` | Order/ticket context, anonymized timestamps | `REDACT_RECORD` (REDACTED) | `VERIFY_RECORD_REDACTED` |
| `rule_06` | `SUPPORT_ATTACHMENT` | Belongs only to subject | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_07` | `ANALYTICS_PROFILE` | Attributable to user | `ANONYMIZE` | Cohort statistics, unlinked metrics | `ANONYMIZE_RECORD` (ANONYMIZED) | `VERIFY_RECORD_ANONYMIZED` |
| `rule_08` | `PRODUCT_TELEMETRY` | Attributable to user | `ANONYMIZE` | Aggregate events, unlinked telemetry | `ANONYMIZE_RECORD` (ANONYMIZED) | `VERIFY_RECORD_ANONYMIZED` |
| `rule_09` | `USER_EXPORT` | Always | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_10` | `MARKETING_PROFILE` | Always | `DELETE` | None | `DELETE_RECORD` (ABSENT) | `VERIFY_RECORD_ABSENT` |
| `rule_11` | `EMAIL_DELIVERY_LOG` | Contains email address | `REDACT` | Delivery status code, timestamp | `REDACT_RECORD` (REDACTED) | `VERIFY_RECORD_REDACTED` |
| `rule_12` | `SECURITY_AUDIT_LOG` | Within retention period | `RETAIN` | `resource_id, subject_reference, event_code, retention_until` | *None (Do not delete)* | `VERIFY_RECORD_PRESENT` |
| `rule_13` | `LEGAL_HOLD_RECORD` | Legal hold is active | `RETAIN` | Full preserved record | *None (Do not delete)* | `VERIFY_RECORD_PRESENT` |
| `rule_14` | `BACKUP_ARCHIVE` | Restore can be blocked | `RETAIN` | Archive key (restore access disabled) | `BLOCK_RESTORE` (BLOCKED) | `VERIFY_RESTORE_BLOCKED` |
| `rule_15` | `ACCOUNT_TOMBSTONE` | Account deleted, reference needed | `REDACT` | Internal `user_id` only (remove name, email, phone, email_hash) | `REDACT_RECORD` (REDACTED) | `VERIFY_RECORD_REDACTED` |

### Special Flow & Replication Rules
- **Active Data Flow (`connector_subscriptions`):** If an active sync job (`enabled=1` / `ACTIVE`) connects to target systems, emit finding `REPORT_ACTIVE_DATA_FLOW` -> remediation `DISABLE_DATA_FLOW` -> verification `VERIFY_DATA_FLOW_DISABLED`.
- **Restore Risk (`backup_restore_entries`):** If `restore_allowed=1` for a backup created before deletion, emit finding `REPORT_RESTORE_RISK` -> remediation `BLOCK_RESTORE` -> verification `VERIFY_RESTORE_BLOCKED`.
