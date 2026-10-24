import hashlib
from dataclasses import dataclass, field
from typing import Set, List, Dict, Optional
from code.loaders import UserIdentity, UserAuditEntry

def compute_sha256(val: str) -> str:
    if not val:
        return ""
    clean = val.strip().lower()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()

@dataclass
class IdentitySet:
    user_id: str
    primary_name: str
    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    email_hashes: Set[str] = field(default_factory=set)
    audit_ids: Set[str] = field(default_factory=set)

    def all_search_terms(self) -> List[str]:
        terms = set()
        if self.user_id:
            terms.add(self.user_id)
        if self.primary_name:
            terms.add(self.primary_name)
        for e in self.emails:
            if e:
                terms.add(e)
                # plus address variant
                if "+" in e:
                    base = e.split("+")[0] + "@" + e.split("@")[1]
                    terms.add(base)
        for p in self.phones:
            if p:
                terms.add(p)
                # stripped phone
                digits = "".join(filter(str.isdigit, p))
                if len(digits) >= 8:
                    terms.add(digits)
        for h in self.email_hashes:
            if h:
                terms.add(h)
        return sorted(list(terms))

class IdentityResolver:
    def __init__(self, identities: Dict[str, UserIdentity], audit_logs: List[UserAuditEntry]):
        self.identities = identities
        self.audit_logs = audit_logs

        # Build email to user_id maps
        self.current_email_to_uid: Dict[str, str] = {}
        for uid, ident in identities.items():
            self.current_email_to_uid[ident.email.strip().lower()] = uid

        # Build historical map by tracing backward from verified identities
        self.user_to_historical_emails: Dict[str, Set[str]] = {uid: set() for uid in identities}
        for uid, ident in identities.items():
            curr = ident.email.strip().lower()
            user_audits = [a for a in audit_logs if a.user_id == uid and a.field_name == "email"]
            user_audits.sort(key=lambda a: a.event_time, reverse=True)
            chain = {curr}
            for entry in user_audits:
                chain.add(entry.old_value.strip().lower())
                chain.add(entry.new_value.strip().lower())
            self.user_to_historical_emails[uid] = chain

        self.historical_email_to_uid: Dict[str, str] = {}
        for uid, emails in self.user_to_historical_emails.items():
            for e in emails:
                if e not in self.current_email_to_uid:
                    self.historical_email_to_uid[e] = uid

    def resolve(self, request_email: str) -> Optional[IdentitySet]:
        req_norm = request_email.strip().lower()
        user_id = self.current_email_to_uid.get(req_norm)

        if not user_id:
            user_id = self.historical_email_to_uid.get(req_norm)

        # Handle plus-addressing fallback: e.g. name+tag@domain -> name@domain
        if not user_id and "+" in req_norm:
            base_email = req_norm.split("+")[0] + "@" + req_norm.split("@")[1]
            user_id = self.current_email_to_uid.get(base_email) or self.historical_email_to_uid.get(base_email)

        if not user_id:
            return None

        # Build identity set
        ident = self.identities.get(user_id)
        name = ident.name if ident else ""
        
        emails = {req_norm}
        phones = set()
        hashes = {compute_sha256(req_norm)}
        audit_ids = set()

        if ident:
            if ident.email:
                e_clean = ident.email.strip().lower()
                emails.add(e_clean)
                hashes.add(compute_sha256(e_clean))
            if ident.phone:
                phones.add(ident.phone.strip())
            if ident.email_hash:
                hashes.add(ident.email_hash.strip().lower())

        # Collect from audit logs for this specific user_id
        for entry in self.audit_logs:
            if entry.user_id == user_id:
                audit_ids.add(entry.audit_id)
                if entry.field_name == "email":
                    if entry.old_value:
                        old_e = entry.old_value.strip().lower()
                        emails.add(old_e)
                        hashes.add(compute_sha256(old_e))
                    if entry.new_value:
                        new_e = entry.new_value.strip().lower()
                        emails.add(new_e)
                        hashes.add(compute_sha256(new_e))
                elif entry.field_name == "phone":
                    if entry.old_value:
                        phones.add(entry.old_value.strip())
                    if entry.new_value:
                        phones.add(entry.new_value.strip())
                elif entry.field_name == "email_hash":
                    if entry.old_value:
                        hashes.add(entry.old_value.strip().lower())
                    if entry.new_value:
                        hashes.add(entry.new_value.strip().lower())

        return IdentitySet(
            user_id=user_id,
            primary_name=name,
            emails=emails,
            phones=phones,
            email_hashes=hashes,
            audit_ids=audit_ids
        )
