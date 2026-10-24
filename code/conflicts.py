"""
Conflict Resolution Engine for Deletion Audit Policy Rules.

This module resolves conflicting policy directives when multiple rules apply
to the same data category or resource.

Invariants & Precedence Rules:
1. RETENTION WINS OVER DELETION: Legal, regulatory, or security retention requirements
   strictly override any deletion directive.
2. REDACTION/ANONYMIZATION WINS OVER UNRESTRICTED RETENTION: If data may be kept
   but contains direct PII, the redaction or anonymization requirement takes precedence.
3. DISABLE FLOW WINS OVER ACTIVE FLOW: Any directive to disable a synchronization,
   export, or streaming data flow overrides any permission to keep it running.
4. BLOCK RESTORE WINS OVER UNRESTRICTED BACKUP: A restore path identified as a
   recreation risk must be blocked regardless of general backup retention policies.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PolicyRule:
    rule_id: str
    category: str
    condition: str
    action: str  # DELETE, RETAIN, REDACT, ANONYMIZE, DISABLE, BLOCK
    priority: int = 0

class ConflictResolver:
    """
    Evaluates competing policy actions on a resource and resolves conflicts deterministically.
    """

    # Explicit action precedence weights: higher number wins in direct conflicts
    # Retention / Safety holds take ultimate priority
    ACTION_PRECEDENCE = {
        "RETAIN": 100,        # Highest priority: Legal / Security holds cannot be overridden by deletion
        "BLOCK": 90,          # Restore risks must be blocked
        "DISABLE": 80,        # Active recreation data flows must be disabled
        "ANONYMIZE": 70,      # Irreversible unlinking
        "REDACT": 60,         # Direct PII stripping
        "DELETE": 50,         # Complete removal
        "KEEP": 10            # Unrestricted keep / default
    }

    @classmethod
    def resolve_conflicting_actions(cls, actions: List[str]) -> str:
        """
        Given a list of competing policy actions for the same record/resource,
        returns the winning action according to the precedence hierarchy.
        """
        if not actions:
            return "DELETE"
        
        # Filter and clean
        cleaned = [a.strip().upper() for a in actions if a.strip()]
        if not cleaned:
            return "DELETE"

        # Special Case: Retention strictly overrides deletion
        if "RETAIN" in cleaned and "DELETE" in cleaned:
            return "RETAIN"

        # General case: highest weight in ACTION_PRECEDENCE wins
        sorted_actions = sorted(cleaned, key=lambda a: cls.ACTION_PRECEDENCE.get(a, 0), reverse=True)
        return sorted_actions[0]

    @classmethod
    def resolve_rule_conflict(cls, rules: List[PolicyRule]) -> PolicyRule:
        """
        Selects the authoritative PolicyRule when multiple rules match a resource.
        """
        if not rules:
            raise ValueError("Cannot resolve empty rules list")
        if len(rules) == 1:
            return rules[0]

        actions = [r.action for r in rules]
        winning_action = cls.resolve_conflicting_actions(actions)
        for r in rules:
            if r.action.strip().upper() == winning_action:
                return r

        return rules[0]
