import math
import requests
from tourism.models import Hotel, Place, Restaurant, SafetyFacility

STARTING_HUBS = {
    "Dhaka": (23.8103, 90.4125),
    "Hazrat Shahjalal Airport (DAC)": (23.8433, 90.3978),
    "Chattogram": (22.3569, 91.7832),
    "Sylhet": (24.8949, 91.8687),
    "Cox's Bazar": (21.4272, 92.0058),
    "Khulna": (22.8456, 89.5403),
    "Rajshahi": (24.3745, 88.6042),
    "Barishal": (22.7010, 90.3535),
    "Rangpur": (25.7439, 89.2752),
    "Bogura": (24.8465, 89.3773),
    "Cumilla": (23.4607, 91.1809),
    "Sreemangal": (24.3065, 91.7296),
    "Bandarban": (22.1953, 92.2184),
    "Rangamati": (22.6533, 92.1789),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def _format_duration(hours: float) -> str:
    hrs = int(hours)
    mins = int(round((hours - hrs) * 60))
    if mins == 60:
        hrs += 1
        mins = 0
    if hrs == 0:
        return f"{mins} mins"
    return f"{hrs}h {mins}m" if mins else f"{hrs}h"


def calculate_route(start_name: str, destination: Place):
    start_coords = STARTING_HUBS.get(start_name)
    if not start_coords:
        start_place = Place.objects.filter(name__iexact=start_name).first()
        if start_place:
            start_coords = (start_place.latitude, start_place.longitude)
        else:
            start_name = "Dhaka"
            start_coords = STARTING_HUBS["Dhaka"]

    s_lat, s_lon = start_coords
    d_lat, d_lon = destination.latitude, destination.longitude
    straight_km = haversine_km(s_lat, s_lon, d_lat, d_lon)

    route_geometry = [[s_lat, s_lon], [d_lat, d_lon]]
    road_km = round(max(1.5, straight_km * 1.32), 1)
    osrm_used = False

    if straight_km > 0.5:
        try:
            url = (
                f"https://router.project-osrm.org/route/v1/driving/"
                f"{s_lon},{s_lat};{d_lon},{d_lat}?overview=full&geometries=geojson"
            )
            r = requests.get(url, timeout=4)
            if r.status_code == 200:
                routes = r.json().get("routes") or []
                if routes:
                    road_km = round(routes[0]["distance"] / 1000.0, 1)
                    coords = routes[0]["geometry"]["coordinates"]
                    # GeoJSON uses [lon, lat]; Leaflet prefers [lat, lon]
                    route_geometry = [[c[1], c[0]] for c in coords]
                    osrm_used = True
        except Exception:
            pass

    # Realistic Bangladesh transport options
    transport_options = []
    if road_km <= 25:
        transport_options.append({
            "mode": "CNG Auto-Rickshaw / Ride-Share",
            "estimated_time": _format_duration(max(0.25, road_km / 22.0)),
            "estimated_fare_bdt": f"৳{int(max(120, road_km * 35))} – ৳{int(max(200, road_km * 55))}",
            "notes": "Fastest door-to-door urban transfer; confirm fare or use meter/app.",
        })
        transport_options.append({
            "mode": "Rickshaw / Local E-Bike",
            "estimated_time": _format_duration(max(0.3, road_km / 14.0)),
            "estimated_fare_bdt": f"৳{int(max(60, road_km * 20))} – ৳{int(max(120, road_km * 32))}",
            "notes": "Ideal for Old Dhaka lanes and short intra-city hops.",
        })
    else:
        transport_options.append({
            "mode": "AC / Sleeper Highway Coach (Green Line, Hanif, Shohagh)",
            "estimated_time": _format_duration(road_km / 46.0),
            "estimated_fare_bdt": f"৳{int(max(450, road_km * 3.2))} – ৳{int(max(900, road_km * 5.2))}",
            "notes": "Comfortable inter-district highway travel with online seat booking.",
        })
        if destination.division in ("Sylhet", "Chattogram", "Rajshahi", "Khulna", "Rangpur"):
            transport_options.append({
                "mode": "Bangladesh Railway Intercity Train",
                "estimated_time": _format_duration(road_km / 52.0),
                "estimated_fare_bdt": f"৳{int(max(300, road_km * 1.9))} – ৳{int(max(700, road_km * 3.8))}",
                "notes": "Scenic & reliable; book Shovan Chair or Snigdha via Rail Sheba.",
            })
        if road_km > 220 and destination.district in ("Cox's Bazar", "Sylhet", "Chattogram", "Jashore", "Dinajpur"):
            transport_options.append({
                "mode": "Domestic Flight + Local Transfer",
                "estimated_time": "1h 15m flight + local transfer",
                "estimated_fare_bdt": "৳4,500 – ৳8,500",
                "notes": "Operated daily from Dhaka (DAC) by Biman, US-Bangla, and Novoair.",
            })
        if "Saint Martin" in destination.name:
            transport_options.append({
                "mode": "Teknaf / Cox's Bazar Tourist Ship",
                "estimated_time": "2h 30m sea crossing (seasonal)",
                "estimated_fare_bdt": "৳1,000 – ৳2,500",
                "notes": "Operates primarily Nov–Mar subject to coastal weather & conservation caps.",
            })

    # Nearby hotels, restaurants & safety facilities
    hotels = []
    for h in Hotel.objects.all():
        dist = haversine_km(d_lat, d_lon, h.latitude, h.longitude)
        if dist <= 65 or h.place_id == destination.id or h.city.lower() == destination.district.lower():
            hotels.append({
                "id": h.id,
                "name": h.name,
                "city": h.city,
                "tier": h.tier,
                "price_per_night_bdt": h.price_per_night_bdt,
                "rating": h.rating,
                "distance_km": dist,
                "latitude": h.latitude,
                "longitude": h.longitude,
            })
    hotels.sort(key=lambda x: x["distance_km"])

    restaurants = []
    for r in Restaurant.objects.all():
        dist = haversine_km(d_lat, d_lon, r.latitude, r.longitude)
        if dist <= 65 or r.place_id == destination.id or r.city.lower() == destination.district.lower():
            restaurants.append({
                "id": r.id,
                "name": r.name,
                "city": r.city,
                "cuisine_type": r.cuisine_type,
                "avg_meal_bdt": r.avg_meal_bdt,
                "rating": r.rating,
                "is_halal_verified": r.is_halal_verified,
                "is_vegetarian_friendly": r.is_vegetarian_friendly,
                "distance_km": dist,
                "latitude": r.latitude,
                "longitude": r.longitude,
            })
    restaurants.sort(key=lambda x: x["distance_km"])

    safety = []
    for s in SafetyFacility.objects.all():
        dist = haversine_km(d_lat, d_lon, s.latitude, s.longitude)
        if dist <= 85 or s.place_id == destination.id or s.division == destination.division:
            safety.append({
                "id": s.id,
                "name": s.name,
                "facility_type": s.facility_type,
                "facility_label": s.get_facility_type_display(),
                "phone": s.phone,
                "address": s.address,
                "emergency_24h": s.emergency_24h,
                "distance_km": dist,
                "latitude": s.latitude,
                "longitude": s.longitude,
            })
    safety.sort(key=lambda x: x["distance_km"])

    return {
        "start": {"name": start_name, "latitude": s_lat, "longitude": s_lon},
        "destination": {
            "id": destination.id,
            "name": destination.name,
            "slug": destination.slug,
            "district": destination.district,
            "division": destination.division,
            "latitude": d_lat,
            "longitude": d_lon,
            "image_url": destination.image_url,
        },
        "straight_distance_km": straight_km,
        "road_distance_km": road_km,
        "estimated_drive_time": _format_duration(road_km / 45.0),
        "routing_source": "OSRM Road Network" if osrm_used else "CholoGhuri Geodesic Highway Estimator",
        "route_geometry": route_geometry,
        "transport_options": transport_options,
        "nearby_hotels": hotels[:5],
        "nearby_restaurants": restaurants[:5],
        "nearby_safety": safety[:6],
    }
