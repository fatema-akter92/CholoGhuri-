from tourism.models import Hotel, Place, Restaurant
from tourism.services.route_service import haversine_km


def build_smart_itinerary(
    start_city="Dhaka",
    duration_days=5.0,
    duration_label="5 days",
    budget_bdt=30000,
    budget_tier="mid",
    traveler_type="solo",
    interests=None,
    weather_aware=True,
):
    interests = [i.lower() for i in (interests or [])]
    days_count = 1 if duration_days < 1 else int(round(duration_days))

    all_places = list(Place.objects.select_related("category").all())
    hotels = list(Hotel.objects.all())
    restaurants = list(Restaurant.objects.all())

    # Score destinations based on interests, budget tier, traveler type, and duration
    scored = []
    for p in all_places:
        score = p.avg_rating * 2.0
        p_interests = [x.lower() for x in (p.interests or [])]
        cat_lower = p.category.name.lower()

        for intr in interests:
            if intr in p_interests or intr in cat_lower or intr in p.description.lower():
                score += 12.0
            if intr == "nature" and ("hill" in cat_lower or "forest" in cat_lower or "hidden" in cat_lower):
                score += 8.0
            if intr == "sea" and "beach" in cat_lower:
                score += 10.0
            if intr == "historical" and ("historical" in cat_lower or "archaeological" in cat_lower):
                score += 10.0
            if intr == "food" and "food" in cat_lower:
                score += 9.0

        if budget_tier == p.budget_tier:
            score += 4.0
        if duration_days <= 0.6 and p.district.lower() == start_city.lower():
            score += 20.0
        elif duration_days <= 1.0 and haversine_km(23.8103, 90.4125, p.latitude, p.longitude) < 120:
            score += 10.0

        if traveler_type == "family" and p.budget_tier != "low":
