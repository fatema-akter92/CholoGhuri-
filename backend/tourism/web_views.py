import json
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie

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
from .festivals import BANGLADESH_FESTIVALS, FESTIVAL_SECTIONS


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

    upcoming_festivals = [f for f in BANGLADESH_FESTIVALS if f.get("home_highlight")][:12]
    if len(upcoming_festivals) < 4:
        upcoming_festivals = BANGLADESH_FESTIVALS[:12]

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
            "upcoming_festivals": upcoming_festivals,
            "festival_sections": FESTIVAL_SECTIONS,
            "total_festivals_count": len(BANGLADESH_FESTIVALS),
            "all_places_light": all_places_light,
        },
    )


def festivals_view(request):
    selected_season = request.GET.get("season", "all")
    selected_division = request.GET.get("division", "").strip()

    division_options = sorted(list({f["division"] for f in BANGLADESH_FESTIVALS}))
    items = list(BANGLADESH_FESTIVALS)
    if selected_season != "all":
        items = [f for f in items if f["season_key"] == selected_season]
    if selected_division:
        items = [
            f
            for f in items
            if selected_division.lower() in f["division"].lower()
            or selected_division.lower() in f["district"].lower()
        ]

    return render(
        request,
        "festivals.html",
        {
            "sections": FESTIVAL_SECTIONS,
            "festivals": items,
            "selected_season": selected_season,
            "selected_division": selected_division,
            "division_options": division_options,
            "total_count": len(BANGLADESH_FESTIVALS),
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


@ensure_csrf_cookie
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
        elif action == "register":
            uname = (request.POST.get("username") or "").strip()
            email = (request.POST.get("email") or "").strip()
            pwd = request.POST.get("password") or ""
            fname = (request.POST.get("first_name") or "").strip()
            lname = (request.POST.get("last_name") or "").strip()
            nat = (request.POST.get("nationality") or "International Visitor").strip()

            if len(pwd) < 6:
                messages.error(request, "Password must be at least 6 characters.")
                mode = "register"
            elif User.objects.filter(username__iexact=uname).exists():
                messages.error(request, "That username is already taken.")
                mode = "register"
            else:
                user = User.objects.create_user(
                    username=uname, email=email, password=pwd, first_name=fname, last_name=lname
                )
                TravelerProfile.objects.create(user=user, nationality=nat)
                login(request, user)
                messages.success(request, "Account created! Welcome to CholoGhuri.")
                return redirect(next_url)

    return render(request, "auth.html", {"mode": mode, "next_url": next_url})


def logout_web_view(request):
    logout(request)
    messages.info(request, "Signed out cleanly.")
    return redirect("/")


@login_required
def dashboard_view(request):
    profile, _ = TravelerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_profile":
            request.user.first_name = (request.POST.get("first_name") or "").strip()
            request.user.last_name = (request.POST.get("last_name") or "").strip()
            request.user.email = (request.POST.get("email") or "").strip()
            request.user.save()
            profile.nationality = (request.POST.get("nationality") or "Bangladesh").strip()
            profile.phone = (request.POST.get("phone") or "").strip()
            profile.preferred_budget_tier = request.POST.get("preferred_budget_tier", "mid")
            profile.emergency_contact_name = (request.POST.get("emergency_contact_name") or "").strip()
            profile.emergency_contact_phone = (request.POST.get("emergency_contact_phone") or "").strip()
            profile.dietary_preferences = request.POST.getlist("dietary_preferences")
            profile.save()
            messages.success(request, "Traveler profile updated.")
            return redirect("/dashboard/")
        elif action == "submit_feedback":
            p_id = request.POST.get("place_id") or None
            FeedbackCorrection.objects.create(
                user=request.user,
                place_id=int(p_id) if p_id else None,
                subject=(request.POST.get("subject") or "Feedback").strip()[:180],
                message=(request.POST.get("message") or "").strip(),
                correction_type=request.POST.get("correction_type", "general"),
            )
            messages.success(request, "Feedback & correction request submitted.")
            return redirect("/dashboard/?tab=feedback")
        elif action == "remove_wishlist":
            WishlistItem.objects.filter(user=request.user, place_id=request.POST.get("place_id")).delete()
            messages.info(request, "Removed from saved wishlist.")
            return redirect("/dashboard/?tab=wishlist")

    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related("place", "place__category")
    trips = TripPlan.objects.filter(user=request.user).prefetch_related("expenses")
    hotel_bookings = HotelBooking.objects.filter(user=request.user).select_related("hotel")
    reviews = Review.objects.filter(user=request.user).select_related("place")
    feedbacks = FeedbackCorrection.objects.filter(user=request.user).select_related("place")
    all_places = Place.objects.order_by("name")
    tab = request.GET.get("tab", "wishlist")

    return render(
        request,
        "dashboard.html",
        {
            "profile": profile,
            "wishlist_items": wishlist_items,
            "trips": trips,
            "hotel_bookings": hotel_bookings,
            "reviews": reviews,
            "feedbacks": feedbacks,
            "all_places": all_places,
            "tab": tab,
        },
    )


def hotel_detail_view(request, slug):
    hotel = get_object_or_404(Hotel.objects.select_related("place"), slug=slug)
    today = date.today()
    default_checkin = (today + timedelta(days=3)).isoformat()
    default_checkout = (today + timedelta(days=4)).isoformat()
    latest_booking = None

    if request.method == "POST":
        guest_name = (request.POST.get("guest_name") or "").strip()[:140]
        guest_phone = (request.POST.get("guest_phone") or "").strip()[:40]
        guest_email = (request.POST.get("guest_email") or "").strip()
        room_type = (request.POST.get("room_type") or "Standard / Deluxe Room")[:80]
        rooms = max(1, int(request.POST.get("rooms") or 1))
        guests = max(1, int(request.POST.get("guests") or 2))
        special_requests = (request.POST.get("special_requests") or "").strip()

        try:
            ci = date.fromisoformat(request.POST.get("check_in") or default_checkin)
            co = date.fromisoformat(request.POST.get("check_out") or default_checkout)
        except ValueError:
            ci = today + timedelta(days=3)
            co = today + timedelta(days=4)
        nights = max(1, (co - ci).days)
        mult = 1.6 if "Family" in room_type else 1.35 if "Suite" in room_type else 1.0
        total_bdt = int(round(hotel.price_per_night_bdt * nights * rooms * mult))

        latest_booking = HotelBooking.objects.create(
            hotel=hotel,
            user=request.user if request.user.is_authenticated else None,
            guest_name=guest_name or "Valued Guest",
            guest_phone=guest_phone,
            guest_email=guest_email,
            check_in=ci,
            check_out=co,
            rooms=rooms,
            guests=guests,
            room_type=room_type,
            total_bdt=total_bdt,
            special_requests=special_requests,
        )
        messages.success(request, f"Reservation confirmed! Booking Code: {latest_booking.booking_code}")

    return render(
        request,
        "hotel_detail.html",
        {
            "hotel": hotel,
            "default_checkin": default_checkin,
            "default_checkout": default_checkout,
            "latest_booking": latest_booking,
        },
    )


def _is_staff(u):
    return u.is_authenticated and u.is_staff


@user_passes_test(_is_staff, login_url="/auth/")
def admin_portal_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_place":
            name = (request.POST.get("name") or "").strip()
            slug = slugify(name)
            cat = get_object_or_404(Category, pk=int(request.POST.get("category_id")))
            Place.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "tagline": (request.POST.get("tagline") or "").strip(),
                    "category": cat,
                    "division": request.POST.get("division", "Dhaka"),
                    "district": request.POST.get("district", "Dhaka"),
                    "latitude": float(request.POST.get("latitude") or 23.8103),
                    "longitude": float(request.POST.get("longitude") or 90.4125),
                    "description": (request.POST.get("description") or "").strip(),
                    "image_url": (request.POST.get("image_url") or "/media/places/coxs-bazar.jpg").strip(),
                    "entry_fee_bdt": int(request.POST.get("entry_fee_bdt") or 0),
                    "entry_fee_foreigner_bdt": int(request.POST.get("entry_fee_foreigner_bdt") or 0),
                    "opening_hours": (request.POST.get("opening_hours") or "9:00 AM – 5:00 PM").strip(),
                    "budget_tier": request.POST.get("budget_tier", "mid"),
                    "seasonal_restrictions": (request.POST.get("seasonal_restrictions") or "").strip(),
                    "info_source": (request.POST.get("info_source") or "Admin Field Verification").strip(),
                    "last_verified_date": date.today(),
                },
            )
            messages.success(request, f"Destination '{name}' saved & verified.")
            return redirect("/admin-portal/?tab=content")

        elif action == "delete_place":
            Place.objects.filter(pk=int(request.POST.get("place_id"))).delete()
            messages.info(request, "Destination removed.")
            return redirect("/admin-portal/?tab=content")

        elif action == "verify_place_now":
            Place.objects.filter(pk=int(request.POST.get("place_id"))).update(last_verified_date=date.today())
            messages.success(request, "Destination verification date refreshed to today.")
            return redirect("/admin-portal/?tab=freshness")

        elif action == "fix_hotel_link":
            Hotel.objects.filter(pk=int(request.POST.get("hotel_id"))).update(
                link_status="active", is_verified_business=True
            )
            messages.success(request, "Hotel booking link marked active & verified.")
            return redirect("/admin-portal/?tab=freshness")

        elif action == "guide_status":
            LocalGuide.objects.filter(pk=int(request.POST.get("guide_id"))).update(
                verification_status=request.POST.get("status", "verified")
            )
            messages.success(request, "Guide verification status updated.")
            return redirect("/admin-portal/?tab=moderation")

        elif action == "moderate_review":
            rev = get_object_or_404(Review, pk=int(request.POST.get("review_id")))
            decision = request.POST.get("decision")
            if decision == "approve":
                rev.is_reported = False
                rev.is_approved = True
                rev.save()
            elif decision == "hide":
                rev.is_approved = False
                rev.save()
            elif decision == "delete":
                rev.delete()
            messages.success(request, "Review moderation action applied.")
            return redirect("/admin-portal/?tab=moderation")

        elif action == "resolve_feedback":
            fb = get_object_or_404(FeedbackCorrection, pk=int(request.POST.get("feedback_id")))
            fb.status = request.POST.get("status", "resolved")
            fb.admin_note = (request.POST.get("admin_note") or "Updated by Admin").strip()
            fb.save()
            messages.success(request, "Correction request updated.")
            return redirect("/admin-portal/?tab=moderation")

    most_viewed = list(Place.objects.order_by("-view_count")[:8])
    max_views = max([p.view_count for p in most_viewed] or [1])
    most_saved = list(Place.objects.annotate(save_count=Count("wishlisted_by")).order_by("-save_count", "-view_count")[:8])
    max_saves = max([p.save_count for p in most_saved] or [1])

    popular_searches = list(SearchLog.objects.filter(is_failure=False).values("query").annotate(count=Count("id")).order_by("-count")[:8])
    failed_searches = list(SearchLog.objects.filter(is_failure=True).values("query").annotate(count=Count("id")).order_by("-count")[:8])

    ai_logs = list(AIQueryLog.objects.select_related("user").all()[:12])
    ai_stats = {
        "total": AIQueryLog.objects.count(),
        "avg_latency": round(float(AIQueryLog.objects.aggregate(a=Avg("latency_ms"))["a"] or 0), 1),
        "total_tokens": AIQueryLog.objects.aggregate(s=Sum("tokens_used"))["s"] or 0,
        "total_cost": round(float(AIQueryLog.objects.aggregate(s=Sum("estimated_cost_usd"))["s"] or 0.0), 5),
        "helpful": AIQueryLog.objects.filter(helpful_vote=1).count(),
        "unhelpful": AIQueryLog.objects.filter(helpful_vote=-1).count(),
    }

    trip_budgets = list(TripPlan.objects.values("budget_tier").annotate(count=Count("id"), avg_bdt=Avg("budget_bdt")).order_by("-count"))
    trip_durations = list(TripPlan.objects.values("duration_label").annotate(count=Count("id")).order_by("-count")[:6])

    stale_cutoff = date.today() - timedelta(days=90)
    stale_places = list(Place.objects.filter(Q(last_verified_date__isnull=True) | Q(last_verified_date__lt=stale_cutoff)))
    flagged_hotels = list(Hotel.objects.exclude(link_status="active"))

    tab = request.GET.get("tab", "analytics")
    return render(
        request,
        "admin_portal.html",
        {
            "tab": tab,
            "overview": {
                "places": Place.objects.count(),
                "hotels": Hotel.objects.count(),
                "restaurants": Restaurant.objects.count(),
                "reviews": Review.objects.count(),
                "reported_reviews": Review.objects.filter(is_reported=True).count(),
                "pending_guides": LocalGuide.objects.filter(verification_status="pending").count(),
                "open_corrections": FeedbackCorrection.objects.filter(status="open").count(),
                "trips": TripPlan.objects.count(),
            },
            "most_viewed": most_viewed,
            "max_views": max_views,
            "most_saved": most_saved,
            "max_saves": max_saves,
            "popular_searches": popular_searches,
            "failed_searches": failed_searches,
            "ai_stats": ai_stats,
            "ai_logs": ai_logs,
            "trip_budgets": trip_budgets,
            "trip_durations": trip_durations,
            "stale_places": stale_places,
            "flagged_hotels": flagged_hotels,
            "all_places": Place.objects.select_related("category").order_by("name"),
            "categories": Category.objects.order_by("display_order"),
            "all_guides": LocalGuide.objects.order_by("-created_at"),
            "reported_reviews_list": Review.objects.filter(Q(is_reported=True) | Q(is_approved=False)).select_related("place", "user"),
            "feedback_list": FeedbackCorrection.objects.select_related("place", "user").order_by("-created_at"),
        },
    )
