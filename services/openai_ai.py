"""OpenAI (ChatGPT) integration utilities.

Provides provider-parallel functions mirroring gemini_ai: summarize_weather and answer_weather_question.
Reads OPENAI_API_KEY from st.secrets then environment. Safe fallbacks if not configured.
"""
from __future__ import annotations
import os
from functools import lru_cache  # retained for other potential use
import re
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

_OPENAI_CLIENT_CACHE: dict[str, tuple[OpenAI, float, str]] = {}
_OPENAI_CACHE_TTL = 300.0  # seconds

def _configure() -> Optional[OpenAI]:
    """Return (and cache briefly) an OpenAI client using the current key.

    We avoid lru_cache so updates to secrets propagate without app restart.
    A lightweight TTL cache reduces repeated client construction.
    """
    if not _HAS_OPENAI:
        return None
    # Pull current key (strip whitespace)
    key = None
    try:
        raw = st.secrets.get("OPENAI_API_KEY")  # type: ignore[attr-defined]
        key = raw.strip() if isinstance(raw, str) else raw
    except Exception:
        key = None
    if not key:
        env_raw = os.getenv("OPENAI_API_KEY")
        key = env_raw.strip() if env_raw else None
    if not key:
        return None
    # Placeholder detection
    if key.startswith("REPLACE_") or key.startswith("YOUR_") or "REPLACE_WITH" in key:
        try:
            logs = st.session_state.get('ai_logs', [])
            logs.append('Placeholder OpenAI API key detected. Provide a real key from https://platform.openai.com/account/api-keys')
            st.session_state['ai_logs'] = logs[-50:]
        except Exception:
            pass
        return None
    # Optionally pick up org/project (if provided)
    org = None
    project = None
    for cand in ("OPENAI_ORG", "OPENAI_ORGANIZATION"):
        v = st.secrets.get(cand) if hasattr(st, 'secrets') and cand in st.secrets else os.getenv(cand)  # type: ignore[attr-defined]
        if v:
            org = v.strip()
            break
    for cand in ("OPENAI_PROJECT", "OPENAI_PROJ"):
        v = st.secrets.get(cand) if hasattr(st, 'secrets') and cand in st.secrets else os.getenv(cand)  # type: ignore[attr-defined]
        if v:
            project = v.strip()
            break

    # Warn on project-scoped key if no org/project provided
    if key.startswith("sk-proj-") and not (org or project):
        try:
            logs = st.session_state.get('ai_logs', [])
            logs.append('Project-scoped key detected without OPENAI_ORG/OPENAI_PROJECT; API may reject calls.')
            st.session_state['ai_logs'] = logs[-50:]
        except Exception:
            pass

    # Fingerprint for diagnostics (not printed here, only stored)
    try:
        fp = f"{key[:5]}...{key[-4:]}"
        st.session_state['openai_key_fingerprint'] = fp
    except Exception:
        pass

    # Check TTL cache
    import time
    now = time.time()
    cached = _OPENAI_CLIENT_CACHE.get('client')
    if cached:
        client_obj, ts, cached_key = cached
        if now - ts < _OPENAI_CACHE_TTL and cached_key == key:
            return client_obj
    # Build / rebuild client
    try:
        params = {"api_key": key}
        if org:
            params["organization"] = org
        if project:
            # openai python may support project via 'project' kw; if not, it's ignored
            params["project"] = project  # type: ignore
        client = OpenAI(**params)  # type: ignore[arg-type]
        _OPENAI_CLIENT_CACHE['client'] = (client, now, key)
        return client
    except Exception:
        return None

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
            # Redact any API key fragments from the error string
            raw = f"{model}: {e.__class__.__name__}: {e}"
            redacted = _redact_keys(raw)
            # Map common invalid key indicators to a short code
            if 'invalid_api_key' in raw.lower() or 'incorrect api key' in raw.lower():
                last_err = 'invalid_api_key'
            else:
                last_err = redacted
            # log recent errors in session_state if available
            try:
                logs = st.session_state.get('ai_logs', [])
                logs.append((redacted if last_err != 'invalid_api_key' else 'invalid_api_key')[:400])
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
        if err == 'invalid_api_key':
            return "OpenAI summary unavailable (invalid API key – rotate it in your OpenAI dashboard and update Streamlit secrets)."
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
        if err == 'invalid_api_key':
            return "OpenAI answer unavailable (invalid API key – rotate key & update secrets)."
        return f"OpenAI answer unavailable ({err})."
    return text or "No answer generated"


def check_openai_health() -> dict:
    client = _configure()
    if not client:
        return {"configured": False, "ok": False, "error": "API key missing or library not installed"}
    text, err = _chat(client, [{"role": "user", "content": "Return the word OK"}], temperature=0, max_tokens=5)
    if err:
        return {"configured": True, "ok": False, "error": err[:300]}
    return {"configured": True, "ok": True, "model": _SELECTED_MODEL}


_KEY_PATTERN = re.compile(r"sk-[a-zA-Z0-9_-]{8,}")

def _redact_keys(message: str) -> str:
    """Redact any OpenAI-style keys from an error message to avoid leaking them in UI/logs."""
    return _KEY_PATTERN.sub("sk-***redacted***", message)
