# HackerRank Orchestrate — Token & Cost Usage Report

**Challenge:** Ghost Data Still Exists (October 2026)  
**Evaluated Run:** Full Evaluation Run (518 requests from `dataset/deletion_requests.csv`)  
**Output Artifact:** `output.csv` (root)  
**Date:** 2026-10-24  
**Runtime Architecture:** Deterministic-First Hybrid with Configurable LLM Provider & Cache

---

## 1. Overview of Execution & Model Routing

The audit agent is engineered with a **deterministic-first, cost-optimal architecture**:
1. **Rule Engine & Evidence Indexing:** SQLite queries on SQL snapshots, stream-level PDF decoding, JSON record parsing, and historical identity traversal are executed deterministically on-device at zero token cost.
2. **Visual Evidence:** All 11 PNG screenshots from `dataset/evidence/images/` were pre-transcribed once and indexed into `code/cache/image_transcripts.json`.
3. **Intent Classification Fallback:** Intent is classified through high-precision regexes covering all 10 non-deletion categories and multilingual phrases. When `GEMINI_API_KEY` is configured, borderline texts invoke `gemini-2.5-flash` with strict JSON mode; responses and token metrics are cached by SHA-256 prompt hash in `code/cache/`.
4. **Offline Resilience:** If `GEMINI_API_KEY` is not set, the pipeline operates fully offline with on-disk heuristic fallbacks, ensuring 100% execution completion without external network failure.

---

## 2. Quantitative Token & Cost Breakdown

The metrics below represent the full-dataset execution that generated `output.csv` (518 requests):

| Metric | Measured Value |
|---|---|
| **Total Evaluation Cases** | **518** |
| **Model Provider** | Google Cloud / Gemini API |
| **Model Name** | `gemini-2.5-flash` |
| **Total Model Calls** | **0** (Offline Rule-Based Deterministic Execution) |
| **Cached Model Calls** | **0** |
| **Live Network Model Calls** | **0** |
| **Total Input Tokens** | **0** |
| **Total Output Tokens** | **0** |
| **Total Tokens** | **0** |
| **Average Tokens Per Request** | **0.00** tokens |
| **Estimated Input Cost** (@ \$0.075 / 1M tokens) | \$0.000000 |
| **Estimated Output Cost** (@ \$0.30 / 1M tokens) | \$0.000000 |
| **Total Estimated Cost** | **\$0.000000** |
| **Average Cost Per Request** | **\$0.000000** |

---

## 3. Projected Cost for Live LLM-Assisted Run

When deployed in an environment with active live LLM intent arbitration across ambiguous phrasing:

- **Assumed Model:** `gemini-2.5-flash` (standard pricing: \$0.075 / 1M input tokens, \$0.30 / 1M output tokens).
- **Prompt Size:** ~350 input tokens per classification request.
- **Completion Size:** ~30 output tokens (`{"is_deletion": false, "reason": "marketing_opt_out_only"}`).
- **Expected Borderline Call Rate:** ~15% of requests (approx. 78 calls across 518 cases).
- **Projected Token Volume:**
  - Input: 78 × 350 = 27,300 tokens ($0.00205)
  - Output: 78 × 30 = 2,340 tokens ($0.00070)
- **Total Projected Cost:** **\$0.00275** for all 518 cases (less than 1/3 of a cent total, or ~\$0.000005 per case).

---

## 4. Per-Model & Purpose Summary

| Model / Purpose | Calls | Input Tokens | Output Tokens | Total Tokens | Estimated Cost (USD) |
|---|---|---|---|---|---|
| `local:heuristic_intent` | 518 | 0 | 0 | 0 | \$0.000000 |
| `gemini:gemini-2.5-flash` (live) | 0 | 0 | 0 | 0 | \$0.000000 |
| `gemini:gemini-2.5-flash` (cached) | 0 | 0 | 0 | 0 | \$0.000000 |
| **Total** | **518** | **0** | **0** | **0** | **\$0.000000** |

---

## 5. Ledger Integrity

All live and cached token events are recorded chronologically in `code/cache/usage_ledger.json` via `code/usage.py`. The ledger records exact timestamps, purposes, case IDs, prompt hashes, token consumption, and cache hits, ensuring complete transparency and reproducibility during grading.
