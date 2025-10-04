# app.py
import streamlit as st
import datetime
from services.nasa_api import fetch_nasa_power_monthly_averages
from services.weather_api import get_forecast
from utils.helpers import process_forecast
from ui.components import show_result

st.title("🌦️ Will It Rain On My Parade?")


city = st.text_input("Enter City:")
date = st.date_input("Select Date:", datetime.date.today())

# Section: Historical Monthly Averages
st.subheader("📊 Historical Monthly Averages (NASA POWER)")
if city:
    month = st.selectbox("Select Month:", list(range(1, 13)), index=date.month-1)
    year = st.number_input("Year (for historical context):", min_value=1981, max_value=datetime.date.today().year, value=date.year)
    if st.button("Show Historical Averages"):
        with st.spinner("Fetching NASA POWER data..."):
            try:
                result = fetch_nasa_power_monthly_averages(city, int(year), int(month))
                st.success(f"Historical averages for {city} in {datetime.date(1900, month, 1).strftime('%B')} {year}:")
                st.write(f"- Avg Rainfall: {result['avg_rainfall_mm']:.1f} mm/day")
                st.write(f"- Avg Temperature: {result['avg_temperature_c']:.1f} °C")
                st.caption(f"(Data from NASA POWER, coordinates: {result['latitude']:.2f}, {result['longitude']:.2f})")
            except Exception as e:
                st.error(f"Failed to fetch NASA POWER data: {e}")

if st.button("Check Weather"):
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
