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
        primary_place = selected[d_idx % len(selected)]
        # Pick nearby/secondary place in same division if available
        secondary_place = next(
            (
                p
                for p in selected
                if p.id != primary_place.id and p.division == primary_place.division
            ),
            None,
        )

        # Match hotel & restaurant near primary place
        day_hotel = next(
            (h for h in hotels if h.place_id == primary_place.id and h.tier == budget_tier),
            next((h for h in hotels if h.division == primary_place.division), hotels[0] if hotels else None),
        )
        day_rest = next(
            (r for r in restaurants if r.place_id == primary_place.id),
            next((r for r in restaurants if r.division == primary_place.division), restaurants[0] if restaurants else None),
        )

        h_cost = 0 if duration_days < 1 else int((day_hotel.price_per_night_bdt if day_hotel else tier_hotel_cost) * scale)
        f_cost = int(((day_rest.avg_meal_bdt * 2.5) if day_rest else tier_food_cost) * scale)
        t_cost = int(tier_transport_base * scale)
        e_cost = primary_place.entry_fee_bdt + (secondary_place.entry_fee_bdt if secondary_place else 0)

        total_hotel += h_cost
        total_food += f_cost
        total_transport += t_cost
        total_entry += e_cost

        slots = [
            {
                "time": "08:30 AM – 12:30 PM",
                "activity": f"Explore {primary_place.name} ({primary_place.district})",
                "details": primary_place.tagline or primary_place.description[:140],
                "place_slug": primary_place.slug,
                "place_id": primary_place.id,
            },
            {
                "time": "01:00 PM – 02:30 PM",
                "activity": f"Local Culinary Stop at {day_rest.name if day_rest else 'Regional Kitchen'}",
                "details": (
                    f"Must try: {', '.join(day_rest.menu_highlights[:2])}"
                    if day_rest and day_rest.menu_highlights
                    else f"Authentic regional dining in {primary_place.district}"
                ),
            },
            {
                "time": "03:00 PM – 06:30 PM",
                "activity": (
                    f"Visit {secondary_place.name}"
                    if secondary_place
                    else f"Sunset & Local Markets around {primary_place.district}"
                ),
                "details": (
                    secondary_place.tagline
                    if secondary_place
                    else (primary_place.travel_tips[0] if primary_place.travel_tips else "Relaxed evening sightseeing.")
                ),
                "place_slug": secondary_place.slug if secondary_place else primary_place.slug,
            },
        ]

        if duration_days < 1:
            slots = slots[:2]

        itinerary.append({
            "day": d_idx + 1,
            "title": f"Day {d_idx + 1}: {primary_place.district} & {primary_place.name}",
            "division": primary_place.division,
            "destination": {
                "id": primary_place.id,
                "name": primary_place.name,
                "slug": primary_place.slug,
                "image_url": primary_place.image_url,
                "safety_tip": (primary_place.safety_tips[0] if primary_place.safety_tips else "Keep hydration & ID handy."),
            },
            "hotel": (
                {
                    "id": day_hotel.id,
                    "name": day_hotel.name,
                    "tier": day_hotel.tier,
                    "price_per_night_bdt": day_hotel.price_per_night_bdt,
                }
                if (day_hotel and duration_days >= 1)
                else None
            ),
            "restaurant": (
                {
                    "id": day_rest.id,
                    "name": day_rest.name,
                    "cuisine_type": day_rest.cuisine_type,
                    "avg_meal_bdt": day_rest.avg_meal_bdt,
                }
                if day_rest
                else None
            ),
            "estimated_day_cost_bdt": h_cost + f_cost + t_cost + e_cost,
            "rainy_backup": primary_place.rainy_day_alternative_note
            or "Switch to indoor heritage museums or local tea/food trails if rain intensifies.",
            "slots": slots,
        })

    total_est = total_transport + total_hotel + total_food + total_entry
    breakdown = {
        "transport_bdt": total_transport,
        "hotel_bdt": total_hotel,
        "food_bdt": total_food,
        "entry_fees_bdt": total_entry,
        "total_bdt": total_est,
        "target_budget_bdt": budget_bdt,
        "within_budget": total_est <= budget_bdt if budget_bdt else True,
    }

    weather_notes = (
        "Weather-Aware Mode Active: Check live forecast 24h before coastal/hill travel. "
        "Indoor heritage backups are included for every day."
        if weather_aware
        else "Standard clear-season pacing applied."
    )

    return {
        "title": f"{duration_label.title()} Bangladesh Smart Trip from {start_city}",
        "start_city": start_city,
        "duration_days": duration_days,
        "duration_label": duration_label,
        "budget_bdt": budget_bdt,
        "budget_tier": budget_tier,
        "traveler_type": traveler_type,
        "interests": interests,
        "recommended_places": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "district": p.district,
                "category": p.category.name,
                "image_url": p.image_url,
            }
            for p in selected
        ],
        "itinerary": itinerary,
        "estimated_breakdown": breakdown,
        "weather_notes": weather_notes,
    }
