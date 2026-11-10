import json
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from accounts.models import TravelerProfile
from .models import (
    AIQueryLog,
    Category,
    FeedbackCorrection,
    Hotel,
    HotelBooking,
    LocalGuide,
    Place,
    Restaurant,
    Review,
    SafetyFacility,
    SearchLog,
    TripExpense,
    TripPlan,
    WishlistItem,
)
from .services.itinerary_engine import build_smart_itinerary
from .services.nlp_search import search_places_nlp
from .services.route_service import STARTING_HUBS, haversine_km
from .services.translator_service import SUPPORTED_LANGUAGES, TRAVEL_PHRASES
from .famous_foods import FAMOUS_FOODS, FOOD_SECTIONS


def home_view(request):
    hero_places = list(Place.objects.select_related("category").filter(is_featured_hero=True))
    if len(hero_places) < 6:
        hero_places = list(Place.objects.select_related("category").all()[:8])
    categories = Category.objects.annotate(place_count=Count("places")).order_by("display_order", "name")
    featured_places = list(
        Place.objects.select_related("category")
        .annotate(review_count=Count("reviews", filter=Q(reviews__is_approved=True)))
        .order_by("-view_count")[:8]
    )
    culinary_places = list(
        Place.objects.select_related("category").filter(category__slug="food-tourism")[:3]
    )
    all_places_light = list(Place.objects.values("slug", "name", "district").order_by("name"))

    # Pick 2 signature dishes from each of the 5 sections so homepage covers all 5 culinary categories
    home_food_picks = []
    for sec in FOOD_SECTIONS:
        sec_items = [f for f in FAMOUS_FOODS if f["section"] == sec["key"]]
        home_food_picks.extend(sec_items[:2])

    return render(
        request,
        "home.html",
        {
            "hero_places": hero_places,
            "categories": categories,
            "featured_places": featured_places,
            "culinary_places": culinary_places,
            "famous_foods": home_food_picks,
            "food_sections": FOOD_SECTIONS,
            "total_foods_count": len(FAMOUS_FOODS),
            "all_places_light": all_places_light,
        },
    )


def foods_view(request):
    selected_section = request.GET.get("section", "all")
    selected_place = request.GET.get("place", "").strip()

    region_options = sorted(list({f["famous_place"] for f in FAMOUS_FOODS}))
    grouped_sections = []
    for sec in FOOD_SECTIONS:
        if selected_section != "all" and sec["key"] != selected_section:
            continue
        items = [f for f in FAMOUS_FOODS if f["section"] == sec["key"]]
        if selected_place:
            items = [f for f in items if selected_place.lower() in f["famous_place"].lower() or selected_place.lower() in f["region"].lower()]
        if items:
            grouped_sections.append({"meta": sec, "items": items})

    return render(
        request,
        "foods.html",
        {
            "sections": FOOD_SECTIONS,
            "grouped_sections": grouped_sections,
            "selected_section": selected_section,
            "selected_place": selected_place,
            "region_options": region_options,
            "total_count": len(FAMOUS_FOODS),
        },
    )


def destinations_view(request):
    qs = Place.objects.select_related("category").annotate(
        review_count=Count("reviews", filter=Q(reviews__is_approved=True))
    )
    categories = Category.objects.annotate(place_count=Count("places")).order_by("display_order")
    divisions = sorted(list(Place.objects.values_list("division", flat=True).distinct()))

    selected_cat = request.GET.get("category", "")
    selected_div = request.GET.get("division", "")
    selected_tier = request.GET.get("budget_tier", "")
    selected_interest = request.GET.get("interest", "")
    indoor_only = request.GET.get("indoor", "")
    nlp_query = (request.GET.get("nlp") or request.GET.get("q") or "").strip()

    if selected_cat:
        qs = qs.filter(category__slug=selected_cat)
    if selected_div:
        qs = qs.filter(division__iexact=selected_div)
    if selected_tier:
        qs = qs.filter(budget_tier=selected_tier)
    if indoor_only in ("1", "true", "on"):
        qs = qs.filter(is_indoor_friendly=True)

    explanation = ""
    nlp_intent = None
    if nlp_query:
        nlp_intent, explanation, matched_list = search_places_nlp(nlp_query, queryset=qs)
        if selected_interest:
            matched_list = [
                p for p in matched_list if selected_interest.lower() in [i.lower() for i in (p.interests or [])]
            ]
        SearchLog.objects.create(
            query=nlp_query[:255],
            parsed_intent=nlp_intent,
            results_count=len(matched_list),
            is_failure=(len(matched_list) == 0),
        )
        places = matched_list
    else:
        places = list(qs)
        if selected_interest:
            places = [
                p for p in places if selected_interest.lower() in [i.lower() for i in (p.interests or [])]
            ]

    return render(
        request,
        "destinations.html",
        {
            "places": places,
            "categories": categories,
            "divisions": divisions,
            "selected_cat": selected_cat,
            "selected_div": selected_div,
            "selected_tier": selected_tier,
            "selected_interest": selected_interest,
            "indoor_only": indoor_only,
            "nlp_query": nlp_query,
            "explanation": explanation,
            "nlp_intent": nlp_intent,
            "interests_list": ["sea", "nature", "wildlife", "historical", "spiritual", "food", "adventure", "family", "photography"],
        },
    )


def place_detail_view(request, slug):
    place = get_object_or_404(
        Place.objects.select_related("category").annotate(
            review_count=Count("reviews", filter=Q(reviews__is_approved=True))
        ),
        slug=slug,
    )

    # Handle review post
    if request.method == "POST":
        form_action = request.POST.get("form_action", "review")
        if form_action == "review":
            if not request.user.is_authenticated:
                messages.warning(request, "Please sign in to submit a review.")
                return redirect(f"/auth/?next=/destinations/{slug}/")
            rating = max(1, min(5, int(request.POST.get("rating", 5))))
            Review.objects.create(
                place=place,
                user=request.user,
                rating=rating,
                title=(request.POST.get("title") or "Great Place").strip()[:160],
                comment=(request.POST.get("comment") or "").strip(),
                photo_url=(request.POST.get("photo_url") or "").strip(),
                visit_type=request.POST.get("visit_type", "friends"),
            )
            avg = place.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"))["avg"]
            if avg:
                place.avg_rating = round(float(avg), 2)
                place.save(update_fields=["avg_rating"])
            messages.success(request, "Thank you! Your review has been published.")
            return redirect(f"/destinations/{slug}/#reviews")

        if form_action == "correction":
            FeedbackCorrection.objects.create(
                user=request.user if request.user.is_authenticated else None,
                place=place,
                subject=(request.POST.get("subject") or f"Update for {place.name}")[:180],
                message=(request.POST.get("message") or "").strip(),
                correction_type=request.POST.get("correction_type", "general"),
            )
            messages.success(request, "Correction request submitted to CholoGhuri moderators. Thank you!")
            return redirect(f"/destinations/{slug}/")

    Place.objects.filter(pk=place.pk).update(view_count=place.view_count + 1)
    place.view_count += 1

    nearby_hotels = []
    for h in Hotel.objects.all():
        dist = haversine_km(place.latitude, place.longitude, h.latitude, h.longitude)
        if h.place_id == place.id or dist <= 55:
            h.distance_km = dist
            nearby_hotels.append(h)
    nearby_hotels.sort(key=lambda x: x.distance_km)

    nearby_restaurants = []
    for r in Restaurant.objects.all():
        dist = haversine_km(place.latitude, place.longitude, r.latitude, r.longitude)
        if r.place_id == place.id or dist <= 55:
            r.distance_km = dist
            nearby_restaurants.append(r)
    nearby_restaurants.sort(key=lambda x: x.distance_km)

    nearby_safety = []
    for s in SafetyFacility.objects.all():
        dist = haversine_km(place.latitude, place.longitude, s.latitude, s.longitude)
        if s.place_id == place.id or dist <= 75 or s.division == place.division:
            s.distance_km = dist
            nearby_safety.append(s)
    nearby_safety.sort(key=lambda x: x.distance_km)

    reviews = place.reviews.filter(is_approved=True).select_related("user")

    return render(
        request,
        "place_detail.html",
        {
            "place": place,
            "reviews": reviews,
            "nearby_hotels": nearby_hotels[:6],
            "nearby_restaurants": nearby_restaurants[:6],
            "nearby_safety": nearby_safety[:6],
        },
    )


def map_view(request):
    places = list(Place.objects.select_related("category").all())
    hubs = list(STARTING_HUBS.keys())
    dest_slug = request.GET.get("dest", places[0].slug if places else "")
    return render(
        request,
        "map.html",
        {
            "places": places,
            "hubs": hubs,
            "selected_dest": dest_slug,
        },
    )


def planner_view(request):
    highlight_slug = request.GET.get("highlight", "")
    user_trips = (
        list(TripPlan.objects.filter(user=request.user).prefetch_related("expenses"))
        if request.user.is_authenticated
        else []
    )
    hubs = list(STARTING_HUBS.keys())

    generated_plan = None
    if request.method == "POST":
        action = request.POST.get("action", "generate")
        if action == "generate":
            start_city = request.POST.get("start_city", "Dhaka")
            duration_label = request.POST.get("duration_label", "5 days")
            duration_map = {
                "half_day": 0.5,
                "1_day": 1.0,
                "3_days": 3.0,
                "5_days": 5.0,
                "7_days": 7.0,
            }
            duration_days = duration_map.get(duration_label, 5.0)
            budget_bdt = int(request.POST.get("budget_bdt") or 30000)
            budget_tier = request.POST.get("budget_tier", "mid")
            traveler_type = request.POST.get("traveler_type", "solo")
            interests = request.POST.getlist("interests") or ["nature", "sea", "historical", "food"]
            weather_aware = request.POST.get("weather_aware") == "on"

            generated_plan = build_smart_itinerary(
                start_city=start_city,
                duration_days=duration_days,
                duration_label=duration_label.replace("_", " "),
                budget_bdt=budget_bdt,
                budget_tier=budget_tier,
                traveler_type=traveler_type,
                interests=interests,
                weather_aware=weather_aware,
            )

            if request.POST.get("save_trip") == "1":
                saved = TripPlan.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    title=generated_plan["title"],
                    start_city=start_city,
                    duration_days=duration_days,
                    duration_label=generated_plan["duration_label"],
                    budget_bdt=budget_bdt,
                    budget_tier=budget_tier,
                    traveler_type=traveler_type,
                    interests=interests,
                    itinerary_json=generated_plan["itinerary"],
                    estimated_breakdown_json=generated_plan["estimated_breakdown"],
                    weather_notes=generated_plan["weather_notes"],
                )
                messages.success(request, f"Trip saved! Share Code: {saved.share_code}")
                return redirect(f"/trips/shared/{saved.share_code}/")

        elif action == "add_expense" and request.user.is_authenticated:
            trip_id = int(request.POST.get("trip_id"))
            trip = get_object_or_404(TripPlan, pk=trip_id, user=request.user)
            TripExpense.objects.create(
                trip=trip,
                category=request.POST.get("category", "food"),
                title=(request.POST.get("title") or "Expense").strip()[:160],
                amount_bdt=int(request.POST.get("amount_bdt") or 0),
                day_number=int(request.POST.get("day_number") or 1),
            )
            messages.success(request, "Actual expense added to tracker.")
            return redirect("/planner/#saved-trips")

        elif action == "delete_expense" and request.user.is_authenticated:
            exp_id = int(request.POST.get("expense_id"))
            TripExpense.objects.filter(pk=exp_id, trip__user=request.user).delete()
            messages.info(request, "Expense removed.")
            return redirect("/planner/#saved-trips")

    # Pre-populate a helpful default preview when first visiting planner
    if not generated_plan:
        generated_plan = build_smart_itinerary(
            start_city="Dhaka",
            duration_days=5.0,
            duration_label="5 days",
            budget_bdt=30000,
            budget_tier="mid",
            traveler_type="solo",
            interests=["nature", "sea", "historical", "food"],
            weather_aware=True,
        )

    return render(
        request,
        "planner.html",
        {
            "hubs": hubs,
            "highlight_slug": highlight_slug,
            "generated_plan": generated_plan,
            "user_trips": user_trips,
        },
    )


def trip_shared_view(request, share_code):
    trip = get_object_or_404(TripPlan.objects.prefetch_related("expenses"), share_code=share_code)
    actual_total = sum(e.amount_bdt for e in trip.expenses.all())
    est_total = trip.estimated_breakdown_json.get("total_bdt", trip.budget_bdt)
    return render(
        request,
        "trip_shared.html",
        {
            "trip": trip,
            "actual_total": actual_total,
            "est_total": est_total,
        },
    )


def hotels_food_view(request):
    tab = request.GET.get("tab", "hotels")
    city_q = (request.GET.get("city") or "").strip()
    division_q = request.GET.get("division", "")
    tier_q = request.GET.get("tier", "")
    max_price = request.GET.get("max_price", "")
    facility_q = request.GET.get("facility", "")

    hotels = Hotel.objects.select_related("place").all()
    if city_q:
        hotels = hotels.filter(Q(city__icontains=city_q) | Q(name__icontains=city_q))
    if division_q:
        hotels = hotels.filter(division__iexact=division_q)
    if tier_q:
        hotels = hotels.filter(tier=tier_q)
    if max_price.isdigit():
        hotels = hotels.filter(price_per_night_bdt__lte=int(max_price))
    hotels_list = list(hotels)
    if facility_q:
        hotels_list = [h for h in hotels_list if any(facility_q.lower() in f.lower() for f in (h.facilities or []))]

    # Restaurant filters
    cuisine_q = (request.GET.get("cuisine") or "").strip()
    price_range = request.GET.get("price_range", "")
    halal = request.GET.get("halal") == "1"
    veg = request.GET.get("vegetarian") == "1"
    nut_free = request.GET.get("nut_free") == "1"
    dairy_free = request.GET.get("dairy_free") == "1"
    shellfish_free = request.GET.get("shellfish_free") == "1"

    rests = Restaurant.objects.select_related("place").all()
    if city_q:
        rests = rests.filter(Q(city__icontains=city_q) | Q(name__icontains=city_q) | Q(regional_specialty__icontains=city_q))
    if division_q:
        rests = rests.filter(division__iexact=division_q)
    if cuisine_q:
        rests = rests.filter(Q(cuisine_type__icontains=cuisine_q) | Q(regional_specialty__icontains=cuisine_q))
    if price_range:
        rests = rests.filter(price_range=price_range)
    if halal:
        rests = rests.filter(is_halal_verified=True)
    if veg:
        rests = rests.filter(is_vegetarian_friendly=True)
    if nut_free:
        rests = rests.filter(is_nut_free_safe=True)
    if dairy_free:
        rests = rests.filter(is_dairy_free_safe=True)
    if shellfish_free:
        rests = rests.filter(is_shellfish_free_safe=True)

    divisions = sorted(list(Place.objects.values_list("division", flat=True).distinct()))
    return render(
        request,
        "hotels_food.html",
        {
            "tab": tab,
            "hotels": hotels_list,
            "restaurants": list(rests),
            "divisions": divisions,
            "filters": {
                "city": city_q,
                "division": division_q,
                "tier": tier_q,
                "max_price": max_price,
                "facility": facility_q,
                "cuisine": cuisine_q,
                "price_range": price_range,
                "halal": halal,
                "vegetarian": veg,
                "nut_free": nut_free,
                "dairy_free": dairy_free,
                "shellfish_free": shellfish_free,
            },
        },
    )


def assistant_view(request):
    initial_q = request.GET.get("q", "")
    return render(request, "assistant.html", {"initial_q": initial_q})


def translator_view(request):
    selected_lang = (request.GET.get("lang") or "bn").strip().lower()
    lang_map = {l["code"]: l for l in SUPPORTED_LANGUAGES}
    if selected_lang not in lang_map:
        selected_lang = "bn"
    active_lang = lang_map[selected_lang]

    selected_cat = request.GET.get("category", "All")
    categories = sorted(list({p["category"] for p in TRAVEL_PHRASES}))
    raw_phrases = (
        TRAVEL_PHRASES
        if selected_cat == "All"
        else [p for p in TRAVEL_PHRASES if p["category"] == selected_cat]
    )

    display_phrases = []
    for p in raw_phrases:
        target_text = p.get(selected_lang, p["bn"])
        display_phrases.append({
            "id": p["id"],
            "category": p["category"],
            "en": p["en"],
            "bn": p["bn"],
            "phonetic_bn": p["phonetic_bn"],
            "display_text": target_text,
            "speech_code": active_lang["speech_code"],
            "lang_name": active_lang["name"],
            "show_phonetic": selected_lang == "bn",
        })

    return render(
        request,
        "translator.html",
        {
            "languages": SUPPORTED_LANGUAGES,
            "active_lang": active_lang,
            "categories": categories,
            "phrases": display_phrases,
            "selected_lang": selected_lang,
            "selected_cat": selected_cat,
        },
    )


def safety_view(request):
    if request.method == "POST":
        LocalGuide.objects.create(
            full_name=(request.POST.get("full_name") or "").strip()[:140],
            city=(request.POST.get("city") or "").strip()[:80],
            division=request.POST.get("division", "Dhaka"),
            languages=[x.strip() for x in (request.POST.get("languages") or "English, Bengali").split(",") if x.strip()],
            specialties=[x.strip() for x in (request.POST.get("specialties") or "Sightseeing").split(",") if x.strip()],
            daily_rate_bdt=int(request.POST.get("daily_rate_bdt") or 2000),
            phone=(request.POST.get("phone") or "").strip()[:50],
            license_ref=(request.POST.get("license_ref") or "").strip()[:100],
            bio=(request.POST.get("bio") or "").strip(),
            verification_status="pending",
        )
        messages.success(request, "Your local guide verification application has been submitted for Admin review!")
        return redirect("/safety/#guides")

    division_q = request.GET.get("division", "")
    ftype_q = request.GET.get("type", "")
    facilities = SafetyFacility.objects.all()
    if division_q:
        facilities = facilities.filter(division__iexact=division_q)
    if ftype_q:
        facilities = facilities.filter(facility_type=ftype_q)

    guides = LocalGuide.objects.filter(verification_status="verified")
    emergency_phrases = [p for p in TRAVEL_PHRASES if p["category"] == "Emergency & Medical"]
    divisions = sorted(list(Place.objects.values_list("division", flat=True).distinct()))
    user_trips = TripPlan.objects.filter(user=request.user)[:5] if request.user.is_authenticated else []

    return render(
        request,
        "safety.html",
        {
            "facilities": list(facilities),
            "guides": list(guides),
            "emergency_phrases": emergency_phrases,
            "divisions": divisions,
            "division_q": division_q,
            "ftype_q": ftype_q,
            "user_trips": user_trips,
        },
    )


def auth_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "/dashboard/"
    mode = request.GET.get("mode", "login")

    if request.method == "POST":
        action = request.POST.get("action", "login")
        if action == "login":
            identifier = (request.POST.get("username") or "").strip()
            password = request.POST.get("password") or ""
            uname = identifier
            if "@" in identifier:
                matched = User.objects.filter(email__iexact=identifier).first()
                if matched:
                    uname = matched.username
            user = authenticate(request, username=uname, password=password)
            if user:
                TravelerProfile.objects.get_or_create(user=user)
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect("/admin-portal/" if user.is_staff and next_url == "/dashboard/" else next_url)
            messages.error(request, "Invalid username/email or password.")
            mode = "login"
