from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = Path(os.environ.get("DATASET_DIR", REPO_ROOT / "dataset")).resolve()
EVIDENCE_DIR = DATASET_DIR / "evidence"
OUTPUT_CSV_PATH = Path(os.environ.get("OUTPUT_CSV_PATH", REPO_ROOT / "output.csv")).resolve()
CACHE_DIR = Path(os.environ.get("CACHE_DIR", REPO_ROOT / "code" / "cache")).resolve()
PROMPTS_DIR = REPO_ROOT / "code" / "prompts"

# LLM Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Price assumptions (gemini-2.5-flash standard pricing per million tokens)
INPUT_PRICE_PER_M = 0.075   # $0.075 / 1M input tokens
OUTPUT_PRICE_PER_M = 0.30   # $0.30 / 1M output tokens

# Analytics Linking Feature Switch (Brief 3D)
LINK_NULL_IDENTIFIER_ANALYTICS = os.environ.get("LINK_NULL_IDENTIFIER_ANALYTICS", "true").lower() in ["1", "true", "yes"]

CACHE_DIR.mkdir(parents=True, exist_ok=True)
