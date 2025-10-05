import requests
from config.settings import POLLUTION_API_KEY, POLLUTION_BASE_URL

def get_pollution_stats(city: str):
    """Fetch pollution stats for a city using OpenWeatherMap Air Pollution API."""
    # Geocoding to get lat/lon
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={POLLUTION_API_KEY}"
    geo_resp = requests.get(geo_url)
    if geo_resp.status_code != 200 or not geo_resp.json():
        return None
    loc = geo_resp.json()[0]
    lat, lon = loc['lat'], loc['lon']
    # Fetch pollution data
    params = {"lat": lat, "lon": lon, "appid": POLLUTION_API_KEY}
    resp = requests.get(POLLUTION_BASE_URL, params=params)
    if resp.status_code == 200:
        return resp.json()
    return None
