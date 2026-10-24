# Policy Conflict Resolution Architecture

## Overview

In an enterprise commerce deletion audit, policies originate from multiple jurisdictions (e.g. GDPR Right to Erasure, HIPAA, PCI-DSS, corporate audit rules, and legal preservation orders). Different policy rules frequently collide when evaluated against the same data resource or user profile.

The `code.conflicts.ConflictResolver` module implements a deterministic conflict resolution hierarchy based on established privacy law and safety engineering principles.

---

## Conflict Precedence Hierarchy

When multiple rules target the same resource, conflicts are resolved using the following order of precedence:

```
[Level 1: Highest]  RETAIN      (Legal holds, regulatory preservation, immutable security audit logs)
[Level 2]           BLOCK       (Prevent restore operations that recreate deleted subjects)
[Level 3]           DISABLE     (Stop active connectors, replicators, and data synchronization flows)
[Level 4]           ANONYMIZE   (Irreversible unlinking of analytics and behavioral telemetries)
[Level 5]           REDACT      (Direct PII stripping on tombstones and support messages)
[Level 6]           DELETE      (Complete removal of user profile, index records, and exports)
[Level 7: Lowest]   KEEP        (Default inactive state without special treatment)
```

---

## Core Precedence Invariants

### 1. Retention Overrides Deletion (`RETAIN` > `DELETE`)
- **Principle:** Statutory compliance and legal holds supersede general erasure requests.
- **Application:** Rule 12 (`SECURITY_AUDIT_LOG`) and legal discovery attachments (`LEGAL_HOLD_RECORD`) must be retained even if the subject requests complete account eradication. If a deletion rule and a retention rule match the same log row, `RETAIN` strictly wins, resulting in a `VERIFY_RECORD_PRESENT` step rather than `DELETE_RECORD`.

### 2. Redaction / Anonymization Overrides Unrestricted Keep (`REDACT` / `ANONYMIZE` > `KEEP`)
- **Principle:** When a record category is permitted to remain in the system, direct personal identifiers must not remain exposed.
- **Application:** Account tombstones (`ACCOUNT_TOMBSTONE`, rule_15) preserve internal referential integrity (e.g. stable `user_id`), but direct identifiers (name, email, phone, email hash) must be redacted. Similarly, analytics profiles (`ANALYTICS_PROFILE`, rule_07) can be kept only after irreversible anonymization.

### 3. Disable Data Flow Overrides Active Keep (`DISABLE` > `KEEP`)
- **Principle:** Active processes that synchronize or export data must be halted to prevent continuous downstream propagation or recreation.
- **Application:** Integration connectors (`ACTIVE_DATA_FLOW`, AGENTS.md §6.4) must be disabled before changing dependent records.

### 4. Block Restore Overrides Unrestricted Backup (`BLOCK` > `KEEP`)
- **Principle:** Disaster recovery paths must not restore subjects whose data was legally deleted.
- **Application:** Backups (`BACKUP_ARCHIVE`, rule_14) must have restore paths blocked before the deletion is considered complete.

---

## Unit Testing & Verification

The synthetic rule suite in `code/evaluation/test_policy.py` validates all four conflict categories under adversarial edge-case conditions.
