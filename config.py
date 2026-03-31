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

# Preferred models in priority order (best first)
_FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro-vision",
]


def detect_gemini_model(api_key: str = "") -> tuple[str, str]:
    """
    Auto-detect the best available Gemini model.

    Returns (model_name, source) where source is one of:
        "override"  — user set GEMINI_MODEL explicitly
        "detected"  — discovered via list_models() API
        "fallback"  — using first model from fallback list (API listing failed)
    """
    # 1. Check for explicit user override
    override = _get_secret("GEMINI_MODEL")
    if override:
        return override, "override"

    # 2. Try listing available models from the API
    key = api_key or GEMINI_API_KEY
    if key and key not in ("", "your-api-key-here", "YOUR_API_KEY") and len(key) > 10:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            available = set()
            for m in genai.list_models():
                if "generateContent" in (m.supported_generation_methods or []):
                    # m.name is like "models/gemini-2.0-flash"
                    short = m.name.replace("models/", "")
                    available.add(short)
            # Pick the best available model from our preference list
            for preferred in _FALLBACK_MODELS:
                if preferred in available:
                    return preferred, "detected"
            # If none of our preferred models found, pick the first flash/pro model
            for name in sorted(available):
                if "gemini" in name:
                    return name, "detected"
        except Exception:
            pass

    # 3. Fallback — return first preferred model
    return _FALLBACK_MODELS[0], "fallback"


# Resolve model at import time (cached for the session)
GEMINI_MODEL, GEMINI_MODEL_SOURCE = detect_gemini_model()

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


def is_valid_api_key(key: str) -> bool:
    """Return True if an API key string looks valid (non-empty, not placeholder)."""
    return bool(
        key
        and key not in ("", "your-api-key-here", "YOUR_API_KEY")
        and len(key) > 10
    )


def is_api_configured(key: str = "") -> bool:
    """Return True if the given key (or the default GEMINI_API_KEY) looks valid."""
    return is_valid_api_key(key or GEMINI_API_KEY)
