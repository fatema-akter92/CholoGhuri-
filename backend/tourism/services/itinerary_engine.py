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
            score += 2.0
        if p.is_featured_hero:
            score += 3.0

        scored.append((score, p))

    scored.sort(key=lambda x: -x[0])

    # Choose top destinations proportioned to trip length, ensuring category diversity
    selected = []
    used_slugs = set()
    used_divs = {}
    target_places = 2 if duration_days < 1 else min(len(all_places), max(2, days_count + 1))

    for _, p in scored:
        if p.slug in used_slugs:
            continue
        if len(selected) >= target_places:
            break
        # Keep regional flow sensible on multi-day trips
        if days_count <= 2 and used_divs and p.division not in used_divs and len(selected) >= 1:
            if haversine_km(selected[0].latitude, selected[0].longitude, p.latitude, p.longitude) > 180:
                continue
        selected.append(p)
        used_slugs.add(p.slug)
        used_divs[p.division] = used_divs.get(p.division, 0) + 1

    if not selected:
        selected = [p for _, p in scored[:3]]

    # Group into day-by-day schedule
    itinerary = []
    tier_hotel_cost = {"low": 1600, "mid": 4200, "luxury": 10500}.get(budget_tier, 4200)
    tier_food_cost = {"low": 700, "mid": 1400, "luxury": 3000}.get(budget_tier, 1400)
    tier_transport_base = {"low": 900, "mid": 2000, "luxury": 4500}.get(budget_tier, 2000)

    # Scale gently if user entered an exact BDT budget
    raw_est = days_count * (tier_hotel_cost + tier_food_cost + tier_transport_base)
    scale = 1.0
    if budget_bdt > 0 and raw_est > budget_bdt:
        scale = max(0.45, (budget_bdt * 0.92) / raw_est)

    total_transport = 0
    total_hotel = 0
    total_food = 0
    total_entry = 0

    for d_idx in range(days_count):
