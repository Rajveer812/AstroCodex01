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
