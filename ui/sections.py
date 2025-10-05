"""
UI section rendering helpers for Will It Rain On My Parade?
"""
import streamlit as st
import pandas as pd
import calendar
from streamlit_folium import st_folium
import folium

def render_header() -> None:
        """Render the app header and subtitle."""
        st.markdown("""
        <div style='text-align:center; margin-bottom:2em;'>
            <span style='font-size:2.7rem;'>🌦️</span>
            <span style='font-size:2.3rem; font-weight:700; color:#4f8cff;'>Astrocast</span>
            <br>
            <span style='font-size:1.15rem; color:#444;'>Actionable weather, climate & air quality intelligence for better outdoor planning.<br>Powered by <b>OpenWeatherMap</b>, <b>NASA POWER</b> & AI.</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

def render_inputs() -> tuple[str, pd.Timestamp, bool, any, list]:
    """Render city/date input and forecast placeholder."""
    cols = st.columns([1.2, 1])
    with cols[0]:
        st.markdown("<div class='section-title'>📍 Event Location & Date</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Enter your city and parade date to get a personalized forecast and suitability score.</div>", unsafe_allow_html=True)
        city = st.text_input("City:", key="city_input")
        date = st.date_input("Date:", pd.Timestamp.today(), key="date_input")
        check_weather = st.button("Check Weather", key="weather_btn")
    with cols[1]:
        st.markdown("<div class='section-title'>☀️ Today's Forecast</div>", unsafe_allow_html=True)
        forecast_placeholder = st.empty()
    return city, date, check_weather, forecast_placeholder, cols

def render_suitability_card(score: int, message: str, suggestion: str, condition_emoji: str | None = None, condition_desc: str | None = None) -> None:
    """Render the parade suitability score card with optional condition emoji and tooltip."""
    tooltip_attr = f"title='{condition_desc}'" if condition_desc else ""
    emoji_html = f"<span style='font-size:2rem; margin-right:0.35rem;' {tooltip_attr}>{condition_emoji}</span>" if condition_emoji else ""
    st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-title'>🎉 Parade Suitability Score</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; align-items:baseline; gap:0.4rem;'>{emoji_html}<div class='score-big' style='margin:0;'>{score}/100</div></div>", unsafe_allow_html=True)
    if condition_desc:
        st.caption(f"Condition: {condition_desc}")
    st.caption(message)
    st.markdown(f"<div class='suggestion'>Event Suggestion: {suggestion}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_nasa_section(city: str, date: pd.Timestamp) -> tuple[bool, int, int]:
    """Render NASA POWER historical averages section."""
    st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📊 Historical Monthly Averages (NASA POWER)</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>See what’s normal for your city and month, based on decades of NASA data.</div>", unsafe_allow_html=True)
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    cols_hist = st.columns([1, 1])
    with cols_hist[0]:
        month_display = st.selectbox("Select Month:", month_names, index=date.month-1, key="hist_month")
        month_hist = month_names.index(month_display) + 1
    with cols_hist[1]:
        year_hist = st.number_input("Year (for historical context):", min_value=1981, max_value=pd.Timestamp.today().year, value=date.year, key="hist_year")
    show_hist = st.button("Show Historical Averages", key="hist_btn")
    st.markdown("</div>", unsafe_allow_html=True)
    return show_hist, month_hist, year_hist

def render_nasa_results(city: str, month_hist: int, year_hist: int, result: dict) -> None:
    """Render NASA POWER historical results as a table."""
    st.success(f"Historical averages for {city} in {calendar.month_name[int(month_hist)]} {int(year_hist)}:")
    df = pd.DataFrame({
        'Metric': ['Avg Rainfall (mm/day)', 'Avg Temperature (°C)'],
        'Value': [result['avg_rainfall_mm'], result['avg_temperature_c']]
    })
    st.dataframe(df, width='stretch', hide_index=True)
    st.caption(f"(Data from NASA POWER, coordinates: {result['latitude']:.2f}, {result['longitude']:.2f})")

def render_pollution_stats(city: str, pollution_data: dict) -> None:
    """Render air pollution stats as a table."""
    st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🌫️ Air Pollution Index</div>", unsafe_allow_html=True)
    if not pollution_data or 'list' not in pollution_data or not pollution_data['list']:
        st.error(f"No pollution data available for {city}.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    stats = pollution_data['list'][0]['main']
    components = pollution_data['list'][0]['components']
    df = pd.DataFrame({
        'Metric': ['AQI (Index)', 'CO (μg/m³)', 'NO (μg/m³)', 'NO2 (μg/m³)', 'O3 (μg/m³)', 'SO2 (μg/m³)', 'PM2.5 (μg/m³)', 'PM10 (μg/m³)'],
        'Value': [stats['aqi'], components['co'], components['no'], components['no2'], components['o3'], components['so2'], components['pm2_5'], components['pm10']]
    })
    st.dataframe(df, width='stretch', hide_index=True)
    st.caption("AQI: 1-Good, 2-Fair, 3-Moderate, 4-Poor, 5-Very Poor")
    st.markdown("</div>", unsafe_allow_html=True)

def render_map_panel(center: list | None = None, pin: list | None = None) -> dict | None:
    """Render the interactive map panel with NASA GIBS layers and optional pin."""
    st.markdown("""
    <style>
    .map-panel { position: relative; z-index: 100; }
    .map-close-btn { position: absolute; top: 10px; right: 10px; z-index: 101; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<div class='modern-card map-panel'>", unsafe_allow_html=True)
    if center is None:
        center = [20, 0]
    m = folium.Map(location=center, zoom_start=6 if center != [20, 0] else 2, control_scale=True)
    # NASA GIBS layers
    folium.raster_layers.TileLayer(
        tiles="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{time}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
        attr="NASA GIBS - True Color",
        name="True Color",
        overlay=True,
        control=True,
        fmt="image/jpeg",
        max_zoom=9,
        min_zoom=1,
        show=True,
        time="2023-10-01"
    ).add_to(m)
    folium.raster_layers.TileLayer(
        tiles="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Cloud_Fraction_Day/default/{time}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png",
        attr="NASA GIBS - Cloud Fraction",
        name="Cloud Fraction",
        overlay=True,
        control=True,
        fmt="image/png",
        max_zoom=9,
        min_zoom=1,
        show=False,
        time="2023-10-01"
    ).add_to(m)
    folium.raster_layers.TileLayer(
        tiles="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MERRA2_Surface_Temperature/default/{time}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png",
        attr="NASA GIBS - Surface Temp",
        name="Surface Temperature",
        overlay=True,
        control=True,
        fmt="image/png",
        max_zoom=9,
        min_zoom=1,
        show=False,
        time="2023-10-01"
    ).add_to(m)
    folium.LayerControl().add_to(m)
    # Add draggable pin if requested
    if pin:
        folium.Marker(location=pin, draggable=True, popup="Pin Location").add_to(m)
    map_data = st_folium(m, width=700, height=400, returned_objects=["last_clicked", "last_object_clicked_tooltip", "center", "all_drawings"], key="main_map")
    st.markdown("</div>", unsafe_allow_html=True)
    return map_data

def render_map_icon() -> None:
    """Render the map toggle icon button."""
    cols = st.columns([10, 1])
    with cols[1]:
        if st.button("🌍", key="toggle_map_btn", help="Show/hide interactive map"):
            st.session_state['show_map'] = not st.session_state.get('show_map', False)
