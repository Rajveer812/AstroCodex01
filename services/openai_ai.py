"""OpenAI (ChatGPT) integration utilities.

Provides provider-parallel functions mirroring gemini_ai: summarize_weather and answer_weather_question.
Reads OPENAI_API_KEY from st.secrets then environment. Safe fallbacks if not configured.
"""
from __future__ import annotations
import os
from functools import lru_cache  # retained for other potential use
import re
from typing import Dict, Optional, Tuple, List

# Optional Gemini fallback (import lazily to avoid hard dependency if absent)
try:
    from services import gemini_ai  # type: ignore
    _HAS_GEMINI = True
except Exception:  # pragma: no cover
    _HAS_GEMINI = False

import streamlit as st

try:  # Lazy import guard
    from openai import OpenAI  # type: ignore
    _HAS_OPENAI = True
except Exception:  # pragma: no cover
    _HAS_OPENAI = False

def _load_model_candidates() -> List[str]:
    explicit = None
    try:
        explicit = st.secrets.get("OPENAI_MODEL")  # type: ignore[attr-defined]
    except Exception:
        pass
    if not explicit:
        explicit = os.getenv("OPENAI_MODEL")
    ordered: List[str] = []
    if explicit:
        ordered.append(str(explicit).strip())
    ordered.extend([
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4o-2024-08-06",
        "gpt-4.1-mini",
        "gpt-4.1",
        "gpt-3.5-turbo"
    ])
    # de-dup preserving order
    seen = set()
    uniq: List[str] = []
    for m in ordered:
        if m and m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq

_MODEL_CANDIDATES: List[str] = _load_model_candidates()
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
            raw = f"{model}: {e.__class__.__name__}: {e}"
            redacted = _redact_keys(raw)
            lower = raw.lower()
            if 'invalid_api_key' in lower or 'incorrect api key' in lower or 'unauthorized' in lower:
                last_err = 'invalid_api_key'
            elif 'model_not_found' in lower or 'no such model' in lower or 'does not exist' in lower:
                last_err = 'model_not_found'
            elif 'rate limit' in lower or 'capacity' in lower or 'overloaded' in lower:
                last_err = 'rate_limited'
            elif 'timeout' in lower or 'timed out' in lower:
                last_err = 'timeout'
            elif 'organization' in lower and 'not allowed' in lower:
                last_err = 'org_scope'
            elif 'project' in lower and ('not found' in lower or 'forbidden' in lower):
                last_err = 'project_scope'
            elif 'connect' in lower and ('refused' in lower or 'failed' in lower):
                last_err = 'network'
            else:
                last_err = redacted
            try:
                logs = st.session_state.get('ai_logs', [])
                logs.append((redacted if last_err not in {'invalid_api_key'} else last_err)[:400])
                st.session_state['ai_logs'] = logs[-50:]
            except Exception:
                pass
            # If key invalid, flush the cached client so a rotated key is picked up next attempt
            if last_err == 'invalid_api_key':
                try:
                    _OPENAI_CLIENT_CACHE.pop('client', None)
                except Exception:
                    pass
            continue
    return None, last_err or "Unknown error"


def _fallback_summary(weather: Dict[str, float]) -> str:
    temp = weather.get("temp") or weather.get("T2M")
    wind = weather.get("wind") or weather.get("WS2M")
    humidity = weather.get("humidity") or weather.get("RH2M")
    rain = weather.get("rain") or weather.get("total_rain")
    segs = []
    if temp is not None:
        segs.append(f"{temp:.1f}°C")
    if humidity is not None:
        segs.append(f"{humidity:.0f}% RH")
    if wind is not None:
        segs.append(f"{wind:.1f} m/s wind")
    if rain is not None:
        segs.append(("~" + f"{rain:.1f} mm rain") if rain > 0 else "dry")
    return " | ".join(segs) if segs else "No data"

def summarize_weather(weather: Dict[str, float]) -> str:
    client = _configure()
    if not client:
        # Try Gemini fallback if available
        if _HAS_GEMINI and gemini_ai.is_gemini_configured():  # type: ignore[attr-defined]
            try:
                return gemini_ai.summarize_weather(weather)  # type: ignore[attr-defined]
            except Exception:
                pass
        return _fallback_summary(weather)
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
        # On any error: degrade to heuristic or Gemini
        if _HAS_GEMINI and gemini_ai.is_gemini_configured():  # type: ignore[attr-defined]
            try:
                gtxt = gemini_ai.summarize_weather(weather)  # type: ignore[attr-defined]
                return gtxt + ""  # already user-friendly
            except Exception:
                pass
        return _fallback_summary(weather)
    return text or "No summary generated"


def answer_weather_question(question: str, context: str = "") -> str:
    client = _configure()
    if not client:
        if _HAS_GEMINI and gemini_ai.is_gemini_configured():  # type: ignore[attr-defined]
            try:
                return gemini_ai.answer_weather_question(question, context)  # type: ignore[attr-defined]
            except Exception:
                pass
        return _heuristic_answer(question, context)
    base = (
        "You are a concise helpful weather assistant. Use only the factual data provided in context if present. "
        "If user asks for a forecast beyond available range (5 days) politely explain the limit."
    )
    prompt = f"{base}\nContext:\n{context}\n\nUser question: {question}\nAnswer:"
    text, err = _chat(client, [{"role": "user", "content": prompt}], temperature=0.5, max_tokens=400)
    if err:
        if _HAS_GEMINI and gemini_ai.is_gemini_configured():  # type: ignore[attr-defined]
            try:
                return gemini_ai.answer_weather_question(question, context)  # type: ignore[attr-defined]
            except Exception:
                pass
        # Refresh validation snapshot after an error so UI can react
        try:
            st.session_state['openai_validation'] = validate_openai_key()
        except Exception:
            pass
        return _heuristic_answer(question, context)
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


def validate_openai_key() -> Dict[str, Optional[str]]:
    """Proactively validate the configured OpenAI key with a 1-token style request.

    Returns dict with fields:
      configured: bool
      ok: bool
      code: short code (e.g., invalid_api_key, model_not_found, network, timeout)
      model: model attempted
      error: raw/redacted error string (optional)
    """
    client = _configure()
    if not client:
        return {"configured": False, "ok": False, "code": "missing", "model": None, "error": None}
    # Use a deterministic tiny prompt.
    text, err = _chat(client, [{"role": "user", "content": "Return OK"}], temperature=0, max_tokens=5)
    if err:
        code = err if err in {"invalid_api_key","model_not_found","rate_limited","timeout","org_scope","project_scope","network"} else "other"
        return {"configured": True, "ok": False, "code": code, "model": _SELECTED_MODEL, "error": err}
    return {"configured": True, "ok": True, "code": "ok", "model": _SELECTED_MODEL, "error": None}


def _heuristic_answer(question: str, context: str) -> str:
    """Very lightweight rule-based fallback answer using provided context string.

    Extracts temp, humidity, wind, rain metrics if present in context and builds a concise response.
    """
    q_lower = question.lower()
    import re as _re
    metrics = {}
    # Expected context pattern inserted by app: 'temp 23.4C, humidity 55%, wind 3.2 m/s, rain 0.0 mm'
    temp_m = _re.search(r"temp\s*[:=]?\s*(-?\d+\.?\d*)\s*c", context, _re.IGNORECASE)
    if temp_m:
        metrics['temp'] = float(temp_m.group(1))
    hum_m = _re.search(r"humidity\s*[:=]?\s*(\d+)\s*%", context, _re.IGNORECASE)
    if hum_m:
        metrics['humidity'] = float(hum_m.group(1))
    wind_m = _re.search(r"wind\s*[:=]?\s*(\d+\.?\d*)\s*m/?s", context, _re.IGNORECASE)
    if wind_m:
        metrics['wind'] = float(wind_m.group(1))
    rain_m = _re.search(r"rain\s*[:=]?\s*(\d+\.?\d*)\s*mm", context, _re.IGNORECASE)
    if rain_m:
        metrics['rain'] = float(rain_m.group(1))
    parts: List[str] = []
    if 'temp' in metrics and ('temp' in q_lower or 'temperature' in q_lower or not parts):
        parts.append(f"Temperature approx {metrics['temp']:.1f}°C")
    if 'humidity' in metrics and ('humidity' in q_lower):
        parts.append(f"Humidity about {metrics['humidity']:.0f}%")
    if 'wind' in metrics and ('wind' in q_lower or 'breeze' in q_lower):
        parts.append(f"Wind near {metrics['wind']:.1f} m/s")
    if 'rain' in metrics and ('rain' in q_lower or 'precip' in q_lower or 'wet' in q_lower):
        if metrics['rain'] > 0:
            parts.append(f"Rain expected ~{metrics['rain']:.1f} mm")
        else:
            parts.append("Little to no rain expected")
    if not parts:
        if metrics:
            # Provide generic summary if user asked something else
            base = [f"{metrics['temp']:.1f}°C" if 'temp' in metrics else None,
                    f"{metrics['humidity']:.0f}% RH" if 'humidity' in metrics else None,
                    f"{metrics['wind']:.1f} m/s wind" if 'wind' in metrics else None,
                    (f"{metrics['rain']:.1f} mm rain" if metrics.get('rain',0)>0 else 'dry') if 'rain' in metrics else None]
            parts = [p for p in base if p]
        else:
            return "Forecast not loaded yet – run a weather check first to enable AI answers." 
    return ", ".join(parts) + ". (AI fallback)"
