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
