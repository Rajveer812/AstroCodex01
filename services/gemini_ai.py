"""Gemini AI integration utilities.

Reads API key from environment variable GEMINI_API_KEY. Provides a helper to
summarize weather conditions. Uses a lightweight caching layer to avoid
repeated identical summaries within a session.
"""
from __future__ import annotations
import os
import streamlit as st
from functools import lru_cache
from typing import Dict, Optional, Tuple, List
import traceback

try:
    import google.generativeai as genai  # type: ignore
    _HAS_LIB = True
except Exception:  # pragma: no cover
    _HAS_LIB = False

# Model selection: try user override via env GEMINI_MODEL first, then fallback list.
_MODEL_CANDIDATES = [
    os.getenv("GEMINI_MODEL"),  # optional explicit override
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro",
    "gemini-pro",              # older naming
    "gemini-1.0-pro",          # legacy fallback
]
_MODEL_CANDIDATES = [m for m in _MODEL_CANDIDATES if m]  # remove Nones
_SELECTED_MODEL: Optional[str] = None
_MODEL_OVERRIDE: Optional[str] = None  # explicit user-chosen model


def get_model_candidates() -> List[str]:  # public
    return list(_MODEL_CANDIDATES)


def set_model_override(model: Optional[str]) -> None:  # public
    global _MODEL_OVERRIDE, _SELECTED_MODEL
    _MODEL_OVERRIDE = model if model else None
    # Clear previously selected to force re-probe in priority order
    _SELECTED_MODEL = None


def get_selected_model() -> Optional[str]:  # public
    return _SELECTED_MODEL or _MODEL_OVERRIDE

@lru_cache(maxsize=1)
def _configure() -> bool:
    if not _HAS_LIB:
        return False
    # Priority: secrets -> env var
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        api_key = None
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False


def _try_generate(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """Internal helper to generate content and capture detailed error.

    Returns (text, error). If error is not None, text may be None.
    """
    if not _configure():
        return None, "Not configured"
    global _SELECTED_MODEL
    last_error: Optional[str] = None
    # If we already have a working model, try it first
    candidates = []
    if _MODEL_OVERRIDE:
        candidates.append(_MODEL_OVERRIDE)
    if _SELECTED_MODEL and _SELECTED_MODEL not in candidates:
        candidates.append(_SELECTED_MODEL)
    candidates += [m for m in _MODEL_CANDIDATES if m and m != _SELECTED_MODEL]
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt)
            text = (resp.text or "").strip()
            _SELECTED_MODEL = model_name  # cache working model
            return text, None
        except Exception as e:  # pragma: no cover
            last_error = f"{model_name}: {e.__class__.__name__}: {e}"
            # Opportunistic debug logging if app prepared session storage
            try:  # avoid hard dependency
                if hasattr(st, 'session_state'):
                    logs = st.session_state.get('ai_logs', [])
                    logs.append(last_error[:400])
                    st.session_state['ai_logs'] = logs[-50:]  # keep last 50
            except Exception:
                pass
            continue
    return None, last_error or "Unknown error"


def check_gemini_health() -> dict:
    """Lightweight health probe to help UI show why Gemini may be unavailable.

    Returns a dict with keys: configured (bool), library (bool), ok (bool), error (str|None)
    """
    lib_ok = _HAS_LIB
    configured = _configure()
    if not lib_ok:
        return {"library": False, "configured": False, "ok": False, "error": "google-generativeai not installed"}
    if not configured:
        return {"library": True, "configured": False, "ok": False, "error": "API key missing/invalid"}
    # Minimal probe: short test prompt (won't burn many tokens)
    text, err = _try_generate("Return the word OK")
    if err:
        return {"library": True, "configured": True, "ok": False, "error": err[:300]}
    return {"library": True, "configured": True, "ok": True, "error": None}

def is_gemini_configured() -> bool:
    """Public helper to let UI display an active/inactive badge."""
    return _configure()

def summarize_weather(weather: Dict[str, float]) -> str:
    """Return a concise natural-language summary of the provided weather dict.

    Expected keys (if present): temp / T2M, wind / WS2M, humidity / RH2M, rain.
    Silently ignores missing keys. Returns explanatory message if unavailable.
    """
    if not _configure():
        return "Gemini not configured (add GEMINI_API_KEY to secrets or env)."
    # Normalize keys
    temp = weather.get("temp") or weather.get("T2M")
    wind = weather.get("wind") or weather.get("WS2M")
    humidity = weather.get("humidity") or weather.get("RH2M")
    rain = weather.get("rain") or weather.get("total_rain")

    parts = []
    if temp is not None:
        parts.append(f"temperature {temp:.1f}°C")
    if humidity is not None:
        parts.append(f"humidity {humidity:.0f}%")
    if wind is not None:
        parts.append(f"wind {wind:.1f} m/s")
    if rain is not None:
        if rain > 0:
            parts.append(f"rain total ~{rain:.1f} mm expected")
        else:
            parts.append("no rain expected")
    if not parts:
        return "Insufficient weather data for summary."

    prompt = (
        "Write a friendly 2 sentence summary highlighting "
        + ", ".join(parts)
        + ". Keep it concise and helpful for planning an outdoor event."
    )
    text, err = _try_generate(prompt)
    if err:
        return f"Gemini summary unavailable ({err})."
    return text or "No summary generated"


def answer_weather_question(question: str, context: str = "") -> str:
    """Free-form weather Q&A using Gemini if configured.

    :param question: Raw user question.
    :param context: Optional injected factual context (already retrieved weather facts).
    """
    if not _configure():
        return ("(AI disabled) Configure GEMINI_API_KEY in .streamlit/secrets.toml or env.")
    base = (
        "You are a concise helpful weather assistant. Use only the factual data provided in context if present. "
        "If user asks for a forecast beyond available range (5 days) politely explain the limit."
    )
    prompt = f"{base}\nContext:\n{context}\n\nUser question: {question}\nAnswer:"
    text, err = _try_generate(prompt)
    if err:
        return f"Gemini answer unavailable ({err})."
    return text or "No answer generated"
