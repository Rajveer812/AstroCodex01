# ui/components.py
import streamlit as st

def show_result(city, date, weather):
    """Display forecast results nicely on the UI."""
    st.subheader(f"Weather forecast for {city} on {date}:")
    
    if weather["total_rain"] > 0:
        st.error("🌧️ Yes, it may rain!")
    elif weather["total_rain"] == 0:
        st.success("☀️ No, skies look clear!")
    else:
        st.info("🌈 Uncertain, check later.")

    st.write(f"🌡️ Temperature: {weather['avg_temp']:.1f} °C")
    st.write(f"💧 Humidity: {weather['avg_humidity']:.0f}%")
    st.write(f"🌬️ Wind Speed: {weather['avg_wind']:.1f} m/s")
