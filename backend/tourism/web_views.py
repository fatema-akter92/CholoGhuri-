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
