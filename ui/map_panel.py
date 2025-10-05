"""Reusable interactive map panel component with NASA GIBS layers and click-to-fetch data."""
from __future__ import annotations
import datetime
import streamlit as st
import folium
from folium.elements import MacroElement
from jinja2 import Template
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
from utils.helpers import process_forecast
from services.weather_api import get_forecast_by_coords

# --- Helpers with simple caching ---
@st.cache_data(show_spinner=False, ttl=3600)
def reverse_geocode(lat: float, lon: float) -> str | None:
    geolocator = Nominatim(user_agent="astro_codex_app")
    try:
        location = geolocator.reverse((lat, lon), language='en', timeout=5)
        if location and location.address:
            return location.address
    except Exception:
        return None
    return None



def render_map_section():
    """Render map toggle + map + detail card."""
    # Ensure required session keys
    if 'map_center' not in st.session_state:
        st.session_state['map_center'] = [20, 0]
    if 'map_pin' not in st.session_state:
        st.session_state['map_pin'] = None
    if 'show_map_panel' not in st.session_state:
        st.session_state['show_map_panel'] = False

    toggle_label = "Hide NASA Weather Map" if st.session_state['show_map_panel'] else "Show NASA Weather Map"
    if st.button(f"🌍 {toggle_label}", key="toggle_map_panel_btn"):
        st.session_state['show_map_panel'] = not st.session_state['show_map_panel']

    if not st.session_state['show_map_panel']:
        return

    # Center marker implemented inside Leaflet (no external overlay positioning issues)
    class CenterMarker(MacroElement):
        _template = Template("""
        {% macro script(this, kwargs) %}
        (function(){
            var map = {{this._parent.get_name()}};
            var iconHtml = '<div style="font-size:34px; line-height:34px; transform: translate(-50%, -50%); position:absolute;">📍</div>';
            var centerIcon = L.divIcon({html: iconHtml, className: 'center-marker', iconSize: [34,34], iconAnchor:[17,17]});
            var marker = L.marker(map.getCenter(), {icon:centerIcon, interactive:false, keyboard:false}).addTo(map);
            function update(){ marker.setLatLng(map.getCenter()); }
            map.on('move', update);
            map.on('zoom', update);
        })();
        {% endmacro %}
        """)
    # Card wrapper only for the map itself
    st.markdown("<div class='modern-card' style='padding:0;box-shadow:0 4px 16px #0002;'>", unsafe_allow_html=True)
    today = datetime.date.today().strftime('%Y%m%d')
    m = folium.Map(location=st.session_state['map_center'], zoom_start=6 if st.session_state['map_center'] != [20, 0] else 2, control_scale=True)
    folium.raster_layers.TileLayer(
        tiles=f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg",
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
        tiles=f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Cloud_Fraction_Day/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.png",
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
        tiles=f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MERRA2_Surface_Temperature/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.png",
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
    # Add always-centered visual marker
    m.add_child(CenterMarker())

    if st.session_state['map_pin']:
        folium.Marker(location=st.session_state['map_pin'], draggable=True, popup="Pin Location").add_to(m)

    map_data = st_folium(
        m,
        width=1100,
        height=650,
        returned_objects=["last_clicked", "center"],
        key="interactive_map_panel"
    )
    # Close map card wrapper BEFORE any other elements to avoid large blank white area
    st.markdown('</div>', unsafe_allow_html=True)
    # Pin center action button below map (not inside card to prevent empty card space)
    # Styled pin center button + instruction
    cols_actions = st.columns([1,3])
    with cols_actions[0]:
        pin_center = st.button("📌 Pin Center", key="pin_center_btn", help="Set pin to current map center")
    with cols_actions[1]:
        st.markdown("<div style='font-size:0.9rem; color:#555; padding-top:0.55em;'>Pan/zoom map, then click Pin Center or click directly on the map.</div>", unsafe_allow_html=True)

    if map_data and map_data.get('last_clicked'):
        coords = map_data['last_clicked']
        st.session_state['map_pin'] = [coords['lat'], coords['lng']]
        st.session_state['map_center'] = [coords['lat'], coords['lng']]
    # If user wants to pin the visual center
    if 'pin_center_btn' in st.session_state and pin_center:
        # Some versions of st_folium expose center; fallback to existing center if missing
        center_info = None
        if map_data:
            center_info = map_data.get('center') or None
        if center_info and isinstance(center_info, dict):
            c_lat = center_info.get('lat', st.session_state['map_center'][0])
            c_lng = center_info.get('lng', st.session_state['map_center'][1])
        else:
            c_lat, c_lng = st.session_state['map_center']
        st.session_state['map_pin'] = [c_lat, c_lng]
        st.session_state['map_center'] = [c_lat, c_lng]

    if not st.session_state['map_pin']:
        return

    lat, lon = st.session_state['map_pin']
    # Compact dark theme card instead of large white modern-card
    st.markdown(
        """
        <style>
        .map-data-card {background:#111a22; border:1px solid #243649; border-radius:14px; padding:0.85em 1.05em; margin-top:0.5em;}
        .map-badge {display:inline-block; background:#1e293b; color:#e2e8f0; font-size:0.65rem; letter-spacing:0.5px; padding:3px 8px; border-radius:10px; font-weight:600; margin-right:6px;}
        .map-badge.nasa {background:#023859; color:#cde9ff;}
        .map-badge.owm {background:#2d2d33; color:#f1f5f9;}
        .map-field {font-size:0.9rem; margin:2px 0;}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="map-data-card">', unsafe_allow_html=True)
    location_name = reverse_geocode(lat, lon)
    if location_name:
        st.markdown(f"<div class='map-field'><b>📍 Pin Location:</b> {lat:.4f}, {lon:.4f} — {location_name}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='map-field'><b>📍 Pin Location:</b> {lat:.4f}, {lon:.4f}</div>", unsafe_allow_html=True)

    # Only OpenWeatherMap data (NASA removed per request)
    try:
        with st.spinner('Fetching weather (OpenWeatherMap)…'):
            forecast_data = get_forecast_by_coords(lat, lon)
            if not forecast_data:
                st.error("OpenWeatherMap request failed (no data).")
            else:
                weather = process_forecast(forecast_data, datetime.date.today().strftime('%Y-%m-%d'))
                if weather:
                    st.markdown("<div class='map-badge owm'>OpenWeatherMap</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='map-field'><b>🌡 Temperature:</b> {weather['avg_temp']:.1f} °C</div>", unsafe_allow_html=True)
                    if 'avg_wind' in weather:
                        st.markdown(f"<div class='map-field'><b>🌬 Wind:</b> {weather['avg_wind']:.1f} m/s</div>", unsafe_allow_html=True)
                    if 'avg_humidity' in weather:
                        st.markdown(f"<div class='map-field'><b>💧 Humidity:</b> {weather['avg_humidity']:.0f}%</div>", unsafe_allow_html=True)
                    if 'total_rain' in weather:
                        st.markdown(f"<div class='map-field'><b>🌧 Rain (next 24h est):</b> {weather['total_rain']:.1f} mm</div>", unsafe_allow_html=True)
                else:
                    st.error("No valid temperature data from OpenWeatherMap forecast.")
    except Exception as e:
        st.error(f"OpenWeatherMap error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
