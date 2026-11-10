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
