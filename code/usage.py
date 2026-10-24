import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
from code.config import CACHE_DIR, INPUT_PRICE_PER_M, OUTPUT_PRICE_PER_M

@dataclass
class CallRecord:
    purpose: str
    case_id: Optional[str]
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cached: bool

class UsageLedger:
    _instance = None

    def __init__(self, ledger_file: Optional[Path] = None):
        self.ledger_file = ledger_file or (CACHE_DIR / "usage_ledger.json")
        self.records: List[CallRecord] = []
        self._load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UsageLedger()
        return cls._instance

    def _load(self):
        if self.ledger_file.exists():
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = [CallRecord(**r) for r in data]
            except Exception:
                self.records = []

    def record_call(self, purpose: str, case_id: Optional[str], model: str, provider: str, input_tokens: int, output_tokens: int, cached: bool):
        rec = CallRecord(
            purpose=purpose,
            case_id=case_id,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=cached
        )
        self.records.append(rec)
        self._save()

    def _save(self):
        try:
            with open(self.ledger_file, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self.records], f, indent=2)
        except Exception:
            pass

    def get_summary(self, total_cases: int = 518) -> Dict:
        total_calls = len(self.records)
        cached_calls = sum(1 for r in self.records if r.cached)
        live_calls = total_calls - cached_calls
        total_input_tokens = sum(r.input_tokens for r in self.records)
        total_output_tokens = sum(r.output_tokens for r in self.records)
        total_tokens = total_input_tokens + total_output_tokens

        # Cost calculation
        cost_input = (total_input_tokens / 1_000_000) * INPUT_PRICE_PER_M
        cost_output = (total_output_tokens / 1_000_000) * OUTPUT_PRICE_PER_M
        total_cost = cost_input + cost_output

        by_purpose = {}
        for r in self.records:
            by_purpose[r.purpose] = by_purpose.get(r.purpose, 0) + 1

        by_model = {}
        for r in self.records:
            key = f"{r.provider}:{r.model}"
            if key not in by_model:
                by_model[key] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0
                }
            by_model[key]["calls"] += 1
            by_model[key]["input_tokens"] += r.input_tokens
            by_model[key]["output_tokens"] += r.output_tokens
            m_cost = ((r.input_tokens / 1_000_000) * INPUT_PRICE_PER_M) + ((r.output_tokens / 1_000_000) * OUTPUT_PRICE_PER_M)
            by_model[key]["cost"] += m_cost

        return {
            "total_cases": total_cases,
            "total_calls": total_calls,
            "live_calls": live_calls,
            "cached_calls": cached_calls,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "avg_tokens_per_case": round(total_tokens / total_cases, 2) if total_cases else 0.0,
            "total_cost": round(total_cost, 6),
            "avg_cost_per_case": round(total_cost / total_cases, 6) if total_cases else 0.0,
            "by_purpose": by_purpose,
            "by_model": by_model
        }

global_usage_ledger = UsageLedger.get_instance()
