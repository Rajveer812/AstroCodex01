"""Central configuration & dynamic settings loaders.

Sensitive values (API keys) are NOT hardcoded. They are resolved in this order:
1. Streamlit secrets (st.secrets[...]) when Streamlit is running.
2. Environment variables.
3. Fallback: None (callers decide how to handle missing key).

Never commit real API keys to the repository. Ensure `.streamlit/secrets.toml` remains git-ignored.
"""

from __future__ import annotations

import os
from typing import Optional

try:  # Streamlit may not be present during some tooling runs
	import streamlit as st  # type: ignore
except Exception:  # pragma: no cover - optional dependency environment
	st = None  # type: ignore


def _get_secret(name: str) -> Optional[str]:
	"""Attempt to read a secret from st.secrets then environment.

	Returns None if not found. Does not raise so callers can degrade gracefully.
	"""
	# 1. Streamlit secrets
	if st is not None:
		try:
			if name in st.secrets:  # type: ignore[attr-defined]
				val = st.secrets.get(name)  # type: ignore[attr-defined]
				if isinstance(val, str) and val.strip():
					return val.strip()
		except Exception:
			pass
	# 2. Environment variable
	val = os.getenv(name)
	if val and val.strip():
		return val.strip()
	return None


# Public accessor functions (prefer functions over module-level constants for secrets)
def get_openweather_api_key() -> Optional[str]:
	return _get_secret("OPENWEATHER_API_KEY")


# Non-secret static endpoints
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"
POLLUTION_BASE_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

# Geocoding / Nominatim settings
# Increase timeout to reduce ReadTimeouts; keep retries modest to respect usage policy.
GEOCODE_TIMEOUT_SECONDS = 5
GEOCODE_MAX_RETRIES = 3
GEOCODE_BACKOFF_BASE = 0.5  # seconds, exponential backoff multiplier
GEOCODE_USER_AGENT = "astro_codex_app/1.0 (contact: replace_with_email)"
