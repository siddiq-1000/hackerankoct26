import hashlib
import json
import os
import urllib.request
import urllib.error
from typing import Optional, Dict
from code.config import CACHE_DIR, LLM_MODEL, LLM_PROVIDER, GEMINI_API_KEY
from code.usage import UsageLedger

CACHE_FILE = CACHE_DIR / "llm_cache.json"

def _load_cache() -> Dict[str, dict]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_cache(cache: Dict[str, dict]):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

_warned_no_key = False

def query_llm(
    prompt: str,
    purpose: str = "general",
    case_id: Optional[str] = None,
    system_instruction: str = ""
) -> str:
    global _warned_no_key
    ledger = UsageLedger.get_instance()
    cache = _load_cache()

    cache_key = hashlib.sha256(f"{system_instruction}\n---\n{prompt}".encode("utf-8")).hexdigest()

    if cache_key in cache:
        entry = cache[cache_key]
        ledger.record_call(
            purpose=purpose,
            case_id=case_id,
            model=entry.get("model", LLM_MODEL),
            provider=entry.get("provider", LLM_PROVIDER),
            input_tokens=entry.get("input_tokens", 0),
            output_tokens=entry.get("output_tokens", 0),
            cached=True
        )
        return entry.get("response", "")

    # Not in cache: check for API key
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        if not _warned_no_key:
            print("[INFO] GEMINI_API_KEY not configured. Operating offline with local deterministic heuristics.")
            _warned_no_key = True
        return ""

    # Call Gemini REST API natively with urllib (no third-party lib required)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    contents = []
    if system_instruction:
        contents.append({"role": "user", "parts": [{"text": f"System context:\n{system_instruction}\n\nTask:\n{prompt}"}]})
    else:
        contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        candidate = data.get("candidates", [{}])[0]
        text_content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", len(prompt) // 4)
        output_tokens = usage.get("candidatesTokenCount", len(text_content) // 4)

        cache[cache_key] = {
            "prompt_hash": cache_key,
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL,
            "purpose": purpose,
            "response": text_content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
        _save_cache(cache)

        ledger.record_call(
            purpose=purpose,
            case_id=case_id,
            model=LLM_MODEL,
            provider=LLM_PROVIDER,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=False
        )
        return text_content
    except Exception as e:
        print(f"[WARNING] LLM API call failed ({e}). Proceeding with rule-based fallback.")
        return ""
