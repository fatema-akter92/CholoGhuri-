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
