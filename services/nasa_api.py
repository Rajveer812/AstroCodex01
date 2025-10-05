"""NASA POWER API integration helpers.

Includes geocoding via geopy (Nominatim) and convenience wrappers for
monthly and daily aggregations. Adds defensive error handling so a
missing optional dependency surfaces a clear message in the Streamlit UI.
"""

# Import required modules
import requests
from datetime import datetime, timedelta

try:
	from geopy.geocoders import Nominatim  # type: ignore
except ModuleNotFoundError as e:  # pragma: no cover - import guard
	# Defer raising until actually needed so the rest of the app can still load
	Nominatim = None  # type: ignore
	_geopy_import_error = e
else:
	_geopy_import_error = None


def get_city_coordinates(city_name: str) -> tuple[float, float]:
	"""Return latitude and longitude for a city name using geopy.

	Raises:
		RuntimeError: If geopy is not installed.
		ValueError: If the city cannot be geocoded.
	"""
	if _geopy_import_error or Nominatim is None:  # type: ignore
		raise RuntimeError(
			"geopy is required for city geocoding but is not installed. "
			"Add 'geopy' to requirements.txt and reinstall."
		)
	geolocator = Nominatim(user_agent="astro_codex_app")
	location = geolocator.geocode(city_name)
	if not location:
		raise ValueError(f"City '{city_name}' not found.")
	return location.latitude, location.longitude


def fetch_nasa_power_monthly_averages(city_name: str, year: int, month: int) -> dict:
	"""
	Fetch monthly average rainfall (mm/day) and temperature (°C) for a city and month using NASA POWER API.
	Returns: dict with 'avg_rainfall_mm', 'avg_temperature_c', 'latitude', 'longitude'.
	Raises RuntimeError on API or parsing errors.
	"""
	lat, lon = get_city_coordinates(city_name)
	start_date = datetime(year, month, 1)
	end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
	start_str = start_date.strftime('%Y%m%d')
	end_str = (end_date - timedelta(days=1)).strftime('%Y%m%d')
	base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
	params = {
		"parameters": "PRECTOTCORR,T2M",
		"community": "RE",
		"longitude": lon,
		"latitude": lat,
		"start": start_str,
		"end": end_str,
		"format": "JSON"
	}
	try:
		response = requests.get(base_url, params=params, timeout=15)
		response.raise_for_status()
		data = response.json()
		daily_data = data["properties"]["parameter"]
		rainfall = [v for v in daily_data["PRECTOTCORR"].values() if v != -999.0]
		temperature = [v for v in daily_data["T2M"].values() if v != -999.0]
		avg_rainfall = sum(rainfall) / len(rainfall) if rainfall else None
		avg_temperature = sum(temperature) / len(temperature) if temperature else None
		return {
			"city": city_name,
			"latitude": lat,
			"longitude": lon,
			"month": month,
			"year": year,
			"avg_rainfall_mm": avg_rainfall,
			"avg_temperature_c": avg_temperature
		}
	except Exception as e:
		raise RuntimeError(f"Error fetching or parsing NASA POWER API: {e}")


def fetch_nasa_power_daily(lat: float, lon: float, date: str) -> dict | None:
	"""
	Fetch NASA POWER daily T2M, WS2M, RH2M for given lat/lon and date (YYYYMMDD).
	Returns dict or None if data is missing.
	"""
	base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
	params = {
		"parameters": "T2M,WS2M,RH2M",
		"community": "RE",
		"longitude": lon,
		"latitude": lat,
		"start": date,
		"end": date,
		"format": "JSON"
	}
	try:
		response = requests.get(base_url, params=params, timeout=10)
		response.raise_for_status()
		data = response.json()
		param = data["properties"]["parameter"]
		t2m = list(param["T2M"].values())[0]
		ws2m = list(param["WS2M"].values())[0]
		rh2m = list(param["RH2M"].values())[0]
		if any(v == -999.0 for v in [t2m, ws2m, rh2m]):
			return None
		return {"T2M": t2m, "WS2M": ws2m, "RH2M": rh2m}
	except Exception:
		return None
