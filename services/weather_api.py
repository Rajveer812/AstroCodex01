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
