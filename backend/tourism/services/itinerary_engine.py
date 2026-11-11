from tourism.models import Hotel, Place, Restaurant
from tourism.services.route_service import haversine_km

TIER_RATES = {
    "low": {
        "hotel_default": 1700,
        "hotel_min": 1200,
        "hotel_max": 2500,
        "food_default": 680,
        "food_min": 550,
        "food_max": 850,
        "food_mult": 1.8,
        "transport_base": 850,
    },
    "mid": {
        "hotel_default": 4400,
        "hotel_min": 3500,
        "hotel_max": 6000,
        "food_default": 1500,
        "food_min": 1250,
        "food_max": 1950,
        "food_mult": 2.6,
        "transport_base": 1800,
    },
    "luxury": {
        "hotel_default": 12500,
        "hotel_min": 9500,
        "hotel_max": 22000,
        "food_default": 3600,
        "food_min": 3000,
        "food_max": 4800,
        "food_mult": 4.4,
        "transport_base": 4500,
    },
}


def _clamp(val, low_v, high_v):
    return max(low_v, min(high_v, int(round(val))))


def _pick_hotel_for_tier(hotels, primary_place, budget_tier):
    """Select a tier-appropriate hotel so low-cost never receives luxury hotel rates."""
    if not hotels:
        return None
    if budget_tier == "low":
        groups = [
            sorted([h for h in hotels if h.place_id == primary_place.id and h.tier == "low"], key=lambda x: x.price_per_night_bdt),
            sorted([h for h in hotels if h.division == primary_place.division and h.tier == "low"], key=lambda x: x.price_per_night_bdt),
            sorted([h for h in hotels if h.tier == "low"], key=lambda x: x.price_per_night_bdt),
            sorted(hotels, key=lambda x: x.price_per_night_bdt),
        ]
    elif budget_tier == "luxury":
        groups = [
            sorted([h for h in hotels if h.place_id == primary_place.id and h.tier == "luxury"], key=lambda x: -x.price_per_night_bdt),
            sorted([h for h in hotels if h.division == primary_place.division and h.tier == "luxury"], key=lambda x: -x.price_per_night_bdt),
            sorted([h for h in hotels if h.tier == "luxury"], key=lambda x: -x.price_per_night_bdt),
            sorted(hotels, key=lambda x: -x.price_per_night_bdt),
        ]
    else:
        groups = [
            sorted([h for h in hotels if h.place_id == primary_place.id and h.tier == "mid"], key=lambda x: abs(x.price_per_night_bdt - 4500)),
            sorted([h for h in hotels if h.division == primary_place.division and h.tier == "mid"], key=lambda x: abs(x.price_per_night_bdt - 4500)),
            sorted([h for h in hotels if h.tier == "mid"], key=lambda x: abs(x.price_per_night_bdt - 4500)),
            sorted(hotels, key=lambda x: abs(x.price_per_night_bdt - 4500)),
        ]
    for grp in groups:
        if grp:
            return grp[0]
    return hotels[0]


def _pick_restaurant_for_tier(restaurants, primary_place, budget_tier):
    if not restaurants:
        return None
    if budget_tier == "low":
        groups = [
            sorted([r for r in restaurants if r.place_id == primary_place.id], key=lambda x: x.avg_meal_bdt),
            sorted([r for r in restaurants if r.division == primary_place.division], key=lambda x: x.avg_meal_bdt),
            sorted(restaurants, key=lambda x: x.avg_meal_bdt),
        ]
    elif budget_tier == "luxury":
        groups = [
            sorted([r for r in restaurants if r.place_id == primary_place.id], key=lambda x: -x.avg_meal_bdt),
            sorted([r for r in restaurants if r.division == primary_place.division], key=lambda x: -x.avg_meal_bdt),
            sorted(restaurants, key=lambda x: -x.avg_meal_bdt),
        ]
    else:
        groups = [
            [r for r in restaurants if r.place_id == primary_place.id],
            [r for r in restaurants if r.division == primary_place.division],
            restaurants,
        ]
    for grp in groups:
        if grp:
            return grp[0]
    return restaurants[0]


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
    budget_tier = budget_tier if budget_tier in TIER_RATES else "mid"
    cfg = TIER_RATES[budget_tier]
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

    # Choose top destinations proportioned to trip length, ensuring regional diversity
    selected = []
    used_slugs = set()
    used_divs = {}
    target_places = 2 if duration_days < 1 else min(len(all_places), max(2, days_count + 1))

    for _, p in scored:
        if p.slug in used_slugs:
            continue
        if len(selected) >= target_places:
            break
        if days_count <= 2 and used_divs and p.division not in used_divs and len(selected) >= 1:
            if haversine_km(selected[0].latitude, selected[0].longitude, p.latitude, p.longitude) > 180:
                continue
        selected.append(p)
        used_slugs.add(p.slug)
        used_divs[p.division] = used_divs.get(p.division, 0) + 1

    if not selected:
        selected = [p for _, p in scored[:3]]

    # Group into day-by-day schedule with strict tier-monotonic pricing (low < mid < luxury)
    itinerary = []
    tier_baseline_day = cfg["hotel_default"] + cfg["food_default"] + cfg["transport_base"]
    raw_est = days_count * tier_baseline_day
    tier_factor = 1.0
    if budget_bdt > 0 and raw_est > 0:
        ratio = budget_bdt / raw_est
        # Gentle adjustment strictly bounded within each tier so tiers never invert
        tier_factor = max(0.88, min(1.08, ratio))

    total_transport = 0
    total_hotel = 0
    total_food = 0
    total_entry = 0

    for d_idx in range(days_count):
        primary_place = selected[d_idx % len(selected)]
        secondary_place = next(
            (
                p
                for p in selected
                if p.id != primary_place.id and p.division == primary_place.division
            ),
            None,
        )

        day_hotel = _pick_hotel_for_tier(hotels, primary_place, budget_tier)
        day_rest = _pick_restaurant_for_tier(restaurants, primary_place, budget_tier)

        raw_h = day_hotel.price_per_night_bdt if day_hotel else cfg["hotel_default"]
        clamped_h = _clamp(raw_h, cfg["hotel_min"], cfg["hotel_max"])
        h_cost = 0 if duration_days < 1 else _clamp(clamped_h * tier_factor, cfg["hotel_min"], cfg["hotel_max"])

        raw_f = (day_rest.avg_meal_bdt * cfg["food_mult"]) if day_rest else cfg["food_default"]
        clamped_f = _clamp(raw_f, cfg["food_min"], cfg["food_max"])
        f_cost = _clamp(clamped_f * tier_factor, cfg["food_min"], cfg["food_max"])
        if duration_days < 1:
            f_cost = int(round(f_cost * 0.6))

        t_base = cfg["transport_base"] * (0.65 if duration_days < 1 else 1.0)
        t_cost = int(round(t_base * tier_factor))
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
                    "price_per_night_bdt": h_cost,
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
