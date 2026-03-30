"""
Configuration for MediBill Audit
API keys are loaded from environment variables or a .env file.
"""

import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try loading from CWD
except ImportError:
    pass  # python-dotenv not installed; rely on system env vars

# ─── Gemini API ───────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# ─── App settings ─────────────────────────────────────────────────────────────
APP_NAME = "MediBill Audit"
APP_VERSION = "1.0.0"
APP_TAGLINE = "AI-Powered Hospital Bill Checker for Patients"

# ─── Analysis thresholds ──────────────────────────────────────────────────────
# % above benchmark to flag as OVERCHARGED
DEFAULT_OVERCHARGE_THRESHOLD = 20
# % above benchmark to flag as MAJOR overcharge
MAJOR_OVERCHARGE_THRESHOLD = 50
# Minimum item amount (INR) to flag if unmatched
UNKNOWN_ITEM_FLAG_THRESHOLD = 500

# ─── Benchmarks file ──────────────────────────────────────────────────────────
BENCHMARKS_FILE = Path(__file__).parent / "benchmarks" / "rates.json"


def is_api_configured() -> bool:
    """Return True if the Gemini API key looks valid (non-empty, not placeholder)."""
    return bool(
        GEMINI_API_KEY
        and GEMINI_API_KEY not in ("", "your-api-key-here", "YOUR_API_KEY")
        and len(GEMINI_API_KEY) > 10
    )
