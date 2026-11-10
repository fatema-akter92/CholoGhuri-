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
