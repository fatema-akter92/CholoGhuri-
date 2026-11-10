from datetime import date, timedelta
import requests
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AIQueryLog,
    Category,
    FeedbackCorrection,
    Hotel,
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
from .serializers import (
    AIQueryLogSerializer,
    CategorySerializer,
    FeedbackCorrectionSerializer,
    HotelSerializer,
    LocalGuideSerializer,
    PlaceDetailSerializer,
    PlaceListSerializer,
    PlaceWriteSerializer,
    RestaurantSerializer,
    ReviewSerializer,
    SafetyFacilitySerializer,
    TripExpenseSerializer,
    TripPlanSerializer,
    WishlistItemSerializer,
)
from .services.ai_assistant import generate_ai_response
from .services.itinerary_engine import build_smart_itinerary
from .services.nlp_search import search_places_nlp
from .services.route_service import STARTING_HUBS, calculate_route, haversine_km
from .services.translator_service import SUPPORTED_LANGUAGES, TRAVEL_PHRASES, translate_text
from .services.weather_service import get_destination_weather


def _wishlist_ids_for(request):
    if request.user and request.user.is_authenticated:
        return set(WishlistItem.objects.filter(user=request.user).values_list("place_id", flat=True))
    return set()


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cats = Category.objects.annotate(place_count=Count("places")).order_by("display_order", "name")
        return Response(CategorySerializer(cats, many=True).data)


class PlaceListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Place.objects.select_related("category").annotate(
            review_count=Count("reviews", filter=Q(reviews__is_approved=True))
        )

        category = request.query_params.get("category")
        division = request.query_params.get("division")
        budget_tier = request.query_params.get("budget_tier")
        interest = request.query_params.get("interest")
        max_fee = request.query_params.get("max_fee")
        featured = request.query_params.get("featured_hero")
        indoor = request.query_params.get("indoor")
        nlp_query = (request.query_params.get("nlp") or request.query_params.get("q") or "").strip()

        if category:
            qs = qs.filter(category__slug=category)
        if division:
            qs = qs.filter(division__iexact=division)
        if budget_tier:
            qs = qs.filter(budget_tier=budget_tier)
        if max_fee is not None and str(max_fee).isdigit():
            qs = qs.filter(entry_fee_bdt__lte=int(max_fee))
        if featured in ("1", "true", "True"):
            qs = qs.filter(is_featured_hero=True)
        if indoor in ("1", "true", "True"):
            qs = qs.filter(is_indoor_friendly=True)

        intent_info = None
        explanation = ""
        if nlp_query:
            intent_info, explanation, matched_list = search_places_nlp(nlp_query, queryset=qs)
            if interest:
                matched_list = [
                    p for p in matched_list if interest.lower() in [i.lower() for i in (p.interests or [])]
                ]
            SearchLog.objects.create(
                query=nlp_query[:255],
                parsed_intent=intent_info,
                results_count=len(matched_list),
                is_failure=(len(matched_list) == 0),
            )
            places = matched_list
        else:
            places = list(qs)
            if interest:
                places = [
                    p for p in places if interest.lower() in [i.lower() for i in (p.interests or [])]
