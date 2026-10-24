from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = REPO_ROOT / "dataset"
EVIDENCE_DIR = DATASET_DIR / "evidence"
OUTPUT_CSV_PATH = REPO_ROOT / "output.csv"
CACHE_DIR = REPO_ROOT / "code" / "cache"
PROMPTS_DIR = REPO_ROOT / "code" / "prompts"

# LLM Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Price assumptions (gemini-2.5-flash standard pricing per million tokens)
INPUT_PRICE_PER_M = 0.075   # $0.075 / 1M input tokens
OUTPUT_PRICE_PER_M = 0.30   # $0.30 / 1M output tokens

CACHE_DIR.mkdir(parents=True, exist_ok=True)
