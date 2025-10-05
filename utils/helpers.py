# utils/helpers.py
WEATHER_EMOJI_MAP = {
    # day variants
    ('Clear','day'): '☀️',
    ('Clear','night'): '🌕',
    ('Clouds','day'): '☁️',
    ('Clouds','night'): '☁️',
    ('Rain','day'): '🌧️',
    ('Rain','night'): '🌧️',
    ('Drizzle','day'): '🌦️',
    ('Drizzle','night'): '�️',
    ('Thunderstorm','day'): '⛈️',
    ('Thunderstorm','night'): '⛈️',
    ('Snow','day'): '❄️',
    ('Snow','night'): '❄️',
    ('Mist','day'): '🌫️',
    ('Mist','night'): '🌫️',
    ('Smoke','day'): '🌫️',
    ('Smoke','night'): '🌫️',
    ('Haze','day'): '🌫️',
    ('Haze','night'): '🌫️',
    ('Dust','day'): '🌫️',
    ('Dust','night'): '🌫️',
    ('Fog','day'): '🌫️',
    ('Fog','night'): '🌫️',
    ('Sand','day'): '🌫️',
    ('Sand','night'): '🌫️',
    ('Ash','day'): '🌫️',
    ('Ash','night'): '🌫️',
    ('Squall','day'): '💨',
    ('Squall','night'): '💨',
    ('Tornado','day'): '🌪️',
    ('Tornado','night'): '🌪️'
}

def process_forecast(data, target_date: str):
    """Filter forecasts for the target date and compute averages.
    Adds a dominant condition and emoji chosen by frequency; falls back to first entry.
    """
    forecasts = [f for f in data["list"] if f["dt_txt"].startswith(target_date)]

    if not forecasts:
        return None

    temps = [f["main"]["temp"] for f in forecasts]
    humidity = [f["main"]["humidity"] for f in forecasts]
    wind = [f["wind"]["speed"] for f in forecasts]

    rain_chances = []
    for f in forecasts:
        if "rain" in f and "3h" in f["rain"]:
            rain_chances.append(f["rain"]["3h"])
        else:
            rain_chances.append(0)

    avg_temp = sum(temps) / len(temps)
    avg_humidity = sum(humidity) / len(humidity)
    avg_wind = sum(wind) / len(wind)
    total_rain = sum(rain_chances)

    # Determine dominant weather condition by frequency of 'weather[0]["main"]'
    cond_counts = {}
    details = []
    for f in forecasts:
        w = (f.get('weather') or [{}])[0]
        main = w.get('main', 'Clear')
        desc = w.get('description', main)
        icon = w.get('icon', '')  # e.g., 10d, 01n
        is_day = icon.endswith('d') if icon else True
        cond_counts[main] = cond_counts.get(main, 0) + 1
        details.append((main, desc, 'day' if is_day else 'night'))
    if cond_counts:
        dominant = sorted(cond_counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
    else:
        dominant = 'Clear'
    # Pick first detail matching dominant for description & day/night
    chosen_desc = dominant
    dayphase = 'day'
    for m, desc, phase in details:
        if m == dominant:
            chosen_desc = desc
            dayphase = phase
            break
    emoji = WEATHER_EMOJI_MAP.get((dominant, dayphase), '☀️')

    return {
        "avg_temp": avg_temp,
        "avg_humidity": avg_humidity,
        "avg_wind": avg_wind,
        "total_rain": total_rain,
        "condition": dominant,
        "condition_emoji": emoji,
        "condition_desc": chosen_desc,
        "condition_dayphase": dayphase,
    }

def closest_forecast_day(data, target_date: str):
    """Return the date string (YYYY-MM-DD) from forecast data closest to target_date.
    Assumes data is OpenWeather 5-day / 3-hour forecast. If target_date present, returns it.
    If no data or list missing, returns None.
    """
    from datetime import datetime
    if not data or 'list' not in data or not data['list']:
        return None
    days = sorted({ item['dt_txt'].split()[0] for item in data['list'] })
    if target_date in days:
        return target_date
    try:
        tgt = datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        return None
    # compute absolute time delta in seconds between midday of each day and target
    best = None
    best_delta = None
    for d in days:
        try:
            cur = datetime.strptime(d, '%Y-%m-%d')
        except ValueError:
            continue
        delta = abs((cur - tgt).total_seconds())
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = d
    return best

def process_forecast_with_fallback(data, target_date: str):
    """Try processing forecast for target_date; if unavailable, fallback to nearest available date.
    Returns tuple: (result_dict or None, used_date or None, substituted: bool)
    """
    primary = process_forecast(data, target_date)
    if primary is not None:
        return primary, target_date, False
    closest = closest_forecast_day(data, target_date)
    if closest is None or closest == target_date:
        return None, target_date, False
    fallback = process_forecast(data, closest)
    return fallback, closest, True
