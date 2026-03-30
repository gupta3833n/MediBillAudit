"""
Configuration for MediBill Audit
API keys are loaded from Streamlit secrets, environment variables, or a .env file.
"""

import os
from pathlib import Path

# Load .env file if it exists (local development)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try loading from CWD
except ImportError:
    pass  # python-dotenv not installed; rely on system env vars


def _get_secret(key: str, default: str = "") -> str:
    """Load a secret: Streamlit secrets → env var → default."""
    # 1. Streamlit Cloud secrets (highest priority)
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass  # Not running inside Streamlit, or key not set
    # 2. Environment variable
    val = os.getenv(key, "")
    if val:
        return val
    # 3. Default
    return default


# ─── Gemini API ───────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = _get_secret("GEMINI_API_KEY")
GEMINI_MODEL: str = _get_secret("GEMINI_MODEL", "gemini-1.5-pro")

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
