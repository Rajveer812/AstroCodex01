"""
Main Streamlit app for Will It Rain On My Parade?
Organized and cleaned for clarity and maintainability.
"""
# --- Imports ---
import streamlit as st
import datetime
import pandas as pd
import calendar
import html
import textwrap
# Third-party and local imports
from services.nasa_api import fetch_nasa_power_monthly_averages
from services.weather_api import get_forecast
from services.pollution_api import get_pollution_stats
from utils.helpers import process_forecast, process_forecast_with_fallback
from utils.scoring import parade_suitability_score, get_event_suggestion
from ui.components import show_result
from ui.sections import render_header, render_inputs, render_suitability_card, render_nasa_section, render_nasa_results, render_pollution_stats
from services.openai_ai import (
    summarize_weather as oa_summarize,
    answer_weather_question as oa_answer,
    is_openai_configured,
    check_openai_health,
    reset_openai_client,
    openai_diagnostics,
)
from ui.map_panel import render_map_section
# OpenAI-only helper wrappers
def ai_summarize(weather_dict):
    if is_openai_configured():
        return oa_summarize(weather_dict)
    return 'OpenAI not configured (add OPENAI_API_KEY).'

def ai_answer(question: str, context: str):
    if is_openai_configured():
        return oa_answer(question, context)
    return '(AI disabled) Configure OPENAI_API_KEY.'

# --- Set Page Config ---
st.set_page_config(
    page_title="Astrocast",
    page_icon="🌦️",
    layout="wide"
)

# --- Custom CSS for better UI ---
st.markdown("""
    <style>
    body, .main {
        background-color: #f5f7fa;
    }
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.15rem;
        padding: 0.7em 2.5em;
        margin-top: 0.7em;
        margin-bottom: 0.7em;
        background: linear-gradient(90deg, #4f8cff 0%, #6f6fff 100%);
        color: white;
        border: none;
        box-shadow: 0 2px 8px #0001;
    }
    .stTextInput>div>input, .stDateInput>div>input {
        border-radius: 10px;
        font-size: 1.15rem;
        padding: 0.7em;
        background: #fff;
        border: 1px solid #dbeafe;
    }
    .modern-card {
        background: #fff;
        border-radius: 18px;
        padding: 2em 2em 1.5em 2em;
        margin-bottom: 2em;
        box-shadow: 0 4px 16px #0002;
    }
    .score-big {
        font-size: 2.7rem;
        font-weight: bold;
        color: #4f8cff;
        margin-bottom: 0.2em;
    }
    .suggestion {
        font-size: 1.25rem;
        font-weight: 500;
        color: #333;
        margin-top: 0.7em;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #4f8cff;
        margin-bottom: 0.5em;
    }
    .section-sub {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 1.2em;
    }
    </style>
""", unsafe_allow_html=True)

# --- Chat Assistant Styles ---
st.markdown("""
<style>
.chat-fab { position: fixed; bottom: 26px; right: 26px; width:62px; height:62px; border-radius:50%; background:linear-gradient(135deg,#4f8cff,#6f6fff); color:#fff; font-size:30px; font-weight:600; border:none; box-shadow:0 4px 14px rgba(0,0,0,0.25); cursor:pointer; z-index:10000; }
.chat-fab:hover { filter:brightness(1.1); }
.chat-panel { position:fixed; bottom:100px; right:26px; width:360px; max-height:520px; background:#ffffff; border-radius:18px; box-shadow:0 10px 28px rgba(0,0,0,0.28); padding:14px 16px 18px; z-index:10001; display:flex; flex-direction:column; }
.chat-header { font-weight:700; font-size:1.05rem; margin-bottom:4px; color:#274b7a; display:flex; align-items:center; justify-content:space-between; }
.chat-messages { flex:1; overflow-y:auto; border:1px solid #e2e8f0; border-radius:12px; padding:8px 10px; background:#f8fbff; }
.chat-msg-user { background:#4f8cff; color:#fff; padding:6px 10px; border-radius:14px; margin:6px 0; font-size:0.85rem; align-self:flex-end; max-width:85%; }
.chat-msg-bot { background:#eef4ff; color:#1e293b; padding:6px 10px; border-radius:14px; margin:6px 0; font-size:0.85rem; align-self:flex-start; max-width:90%; }
.chat-input-row { display:flex; gap:6px; margin-top:8px; }
.chat-input-row textarea { flex:1; border-radius:12px !important; }
.chat-close { cursor:pointer; font-size:1.2rem; line-height:1; padding:2px 8px; border-radius:8px; }
.chat-close:hover { background:#e2e8f0; }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [20, 0]
if 'map_pin' not in st.session_state:
    st.session_state['map_pin'] = None
if 'clicked_coords' not in st.session_state:
    st.session_state['clicked_coords'] = None
if 'show_chat' not in st.session_state:
    st.session_state['show_chat'] = False
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []  # list of dicts: {role:'user'|'bot', 'text':str}



# --- UI: Header and Inputs ---
render_header()

# --- AI Status Bar (top) ---
with st.container():
    ai_col1, ai_col2, ai_col3, ai_col4, ai_col5 = st.columns([1.2,1,1,1,1.2])
    with ai_col1:
        if st.button("🔄 Reset AI Client", help="Clear cached OpenAI client (use after adding key in deployment)"):
            reset_openai_client()
            st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()
    with ai_col2:
        if st.button("✅ Check AI", help="Run a lightweight health check"):
            st.session_state['last_ai_health'] = check_openai_health()
    with ai_col3:
        configured = is_openai_configured()
        badge_color = '#16a34a' if configured else '#64748b'
        st.markdown(f"<div style='padding:6px 10px; border-radius:10px; background:{badge_color}; color:#fff; font-size:0.75rem; font-weight:600; text-align:center;'>AI {'READY' if configured else 'OFF'}</div>", unsafe_allow_html=True)
    with ai_col4:
        if 'last_ai_health' in st.session_state:
            info = st.session_state['last_ai_health']
            if info.get('configured') and info.get('ok'):
                st.success(f"Model: {info.get('model','?')}", icon="🤖")
            else:
                err = info.get('error','not configured')
                st.warning(err[:160], icon="⚠️")
        else:
            st.caption("Use 'Check AI' to view status")
    with ai_col5:
        if st.button("🛠 Diagnostics", help="Show detailed OpenAI diagnostics"):
            st.session_state['openai_diag'] = openai_diagnostics()
        if 'openai_diag' in st.session_state:
            diag = st.session_state['openai_diag']
            st.markdown(
                f"<div style='font-size:0.6rem; line-height:1.15; background:#f1f5f9; padding:6px 8px; border-radius:8px;'>"
                f"legacy={diag.get('legacy_mode')} configured={diag.get('configured')} ok={diag.get('ok')}<br>"
                f"env_key={diag.get('env_has_key')} secrets_key={diag.get('secrets_has_key')}<br>"
                f"model={diag.get('model','?')} error={(diag.get('error') or '')[:70]}" 
                f"</div>",
                unsafe_allow_html=True
            )
city, date, check_weather, forecast_placeholder, cols = render_inputs()
# Remove unnecessary empty white box
# st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

# --- Compare Feature (Weekend Parade) ---
if 'show_compare' not in st.session_state:
    st.session_state['show_compare'] = False
if 'compare_ai_summary' not in st.session_state:
    st.session_state['compare_ai_summary'] = None

@st.cache_data(show_spinner=False, ttl=1800)
def cached_forecast(city_name: str):
    return get_forecast(city_name)

@st.cache_data(show_spinner=False, ttl=3600)
def cached_nasa(city_name: str, year: int, month: int):
    return fetch_nasa_power_monthly_averages(city_name, year, month)

compare_col = st.container()
with compare_col:
    c1, c2, c3 = st.columns([1,1,1])
    with c3:
        if st.button("🔀 Compare Cities", help="Toggle weekend parade comparison"):
            st.session_state['show_compare'] = not st.session_state['show_compare']

def _next_weekend_day(day_name: str):
    today = datetime.date.today()
    target_weekday = 5 if day_name == 'Saturday' else 6
    delta = (target_weekday - today.weekday()) % 7
    return today + datetime.timedelta(days=delta)

def compute_city_score(city_name: str, target_dt: datetime.date):
    if not city_name:
        return None, "Empty city"
    try:
        data = cached_forecast(city_name)
    except Exception as e:
        return None, f"Forecast error: {e}".strip()
    date_str = target_dt.strftime('%Y-%m-%d')
    try:
        weather, used_date, substituted = process_forecast_with_fallback(data, date_str)
    except Exception as e:
        return None, f"Process error: {e}".strip()
    if not weather:
        return None, "No forecast data in window"
    try:
        # Use date actually used (fallback aware)
        used_dt_obj = datetime.datetime.strptime(used_date, '%Y-%m-%d') if weather else target_dt
        hist = cached_nasa(city_name, used_dt_obj.year, used_dt_obj.month)
    except Exception as e:
        hist = None
    rain_prob = 90 if weather['total_rain'] > 5 else 70 if weather['total_rain'] > 0 else 0
    wind_speed = weather.get('avg_wind', 10)
    forecast_input = {
        'rain_probability': rain_prob,
        'temp': weather['avg_temp'],
        'humidity': weather['avg_humidity'],
        'wind_speed': wind_speed
    }
    historical_input = {
        'avg_rainfall_mm': hist['avg_rainfall_mm'] if hist else 0,
        'avg_temp_c': hist['avg_temperature_c'] if hist else weather['avg_temp']
    }
    result = parade_suitability_score(forecast_input, historical_input)
    suggestion = get_event_suggestion(forecast_input)
    payload = {
        'City': city_name.title(),
        'Score': result['score'],
        'RainProb(%)': rain_prob,
        'Temp(°C)': round(weather['avg_temp'],1),
        'Humidity(%)': round(weather['avg_humidity']),
        'Wind(m/s)': round(wind_speed,1),
        'Rain(mm)': round(weather['total_rain'],1),
        'Cond': f"{weather.get('condition_emoji','')} {weather.get('condition','')}",
        'Suggestion': suggestion,
        '_used_date': used_date,
        '_substituted': substituted
    }
    return payload, None

if st.session_state['show_compare']:
    st.markdown("""
    <div style='margin-top:0.8rem; padding:1rem 1.25rem; background:#ffffff; border-radius:16px; box-shadow:0 2px 6px rgba(0,0,0,0.08);'>
      <div style='font-weight:600; font-size:1.1rem; color:#274b7a;'>🏁 Weekend Parade Comparison</div>
      <div style='font-size:0.8rem; color:#475569; margin-top:2px;'>Compare two cities for the upcoming weekend.</div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("compare_form"):
        col_a, col_b, col_day = st.columns([1,1,0.6])
        with col_a:
            city_a = st.text_input("City A", value=city or "")
        with col_b:
            city_b = st.text_input("City B", value="")
        with col_day:
            day_choice = st.selectbox("Day", ["Saturday","Sunday"], index=0)
        submitted_compare = st.form_submit_button("Compare")
    if submitted_compare:
        target_dt = _next_weekend_day(day_choice)
        rows = []
        errors = []
        for cty in [city_a, city_b]:
            payload, err = compute_city_score(cty.strip(), target_dt)
            if payload:
                rows.append(payload)
            else:
                errors.append(f"{cty}: {err}")
        if rows:
            df_cmp = pd.DataFrame(rows).sort_values('Score', ascending=False).reset_index(drop=True)
            # Drop internal fields if present
            internal_cols = [c for c in ['_used_date','_substituted'] if c in df_cmp.columns]
            if internal_cols:
                display_df = df_cmp.drop(columns=internal_cols)
            else:
                display_df = df_cmp
            # Reorder columns for readability
            desired_order = [c for c in ['City','Cond','Score','RainProb(%)','Temp(°C)','Humidity(%)','Wind(m/s)','Rain(mm)','Suggestion'] if c in display_df.columns]
            display_df = display_df[desired_order]
            df_cmp.index = df_cmp.index + 1
            # Color bar for Score
            styled = display_df.style.bar(subset=['Score'], color='#4f8cff').format({
                'Temp(°C)': '{:.1f}', 'Wind(m/s)': '{:.1f}', 'Rain(mm)': '{:.1f}'
            })
            st.markdown(f"**Target Date:** {target_dt} (next {day_choice})")
            st.dataframe(styled, width='stretch')
            leader = df_cmp.iloc[0]
            st.success(f"Best city: {leader['City']} • Score {leader['Score']}/100 – {leader['Suggestion']}")
            # Fallback notice(s)
            subs = [r for r in rows if r.get('_substituted')]
            if subs:
                parts = [f"{r['City']}→{r['_used_date']}" for r in subs]
                st.info("Forecast fallback used (nearest available date): " + ", ".join(parts))
            # AI comparison summary
            if is_openai_configured():
                try:
                    comp_prompt = "Compare these cities for a weekend outdoor parade and give pros and cons then a recommendation.\n" + df_cmp.to_csv(index=False)
                    ai_cmp = oa_answer("Which city is better and why?", comp_prompt)
                    st.session_state['compare_ai_summary'] = ai_cmp
                except Exception as e:
                    st.warning(f"AI summary failed: {e}")
            if st.session_state.get('compare_ai_summary'):
                with st.expander("AI Comparison Summary"):
                    st.write(st.session_state['compare_ai_summary'])
        if errors:
            for e in errors:
                st.warning(e)

# --- Main Logic: Weather, Score, Suggestions ---
if check_weather:
    if not city:
        st.error("⚠️ Please enter a city name")
    else:
        try:
            data = get_forecast(city)
        except Exception as e:
            st.error(f"Weather API error: {e}")
            data = None
        if not data:
            st.error("❌ Failed to fetch data. Check city name or API key.")
        else:
            target_date = date.strftime("%Y-%m-%d")
            try:
                weather, used_date, substituted = process_forecast_with_fallback(data, target_date)
            except Exception as e:
                st.error(f"Forecast processing error: {e}")
                weather = None; used_date = target_date; substituted = False
            if not weather:
                # Differentiate between API empty window vs city not found vs other
                if not data or 'list' not in data:
                    st.error("No forecast entries returned (possible API issue or invalid response).")
                else:
                    st.warning("⚠️ No forecast data available in returned window.")
            else:
                if substituted:
                    st.info(f"Selected date has no forecast points. Showing closest available forecast for {used_date} instead.")
                with cols[1]:
                    # We'll inject summary & share buttons into the same card after computing summary
                    pass
                try:
                    # Use month/year from the used date (fallback aware)
                    used_dt_obj = datetime.datetime.strptime(used_date, "%Y-%m-%d")
                    hist = fetch_nasa_power_monthly_averages(city, used_dt_obj.year, used_dt_obj.month)
                except Exception as e:
                    hist = None
                    st.error(f"NASA POWER error: {e}")
                show_result(city, used_date, weather)
                if hist:
                    rain_prob = 0
                    if weather['total_rain'] > 5:
                        rain_prob = 90
                    elif weather['total_rain'] > 0:
                        rain_prob = 70
                    else:
                        rain_prob = 0
                    wind_speed = weather.get('avg_wind', 10)
                    forecast_input = {
                        'rain_probability': rain_prob,
                        'temp': weather['avg_temp'],
                        'humidity': weather['avg_humidity'],
                        'wind_speed': wind_speed
                    }
                    historical_input = {
                        'avg_rainfall_mm': hist['avg_rainfall_mm'],
                        'avg_temp_c': hist['avg_temperature_c']
                    }
                    result = parade_suitability_score(forecast_input, historical_input)
                    suggestion = get_event_suggestion(forecast_input)
                    render_suitability_card(result['score'], result['message'], suggestion,
                                           condition_emoji=weather.get('condition_emoji'),
                                           condition_desc=weather.get('condition_desc'))
                    # Build AI summary
                    summary = ai_summarize({
                        "temp": weather['avg_temp'],
                        "humidity": weather['avg_humidity'],
                        "wind": weather['avg_wind'],
                        "rain": weather['total_rain']
                    })
                    # Minimal share text: key metrics + single summary line
                    concise_summary = summary  # single summary sentence
                    # Simple share/copy container (no editing, minimal JS)
                    forecast_card = f"""
<style>
    .forecast-simple-card {{ background:#f0f7ff; border-radius:16px; padding:18px 20px 16px; position:relative; box-shadow:0 2px 6px rgba(0,0,0,0.08); }}
    .forecast-actions {{ position:absolute; top:10px; right:10px; display:flex; gap:8px; }}
    .forecast-btn {{ width:36px; height:36px; border:none; border-radius:50%; background:#4f8cff; color:#fff; font-size:15px; cursor:pointer; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.25); }}
    .forecast-btn:hover {{ filter:brightness(1.12); }}
    .forecast-metrics b {{ font-weight:600; }}
    .ai-summary {{ margin-top:8px; font-size:0.9rem; line-height:1.4; }}
</style>
<div class='forecast-simple-card'>
    <div class='forecast-actions'>
         <button id='copyForecast' class='forecast-btn' title='Copy forecast'>📋</button>
         <button id='shareForecast' class='forecast-btn' title='Share forecast'>🔗</button>
    </div>
    <div style='font-weight:600; font-size:1.05rem; margin-bottom:4px;' title='{html.escape(weather.get('condition_desc',''))}'>Today's Forecast {weather.get('condition_emoji','')} {weather.get('condition','')}</div>
    <div class='forecast-metrics' style='font-size:0.85rem; line-height:1.5;'>
         <b>🌡️ Temp:</b> {weather['avg_temp']:.1f}°C &nbsp; | &nbsp;
         <b>💧 Humidity:</b> {weather['avg_humidity']:.0f}% &nbsp; | &nbsp;
         <b>🌬️ Wind:</b> {weather['avg_wind']:.1f} m/s &nbsp; | &nbsp;
         <b>🌧️ Rain:</b> {weather['total_rain']:.1f} mm
    </div>
    <div class='ai-summary' style='margin-top:10px; font-size:0.85rem; line-height:1.35;'>{html.escape(concise_summary)}</div>
</div>
<script>
(function(){{
    const shareText = `Today's Forecast - {city} {target_date}: {weather.get('condition_emoji','')} {weather.get('condition','')} | Temp {weather['avg_temp']:.1f}°C, Humidity {weather['avg_humidity']:.0f}%, Wind {weather['avg_wind']:.1f} m/s, Rain {weather['total_rain']:.1f} mm. Suitability {result['score']}/100 ({suggestion}). {concise_summary}`.trim();
    function fallbackCopy(t){{ const ta=document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); try{{document.execCommand('copy');}}catch(e){{}} document.body.removeChild(ta); }}
    function copy(){{ if(navigator.clipboard){{ navigator.clipboard.writeText(shareText).catch(()=>fallbackCopy(shareText)); }} else fallbackCopy(shareText); }}
    function share(){{ if(navigator.share){{ navigator.share({{text:shareText}}).catch(()=>copy()); }} else copy(); }}
    document.getElementById('copyForecast').onclick=copy;
    document.getElementById('shareForecast').onclick=share;
}})();
</script>
"""
                    with cols[1]:
                        forecast_placeholder.markdown(forecast_card, unsafe_allow_html=True)

                # --- 5-Day Weather Forecast Table ---
                st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>🗓️ 5-Day Weather Forecast</div>", unsafe_allow_html=True)
                forecast_list = data.get("list", [])
                daily = {}
                for entry in forecast_list:
                    date_str = entry["dt_txt"].split()[0]
                    if date_str not in daily:
                        daily[date_str] = {
                            "temps": [], "humidity": [], "wind": [], "rain": [], "conditions": []
                        }
                    daily[date_str]["temps"].append(entry["main"]["temp"])
                    daily[date_str]["humidity"].append(entry["main"]["humidity"])
                    daily[date_str]["wind"].append(entry["wind"]["speed"])
                    rain_val = entry.get("rain", {}).get("3h", 0)
                    daily[date_str]["rain"].append(rain_val)
                    cond_main = (entry.get('weather') or [{}])[0].get('main','Clear')
                    daily[date_str]["conditions"].append(cond_main)
                # Only show next 5 days
                days = list(daily.keys())[:5]
                rows = []
                from utils.helpers import WEATHER_EMOJI_MAP
                for d in days:
                    temps = daily[d]["temps"]
                    humidity = daily[d]["humidity"]
                    wind = daily[d]["wind"]
                    rain = daily[d]["rain"]
                    conds = daily[d]["conditions"]
                    if conds:
                        # pick most frequent
                        freq = {}
                        for c in conds:
                            freq[c] = freq.get(c,0)+1
                        dominant = sorted(freq.items(), key=lambda x: (-x[1], x[0]))[0][0]
                    else:
                        dominant = 'Clear'
                    emoji = WEATHER_EMOJI_MAP.get(dominant, '☀️')
                    rows.append({
                        "Date": d,
                        "Cond": f"{emoji} {dominant}",
                        "Avg Temp (°C)": round(sum(temps)/len(temps), 1),
                        "Avg Humidity (%)": round(sum(humidity)/len(humidity), 1),
                        "Avg Wind (m/s)": round(sum(wind)/len(wind), 1),
                        "Total Rain (mm)": round(sum(rain), 1)
                    })
                df_forecast = pd.DataFrame(rows)
                st.dataframe(df_forecast, width='stretch', hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
            # --- Pollution Stats Section ---
            try:
                pollution_data = get_pollution_stats(city)
                render_pollution_stats(city, pollution_data)
            except Exception as e:
                st.error(f"Pollution API error: {e}")

# --- NASA POWER Historical Monthly Averages Section ---
show_hist, month_hist, year_hist = render_nasa_section(city, date)
if show_hist:
    if not city:
        st.error("⚠️ Please enter a city name")
    else:
        with st.spinner("Fetching NASA POWER data..."):
            try:
                result = fetch_nasa_power_monthly_averages(city, int(year_hist), int(month_hist))
                render_nasa_results(city, month_hist, year_hist, result)
            except Exception as e:
                st.error(f"Failed to fetch NASA POWER data: {e}")

# --- Unified Map Panel ---
render_map_section()

# --- Climate Change Insight Section ---
st.markdown("""
<style>
.climate-card { background:#ffffff; border-radius:18px; padding:1.5rem 1.7rem 1.2rem; box-shadow:0 4px 14px rgba(0,0,0,0.08); margin-top:1.2rem; }
.climate-header { font-size:1.45rem; font-weight:700; color:#274b7a; margin-bottom:0.25rem; }
.climate-sub { font-size:0.85rem; color:#475569; margin-bottom:0.9rem; }
.risk-msg { font-size:0.95rem; font-weight:600; margin-top:0.9rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=3600)
def _climate_multi_year(city_name: str, month: int, start_year: int, end_year: int):
    """Fetch monthly NASA POWER averages for a range of years and aggregate.
    Returns DataFrame with Year, Rainfall(mm/day), Temp(°C) and the averaged metrics."""
    records = []
    for yr in range(start_year, end_year+1):
        try:
            res = fetch_nasa_power_monthly_averages(city_name, yr, month)
            if not res:
                continue
            # Assuming existing helper returns daily average rainfall (mm) and avg temp
            records.append({
                'Year': yr,
                'Rainfall(mm/day)': res.get('avg_rainfall_mm'),
                'Temp(°C)': res.get('avg_temperature_c')
            })
        except Exception:
            continue
    if not records:
        return pd.DataFrame(), None, None
    df = pd.DataFrame(records).dropna()
    if df.empty:
        return df, None, None
    return df, df['Rainfall(mm/day)'].mean(), df['Temp(°C)'].mean()

with st.expander("🌍 Climate Change Insight", expanded=False):
    if not city:
        st.info("Enter a city above to view climate change insight.")
    else:
        insight_month = date.month
        # --- Custom Period Selection ---
        st.markdown("<div style='font-size:0.8rem; color:#475569; margin-bottom:0.4rem;'>Choose historical and recent periods for comparison (min span 5 years, non-overlapping).</div>", unsafe_allow_html=True)
        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        with pcol1:
            hist_start = st.number_input("Hist Start", min_value=1950, max_value=2090, value=1985, step=1)
        with pcol2:
            hist_end = st.number_input("Hist End", min_value=1950, max_value=2090, value=2000, step=1)
        with pcol3:
            recent_start = st.number_input("Recent Start", min_value=1950, max_value=2090, value=2015, step=1)
        with pcol4:
            recent_end = st.number_input("Recent End", min_value=1950, max_value=2090, value=2025, step=1)

        # Validate
        valid = True
        err_msgs = []
        if hist_start > hist_end:
            valid = False; err_msgs.append("Historical start must be <= end")
        if recent_start > recent_end:
            valid = False; err_msgs.append("Recent start must be <= end")
        if (hist_end - hist_start) < 4:
            valid = False; err_msgs.append("Historical span must be at least 5 years")
        if (recent_end - recent_start) < 4:
            valid = False; err_msgs.append("Recent span must be at least 5 years")
        if not (recent_start > hist_end):
            err_msgs.append("Recent period should start after historical period ends to avoid overlap")
        if err_msgs:
            for m in err_msgs:
                st.warning(m)
        if valid and not err_msgs:
            hist_df, hist_rain_avg, hist_temp_avg = _climate_multi_year(city, insight_month, int(hist_start), int(hist_end))
            recent_df, recent_rain_avg, recent_temp_avg = _climate_multi_year(city, insight_month, int(recent_start), int(recent_end))
        else:
            hist_df = recent_df = pd.DataFrame()
        if (hist_df is None or hist_df.empty) or (recent_df is None or recent_df.empty):
            st.warning("Climate data not sufficient for comparison.")
        else:
            # Combine for chart
            chart_df = pd.concat([hist_df, recent_df]).drop_duplicates('Year').sort_values('Year')
            st.markdown(f"<div class='climate-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='climate-header'>Climate Change Insight – {city.title()} (Month: {calendar.month_name[insight_month]})</div>", unsafe_allow_html=True)
            st.markdown("<div class='climate-sub'>Comparison of average monthly precipitation (mm/day) and air temperature (°C) across historical (1985–2000) vs recent (2015–2025) periods.</div>", unsafe_allow_html=True)

            # Anomaly percentages (recent vs historical)
            rain_delta_abs = recent_rain_avg - hist_rain_avg
            rain_delta_pct = (rain_delta_abs / hist_rain_avg * 100) if hist_rain_avg else 0
            temp_delta_abs = recent_temp_avg - hist_temp_avg
            temp_delta_pct = (temp_delta_abs / hist_temp_avg * 100) if hist_temp_avg else 0

            period_label_hist = f"{int(hist_start)}–{int(hist_end)}"
            period_label_recent = f"{int(recent_start)}–{int(recent_end)}"
            colA, colB, colC, colD = st.columns(4)
            colA.metric(f"{period_label_hist} Rain", f"{hist_rain_avg:.2f} mm/d")
            colB.metric(f"{period_label_recent} Rain", f"{recent_rain_avg:.2f} mm/d", delta=f"{rain_delta_abs:+.2f} ({rain_delta_pct:+.1f}%)")
            colC.metric(f"{period_label_hist} Temp", f"{hist_temp_avg:.1f} °C")
            colD.metric(f"{period_label_recent} Temp", f"{recent_temp_avg:.1f} °C", delta=f"{temp_delta_abs:+.1f} ({temp_delta_pct:+.1f}%)")

            # Risk evaluation based on rainfall + temp change
            rain_change_ratio = (recent_rain_avg - hist_rain_avg) / hist_rain_avg if hist_rain_avg else 0
            temp_change = recent_temp_avg - hist_temp_avg if hist_temp_avg else 0
            if rain_change_ratio > 0.5:
                risk_note = f"🚨 Rainfall increased by {rain_change_ratio*100:.0f}%; higher precipitation risk for events."
            elif rain_change_ratio < -0.2:
                risk_note = f"🌿 Rainfall decreased by {abs(rain_change_ratio)*100:.0f}%; slightly lower rain risk."
            else:
                risk_note = "✅ Rainfall change is moderate." 
            if temp_change > 1.5:
                temp_note = f"🔥 Temp up {temp_change:.1f}°C – added heat stress potential."
            elif temp_change < -1:
                temp_note = f"❄️ Temp down {abs(temp_change):.1f}°C – cooler conditions trend." 
            else:
                temp_note = "🌡️ Temperature shift modest." 
            st.markdown(f"<div class='risk-msg'>{risk_note}<br>{temp_note}</div>", unsafe_allow_html=True)

            # Confidence: years actually fetched vs expected span
            expected_hist_years = (int(hist_end) - int(hist_start) + 1)
            expected_recent_years = (int(recent_end) - int(recent_start) + 1)
            actual_hist_years = len(hist_df)
            actual_recent_years = len(recent_df)
            def conf_label(actual, expected):
                if expected == 0:
                    return "n/a"
                ratio = actual / expected
                if ratio >= 0.8:
                    return "High"
                if ratio >= 0.5:
                    return "Moderate"
                return "Low"
            confidence_overall = min(actual_hist_years/expected_hist_years if expected_hist_years else 0,
                                      actual_recent_years/expected_recent_years if expected_recent_years else 0)
            qual = "High" if confidence_overall >= 0.8 else ("Moderate" if confidence_overall >= 0.5 else "Low")
            st.caption(f"Data Confidence: {qual} (Hist {actual_hist_years}/{expected_hist_years} yrs; Recent {actual_recent_years}/{expected_recent_years} yrs)")

            # Dual-axis Plotly chart
            try:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Bar(x=chart_df['Year'], y=chart_df['Rainfall(mm/day)'], name='Rainfall (mm/day)', marker_color='#4f8cff', yaxis='y'))
                fig.add_trace(go.Scatter(x=chart_df['Year'], y=chart_df['Temp(°C)'], name='Temp (°C)', mode='lines+markers', line=dict(color='#ff7f0e', width=2), yaxis='y2'))
                fig.update_layout(
                    height=320,
                    margin=dict(l=50,r=50,t=30,b=40),
                    legend=dict(orientation='h', y=-0.2),
                    barmode='group',
                    template='plotly_white',
                    xaxis=dict(title='Year', tickmode='linear', dtick=2),
                    yaxis=dict(title='Rainfall (mm/day)', showgrid=True, gridcolor='#e2e8f0'),
                    yaxis2=dict(title='Temperature (°C)', overlaying='y', side='right')
                )
                st.plotly_chart(fig, width='stretch')
            except Exception as e:
                st.warning(f"Plotly chart error: {e}")
            # AI Climate Commentary
            if 'climate_ai_comment' not in st.session_state:
                st.session_state['climate_ai_comment'] = None
            ai_cols = st.columns([1,3])
            with ai_cols[0]:
                if is_openai_configured() and st.button("AI Commentary", help="Generate AI summary of climate trends"):
                    try:
                        # Build concise CSV-like context
                        sample_tail = chart_df.tail(10)
                        ctx = sample_tail.to_csv(index=False)
                        prompt = textwrap.dedent(f"""
                        Provide a concise (<=120 words) climate trend commentary for {city.title()} for month {calendar.month_name[insight_month]}. Highlight rainfall and temperature direction, magnitude (% and °C), and event planning implications. Data confidence is {qual}. Data (recent vs historical):\nRain delta {rain_delta_abs:+.2f} mm/day ({rain_delta_pct:+.1f}%), Temp delta {temp_delta_abs:+.1f} °C ({temp_delta_pct:+.1f}%).\nRecent period {period_label_recent} vs historical {period_label_hist}.\nRecent tail data:\n{ctx}
                        """)
                        ai_resp = oa_answer("Climate trend commentary", prompt)
                        st.session_state['climate_ai_comment'] = ai_resp
                    except Exception as e:
                        st.warning(f"AI commentary failed: {e}")
            if st.session_state.get('climate_ai_comment'):
                st.markdown(f"<div style='margin-top:0.5rem; padding:0.75rem 0.9rem; background:#f1f5f9; border-radius:12px; font-size:0.8rem; line-height:1.35;'><b>AI Climate Commentary:</b><br>{html.escape(st.session_state['climate_ai_comment'])}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# --- Floating Chat FAB ---
fab_container = st.container()
fab_html = """
<button class='chat-fab' onclick="window.parent.postMessage({type:'chat_toggle'}, '*')">💬</button>
<script>
window.addEventListener('message', (e)=>{ if(e.data && e.data.type==='chat_toggle_py'){ window.parent.postMessage({type:'chat_toggle'}, '*'); } });
// Use Streamlit custom event via iframe workaround not available; rely on query params fallback if needed.
</script>
"""
st.markdown(fab_html, unsafe_allow_html=True)

# Workaround: Use a button element rendered via empty placeholder to toggle (since JS can't call Python directly here)
toggle_col = st.empty()
if toggle_col.button("", key="hidden_toggle_button", help="internal", on_click=lambda: st.session_state.update(show_chat=not st.session_state['show_chat'])):
    pass

# Display chat panel if toggled
if st.session_state['show_chat']:
    with st.container():
        st.markdown("<div class='chat-panel'>", unsafe_allow_html=True)
        on = is_openai_configured()
        badge = f"<span style='background:{'#16a34a' if on else '#64748b'}; color:#fff; padding:2px 8px; border-radius:12px; font-size:0.65rem; font-weight:600;'>{'AI OpenAI' if on else 'AI OFF'}</span>"
        st.markdown(f"""
            <div class='chat-header'>AI Weather Assistant {badge}
                <span class='chat-close' onClick=\"window.parent.postMessage({{type:'chat_toggle_py'}},'*')\">✕</span>
            </div>
            <div style='font-size:0.70rem; margin-bottom:4px; color:#475569;'>
                Ask about current or upcoming weather. Examples:
                <em>'Rain tomorrow in London?'</em> • <em>'Compare temp Delhi vs Mumbai'</em>
            </div>
            """, unsafe_allow_html=True)
        if not on:
            st.warning("OpenAI not configured. Add OPENAI_API_KEY to .streamlit/secrets.toml")
        # Messages
        msgs_html = [f"<div class='chat-msg-{m['role']}'>{m['text']}</div>" for m in st.session_state['chat_messages']]
        st.markdown(f"<div class='chat-messages'>{''.join(msgs_html) if msgs_html else '<div style=\"font-size:0.75rem;color:#64748b;\">No messages yet. Ask a weather question.</div>'}</div>", unsafe_allow_html=True)
        with st.form(key='chat_form', clear_on_submit=True):
            user_q = st.text_area("Your question", height=70, key='chat_input')
            submitted = st.form_submit_button("Send")
        if submitted and user_q.strip():
            st.session_state['chat_messages'].append({'role':'user','text': user_q.strip()})
            ctx_parts = []
            if 'weather' in locals() and weather:
                ctx_parts.append(f"Forecast target date metrics: temp {weather['avg_temp']:.1f}C, humidity {weather['avg_humidity']:.0f}%, wind {weather['avg_wind']:.1f} m/s, rain {weather['total_rain']:.1f} mm")
            if city:
                ctx_parts.append(f"Current selected city: {city}")
            context = " | ".join(ctx_parts)
            answer = ai_answer(user_q.strip(), context=context)
            st.session_state['chat_messages'].append({'role':'bot','text': answer})
            try:
                st.rerun()
            except AttributeError:
                if hasattr(st, 'experimental_rerun'):
                    st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
