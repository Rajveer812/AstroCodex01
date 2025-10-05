import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import datetime
import os
from services.openai_ai import summarize_weather, is_openai_configured

# --- Streamlit Page Config ---
st.set_page_config(page_title="🛰 NASA Weather Explorer", layout="wide")
st.title("🛰 NASA Weather Explorer")

# --- Helper: Get Today's Date (YYYYMMDD) ---
today = datetime.date.today().strftime('%Y%m%d')

# --- Helper: Fetch NASA POWER Weather Data ---
def fetch_nasa_power_weather(lat, lon, date):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,WS2M,RH2M"
        f"&community=RE&latitude={lat}&longitude={lon}&start={date}&end={date}&format=JSON"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        param = data["properties"]["parameter"]
        t2m = list(param["T2M"].values())[0]
        ws2m = list(param["WS2M"].values())[0]
        rh2m = list(param["RH2M"].values())[0]
        if any(v == -999.0 for v in [t2m, ws2m, rh2m]):
            return None
        return {"T2M": t2m, "WS2M": ws2m, "RH2M": rh2m}
    except Exception:
        return None


# --- Folium Map Setup ---
def create_folium_map(date):
    m = folium.Map(location=[20, 0], zoom_start=2, control_scale=True)
    # NASA GIBS layers
    folium.raster_layers.TileLayer(
        tiles=f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg",
        attr="NASA GIBS - True Color",
        name="🌎 True Color",
        overlay=True,
        control=True,
        fmt="image/jpeg",
        max_zoom=9,
        min_zoom=1,
        show=True
    ).add_to(m)
    folium.raster_layers.TileLayer(
        tiles=f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Cloud_Fraction_Day/default/{date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.png",
        attr="NASA GIBS - Cloud Fraction",
        name="🌤 Clouds",
        overlay=True,
        control=True,
        fmt="image/png",
        max_zoom=9,
        min_zoom=1,
        show=False
    ).add_to(m)
    folium.raster_layers.TileLayer(
        tiles=f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MERRA2_Surface_Temperature/default/{date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.png",
        attr="NASA GIBS - Surface Temp",
        name="🔥 Surface Temp",
        overlay=True,
        control=True,
        fmt="image/png",
        max_zoom=9,
        min_zoom=1,
        show=False
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m

# --- Streamlit UI ---
st.markdown("""
<div style='margin-bottom:1em;'>
Click anywhere on the map to get NASA POWER weather data for that location.<br>
Use the layer control (top-right) to toggle imagery.
</div>
""", unsafe_allow_html=True)

# --- Map State ---
if 'clicked_coords' not in st.session_state:
    st.session_state['clicked_coords'] = None

# --- Show Map ---
m = create_folium_map(today)
map_data = st_folium(m, width=800, height=500, returned_objects=["last_clicked"], key="nasa_map")

# --- Handle Map Click ---
if map_data and map_data.get('last_clicked'):
    coords = map_data['last_clicked']
    lat, lon = coords['lat'], coords['lng']
    st.session_state['clicked_coords'] = (lat, lon)

# --- Show Weather Card ---
if st.session_state['clicked_coords']:
    lat, lon = st.session_state['clicked_coords']
    st.markdown(f"<div class='modern-card' style='margin-top:1em;'>", unsafe_allow_html=True)
    st.markdown(f"<b>📍 Location:</b> {lat:.4f}, {lon:.4f}", unsafe_allow_html=True)
    weather = fetch_nasa_power_weather(lat, lon, today)
    if weather:
        st.markdown(f"<b>🌡 Temperature:</b> {weather['T2M']} °C  ", unsafe_allow_html=True)
        st.markdown(f"<b>🌬 Wind Speed:</b> {weather['WS2M']} m/s  ", unsafe_allow_html=True)
        st.markdown(f"<b>💧 Humidity:</b> {weather['RH2M']} %", unsafe_allow_html=True)
        # AI summary (OpenAI only)
        if is_openai_configured():
            summary = summarize_weather({"T2M": weather['T2M'], "WS2M": weather['WS2M'], "RH2M": weather['RH2M']})
            st.success(f"🤖 OpenAI: {summary}")
        else:
            st.info("AI summary unavailable (add OPENAI_API_KEY).")
    else:
        st.error("No valid NASA POWER data for this location/date.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Placeholders for Future Upgrades ---
st.markdown("""
---
<b>🚧 Coming Soon:</b>
<ul>
<li>Wind vectors/arrows overlay</li>
<li>Precipitation/fire data from NASA FIRMS</li>
<li>Time slider for weather trends</li>
<li>Natural language map queries</li>
</ul>
""", unsafe_allow_html=True)
