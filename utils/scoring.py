"""
Scoring and event suggestion utilities for Will It Rain On My Parade?
"""

def parade_suitability_score(forecast, historical):
    """
    Calculate a Parade Suitability Score (0-100) and return a message.
    forecast: dict with keys 'rain_probability' (0-100), 'temp' (°C), 'humidity' (%)
    historical: dict with keys 'avg_rainfall_mm', 'avg_temp_c'
    """
    score = 100

    # Rain penalty (up to -50)
    rain_penalty = min(forecast['rain_probability'] * 0.5, 50)
    score -= rain_penalty

    # Temperature penalty (outside 20-32°C, up to -30)
    if forecast['temp'] < 20:
        temp_penalty = min((20 - forecast['temp']) * 2, 30)
    elif forecast['temp'] > 32:
        temp_penalty = min((forecast['temp'] - 32) * 2, 30)
    else:
        temp_penalty = 0
    score -= temp_penalty

    # Historical difference penalty (up to -20)
    temp_diff = abs(forecast['temp'] - historical['avg_temp_c'])
    hist_penalty = min(temp_diff * 2, 20)
    score -= hist_penalty

    # Clamp score between 0 and 100
    score = max(0, min(100, round(score)))

    # Message
    if score > 70:
        message = "Safe for parade 🎉"
    elif score >= 40:
        message = "Caution, keep backup 🌈"
    else:
        message = "Risky, expect issues ☔"

    return {"score": score, "message": message}

def get_event_suggestion(forecast):
    """
    Suggest event type based on weather forecast.
    forecast: dict with keys 'rain_probability' (0-100), 'temp' (°C), 'wind_speed' (km/h)
    Returns: string suggestion
    """
    if forecast['rain_probability'] > 50:
        return "Consider indoor backup ☔🎭"
    if forecast['temp'] > 35:
        return "Better for evening/night events 🌙🎤"
    if forecast['wind_speed'] > 30:
        return "Outdoor risky, try indoor 🎪"
    return "Great for outdoor events 🎶🎉"
