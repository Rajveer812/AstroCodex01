# app.py
import streamlit as st
import datetime
from services.nasa_api import fetch_nasa_power_monthly_averages
from services.weather_api import get_forecast
from utils.helpers import process_forecast
from ui.components import show_result




# --- Custom CSS for better UI ---
st.markdown("""
    <style>
    .main {
        background-color: #181c24;
    }
    div[data-testid="stSidebar"] {
        background-color: #23272f;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.5em 2em;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
        background: linear-gradient(90deg, #4f8cff 0%, #6f6fff 100%);
        color: white;
        border: none;
    }
    .stTextInput>div>input {
        border-radius: 8px;
        font-size: 1.1rem;
        padding: 0.5em;
    }
    .stDateInput>div>input {
        border-radius: 8px;
        font-size: 1.1rem;
        padding: 0.5em;
    }
    .stSelectbox>div>div {
        border-radius: 8px;
        font-size: 1.1rem;
        padding: 0.5em;
    }
    </style>
""", unsafe_allow_html=True)


# --- App Title and Description ---
st.markdown("""
<h1 style='text-align: center; font-size: 2.8rem;'>🌦️ Will It Rain On My Parade?</h1>
<p style='text-align: center; font-size: 1.2rem; color: #b0b8c1;'>
  Enter your city and date to get a science-based weather forecast and historical climate insights.<br>
  Powered by OpenWeatherMap and NASA POWER.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Weather Forecast Section (Moved Above Inputs) ---
st.markdown("<h2 style='color:#4f8cff;'>🌤️ Weather Forecast</h2>", unsafe_allow_html=True)
st.caption("Get a 5-day forecast for your parade date.")

# --- Unified City and Date Input ---
col1, col2 = st.columns([2, 1])
with col1:
    city = st.text_input("🏙️ Enter City:")
with col2:
    date = st.date_input("📅 Select Date:", datetime.date.today())

if st.button("Check Weather", key="weather_btn"):
    if not city:
        st.error("⚠️ Please enter a city name")
    else:
        data = get_forecast(city)
        if not data:
            st.error("❌ Failed to fetch data. Check city name or API key.")
        else:
            target_date = date.strftime("%Y-%m-%d")
            weather = process_forecast(data, target_date)
            if not weather:
                st.warning("⚠️ No forecast data for this date (try within 5 days).")
            else:
                # Try to fetch historical averages for the selected month
                try:
                    hist = fetch_nasa_power_monthly_averages(city, date.year, date.month)
                except Exception as e:
                    hist = None
                show_result(city, target_date, weather)
                # Compute and display Parade Suitability Score if historical data is available
                if hist:
                    st.markdown("---")
                    st.subheader("🎉 Parade Suitability Score")
                    # Simple scoring: lower rain, closer to historical avg temp, higher score
                    rain_penalty = min(weather['total_rain'] * 10, 50)  # up to -50
                    temp_diff = abs(weather['avg_temp'] - hist['avg_temperature_c'])
                    temp_penalty = min(temp_diff * 2, 20)  # up to -20
                    base_score = 100 - rain_penalty - temp_penalty
                    score = max(0, min(100, base_score))
                    st.metric("Suitability Score", f"{score:.0f}/100")
                    st.caption("Score penalizes for rain and large deviation from historical average temperature.")

st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

# --- NASA POWER Historical Monthly Averages Section ---
## Removed duplicate header and caption for NASA POWER section


# --- Improved UI for NASA POWER Historical Monthly Averages ---
import calendar
st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='background: #23273a; border-radius: 16px; padding: 2em 2em 1.5em 2em; margin-bottom: 2em;'>
<h2 style='color:#6f6fff; margin-bottom: 0.5em;'>📊 Historical Monthly Averages (NASA POWER)</h2>
<p style='color: #b0b8c1; margin-bottom: 1.5em;'>See what’s normal for your city and month, based on decades of NASA data.</p>
""", unsafe_allow_html=True)

month_names = [calendar.month_name[i] for i in range(1, 13)]
cols = st.columns([1, 1])
with cols[0]:
    month_display = st.selectbox("Select Month:", month_names, index=date.month-1, key="hist_month")
    month_hist = month_names.index(month_display) + 1
with cols[1]:
    year_hist = st.number_input("Year (for historical context):", min_value=1981, max_value=datetime.date.today().year, value=date.year, key="hist_year")

show_hist = st.button("Show Historical Averages", key="hist_btn")
st.markdown("</div>", unsafe_allow_html=True)

if show_hist:
    if not city:
        st.error("⚠️ Please enter a city name")
    else:
        with st.spinner("Fetching NASA POWER data..."):
            try:
                result = fetch_nasa_power_monthly_averages(city, int(year_hist), int(month_hist))
                st.success(f"Historical averages for {city} in {calendar.month_name[int(month_hist)]} {int(year_hist)}:")
                st.markdown(f"""
                    <ul style='font-size:1.1rem;'>
                        <li><b>Avg Rainfall:</b> {result['avg_rainfall_mm']:.1f} mm/day</li>
                        <li><b>Avg Temperature:</b> {result['avg_temperature_c']:.1f} °C</li>
                    </ul>
                """, unsafe_allow_html=True)
                st.caption(f"(Data from NASA POWER, coordinates: {result['latitude']:.2f}, {result['longitude']:.2f})")
            except Exception as e:
                st.error(f"Failed to fetch NASA POWER data: {e}")
