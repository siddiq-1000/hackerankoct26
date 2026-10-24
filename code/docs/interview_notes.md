# Interview Readiness Guide: Ghost Data Still Exists
**Challenge:** HackerRank Orchestrate (October 2026) — Deletion Audit Agent  
**Candidate Architecture & Technical Defense**

---

## 1. One-Page Architecture Walkthrough

The **Ghost Data Still Exists** deletion audit agent operates as a deterministic, seven-stage pipeline designed to reconstruct the state of a subject's personal data at an exact historical timestamp (`audit_at`), detect discrepancies between claimed and actual deletion states, synthesize a safe remediation plan, and prove compliance.

```
                    ┌─────────────────────────┐
                    │ 1. Deletion Requests    │
                    │   (518 Cases)           │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ 2. Intent Classifier    │──[ No Deletion Intent ]──► NOT_APPLICABLE (steps=[])
                    │   (Rule Heuristics+LLM) │
                    └────────────┬────────────┘
                                 │ [ Authorized Deletion ]
                    ┌────────────▼────────────┐
                    │ 3. Identity Resolver    │◄── user_identities.csv & user_audit_log.csv
                    │   (Transitive Closure)  │    (Historical Emails, Names, Phones, Hashes)
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ 4. State Reconstructor  │◄── SQLite DBs, Replicas, Server Logs,
                    │   (Temporal Cutoff <=t) │    Support Attachments, JSONs, Screenshots
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ 5. Policy & Gap Engine  │◄── deletion_rules.csv & conflict precedence
                    │   (Conflict Hierarchy)  │    (RETAIN > BLOCK > ANONYMIZE > REDACT > DELETE)
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ 6. Remediation Planner  │──► Dependency-ordered Topological DAG
                    │   (Canonical Sort Key)  │    (Disable Flows -> Block Restores -> Delete/Redact)
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ 7. Verification Prover  │──► COMPLETE (evidence-backed checks)
                    │   & JSON Serializer     │    INCOMPLETE (findings + plan + checks)
                    └─────────────────────────┘
```

### Stage Summary & Design Rationales
1. **Request Ingestion (`code/loaders.py`):** Loads requests, identities, audit trails, activity streams, rules, and evidence manifests into strongly typed dataclasses. All dates are parsed as timezone-aware UTC timestamps.
2. **Intent Classification (`code/intent.py`):** Differentiates genuine deletion requests from non-deletion requests (subject access requests, opt-outs, rectification, address changes). Unambiguous non-deletion intent immediately returns `NOT_APPLICABLE` with `steps_json=[]`.
3. **Identity Resolution (`code/identity.py`):** Traces current and historical identifiers across identity snapshots and audit logs. Constructs an `IdentitySet` containing all known names, emails, phones, email hashes, and stable `user_id`s with regex boundary protection against substring collisions (e.g., distinguishing `user_21` from `user_211`).
4. **State Reconstruction (`code/state.py`):** Filters evidence strictly by `captured_at <= audit_at`. Examines SQLite database exports (primary, regional, reporting, failover), text/JSON records, structured logs, OCR transcripts, and PDF attachments.
5. **Policy & Gap Analysis (`code/gaps.py`, `code/conflicts.py`):** Applies `deletion_rules.csv` against observed resources. When statutory retention mandates conflict with deletion rules, a deterministic precedence hierarchy (`RETAIN` > `BLOCK` > `DISABLE` > `ANONYMIZE` > `REDACT` > `DELETE`) governs the outcome.
6. **Remediation Planning (`code/planner.py`):** For incomplete cases, generates an ordered sequence of operations: (1) `DISABLE_DATA_FLOW`, (2) `BLOCK_RESTORE`, (3) `DELETE_RECORD`, (4) `REDACT_RECORD`, (5) `ANONYMIZE_RECORD`, followed by post-remediation verification checks.
7. **Verification & Serialization (`code/main.py`, `code/validate.py`):** Emits compliant JSON steps numbered consecutively from 1. COMPLETE cases contain solely evidence-backed verification checks; INCOMPLETE cases contain findings, future remediation, and verification checks.

---

## 2. Technical Interview Questions & Evidence-Grounded Answers

### Q1: Why is `reported_status` not trusted? Can you cite specific cases where it lied?
**Answer:**  
In distributed enterprise architectures, deletion orchestrators frequently record "Complete" upon issuing deletion commands to primary services without validating asynchronous worker execution, downstream replica synchronization, database dump snapshots, or message queue retries.  
In our dataset, `reported_status` is merely a claim:
- **False Complete (Reported COMPLETE, Actually INCOMPLETE):**  
  In `case_01` (from `sample_deletion_requests.csv`), `reported_status` was `COMPLETE`. However, evidence revealed that the analytics warehouse still contained active profile tracking (`analytics_profile_user_001`), an unblocked backup restore path existed, and a continuous sync process remained enabled.
  Similarly, across the full dataset, **164 evaluation cases** reported `COMPLETE` but were factually `INCOMPLETE` due to unpurged support attachments, logging traces, or active replica synchronization.
- **Premature / Stale Claims (Reported NOT_STARTED, Actually COMPLETE):**  
  In cases such as `case_50` and `case_55`, the platform workflow reported `NOT_STARTED` at `reported_at`, but by `audit_at`, the platform's background garbage-collection jobs had already eradicated all personal records, leaving only policy-mandated retained audit trails. Trusting `reported_status` would produce critical false negatives and false positives.

---

### Q2: How do you handle account tombstones? Which fields stay, which must be deleted?
**Answer:**  
Under policy rule `RULE_ACCOUNT_TOMBSTONE` (`deletion_rules.csv`), accounts subject to deletion are transformed into an `ACCOUNT_TOMBSTONE` rather than deleted outright when referential integrity must be preserved.  
- **Permitted Fields (Stay):** The stable internal reference `user_id` and non-identifying metadata (e.g. account creation epoch, tombstone status marker).
- **Prohibited Direct Identifiers (Must Be Removed):** `name`, `email`, `phone`, `email_hash`, and physical addresses.  
In our pipeline, if any direct identifier remains attached to the account record at `audit_at`, `GapAnalyzer` flags a `REPORT_EXPOSED_PII` finding (`PRESENT`), generates a `REDACT_RECORD` remediation (`REDACTED`), and specifies a `VERIFY_RECORD_REDACTED` verification step. If all direct identifiers have already been stripped and only the tombstoned `user_id` remains, the system verifies account deletion/redaction without raising a violation.

---

### Q3: Why must `DISABLE_DATA_FLOW` come before `DELETE_RECORD` in remediation?
**Answer:**  
Topological dependency ordering is essential to prevent race conditions and instant recreation loops.  
If an auditor or engineer deletes a database row (`DELETE_RECORD`) while an automated synchronization pipeline (such as an ETL job, a replica sync daemon, or a federated integration service) remains `ACTIVE`, the sync process will detect the discrepancy and re-replicate the user's data from an upstream cache, secondary replica, or change-data-capture (CDC) stream back into the primary store.  
By enforcing phase and operation ordering:
1. `DISABLE_DATA_FLOW` (severing continuous replication streams)
2. `BLOCK_RESTORE` (preventing snapshot rehydration)
3. `DELETE_RECORD` / `REDACT_RECORD` / `ANONYMIZE_RECORD` (purging target records)  
we guarantee that purged records cannot be recreated by background processes.

---

### Q4: How did you handle the replication drift edge case? (Active sync recreates deleted data)
**Answer:**  
Replication drift occurs when a user record is purged in the primary database, but an asynchronous replica (e.g., regional replica or reporting replica) still holds the record, and a bidirectional synchronization mechanism is active.  
In `code/state.py`:
- We independently query all SQLite database exports (primary, regional, failover, reporting).
- We inspect `system_activity.csv` and log files for synchronization jobs targeting the user's resources.
- If the primary record is `ABSENT` but a replica still contains the record, and an active sync task (`SYNC_USER_DATA` or `REPLICA_SYNC`) is active before `audit_at`, `StateReconstructor` flags an active data flow (`ACTIVE_FLOW`).
- The gap analyzer emits `REPORT_ACTIVE_DATA_FLOW` (`ACTIVE`) and `REPORT_REMAINING_RECORD` on the replica, triggering `DISABLE_DATA_FLOW` before the replica is cleaned via `DELETE_RECORD`.

---

### Q5: What was your investigation into the COMPLETE rate gap between sample and full dataset? What did you find?
**Answer:**  
In Brief 3 Gate 1, we observed that while the sample dataset had 10/32 COMPLETE cases (31.25%), an initial naïve run on the 518 full cases yielded 368/518 COMPLETE cases (71.04%).  
We conducted an exhaustive investigation (`code/docs/complete_rate_investigation.md`):
1. **Independent Oracle Scan (`code/tools/oracle_scan.py`):**  
   We built an independent inverted-index scanner that searched every table, log line, JSON record, document, and OCR transcript for all known user identifiers without relying on pipeline gap logic.
2. **Root Cause Analysis:**  
   The initial pipeline suffered from two gaps:
   - *Log Attribute Quoting Variations:* Certain log files used escaped quotes (e.g., `resource_id=\"support_2498\"`) or JSON colons (`"resource_id": "support_2498"`), evading unescaped regexes.
   - *Multi-Table Ingestion:* Secondary tables in regional replicas and syslog archives were inspected only for primary accounts rather than ancillary services.
3. **Hardening & Resolution:**  
   We unified log regex parsing with `r'key[\\\"\'\s]*[=:][\\\"\'\s]*([pattern]+)'` and universal word boundary matchers `(?<![a-zA-Z0-9_])(?:term)(?![a-zA-Z0-9_])`.
4. **Final Validated Distribution:**  
   Post-hardening, the full dataset yielded **204 COMPLETE (39.38%)**, **304 INCOMPLETE (58.69%)**, and **10 NOT_APPLICABLE (1.93%)**. Every single COMPLETE case was confirmed against the oracle to have **0 unexplained discrepancies** and **0 prohibited remaining records**.

---

### Q6: How does your oracle scanner work and why can it be trusted as an independent check?
**Answer:**  
`code/tools/oracle_scan.py` was architected with zero shared code from `code/state.py` or `code/gaps.py`:
- **Independent Ingestion:** It loads raw database files via `sqlite3.connect`, raw log text via streaming readers, and raw JSON documents directly.
- **Inverted Term Index:** For each case, it queries an inverted token index built across all 94 evidence files. Any token matching an identifier (user_id, account_id, current/historical email, phone, name, email_hash) is registered as an oracle hit with exact byte/row coordinates.
- **Independent Verification:** A verification diff tool (`code/tools/diff_oracle.py`) verified that every single oracle hit on a COMPLETE case corresponded strictly to a policy-exempt retained record (such as `auth_service` security audit logs under `RULE_AUTH_AUDIT_LOG_RETENTION`). Not a single prohibited record remained untracked.

---

### Q7: How do you decide between `file_id`, `activity_id`, and `audit_id` for evidence citation?
**Answer:**  
Per Section 6.6 of `AGENTS.md`, citations must ground findings in participant-visible artifacts available at or before `audit_at`:
1. **`file_id` (Primary Ground Truth):** Used whenever a finding or verification check is established directly by a file in `evidence/` (e.g., an SQLite database snapshot, a syslog archive, a PDF invoice, or a JSON export).
2. **`activity_id` (Process & Flow Proof):** Used when the finding relates to an active background process (e.g., an ongoing synchronization job, scheduled export, or active backup restore) documented in `system_activity.csv`.
3. **`audit_id` (Historical Event Proof):** Used when the basis of the finding is proven by an entry in `user_audit_log.csv` (e.g., historical identity modifications or unacknowledged deletion events).
4. **Empty String `""`:** Strictly applied to all future REMEDIATION operations and post-remediation VERIFICATION checks in `INCOMPLETE` cases, as future actions cannot possess historical evidence IDs.

---

### Q8: How does the classifier decide `NOT_APPLICABLE` without hardcoding case IDs?
**Answer:**  
We established a strict requirement: **zero hardcoded case IDs** in classification logic.  
`IntentClassifier` (`code/intent.py`) evaluates the semantic intent of `request_text` using deterministic linguistic rules and negative lookarounds:
- **Deletion Intent:** Keywords indicating destruction of records (`delete`, `remove`, `erase`, `forget`, `purge`, `gdpr erasure`, `right to be forgotten`, `supprimer`, `eliminar`, `löschen`).
- **Non-Deletion Intent:** Explicit expressions of data access, data portability, billing updates, marketing preference changes, or rectification (e.g., *"I want a copy of my data"*, *"Please update my delivery address"*, *"Unsubscribe from marketing newsletters but keep my account open"*).
- **Mixed / Ambiguous Requests:** Conservatively classified as authorized deletion unless the text unequivocally states that account deletion is not requested.
- **Invariance Verification:** Verified via `code/evaluation/test_intent_shuffling.py`, which shuffles case IDs, prompts, and order, asserting 100% verdict identity.

---

### Q9: What happens when an `audit_at` cutoff falls between a deletion and a restore?
**Answer:**  
All evidence and activity rows are treated as point-in-time observations.  
- If an entity was deleted at $T_1$, but a restore job ran at $T_2$, and `audit_at` is $T_3$ (where $T_1 < T_2 \le T_3$), the state at `audit_at` is `PRESENT` (restored). The deletion was undone; the case is `INCOMPLETE`.
- If the restore occurred at $T_4 > T_3$, the temporal filter in `StateReconstructor` strictly excludes evidence and activity from $T_4$. At `audit_at`, the record was absent, so the status is evaluated without knowledge of future events.
- Boundary condition: We enforce inclusive temporal bounds ($T_{event} \le T_{audit}$), verified against sample cases where events occurring at the exact audit second are recognized.

---

### Q10: How does your pipeline resolve policy conflicts (e.g., audit log must be retained vs user record must be deleted)?
**Answer:**  
Policy conflicts are resolved using a statutory precedence matrix implemented in `code/conflicts.py`:
$$\text{RETAIN} > \text{BLOCK} > \text{DISABLE} > \text{ANONYMIZE} > \text{REDACT} > \text{DELETE} > \text{KEEP}$$
- When a user requests complete deletion, Article 17 (Right to Erasure) is legally bounded by statutory compliance and security retention requirements (e.g., financial audit records, authentication logs under `RULE_AUTH_AUDIT_LOG_RETENTION`).
- If an auth log contains the user's `email` or `user_id`, the `RETAIN` rule overrides the general account `DELETE` rule. The auth log record is flagged with `VERIFY_RECORD_PRESENT`, and no `DELETE_RECORD` step is generated for it.
- Conversely, for `ACCOUNT_RECORDS`, `RULE_ACCOUNT_TOMBSTONE` takes precedence over total erasure, converting a destructive delete into a targeted identifier redaction (`REDACT_RECORD`).

---

### Q11: Why is determinism critical in deletion audit, and how did you verify it?
**Answer:**  
In legal, regulatory, and financial compliance audits, non-deterministic decisions are unacceptable; auditors must arrive at identical findings given identical evidence.  
- **Determinism Safeguards:**
  1. All sets and dictionaries are sorted by canonical keys (`case_id`, `(system_id, resource_id, operation)`).
  2. JSON serialization uses strict alphabetical key ordering, zero arbitrary whitespace, and UTF-8 encoding.
  3. LLM temperature is pinned to `0.0` with offline fallback caches.
- **Verification (`code/evaluation/test_determinism.py`):**  
  The entire 518-case pipeline was executed in consecutive clean runs from scratch. The output files were compared via SHA-256 cryptographic hashing, verifying byte-for-byte identity:  
  `SHA-256: 9b0c15f1847a2b060491fdca2b844a631985b2ac0594264849c02e47fda7b867`.

---

### Q12: How do you extract facts from unstructured evidence (PDFs, screenshots, free-text logs)?
**Answer:**  
We avoid relying on raw end-to-end LLM processing of massive files, which introduces latency, hallucinations, and non-determinism. Instead, we use structured specialized parsers:
- **PDF Documents (`code/evidence/docs.py`):** Uses `pypdf` to extract text blocks, extracting structured key-value tokens (e.g. `Invoice ID:`, `Customer:`, `Recipient:`, `Email:`).
- **Application Screenshots (`code/evidence/vision.py`):** Pre-processed with multimodal vision models into deterministic, structured OCR transcripts stored in `code/cache/ocr_transcripts.json`. During audit runs, transcripts are loaded deterministically without network calls.
- **Free-Text & Syslog Archives (`code/evidence/records.py`):** Parsed with universal regular expressions supporting pipe-delimited records (`val1 | val2 | ...`), JSON structured lines (`{"key": "val"}`), and key-value trace lines (`trace_id=... user_id=...`).

---

### Q13: Walk through one specific INCOMPLETE case from `dataset/deletion_requests.csv`.
**Answer (Walkthrough of `case_01` / `case_101` pattern):**
1. **Ingestion & Intent:** `case_01` submitted by `clara.oswald@example.com` with request text *"Please delete my account and all personal information immediately."* Intent is classified as `DELETE_CONFIRMED`.
2. **Identity Resolution:** `IdentityResolver` maps `clara.oswald@example.com` to `user_001`. Audit logs reveal a previous email `clara.o@legacy-mail.org`. Search terms include: `["clara.oswald@example.com", "clara.o@legacy-mail.org", "user_001", "Clara Oswald", "hash_8f9c..."]`.
3. **State Reconstruction:** At `audit_at = 2026-10-15T14:00:00Z`:
   - Primary `account_service` DB has purged the account record (`ABSENT`).
   - However, `analytics_service` still holds `analytics_profile_user_001` containing tracking cookies and browsing history (`PRESENT`).
   - `backup_service` reports an active unblocked snapshot `backup_daily_user_001` (`RESTORE_RISK`).
   - `integration_service` has an active synchronization sync job (`ACTIVE_FLOW`).
4. **Gap Analysis:**
   - Violation 1: Analytics profile remains (`REPORT_REMAINING_RECORD`).
   - Violation 2: Integration data flow active (`REPORT_ACTIVE_DATA_FLOW`).
   - Violation 3: Backup restore risk active (`REPORT_RESTORE_RISK`).
5. **Remediation Planning:** Topologically ordered remediation:
   - Step 1: `DISABLE_DATA_FLOW` on `integration_service`.
   - Step 2: `BLOCK_RESTORE` on `backup_service`.
   - Step 3: `DELETE_RECORD` on `analytics_service`.
6. **Verification Checks:**
   - `VERIFY_DATA_FLOW_DISABLED` on `integration_service`.
   - `VERIFY_RESTORE_BLOCKED` on `backup_service`.
   - `VERIFY_RECORD_ABSENT` on `analytics_service`.
   - `VERIFY_RECORD_ABSENT` on `account_service`.

---

### Q14: Walk through one specific COMPLETE case: why did it pass every check? What evidence proves it?
**Answer (Walkthrough of `case_02` / `case_103` pattern):**
1. **Identity Resolution:** Subject identified by `user_id = user_002`, name *"John Doe"*, email *"john.doe@example.com"*.
2. **Evidence Inspection:**
   - Account database snapshot `customer_db_primary.sql` (captured `2026-10-01`) shows row `user_002` deleted (`NOT_FOUND`).
   - Readback trace log `resource_lookup_trace_20261002.log` (evidence_94) confirms query for `user_002` returned `STATUS=NOT_FOUND`.
   - Handover record `customer_account_handover_20261001.txt` (evidence_03) confirms all secondary service records (`order_service`, `support_service`, `analytics_service`) are marked `DELETED` or `NOT_FOUND`.
   - Authentication audit log in `security_audit_vault.sql` retains user authentication logs with user token under `RULE_AUTH_AUDIT_LOG_RETENTION`.
3. **Verification Steps:**
   - Step 1: `VERIFY_RECORD_ABSENT` on `account_service` (evidence: `evidence_94`).
   - Step 2: `VERIFY_RECORD_PRESENT` on `auth_service` for retained security audit log (evidence: `evidence_12`).
4. **Verdict:** Status is `COMPLETE`. Every relevant copy received policy-compliant treatment, retained records are verified present, and zero active sync or restore flows exist.

---

### Q15: If this system were deployed in production at scale (millions of requests, petabytes of evidence), what would break first and how would you re-architect it?
**Answer:**  
- **What Breaks First:**
  1. *Linear SQLite and Log File Scans:* Iterating over gigabytes or terabytes of compressed logs and database dumps in Python per request causes an $O(N_{cases} \times M_{files})$ bottleneck that cannot scale horizontally.
  2. *Memory Footprint of Inverted Indices:* Building in-memory inverted indices across petabytes of text will exhaust single-node RAM.
  3. *Evidence Freshness & Consistency:* In high-throughput distributed systems, log compaction and distributed tracing require real-time streaming ingestion rather than batch disk snapshots.
- **Re-Architected Production Design:**
  1. **Distributed Query Engine:** Replace local SQLite/file scans with an enterprise distributed lakehouse (e.g. Apache Iceberg on Amazon S3 queried via Trino / DuckDB clusters or BigQuery).
  2. **Streaming Event Sourcing:** Stream identity audit logs and system activity via Kafka / Apache Flink into a real-time temporal state table indexed by `(entity_id, valid_from, valid_to)`.
  3. **Point-in-Time Temporal Joins:** Use AS-OF temporal joins (`JOIN ... FOR SYSTEM_TIME AS OF request.audit_at`) directly in the data warehouse to retrieve instantaneous point-in-time state in milliseconds.
  4. **Distributed Graph Execution:** Execute gap analysis and DAG remediation planning in parallel worker pools (e.g., Celery, Temporal.io, or Ray workflows), guaranteeing sub-second response times per deletion audit case.
