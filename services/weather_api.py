# services/weather_api.py
import requests
from config.settings import API_KEY, BASE_URL

def get_forecast(city: str):
    """Fetch 5-day forecast data from OpenWeatherMap API."""
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_forecast_by_coords(lat: float, lon: float):
    """Fetch 5-day forecast by geographic coordinates (used for map pin fallback)."""
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None
