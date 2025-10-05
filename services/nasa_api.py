"""NASA POWER API integration helpers.

Includes geocoding via geopy (Nominatim) and convenience wrappers for
monthly and daily aggregations. Adds defensive error handling so a
missing optional dependency surfaces a clear message in the Streamlit UI.
"""

# Import required modules
import requests
from datetime import datetime, timedelta
import time
from functools import lru_cache
from typing import Optional

from config import settings

try:
	from geopy.geocoders import Nominatim  # type: ignore
except ModuleNotFoundError as e:  # pragma: no cover - import guard
	# Defer raising until actually needed so the rest of the app can still load
	Nominatim = None  # type: ignore
	_geopy_import_error = e
else:
	_geopy_import_error = None


@lru_cache(maxsize=256)
def _geocode_city_cached(city_name: str) -> Optional[tuple[float, float]]:
	"""Internal cached geocoding call (returns None if not found)."""
	geolocator = Nominatim(user_agent=settings.GEOCODE_USER_AGENT)
	return _geocode_with_retries(geolocator, city_name)


def _geocode_with_retries(geolocator, city_name: str) -> Optional[tuple[float, float]]:
	retries = settings.GEOCODE_MAX_RETRIES
	base_delay = settings.GEOCODE_BACKOFF_BASE
	for attempt in range(1, retries + 1):
		try:
			location = geolocator.geocode(
				city_name,
				timeout=settings.GEOCODE_TIMEOUT_SECONDS,
			)
			if not location:
				return None
			return (location.latitude, location.longitude)
		except Exception as e:  # Broad catch due to varied geopy exceptions
			if attempt == retries:
				raise RuntimeError(
					f"Geocoding failed for '{city_name}' after {retries} attempts: {e}"
				)
			# Exponential backoff with jitter
			sleep_for = base_delay * (2 ** (attempt - 1)) + (0.05 * attempt)
			time.sleep(sleep_for)
	return None


def get_city_coordinates(city_name: str) -> tuple[float, float]:
	"""Return latitude and longitude for a city name using geopy with retries & cache.

	Raises:
		RuntimeError: If geopy missing or repeated failures occur.
		ValueError: If the city cannot be geocoded.
	"""
	if _geopy_import_error or Nominatim is None:  # type: ignore
		raise RuntimeError(
			"geopy is required for city geocoding but is not installed. "
			"Add 'geopy' to requirements.txt and reinstall."
		)
	coords = _geocode_city_cached(city_name.strip())
	if not coords:
		raise ValueError(f"City '{city_name}' not found or geocoding unavailable.")
	return coords


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
