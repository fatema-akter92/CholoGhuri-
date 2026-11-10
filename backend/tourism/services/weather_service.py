from datetime import datetime
import requests
from tourism.models import Place

WMO_CODES = {
    0: ("Clear Sky", "Sunny"),
    1: ("Mainly Clear", "Sunny"),
    2: ("Partly Cloudy", "Partly Cloudy"),
    3: ("Overcast", "Cloudy"),
    45: ("Morning Fog / Mist", "Misty"),
    48: ("Dense Fog", "Misty"),
    51: ("Light Drizzle", "Drizzle"),
    53: ("Moderate Drizzle", "Drizzle"),
    55: ("Dense Drizzle", "Rain"),
    61: ("Light Rain", "Rain"),
    63: ("Moderate Rain", "Rain"),
    65: ("Heavy Rain", "Heavy Rain"),
    80: ("Rain Showers", "Showers"),
    81: ("Moderate Showers", "Showers"),
    82: ("Heavy Rain Showers", "Heavy Rain"),
    95: ("Thunderstorm", "Storm"),
    96: ("Thunderstorm with Hail", "Storm"),
}


def _current_bd_season():
    month = datetime.now().month
    if month in (11, 12, 1, 2):
        return "winter", "Peak Tourism Season (Cool, Dry & Ideal Visibility)"
    if month in (6, 7, 8, 9, 10):
        return "monsoon", "Monsoon / Lush Green Season (Carry Rain Gear; Check Sea Advisories)"
    return "summer", "Warm Pre-Monsoon Season (Start Sightseeing Early Morning)"


def get_destination_weather(place: Place):
    season_key, season_label = _current_bd_season()
    seasonal_map = place.seasonal_suitability or {"winter": 90, "summer": 70, "monsoon": 55}
    base_season_score = int(seasonal_map.get(season_key, 75))

    live_data = None
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place.latitude,
                "longitude": place.longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,weathercode,windspeed_10m",
                "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,windspeed_10m_max",
                "forecast_days": 5,
                "timezone": "Asia/Dhaka",
            },
            timeout=4,
        )
        if resp.status_code == 200:
            live_data = resp.json()
    except Exception:
        live_data = None

    if live_data and "current" in live_data:
        curr = live_data["current"]
        code = int(curr.get("weathercode", 1))
        desc, short = WMO_CODES.get(code, ("Partly Cloudy", "Partly Cloudy"))
        temp_c = round(float(curr.get("temperature_2m", 28)), 1)
        humidity = int(curr.get("relative_humidity_2m", 72))
        wind = round(float(curr.get("windspeed_10m", 10)), 1)
        precip = round(float(curr.get("precipitation", 0)), 1)

        daily = live_data.get("daily", {})
        forecast = []
        dates = daily.get("time", [])
        for idx, day_str in enumerate(dates):
            d_code = int((daily.get("weathercode") or [1])[idx])
            d_desc, d_short = WMO_CODES.get(d_code, ("Clear", "Clear"))
            forecast.append({
                "date": day_str,
                "condition": d_desc,
                "short": d_short,
                "temp_max": round(float((daily.get("temperature_2m_max") or [30])[idx]), 1),
                "temp_min": round(float((daily.get("temperature_2m_min") or [22])[idx]), 1),
                "rain_mm": round(float((daily.get("precipitation_sum") or [0])[idx]), 1),
                "rain_prob": int((daily.get("precipitation_probability_max") or [10])[idx] or 0),
            })
        source = "Open-Meteo Live Weather API"
    else:
        # Clean deterministic seasonal fallback if API unreachable offline
        defaults = {
            "winter": (24.5, 62, 8.5, 0.0, "Clear & Pleasant", "Sunny"),
            "summer": (33.0, 74, 14.0, 1.2, "Warm & Partly Cloudy", "Partly Cloudy"),
            "monsoon": (29.5, 86, 18.0, 14.5, "Monsoon Showers", "Rain"),
        }
        temp_c, humidity, wind, precip, desc, short = defaults[season_key]
        forecast = [
            {
                "date": f"Day {i + 1}",
                "condition": desc,
                "short": short,
                "temp_max": round(temp_c + 2.0 - (i * 0.3), 1),
                "temp_min": round(temp_c - 6.0, 1),
                "rain_mm": precip,
                "rain_prob": 70 if season_key == "monsoon" else 15,
            }
            for i in range(5)
        ]
        source = "CholoGhuri Seasonal Climate Baseline (Offline Fallback)"

    is_rainy = precip >= 3.0 or any(tag in short.lower() for tag in ("rain", "storm", "showers"))
    is_windy = wind >= 32.0

    # Calculate outdoor suitability
    suitability = base_season_score
    if is_rainy and not place.is_indoor_friendly:
        suitability = max(25, suitability - 38)
    if is_windy and "sea" in (place.interests or []):
        suitability = max(20, suitability - 30)
    suitability = min(99, max(15, suitability))

    alerts = []
    if is_rainy:
        alerts.append(
            f"Rain expected around {place.name}. Outdoor trails, hills, or boat crossings may experience delays."
        )
    if is_windy or (season_key == "monsoon" and "sea" in (place.interests or [])):
        alerts.append(
            "Coastal wind/swell advisory: Verify BIWTA / Coast Guard ferry clearance before island or sea crossings."
        )
    if temp_c >= 34:
        alerts.append("High afternoon heat: Schedule outdoor walking before 10:30 AM or after 3:30 PM.")
    if place.seasonal_restrictions:
        alerts.append(f"Seasonal Notice: {place.seasonal_restrictions}")

    # Suggest rainy-day / indoor-friendly alternatives in same division or Dhaka
    alt_qs = Place.objects.filter(is_indoor_friendly=True).exclude(id=place.id)
    local_alts = alt_qs.filter(division=place.division)
    alternatives_src = list(local_alts[:3]) if local_alts.exists() else list(alt_qs[:3])
    rainy_alternatives = [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "division": p.division,
            "district": p.district,
            "category": p.category.name,
            "image_url": p.image_url,
            "note": p.rainy_day_alternative_note or f"Great sheltered or culinary option in {p.district}.",
        }
        for p in alternatives_src
    ]

    itinerary_update = (
        f"Swap open-air daytime excursions for {rainy_alternatives[0]['name']} or local culinary spots if heavy showers start."
        if (is_rainy and rainy_alternatives)
        else f"Weather looks favorable for {place.name}. Best window: morning light and late afternoon."
    )

    return {
        "place": {"id": place.id, "name": place.name, "slug": place.slug, "district": place.district},
        "source": source,
        "season": {"key": season_key, "label": season_label},
        "current": {
            "temperature_c": temp_c,
            "humidity_pct": humidity,
            "wind_kmh": wind,
            "precipitation_mm": precip,
            "condition": desc,
            "short": short,
        },
        "outdoor_suitability_score": suitability,
        "outdoor_verdict": (
            "Ideal Outdoor Conditions"
            if suitability >= 75
            else "Moderate — Plan Flexibly"
            if suitability >= 50
            else "Challenging Outdoors — Indoor / Cultural Backup Advised"
        ),
        "alerts": alerts,
        "itinerary_update_suggestion": itinerary_update,
        "forecast": forecast,
        "rainy_day_alternatives": rainy_alternatives,
    }
