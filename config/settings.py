# config/settings.py
API_KEY = "555651e7a61bf7475fccd8cdde097302"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"
POLLUTION_API_KEY = API_KEY  # Use same key for pollution API
POLLUTION_BASE_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

# Geocoding / Nominatim settings
# Increase timeout to reduce ReadTimeouts; keep retries modest to respect usage policy.
GEOCODE_TIMEOUT_SECONDS = 5
GEOCODE_MAX_RETRIES = 3
GEOCODE_BACKOFF_BASE = 0.5  # seconds, exponential backoff multiplier
GEOCODE_USER_AGENT = "astro_codex_app/1.0 (contact: your_email@example.com)"
