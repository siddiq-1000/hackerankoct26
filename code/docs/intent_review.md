# Intent Classification Review & Borderline Analysis

This document reviews the intent classification criteria, provides full analysis of the 10 identified `NOT_APPLICABLE` evaluation cases, and audits borderline phrases across all 518 evaluation requests in `dataset/deletion_requests.csv`.

---

## 1. Intent Criteria & Ground Rules

Under the challenge specification (§6.5):
> *"First determine whether `request_text` authorizes deletion. A request for access, correction, export, marketing opt-out, or another non-deletion action is NOT_APPLICABLE, even if other fields resemble a deletion case."*

For any request classified as `NOT_APPLICABLE`:
- `deletion_status` must be `NOT_APPLICABLE`.
- `steps_json` must be `[]` (exact empty JSON array).

---

## 2. Exhaustive Audit of the 10 `NOT_APPLICABLE` Cases

All 10 cases explicitly state non-deletion intent or request actions other than account/personal data erasure:

| Case ID | Verbatim `request_text` | Request Category | Explicit Non-Deletion Signal | Classification Verdict |
|---|---|---|---|---|
| `case_533` | *"The mobile number on my profile is out of date. Please replace it with the new one and leave the account active."* | Profile Correction | *"leave the account active"* | `NOT_APPLICABLE` |
| `case_534` | *"Please stop the promotional emails. I still need the account and my order history, so I am not asking for deletion."* | Marketing Opt-Out | *"not asking for deletion"*, *"still need the account"* | `NOT_APPLICABLE` |
| `case_535` | *"I'd like to download my account information in a portable format. Please keep the account as it is."* | Data Portability / Export | *"keep the account as it is"*, *"download... in a portable format"* | `NOT_APPLICABLE` |
| `case_536` | *"I can't access my profile and need help resetting the login. Do not close the account."* | Access / Password Recovery | *"Do not close the account"* | `NOT_APPLICABLE` |
| `case_537` | *"My surname is misspelled on the account. Can you correct it without removing any of my records?"* | Data Rectification | *"without removing any of my records"* | `NOT_APPLICABLE` |
| `case_538` | *"Please remove me from marketing lists only. I still want receipts and service messages for this account."* | Marketing Opt-Out Only | *"marketing lists only"*, *"still want receipts and service messages"* | `NOT_APPLICABLE` |
| `case_539` | *"Can you tell me what personal information you hold about me? This is an information request, not a request to erase it."* | Subject Access Request (SAR) | *"information request, not a request to erase it"* | `NOT_APPLICABLE` |
| `case_540` | *"I need a copy of last year's invoices for my records. Please leave my profile and purchase history in place."* | Invoice / Record Copy | *"leave my profile and purchase history in place"* | `NOT_APPLICABLE` |
| `case_541` | *"Please change the email address used for this account. I want to continue using the service."* | Profile Update | *"want to continue using the service"* | `NOT_APPLICABLE` |
| `case_542` | *"Could you send me a copy of the information held on my account? I still use it, so please don't delete or change anything."* | Subject Access Request | *"please don't delete or change anything"*, *"I still use it"* | `NOT_APPLICABLE` |

---

## 3. Audit of Borderline Phrasing in Legitimate Deletion Requests

We performed exhaustive lexical scanning across all remaining 508 cases for words that could potentially confuse a naive keyword matcher:

1. **The word "correct":**
   - In 20+ cases (e.g. `case_53`, `case_63`, `case_73`, `case_90`, `case_103`), users state:
     *"Please erase the account linked to this email address. Please apply the correct treatment to records covered by the request."*
   - Analysis: The word *"correct"* here refers to applying the correct deletion/retention treatment per policy, **not** a request to correct personal data. Because the primary verb is *"erase"* or *"permanently delete"*, these are legitimate deletion requests (`COMPLETE` or `INCOMPLETE`), never `NOT_APPLICABLE`.

2. **Multilingual Requests:**
   - Languages present: Spanish (*"eliminar mi cuenta"*), French (*"demande la suppression définitive"*), Portuguese (*"Solicito a exclusão permanente"*), German (*"löschen"*), Italian (*"cancellazione"*), Japanese (*"アカウントの削除"*), Korean (*"계정 삭제"*), Arabic (*"حذف الحساب"*).
   - Analysis: All multilingual cases in the dataset (56 instances) unambiguously request account erasure. None request access or correction.

---

## 4. Verification of Case-ID Independence

To ensure the classifier makes decisions strictly from `request_text` without overfitting to case IDs:
- The classifier `intent.py` takes only `request_text: str`.
- An automated test shuffles the evaluation rows randomly and verifies identical output classifications across 100% of cases.
