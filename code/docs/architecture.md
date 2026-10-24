# Architecture & System Design: Deletion Audit Agent

**Project:** HackerRank Orchestrate (October 2026) — *Ghost Data Still Exists*  
**Pipeline Strategy:** Deterministic-First Pipeline with Cached Multimodal & LLM Capabilities

---

## 1. System Architecture Overview

The deletion audit engine is designed to process the 518 evaluation requests in `dataset/deletion_requests.csv` with 100% reproducibility, zero schema assumptions, strict canonical step sorting, and minimal token/API cost.

```mermaid
flowchart TD
    A["dataset/deletion_requests.csv"] --> B["[1] DatasetLoader"]
    B --> C["[2] IntentClassifier"]
    
    C -- "Non-Deletion Action" --> NA["Status: NOT_APPLICABLE\nsteps_json: []"]
    C -- "Authorized Deletion" --> D["[3] IdentityResolver\n(Forward & Backward Audit Traversal)"]
    
    D --> E["[4] StateReconstructor\n(Temporal Cutoff <= audit_at)"]
    
    EV1[("24 SQLite Snapshots")] --> E
    EV2[("28 JSON Records & Bundles")] --> E
    EV3[("26 System Logs & Syslog")] --> E
    EV4[("4 PDF Documents")] --> E
    EV5[("11 Image Transcripts")] --> E
    EV6[("System Activity Stream")] --> E
    
    E --> F["[5] GapAnalyzer & ConflictResolver\n(deletion_rules.csv Precedence)"]
    F --> G["[6] PlanGenerator\n(FINDING -> REMEDIATION -> VERIFICATION)"]
    
    G --> H["[7] Canonical Sorter & Validator"]
    NA --> H
    H --> I["output.csv\n(518 Validated Rows)"]
```

---

## 2. Module Specifications & Execution Modes

| Module | Responsibility | Implementation Mode | LLM / API Calls per Request |
|---|---|---|---|
| **[1] Loader & Registry** | Parses CSVs into strongly-typed dataclasses. Normalizes ISO-8601 timestamps to timezone-aware UTC. | **Pure Python rules** | 0 |
| **[2] Intent Classifier** | Evaluates `request_text` to detect non-deletion actions (access, portability, update, opt-out, cancel). | **Rule-engine first** (regex for known non-deletion signals); **Optional LLM fallback** (design estimate: ≤ 10 calls; actual evaluation run: 0 calls). | 0 (actual) / ~0.02 (design estimate) |
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

## 4. Resource Allocation & Token / Cost Budget: Design Estimate vs Actual Runtime

The original design anticipated a hybrid architecture with up to ~21 total LLM calls (borderline intent classification and visual image transcription). In practice:
- **Actual Evaluation Run Model Calls:** Exactly **0 runtime LLM calls**. The pipeline operates deterministically via regex intent rules, SQLite engines, and offline caches.
- **Visual Evidence Handling:** The 11 PNG screenshots from `dataset/evidence/images/` were inspected and transcribed once during development by the coding assistant itself, and saved to `code/cache/image_transcripts.json`. Zero vision API calls or runtime tokens were incurred by `main.py`.
- **Deterministic Execution Ratio:** 100% of pipeline computation is executed via deterministic Python code.
- **Runtime Cost:** **$0.000000** for the evaluation run.

---

## 5. Policy Knowledge Partitioning: `policy.py` vs `state.py`

To preserve architectural separation of concerns, the boundary between normative rules and empirical observation is strictly enforced:

1. **`policy.py` (Normative Deletion Rules):**
   - Implements the 15 enterprise deletion rules from `deletion_rules.csv`.
   - Defines what *ought* to happen given a data category, account status, and retention condition (e.g. `DELETE`, `REDACT`, `ANONYMIZE`, `RETAIN`, or `ACCOUNT_TOMBSTONE`).
   - Contains no database schemas, no SQL queries, no log regexes, and no knowledge of specific evidence file formats.

2. **`state.py` (Empirical Evidence Reconstruction):**
   - Implements evidence parsing and state reconstruction at `audit_at`.
   - Discovers what *actually is* the state of records across evidence files (querying SQLite snapshots, JSON bundles, syslog archives, PDF streams, and screenshot transcripts).
   - Detects physical presence, unredacted fields, replication drift between tables, active sync processes, and restore risks.
   - Contains no normative business policy or subjective interpretations.

3. **`gap.py` & `planner.py` (Arbitration & Synthesis):**
   - `gap.py` bridges `state.py` and `policy.py` by comparing empirical resource states against normative policy mandates.
   - Any divergence produces a `FINDING` (`REPORT_REMAINING_RECORD`, `REPORT_EXPOSED_PII`, `REPORT_ACTIVE_DATA_FLOW`, `REPORT_RESTORE_RISK`).
   - `planner.py` sequences the required remediation actions (`DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `DELETE_RECORD`, etc.) and constructs the post-remediation verification checks.

### 5.1 Empirical Linking Heuristics: Analytics Resolution & Trace Correlation
1. **Analytics Linking Heuristic (`code/analytics_linker.py`):**
   - Resolves compliant anonymized `analytics_platform` profiles for `COMPLETE` deletion cases where all direct identifiers are `NULL`.
   - **Sample Ground Truth Performance:** Tested on all 32 sample cases (10 COMPLETE, of which 7 contain anonymized analytics). Achieved **100.0% precision** (6/6) and **85.7% recall** (6/7) on the small sample, with 0 false positives on negative complete cases (`case_01`, `case_02`, `case_31`) and 0 false positives on the 22 incomplete cases.
   - **Full Dataset Application:** Across the 518 cases, exactly 72 `COMPLETE` cases are paired via strict 1-to-1 batch matching with valid physical evidence captured at or before `audit_at`.
   - **Ambiguity & Decoy Protection:** 62 multi-request batches covering 102 cases have unequal request vs event counts; 76 events in `system_activity.csv` are orphans. Under strict safety rules, these ambiguous and orphan records are withheld to prevent decoy mispairing.
2. **Multi-Line Log Trace Correlation:**
   - In asynchronous logging frameworks, query initiation lines record search terms while completion lines record outcomes (`result="hit"`, `rows="1"`, `enabled="true"`) without repeating user identifiers.
   - Correlating all log lines by `trace_id` across all services revealed 4 cases (`case_416`, `case_417`, `case_420`, `case_517`) where leftovers persisted, properly transitioning them to `INCOMPLETE`.

---

## 6. Verification Against Ground Truth

The architecture has been verified against all 32 sample cases in `dataset/sample_output.csv`:
- Correct identification of `COMPLETE` (10 cases) vs `INCOMPLETE` (22 cases).
- Accurate detection of historical correlation keys (`case_12`).
- Symmetric remediation and verification plan generation for all affected resources.
- Correct handling of account tombstones (`case_31`, `case_32`) and replication drift (`case_05`).
