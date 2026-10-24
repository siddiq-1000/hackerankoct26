# Conflict Resolution Architecture & Real Dataset Grounding

This document defines the deterministic conflict resolution precedence implemented in `code/conflicts.py` and `code/state.py`. Every conflict type reflects conditions observed in the challenge dataset (`dataset/`), with corresponding code locations, unit tests, and empirical examples.

---

## 1. Conflict Precedence Hierarchy

When disparate evidence streams report divergent states for the same user or resource, the pipeline resolves them using this strict hierarchy:

```
[Level 1: Highest]  RETAIN       (Rule 12 Security Audit Log retention period)
[Level 2]           BLOCK        (Rule 14 Backup Archive restore paths blocked)
[Level 3]           DISABLE      (Active connectors / replication flows halted)
[Level 4]           ANONYMIZE    (Rule 07 Analytics Profile direct PII unlinked)
[Level 5]           REDACT       (Rule 05 Support message PII stripped, Rule 15 Tombstones)
[Level 6]           DELETE       (Rule 01 User Profile, Rule 03 Search Index removal)
[Level 7: Lowest]   ABSENT       (Absence confirmed across all ground truth stores)
```

---

## 2. Real Conflicts Occurring in Dataset

### Conflict 1: `reported_status` vs. Ground Truth Evidence
- **Precedence Rule:** Ground truth evidence at or before `audit_at` strictly overrides workflow claims (`reported_status`). Reported status is a claim, not proof (§6.5).
- **Code Location:** `code/state.py` (`reconstruct_state`) and `code/planner.py` (`plan_audit`).
- **Unit Test:** `code/evaluation/test_policy.py` (`test_reported_complete_overridden_by_finding`).
- **Real Examples:**
  - `case_33` (`ingrid.dahl@outlook.com`): `reported_status = COMPLETE`, but read replica in `evidence_23` (`customer_data_reporting_replica_20260701.sql`) retains primary profile `account_1407`. Resolved as `INCOMPLETE`.
  - `case_34` (`haruka.s1838@zoho.com`): `reported_status = COMPLETE`, but inventory in `evidence_04` (`customer_data_inventory_20260921.sql`) and trace log `evidence_01` retain exposed support ticket and active connector. Resolved as `INCOMPLETE`.

### Conflict 2: Primary purged vs. Replica / Failover Replication Drift
- **Precedence Rule:** If any database replica, failover copy, or snapshot retains personal data, the record is `PRESENT`, even if the primary database purged it.
- **Code Location:** `code/state.py` (multi-database iteration in `_observe_sql_databases`).
- **Unit Test:** `code/evaluation/custom_cases/case_b.json` (Case B: Regional Replica Drift).
- **Real Examples:**
  - `case_105` (`z.suleiman42@yahoo.com`): Primary database contains no active profile, but failover replica in `evidence_10` (`customer_data_failover_replica_20260829.sql`) retains `account_6345`. Emits `REPORT_REMAINING_RECORD`.
  - `case_153` (`a.adeyemi9897@yahoo.com`): Primary purged, but reporting replica in `evidence_15` (`customer_data_read_replica_20260802.sql`) retains `account_8023`. Emits `REPORT_REMAINING_RECORD`.

### Conflict 3: Activity Stream Claims vs. Physical Evidence State
- **Precedence Rule:** An activity event claiming `SUCCESS` (e.g. `DELETE_RECORD ... reported_result=SUCCESS`) is treated as a claim. If an export or replica captured after the event still contains the record, the physical evidence establishes the resulting state (§6.6).
- **Code Location:** `code/state.py` (`observe_case_state`).
- **Unit Test:** `code/evaluation/test_policy.py` (`test_activity_claim_vs_evidence`).
- **Real Examples:**
  - `case_50` (`darwish.omar@icloud.com`): `reported_status = NOT_STARTED`, but UI screenshot `evidence_19` (`analytics_profile_view_20260713.png`) proves `analytics_7438` is exposed. Emits `REPORT_EXPOSED_PII`.

### Conflict 4: Current vs. Historical Identity Owner (Identity Collision)
- **Precedence Rule:** Identifiers from `user_identities.csv` and change history in `user_audit_log.csv` are resolved to the stable `user_id`. When an intake request arrives under a historical email, the resolver recovers all current and historical attributes without confusing cross-user reassignments.
- **Code Location:** `code/identity.py` (`IdentityResolver.resolve_identity`).
- **Unit Test:** `code/evaluation/custom_cases/case_a.json` (Case A: Historical Email Resolution).
- **Real Examples:**
  - `case_47` (`zofia-dvorak79@proton.me`): Submitted under historical email `zofia-dvorak79@proton.me`. Resolved to current email `zofia-dvorak@proton.me` (`user_45`), matching both current and historical logs.
  - `case_161` (`noah-sullivan83@gmail.com`): Submitted under historical email `noah-sullivan83@gmail.com`. Resolved to current identity `noah-sullivan@gmail.com` (`user_159`).

### Conflict 5: Events Before vs. After `audit_at` Cutoff & Temporal Precedence
- **Precedence Rule:** Only evidence captured at or before `audit_at` influences the case outcome (§6.2). When multiple evidence items captured before `audit_at` present divergent states for the same resource, the **most recent observation at or before `audit_at` wins**. A newer live log probe or replica snapshot captured closer to `audit_at` strictly supersedes an older snapshot.
- **Code Location:** `code/state.py` (temporal filtering `ef.captured_at <= audit_dt` and chronological state reconstruction).
- **Unit Test:** `code/evaluation/custom_cases/case_c.json` (Case C: Post-Cutoff Decoy) and `code/evaluation/test_policy.py`.
- **Real Examples:**
  - `case_21` (`amara-okeke@proton.me`): Audited at `2026-09-15T12:00:00Z`. Subsequent customer snapshot bundle `evidence_02` captured on `2026-09-17T11:44:00Z` is excluded from evaluation; state is established from `evidence_92`.
  - `case_416` (`KEIKO.SATO@OUTLOOK.COM`): `audit_at` is `2026-03-25T09:00:00Z`. Older snapshot `evidence_68` (captured 2026-03-20) showed account absence, but live syslog probe `evidence_39` (captured 2026-03-25T08:59:44Z, 5 days later) proved `search_6600` remained present and connector `data_flow_1412` was active. The newer evidence strictly supersedes the older snapshot, resolving to `INCOMPLETE`.
  - `case_417` (`s.kim14@yahoo.com`): `audit_at` is `2026-03-25T09:00:00Z`. Older snapshot `evidence_68` (2026-03-20) showed account absence, but live syslog probe `evidence_39` (2026-03-25) revealed `profile_lookup_completed rows="1" http_status="200" resource_id="account_4921"` and search hit `search_5479`. Resolved to `INCOMPLETE`.
  - `case_517` (`yetunde.a3014@zoho.com`): `audit_at` is `2026-02-03T06:00:00Z`. Older snapshot `evidence_62` (2026-01-29) was superseded by live stream `evidence_48` (2026-02-03T05:59:42Z) showing `search_2818` present and `data_flow_8165` active. Resolved to `INCOMPLETE`.

### Conflict 6: Null-Identifier Records vs. Subject Grounding (Analytics Resolution)
- **Precedence Rule:** Anonymized records whose direct identifiers are `NULL` under `rule_07` cannot be linked by string search. They are associated with a case if and only if an unambiguous 1-to-1 batch link exists in `system_activity.csv` within the case's workflow window before `reported_at`, backed by valid physical evidence at or before `audit_at`. Ambiguous or orphan records are never assigned.
- **Code Location:** `code/analytics_linker.py` and `code/config.py` (`LINK_NULL_IDENTIFIER_ANALYTICS`).
- **Unit Test:** `code/evaluation/test_custom_cases.py`.
- **Real Examples:**
  - `case_21` (`amara-okeke@proton.me`): Linked to `analytics_5335` via activity `activity_3665` (11:31:34Z) and verified on `evidence_92`.
  - `case_25` (`s.yoon04@gmail.com`): Linked to `analytics_1895` via activity `activity_3602` (11:31:08Z) and verified on `evidence_92`.

### Conflict 7: Multi-Line Syslog Decoupling vs. Trace Correlation
- **Precedence Rule:** In asynchronous logging frameworks, query initiation lines (e.g. `index_query_started`, `profile_lookup_started`) contain subject identifiers (`query="email"`) while completion lines (e.g. `index_query_completed result="hit"`, `profile_lookup_completed rows=1`) contain resource IDs and outcomes without repeating the search terms. Isolated line-by-line filtering discards completion lines, falsely reporting absence. Trace correlation by `trace_id` takes precedence over naive single-line regex filtering (§6.6).
- **Code Location:** `code/state.py` (syslog trace correlation using `trace_id` and `tr-\d+`).
- **Unit Test:** `code/evaluation/test_custom_cases.py` (Case E / Case G).
- **Real Examples:**
  - `case_416` (`KEIKO.SATO@OUTLOOK.COM`): In `evidence_39`, initiation log contained email with `tr-4045793`. Completion line recorded `event="index_query_completed" result="hit" resource_id="search_6600"`. Trace correlation proves search index entry remains present, correctly classifying case as `INCOMPLETE`.
  - `case_417` (`s.kim14@yahoo.com`): In `evidence_39`, initiation log with `tr-0854521` led to `event="profile_lookup_completed" rows="1" http_status="200" resource_id="account_4921"`. Trace correlation confirms account profile persists, correctly classifying case as `INCOMPLETE`.
  - `case_420` (`storres487178@fastmail.com`): In `evidence_39`, trace `tr-0441096` led to `index_query_completed result="hit" resource_id="search_8472"`. Confirms search entry persists, correctly classifying case as `INCOMPLETE`.
  - `case_517` (`yetunde.a3014@zoho.com`): In `evidence_48`, initiation log with `tr-6648486` correlated with `connector_heartbeat resource_id="data_flow_8165" enabled="true"`. Correctly classifies case as `INCOMPLETE` with active data flow finding.
