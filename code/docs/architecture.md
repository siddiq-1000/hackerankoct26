# Architecture & System Design: Deletion Audit Agent

**Project:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**Pipeline Strategy:** Deterministic-First Pipeline with Cached Multimodal & LLM Capabilities

---

## 1. System Architecture Overview

The deletion audit engine is designed to process the 518 evaluation requests in `dataset/deletion_requests.csv` with 100% reproducibility, zero schema assumptions, strict canonical step sorting, and minimal token/API cost.

```
                    ┌──────────────────────────────┐
                    │    deletion_requests.csv     │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                       [1] Loader & Registry
                                   │
                                   ▼
                       [2] Intent Classifier
                                   │
               ┌───────────────────┴───────────────────┐
               │                                       │
     (Non-Deletion Intent)                    (Authorized Deletion)
               │                                       │
               ▼                                       ▼
     NOT_APPLICABLE, []                    [3] Identity Resolver
                                           (user_id, emails, hashes,
                                            phones across all time)
                                                       │
                                                       ▼
                                             [4] Evidence Indexer
                                            (SQLite DBs, JSON caches,
                                             Logs, Decoded PDFs, Images)
                                                       │
                                                       ▼
                                          [5] State Reconstructor
                                          (cutoff at case.audit_at;
                                           grounded vs claimed state)
                                                       │
                                                       ▼
                                             [6] Policy Engine
                                            (deletion_rules.csv:
                                             DELETE/REDACT/ANON/RETAIN)
                                                       │
                                                       ▼
                                              [7] Gap Analyzer
                                           (identify lingering PII,
                                            flows, unblocked restores)
                                                       │
                                                       ▼
                                              [8] Step Planner
                                          (FINDING -> REMEDIATION ->
                                           VERIFICATION, sorted)
                                                       │
                                                       ▼
                                            [9] Output Validator
                                                       │
                                                       ▼
                                            output.csv & Reports
```

---

## 2. Module Specifications & Execution Modes

| Module | Responsibility | Implementation Mode | LLM / API Calls per Request |
|---|---|---|---|
| **[1] Loader & Registry** | Parses CSVs into strongly-typed dataclasses. Normalizes ISO-8601 timestamps to timezone-aware UTC. | **Pure Python rules** | 0 |
| **[2] Intent Classifier** | Evaluates `request_text` to detect non-deletion actions (access, portability, update, opt-out, cancel). | **Rule-engine first** (regex for known non-deletion signals); **LLM fallback** with temperature 0 and disk hash cache. | ~0.02 (≤ 10 calls total across 518 cases) |
| **[3] Identity Resolver** | Resolves `user_id` from current email or historical email. Walks `user_audit_log.csv` forward and backward to assemble full `IdentitySet` (current + historical emails, phones, SHA-256 hashes, user_id). | **Pure Python rules** | 0 |
| **[4] Evidence Indexer** | Ingests all 94 evidence files: executes 24 SQL files into SQLite; parses 28 JSON bundles; regex-indexes 26 log files; decompresses 4 ReportLab PDFs using built-in `base64.a85decode` + `zlib`; transcribes 11 PNG admin screenshots into cached JSON. | **Deterministic engine** (SQLite + JSON/Log/PDF parser) + **One-time Vision cache** for 11 PNGs. | 0 (cached) |
| **[5] State Reconstructor** | Evaluates resource states at cutoff `audit_at`. Filters out events/evidence with `timestamp > audit_at`. Detects replication drift between primary and replica tables. | **Pure Python rules** | 0 |
| **[6] Policy Engine** | Encodes the 15 enterprise deletion rules from `deletion_rules.csv`. Maps data category to permitted action (`DELETE`, `REDACT`, `ANONYMIZE`, `RETAIN`). | **Pure Python rules** | 0 |
| **[7] Gap Analyzer** | Compares actual state against policy requirement. Identifies unpurged records (`REPORT_REMAINING_RECORD`), exposed PII (`REPORT_EXPOSED_PII`), active sync jobs (`REPORT_ACTIVE_DATA_FLOW`), and restore risks (`REPORT_RESTORE_RISK`). | **Pure Python rules** | 0 |
| **[8] Step Planner** | Assembles the complete plan: findings -> remediation actions -> verification checks. Generates post-remediation verification for all remediated items, plus mandatory profile and security audit checks. | **Pure Python rules** | 0 |
| **[9] Output Validator** | Sorts steps by `(phase_rank, op_rank, system_id, resource_id)`. Numbers steps sequentially from 1. Verifies JSON validity, evidence ID existence, and CSV structure. | **Pure Python rules** | 0 |

---

## 3. Data Flow & Contract Alignment

### 3.1 Vocabulary & Canonical Sort Key
All steps adhere strictly to the vocabulary and order from the problem statement:
1. **Phase Rank:** `FINDING` (1) < `REMEDIATION` (2) < `VERIFICATION` (3).
2. **Operation Rank:**
   - FINDING: `REPORT_REMAINING_RECORD` (1) < `REPORT_EXPOSED_PII` (2) < `REPORT_ACTIVE_DATA_FLOW` (3) < `REPORT_RESTORE_RISK` (4).
   - REMEDIATION: `DISABLE_DATA_FLOW` (1) < `BLOCK_RESTORE` (2) < `DELETE_RECORD` (3) < `REDACT_RECORD` (4) < `ANONYMIZE_RECORD` (5).
   - VERIFICATION: `VERIFY_RECORD_ABSENT` (1) < `VERIFY_RECORD_PRESENT` (2) < `VERIFY_RECORD_REDACTED` (3) < `VERIFY_RECORD_ANONYMIZED` (4) < `VERIFY_DATA_FLOW_DISABLED` (5) < `VERIFY_RESTORE_BLOCKED` (6).
3. **`system_id` Ascending:** Case-sensitive ASCII alphabetical order.
4. **`resource_id` Ascending:** Case-sensitive ASCII alphabetical order.

### 3.2 Evidence ID Citation Contract
- For `COMPLETE` status: only `VERIFICATION` steps, each citing a valid evidence `file_id` (e.g. `evidence_54`) proving the current compliant state at `audit_at`.
- For `INCOMPLETE` status: `FINDING` steps cite the evidence `file_id` exposing the violation. `REMEDIATION` and `VERIFICATION` steps use `evidence_id: ""`.
- For `NOT_APPLICABLE` status: `steps_json: []`.

---

## 4. Resource Allocation & Token / Cost Budget

- **Deterministic Execution Ratio:** > 99.5% of total pipeline computation is executed via deterministic Python code.
- **Estimated Model Calls:**
  - Intent classification fallback: 0 to 10 calls total (only on ambiguous multilingual text).
  - Admin image transcription: 11 calls total (one-off, persisted to `code/cache/image_transcripts.json`).
  - Total LLM calls across all 518 cases: **≤ 21 calls**.
  - Average calls per evaluation request: **~0.03 calls/case**.
  - Total estimated token cost: **<$0.05** across the entire dataset.

---

## 5. Verification Against Ground Truth

The architecture has been verified against all 32 sample cases in `dataset/sample_output.csv`:
- Correct identification of `COMPLETE` (10 cases) vs `INCOMPLETE` (22 cases).
- Accurate detection of historical correlation keys (`case_12`).
- Symmetric remediation and verification plan generation for all affected resources.
- Correct handling of account tombstones (`case_31`, `case_32`) and replication drift (`case_05`).
