# utils/helpers.py
def process_forecast(data, target_date: str):
    """Filter forecasts for the target date and compute averages."""
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

    return {
        "avg_temp": avg_temp,
        "avg_humidity": avg_humidity,
        "avg_wind": avg_wind,
        "total_rain": total_rain,
    }
