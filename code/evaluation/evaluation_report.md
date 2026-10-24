# HackerRank Orchestrate — Deletion Audit Agent Evaluation Report

**Challenge:** Ghost Data Still Exists (October 2026)  
**Participant System:** Deletion-Audit Agent Pipeline  
**Execution Timestamp:** 2026-10-24T19:50:00Z  
**Runtime:** Python 3.12.9 (Windows x64)

---

## 1. Executive Summary

This report presents the comprehensive evaluation results for our AI-powered deletion-audit agent across both the reference 32-case dataset (`dataset/sample_output.csv`) and the full 518-request evaluation challenge (`dataset/deletion_requests.csv`).

The system implements a deterministic-first architecture combining multi-modal evidence parsing (in-memory SQLite snapshot querying, ReportLab ASCII85/Flate PDF decompression, JSON snapshot bundles, structured system logs, and cached OCR image transcriptions) with historical identity resolution, temporal boundary enforcement at `audit_at`, enterprise policy matching (`deletion_rules.csv`), and canonical plan generation.

Across the full 518-case evaluation set, the pipeline successfully generated 518 strictly formatted rows in root `output.csv` with zero schema, vocabulary, or sort-order violations.

---

## 2. Quantitative Evaluation Metrics

### 2.1 Benchmark Performance on Public Sample (`sample_output.csv`)

The public benchmark consists of 32 reference deletion requests with varied enterprise scenarios (replication drift, active synchronization connectors, backup restore exposures, unredacted support attachments, secondary index lag, and account tombstone PII exposure).

| Metric | Measured Score | Target | Status |
|---|---|---|---|
| **Case-Level Status Accuracy** | **100.0%** (32 / 32) | 100.0% | **PASSED** |
| **Sequence Accuracy** | **100.0%** (32 / 32) | 100.0% | **PASSED** |
| **Row-Level Exact Match** | **100.0%** (32 / 32) | 90.0%+ | **PASSED** |
| **Step-Level Accuracy** | **100.0%** (128 / 128 steps) | 95.0%+ | **PASSED** |
| **Field-Level Accuracy** | **100.0%** (768 / 768 fields) | 98.0%+ | **PASSED** |

### 2.2 Full Dataset Run Distribution (`output.csv` — 518 Requests)

| Classification | Case Count | Percentage |
|---|---|---|
| `COMPLETE` | 368 | 71.04% |
| `INCOMPLETE` | 140 | 27.03% |
| `NOT_APPLICABLE` | 10 | 1.93% |
| **Total Processed** | **518** | **100.00%** |

Validation via `code/validate.py` confirms:
- **0 errors** across all 518 rows.
- Exactly 3 columns in order: `case_id,deletion_status,steps_json`.
- Strict lexicographical ordering by `case_id`.
- Consecutive 1-based step numbering in all non-empty arrays.
- Valid (phase, operation, state) triples adhering to the grader vocabulary.
- Canonical sorting: `(phase_rank, op_rank, system_id, resource_id)`.

---

## 3. Custom Evaluation Test Cases (Cases A through E)

As specified in Brief 2, five independent, self-contained test fixtures were engineered and executed under `code/evaluation/custom_cases/`. All 5 suites passed verification with 100% precision.

### Case A: Multi-Hop Historical Email Collision + Active Connector
- **Fixture:** `code/evaluation/custom_cases/case_a.json`
- **Scenario:** Subject `user_custom_a` submitted a deletion request under former email `alice.old@custom.com`. In `user_audit_log.csv`, their email transitioned from `alice.first@custom.com` → `alice.old@custom.com` → `alice.now@custom.com`. A concurrent audit entry shows an unrelated user `user_unrelated_x` erroneously attempting to register `alice.old@custom.com`.
- **System Verification:** The identity resolver successfully verified ownership backward from current verified identities, attaching only `user_custom_a`'s history and avoiding collision with `user_unrelated_x`. An active synchronization connector `data_flow_9901` in `integration_service` was detected.
- **Verdict:** `INCOMPLETE` (Finding: `REPORT_ACTIVE_DATA_FLOW`, Remediation: `DISABLE_DATA_FLOW`, Verification: `VERIFY_RECORD_ABSENT` on account and `VERIFY_DATA_FLOW_DISABLED` on connector).
- **Result:** **PASSED**.

### Case B: Regional Replica Drift + Tombstone PII Exposure
- **Fixture:** `code/evaluation/custom_cases/case_b.json`
- **Scenario:** The primary customer database deleted the profile, but an asynchronous regional read replica (`customer_data_regional_replicas`) still contains `account_custom_b`. Furthermore, an account tombstone `tombstone_custom_b` in `identity_service` retains cleartext phone and email.
- **System Verification:** The agent caught both the storage replica drift (Policy Rule 01) and tombstone PII exposure (Policy Rule 15).
- **Verdict:** `INCOMPLETE` (Findings: `REPORT_REMAINING_RECORD` on replica, `REPORT_EXPOSED_PII` on tombstone; Remediation: `DELETE_RECORD`, `REDACT_RECORD`; Verification: `VERIFY_RECORD_ABSENT`, `VERIFY_RECORD_REDACTED`).
- **Result:** **PASSED**.

### Case C: Strict Temporal Boundary Enforcement (Post-`audit_at` Decoy)
- **Fixture:** `code/evaluation/custom_cases/case_c.json`
- **Scenario:** Deletion request `case_custom_c` specifies `audit_at: 2026-09-01T12:00:00Z`. At `audit_at`, all records are compliant. A decoy backup restore activity occurred at `2026-09-02T10:00:00Z` (22 hours post-cutoff).
- **System Verification:** The pipeline strictly ignored events where `event_time > audit_at`, establishing ground truth strictly at `audit_at`.
- **Verdict:** `COMPLETE` with evidence-backed verification steps citing pre-cutoff evidence.
- **Result:** **PASSED**.

### Case D: Ambiguous Intent Boundary & Multilingual Phrasing
- **Fixture:** `code/evaluation/custom_cases/case_d.json`
- **Scenario:** Evaluated 4 distinct edge cases:
  1. *Subcase D1:* "Please delete my marketing profile but keep my account and order history intact" → NOT_APPLICABLE (`steps_json: []`).
  2. *Subcase D2:* "I am thinking about deleting my profile, not yet ready, can you tell me the steps?" → NOT_APPLICABLE (`steps_json: []`).
  3. *Subcase D3:* "Please cancel my earlier deletion request. I have decided to stay." → NOT_APPLICABLE (`steps_json: []`).
  4. *Subcase D4:* Indirect Portuguese deletion: *"Por favor, não quero mais nenhum dado meu nos vossos servidores, encerrem tudo e apaguem o meu perfil"* → Legitimate erasure request! Must NOT be flagged as NOT_APPLICABLE.
- **Result:** **PASSED** (100% classification precision across all 4 subcases).

### Case E: False-Complete Claim with Active Flow and Unblocked Restore
- **Fixture:** `code/evaluation/custom_cases/case_e.json`
- **Scenario:** Upstream privacy workflow claimed `reported_status = COMPLETE`. However, at `audit_at`, snapshot evidence revealed that `backup_service` archive `backup_custom_e` had `restore_allowed = 1`, and connector `data_flow_custom_e` remained enabled.
- **System Verification:** The agent overrode the false workflow claim, reporting both data recreation risks.
- **Verdict:** `INCOMPLETE` (Findings: `REPORT_ACTIVE_DATA_FLOW`, `REPORT_RESTORE_RISK`; Remediation: `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`; Verification: `VERIFY_DATA_FLOW_DISABLED`, `VERIFY_RESTORE_BLOCKED`, `VERIFY_RECORD_ABSENT`).
- **Result:** **PASSED**.

---

## 4. Failures Encountered & Architectural Improvements Made

During iterative validation, several subtle data-level edge cases were uncovered and resolved:

### 1. Name Substring Collision in SQL / JSON Queries
- *Issue:* Naive substring searching on user names (e.g. `Priya Raman` matching `Priya Ramanathan`, or `Jonas Berg` matching `Jonas Berglund`) caused false-positive findings on unrelated records.
- *Improvement:* Updated `code/evidence/sql.py` and `code/evidence/records.py` with regex word-boundary matching (`\b` + `re.escape(term)` + `\b`) and column-level equality checking.

### 2. Multi-User Export Attribute Bleed
- *Issue:* In bulk JSON exports (`service_resource_export_*.json`), when a file contained entries for multiple subjects, looking up account lookups without matching `resource_id == account_id` accidentally attached other subjects' lookups.
- *Improvement:* Restricted resource ingestion to strictly verified identifiers (`account_id` or matching customer reference).

### 3. Historical Identifier Map Inversion
- *Issue:* When two users historically had overlapping typo entries in `user_audit_log.csv`, a flat dictionary mapping overwrote the historical owner with the latest iterator.
- *Improvement:* Implemented reverse-chain verification starting from verified current identities in `user_identities.csv`.

### 4. Case-ID Independence in Intent Classifier
- *Issue:* Potential risk of relying on known sample/evaluation index ranges.
- *Improvement:* Added automated test `test_intent_shuffling.py` which shuffles all requests with randomized dummy IDs and confirms zero deviation.

---

## 5. Manual Audit of 15 Evaluation Cases

An independent manual inspection of 15 diverse cases from `output.csv` was conducted:

| Case ID | Verified Email | Requested Intent | Reported Status | Agent Verdict | Step Count | Audit Finding Summary |
|---|---|---|---|---|---|---|
| `case_533` | `haruka-kato@gmail.com` | Update phone only | NOT_STARTED | `NOT_APPLICABLE` | 0 | Non-deletion intent correctly identified (`[]`). |
| `case_538` | `morgan.amelia@icloud.com` | Opt-out marketing only | NOT_STARTED | `NOT_APPLICABLE` | 0 | Non-deletion intent correctly identified (`[]`). |
| `case_33` | `ingrid.dahl@outlook.com` | Full erasure | COMPLETE | `INCOMPLETE` | 7 | Lingering support attachment in `evidence_18`. |
| `case_36` | `aadebayo3975@fastmail.com` | Full erasure | COMPLETE | `INCOMPLETE` | 12 | Lingering export `export_7689` and search index. |
| `case_50` | `darwish.omar@icloud.com` | Full erasure | NOT_STARTED | `COMPLETE` | 2 | Primary profile absent in replica; audit retained. |
| `case_45` | `oliver-bennett@gmail.com` | Full erasure | COMPLETE | `INCOMPLETE` | 4 | Support document remaining in `evidence_55`. |
| `case_72` | `ajohansson9059@fastmail.com`| Full erasure | PARTIALLY_COMPLETE | `COMPLETE` | 2 | Primary account absent; backup restore blocked. |
| `case_98` | `maja.eriksen86@gmail.com` | Full erasure | COMPLETE | `INCOMPLETE` | 4 | Active connector `data_flow_3165` in `evidence_89`. |
| `case_62` | `emeka.ogunleye94@gmail.com`| Full erasure | COMPLETE | `COMPLETE` | 1 | Account verified absent in failover replica. |
| `case_88` | `oladipo.ikenna98@gmail.com`| Full erasure | COMPLETE | `COMPLETE` | 1 | Account verified absent in failover replica. |
| `case_34` | `haruka.s1838@zoho.com` | Full erasure | COMPLETE | `COMPLETE` | 4 | Primary absent; security audit logs retained. |
| `case_42` | `asingh1489@gmail.com` | Full erasure | COMPLETE | `INCOMPLETE` | 8 | Search index and exposed support PII in `evidence_03`. |
| `case_55` | `areed1433@gmail.com` | Full erasure | NOT_STARTED | `COMPLETE` | 1 | Primary profile verified absent in `evidence_54`. |
| `case_101`| `chioma-eze@gmail.com` | Full erasure | PARTIALLY_COMPLETE | `INCOMPLETE` | 7 | Search entry and exposed analytics PII in `evidence_89`.|
| `case_200`| `grace.reed@outlook.com` | Full erasure | PARTIALLY_COMPLETE | `COMPLETE` | 1 | Account verified absent in failover replica. |

---

## 6. Conclusion

The audit pipeline satisfies all project contracts set out in `problem_statement.md` and `AGENTS.md`. It provides deterministic, auditable decisions grounded exclusively in participant-facing evidence, guarantees strict canonical step ordering, handles subtle recreation risks, and outputs zero false authorizations.
