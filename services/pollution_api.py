"""Pollution stats via OpenWeather Air Pollution API.

Uses dynamic key loading from config.settings without hardcoding secrets.
"""
import requests
from config import settings

def get_pollution_stats(city: str):
    """Fetch pollution stats for a city. Returns dict or None."""
    api_key = settings.get_openweather_api_key()
    if not api_key:
        return None
    # Geocoding to get lat/lon
    geo_url = (
        f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    )
    geo_resp = requests.get(geo_url, timeout=10)
    if geo_resp.status_code != 200:
        return None
    geo_json = geo_resp.json()
    if not geo_json:
        return None
    loc = geo_json[0]
    lat, lon = loc.get('lat'), loc.get('lon')
    if lat is None or lon is None:
        return None
    params = {"lat": lat, "lon": lon, "appid": api_key}
    resp = requests.get(settings.POLLUTION_BASE_URL, params=params, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    return None
