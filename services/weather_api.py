"""OpenWeather forecast helpers.

Reads API key dynamically from settings accessors. Returns None gracefully
when key missing instead of making unauthenticated calls.
"""
import requests
from config import settings

def get_forecast(city: str):
    """Fetch 5-day forecast data. Returns dict or None."""
    api_key = settings.get_openweather_api_key()
    if not api_key:
        return None
    params = {"q": city, "appid": api_key, "units": "metric"}
    response = requests.get(settings.BASE_URL, params=params, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


def get_forecast_diagnostic(city: str):
    """Return (data, error_reason) where error_reason is a short code/string.

    error_reason values:
        missing_key    -> API key not configured
        http_error     -> Non-200 HTTP response
        empty_response -> 200 but body unusable
    """
    api_key = settings.get_openweather_api_key()
    if not api_key:
        return None, "missing_key"
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        resp = requests.get(settings.BASE_URL, params=params, timeout=10)
    except Exception as e:
        return None, f"network:{e}"  # network or timeout
    if resp.status_code == 401:
        return None, "unauthorized"  # invalid key
    if resp.status_code == 404:
        return None, "city_not_found"
    if resp.status_code != 200:
        return None, f"http_error:{resp.status_code}"
    try:
        js = resp.json()
    except Exception:
        return None, "empty_response"
    if not js:
        return None, "empty_response"
    return js, None


def get_forecast_by_coords(lat: float, lon: float):
    """Fetch 5-day forecast by geographic coordinates."""
    api_key = settings.get_openweather_api_key()
    if not api_key:
        return None
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
    response = requests.get(settings.BASE_URL, params=params, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None
