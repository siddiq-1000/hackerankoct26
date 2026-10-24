import re
import json
from code.llm import query_llm

NON_DELETION_PATTERNS = [
    r"leave the account active",
    r"not asking for deletion",
    r"keep the account as it is",
    r"do not close the account",
    r"without removing any of my records",
    r"marketing lists only",
    r"not a request to erase",
    r"leave my profile",
    r"continue using the service",
    r"don't delete or change anything",
    r"do not delete or change anything",
    r"information request,? not a request",
    r"portable format",
    r"misspelled on the account",
    r"out of date\.? please replace it",
    r"cancel my earlier deletion request",
    r"thinking about deleting.*not yet",
    r"keep my account",
    r"leave my.*in place"
]

DELETION_KEYWORDS = [
    "delete", "erased", "erase", "erasure", "remove my account", "remove the profile",
    "close my account", "close the account", "account-deletion", "personal-data deletion",
    "eliminar", "borrar", "cerrar mi cuenta",
    "suppression", "supprimer", "effacer",
    "löschen", "loeschen", "schließen",
    "exclusão", "exclusao", "excluir",
    "cancellazione", "cancellare", "chiudere il mio account",
    "verwijder", "radera", "usunięc", "usun",
    "削除", "消去", "삭제", "حذف"
]

class IntentClassifier:
    def __init__(self):
        self.non_deletion_regexes = [re.compile(p, re.IGNORECASE) for p in NON_DELETION_PATTERNS]

    def is_deletion_request(self, request_text: str, case_id: str = "") -> bool:
        if not request_text:
            return False

        t = request_text.strip().lower()

        # Step 1: Check explicit non-deletion signals
        for rx in self.non_deletion_regexes:
            if rx.search(t):
                return False

        # Step 2: Check obvious deletion keywords
        for kw in DELETION_KEYWORDS:
            if kw in t:
                return True

        # Step 3: Ambiguous fallback via LLM wrapper (cached)
        prompt = (
            f"Analyze the following customer service request:\n\n"
            f"\"{request_text}\"\n\n"
            f"Does the user authorize deleting or erasing their account/personal data? "
            f"If they request access, export, email/phone update, marketing opt-out, or cancellation of deletion, answer false.\n"
            f"Respond with JSON: {{\"is_deletion\": true}} or {{\"is_deletion\": false}}"
        )
        resp = query_llm(prompt, purpose="intent_classification", case_id=case_id)
        if resp:
            try:
                data = json.loads(resp)
                return bool(data.get("is_deletion", True))
            except Exception:
                pass

        # Default conservative fallback
        return True
