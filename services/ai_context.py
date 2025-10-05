"""AI context assembly utilities.

Builds a structured context (JSON-like string) combining:
 - Current day aggregate
 - Up to N future day aggregates (timezone-aware)
 - NASA POWER monthly historical averages (rainfall & temperature)

This minimizes hallucination by giving Gemini explicit numeric facts.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import datetime as _dt

from utils.helpers import aggregate_daily_by_timezone
from services.nasa_api import fetch_nasa_power_monthly_averages

def build_ai_weather_context(
    city: str,
    forecast_data: Dict[str, Any] | None,
    target_used_date: str | None,
    future_days: int = 2,
) -> str:
    """Return a JSON string with structured weather context.

    Structure:
    {
      "city": str,
      "generated_utc": ISO datetime,
      "days": [ {"label": "today"|"day+1"|..., metrics... } ],
      "historical": { "month": int, "avg_rainfall_mm": float|null, "avg_temperature_c": float|null }
    }
    """
    payload: Dict[str, Any] = {
        "city": city,
        "generated_utc": _dt.datetime.utcnow().isoformat() + "Z",
        "days": [],
        "historical": None,
    }
    if not forecast_data or 'list' not in forecast_data:
        return json.dumps(payload)
    # Ensure timezone aggregation base covers today + future days
    # day_offset=0 (today), then 1..future_days
    for offset in range(0, future_days + 1):
        agg = aggregate_daily_by_timezone(forecast_data, day_offset=offset)
        if not agg:
            continue
        label = 'today' if offset == 0 else f'day+{offset}'
        payload['days'].append({
            'label': label,
            'date': agg['date'],
            'avg_temp_c': round(agg['avg_temp'], 2),
            'avg_humidity_pct': round(agg['avg_humidity'], 1),
            'avg_wind_ms': round(agg['avg_wind'], 2),
            'total_rain_mm': round(agg['total_rain'], 2),
        })
    # Historical (NASA POWER) for used date month if available
    try:
        if target_used_date:
            dt_obj = _dt.datetime.strptime(target_used_date, '%Y-%m-%d')
        else:
            dt_obj = _dt.datetime.utcnow()
        hist = fetch_nasa_power_monthly_averages(city, dt_obj.year, dt_obj.month)
        if hist:
            payload['historical'] = {
                'month': dt_obj.month,
                'avg_rainfall_mm': hist.get('avg_rainfall_mm'),
                'avg_temperature_c': hist.get('avg_temperature_c'),
            }
    except Exception:
        pass
    return json.dumps(payload, ensure_ascii=False)

def build_instruction(prompt_question: str) -> str:
    return (
        "You are a precise weather assistant. Use ONLY the numeric facts in the JSON context. "
        "If a value for a requested day (e.g., day+1 rain) is missing, state that it is unavailable. "
        "Provide concise sentences (<=120 words). Avoid speculation. "
        f"User question: {prompt_question}"\
    )
