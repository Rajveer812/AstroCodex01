"""OpenAI (ChatGPT) integration utilities.

Provides provider-parallel functions mirroring gemini_ai: summarize_weather and answer_weather_question.
Reads OPENAI_API_KEY from st.secrets then environment. Safe fallbacks if not configured.
"""
from __future__ import annotations
import os
from typing import Dict, Optional, Tuple, List

import streamlit as st

try:  # Lazy import guard
    from openai import OpenAI  # type: ignore
    _HAS_OPENAI = True
except Exception:  # pragma: no cover
    _HAS_OPENAI = False

_MODEL_CANDIDATES: List[str] = [
    os.getenv("OPENAI_MODEL"),  # explicit override if provided
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4o-2024-08-06",
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-3.5-turbo"  # legacy fallback
]
_MODEL_CANDIDATES = [m for m in _MODEL_CANDIDATES if m]
_SELECTED_MODEL: Optional[str] = None

_OPENAI_CLIENT: Optional[OpenAI] = None  # cached instance
_OPENAI_KEY_FINGERPRINT: Optional[str] = None
_OPENAI_LAST_ERROR: Optional[str] = None

def _load_api_key() -> Optional[str]:
    key = None
    # secrets first
    if st is not None:
        try:
            key = st.secrets.get("OPENAI_API_KEY")  # type: ignore[attr-defined]
        except Exception:
            key = None
    if not key:
        key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    key = key.strip()
    if not key:
        return None
    if key.startswith("REPLACE_") or key.startswith("YOUR_") or "REPLACE_WITH" in key:
        return None
    return key


def _configure(refresh: bool = False) -> Optional[OpenAI]:
    global _OPENAI_CLIENT, _OPENAI_KEY_FINGERPRINT, _OPENAI_LAST_ERROR
    if not _HAS_OPENAI:
        _OPENAI_LAST_ERROR = "openai library not installed"
        return None
    key = _load_api_key()
    if not key:
        _OPENAI_LAST_ERROR = "missing_key"
        _OPENAI_CLIENT = None
        return None
    fp = f"{key[:7]}:{len(key)}"
    if refresh or _OPENAI_CLIENT is None or _OPENAI_KEY_FINGERPRINT != fp:
        try:
            _OPENAI_CLIENT = OpenAI(api_key=key)
            _OPENAI_KEY_FINGERPRINT = fp
            _OPENAI_LAST_ERROR = None
        except Exception as e:  # pragma: no cover
            _OPENAI_CLIENT = None
            _OPENAI_LAST_ERROR = f"init:{e}"[:300]
    return _OPENAI_CLIENT

def is_openai_configured() -> bool:
    return _configure() is not None


def _choose_model() -> List[str]:
    # If a working model already selected, try it first
    if _SELECTED_MODEL:
        return [_SELECTED_MODEL] + [m for m in _MODEL_CANDIDATES if m != _SELECTED_MODEL]
    return list(_MODEL_CANDIDATES)


def _chat(client, messages, temperature: float, max_tokens: int) -> Tuple[Optional[str], Optional[str]]:
    global _SELECTED_MODEL
    last_err = None
    for model in _choose_model():
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            _SELECTED_MODEL = model
            return (resp.choices[0].message.content or "").strip(), None
        except Exception as e:  # pragma: no cover
            msg = str(e)
            # Detect 401 invalid key pattern & force refresh next time
            if "401" in msg or "invalid_api_key" in msg or "Incorrect API key" in msg:
                # Invalidate cached client so a corrected key takes effect without full restart
                _configure(refresh=True)
            last_err = f"{model}: {e.__class__.__name__}: {msg}"[:400]
            # log recent errors in session_state if available
            try:
                logs = st.session_state.get('ai_logs', [])
                logs.append(last_err)
                st.session_state['ai_logs'] = logs[-50:]
            except Exception:
                pass
            continue
    return None, last_err or "Unknown error"


def summarize_weather(weather: Dict[str, float]) -> str:
    client = _configure()
    if not client:
        return "OpenAI not configured (add OPENAI_API_KEY)."
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
        "Write a friendly 2 sentence summary highlighting " + ", ".join(parts) + ". "
        "Keep it concise and helpful for planning an outdoor event."
    )
    text, err = _chat(client, [{"role": "user", "content": prompt}], temperature=0.6, max_tokens=120)
    if err:
        return f"OpenAI summary unavailable ({err})."
    return text or "No summary generated"


def answer_weather_question(question: str, context: str = "") -> str:
    client = _configure()
    if not client:
        return "(AI disabled) Configure OPENAI_API_KEY in .streamlit/secrets.toml or env."
    base = (
        "You are a concise helpful weather assistant. Use only the factual data provided in context if present. "
        "If user asks for a forecast beyond available range (5 days) politely explain the limit."
    )
    prompt = f"{base}\nContext:\n{context}\n\nUser question: {question}\nAnswer:"
    text, err = _chat(client, [{"role": "user", "content": prompt}], temperature=0.5, max_tokens=400)
    if err:
        return f"OpenAI answer unavailable ({err})."
    return text or "No answer generated"


def check_openai_health() -> dict:
    client = _configure()
    if not client:
        return {"configured": False, "ok": False, "error": _OPENAI_LAST_ERROR or "missing"}
    text, err = _chat(client, [{"role": "user", "content": "Return the word OK"}], temperature=0, max_tokens=5)
    if err:
        return {"configured": True, "ok": False, "error": err[:300], "model": _SELECTED_MODEL}
    return {"configured": True, "ok": True, "model": _SELECTED_MODEL}

def get_openai_diagnostics() -> dict:
    return {
        "configured": is_openai_configured(),
        "last_error": _OPENAI_LAST_ERROR,
        "model_selected": _SELECTED_MODEL,
        "key_fingerprint": _OPENAI_KEY_FINGERPRINT,
    }
