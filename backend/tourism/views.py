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
                ]

        serializer = PlaceListSerializer(
            places,
            many=True,
            context={"wishlist_place_ids": _wishlist_ids_for(request)},
        )
        return Response({
            "count": len(serializer.data),
            "nlp_intent": intent_info,
            "explanation": explanation,
            "results": serializer.data,
        })


class PlaceDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        place = get_object_or_404(
            Place.objects.select_related("category").annotate(
                review_count=Count("reviews", filter=Q(reviews__is_approved=True))
            ),
            slug=slug,
        )
        Place.objects.filter(pk=place.pk).update(view_count=place.view_count + 1)
        place.view_count += 1

        detail_data = PlaceDetailSerializer(
            place,
            context={"wishlist_place_ids": _wishlist_ids_for(request)},
        ).data

        # Attach nearby hotels, restaurants, and safety facilities
        nearby_hotels = []
        for h in Hotel.objects.all():
            dist = haversine_km(place.latitude, place.longitude, h.latitude, h.longitude)
            if h.place_id == place.id or dist <= 55:
                d = HotelSerializer(h).data
                d["distance_km"] = dist
                nearby_hotels.append(d)
        nearby_hotels.sort(key=lambda x: x["distance_km"])

        nearby_restaurants = []
        for r in Restaurant.objects.all():
            dist = haversine_km(place.latitude, place.longitude, r.latitude, r.longitude)
            if r.place_id == place.id or dist <= 55:
                d = RestaurantSerializer(r).data
                d["distance_km"] = dist
                nearby_restaurants.append(d)
        nearby_restaurants.sort(key=lambda x: x["distance_km"])

        nearby_safety = []
        for s in SafetyFacility.objects.all():
            dist = haversine_km(place.latitude, place.longitude, s.latitude, s.longitude)
            if s.place_id == place.id or dist <= 70 or s.division == place.division:
                d = SafetyFacilitySerializer(s).data
                d["distance_km"] = dist
                nearby_safety.append(d)
        nearby_safety.sort(key=lambda x: x["distance_km"])

        detail_data["nearby_hotels"] = nearby_hotels[:6]
        detail_data["nearby_restaurants"] = nearby_restaurants[:6]
        detail_data["nearby_safety"] = nearby_safety[:6]
        return Response(detail_data)


class PlaceWeatherView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        place = get_object_or_404(Place.objects.select_related("category"), slug=slug)
        return Response(get_destination_weather(place))


class PlaceReviewView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, slug):
        place = get_object_or_404(Place, slug=slug)
        reviews = place.reviews.filter(is_approved=True).select_related("user")
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request, slug):
        place = get_object_or_404(Place, slug=slug)
        rating = int(request.data.get("rating", 5))
        rating = max(1, min(5, rating))
        review = Review.objects.create(
            place=place,
            user=request.user,
            rating=rating,
            title=(request.data.get("title") or "Great Experience").strip()[:160],
            comment=(request.data.get("comment") or "").strip(),
            photo_url=(request.data.get("photo_url") or "").strip(),
            visit_type=request.data.get("visit_type", "friends"),
        )
        avg = place.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"))["avg"]
        if avg:
            place.avg_rating = round(float(avg), 2)
            place.save(update_fields=["avg_rating"])
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReportReviewView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.is_reported = True
        review.report_reason = (request.data.get("reason") or "Flagged by community traveler")[:255]
        review.save(update_fields=["is_reported", "report_reason"])
        return Response({"detail": "Review reported for moderation."})


class HotelListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Hotel.objects.select_related("place").all()
        city = request.query_params.get("city")
        division = request.query_params.get("division")
        tier = request.query_params.get("tier")
        max_price = request.query_params.get("max_price")
        min_rating = request.query_params.get("min_rating")
        facility = request.query_params.get("facility")
        q = (request.query_params.get("q") or "").strip()

        if city:
            qs = qs.filter(city__icontains=city)
        if division:
            qs = qs.filter(division__iexact=division)
        if tier:
            qs = qs.filter(tier=tier)
        if max_price and str(max_price).isdigit():
            qs = qs.filter(price_per_night_bdt__lte=int(max_price))
        if min_rating:
            try:
                qs = qs.filter(rating__gte=float(min_rating))
            except ValueError:
                pass
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(city__icontains=q)
                | Q(division__icontains=q)
                | Q(description__icontains=q)
            )

        hotels = list(qs)
        if facility:
            fac_lower = facility.lower()
            hotels = [h for h in hotels if any(fac_lower in f.lower() for f in (h.facilities or []))]

        return Response(HotelSerializer(hotels, many=True).data)


class RestaurantListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Restaurant.objects.select_related("place").all()
        city = request.query_params.get("city")
        division = request.query_params.get("division")
        price_range = request.query_params.get("price_range")
        cuisine = request.query_params.get("cuisine")
        halal = request.query_params.get("halal")
        vegetarian = request.query_params.get("vegetarian")
        nut_free = request.query_params.get("nut_free")
        dairy_free = request.query_params.get("dairy_free")
        shellfish_free = request.query_params.get("shellfish_free")
        q = (request.query_params.get("q") or "").strip()

        if city:
            qs = qs.filter(city__icontains=city)
        if division:
            qs = qs.filter(division__iexact=division)
        if price_range:
            qs = qs.filter(price_range=price_range)
        if cuisine:
            qs = qs.filter(Q(cuisine_type__icontains=cuisine) | Q(regional_specialty__icontains=cuisine))
        if halal in ("1", "true", "True"):
            qs = qs.filter(is_halal_verified=True)
        if vegetarian in ("1", "true", "True"):
            qs = qs.filter(is_vegetarian_friendly=True)
        if nut_free in ("1", "true", "True"):
            qs = qs.filter(is_nut_free_safe=True)
        if dairy_free in ("1", "true", "True"):
            qs = qs.filter(is_dairy_free_safe=True)
        if shellfish_free in ("1", "true", "True"):
            qs = qs.filter(is_shellfish_free_safe=True)
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(city__icontains=q)
                | Q(cuisine_type__icontains=q)
                | Q(regional_specialty__icontains=q)
            )

        return Response(RestaurantSerializer(qs, many=True).data)


class SafetySupportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = SafetyFacility.objects.select_related("place").all()
        division = request.query_params.get("division")
        facility_type = request.query_params.get("type")
        q = (request.query_params.get("q") or "").strip()
        if division:
            qs = qs.filter(division__iexact=division)
        if facility_type:
            qs = qs.filter(facility_type=facility_type)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(city__icontains=q) | Q(address__icontains=q))

        helplines = [
            {"name": "National Emergency Service (Police / Ambulance / Fire)", "number": "999", "hours": "24/7 Toll-Free"},
            {"name": "Bangladesh Tourist Police Hotline", "number": "01320-222222", "hours": "24/7 Dedicated Tourist Desk"},
            {"name": "Bangladesh Coast Guard (Coastal / Island Rescue)", "number": "16111", "hours": "24/7 Maritime Emergency"},
            {"name": "Health Helpline (Shastho Batayon)", "number": "16263", "hours": "24/7 Medical Advice"},
        ]

        advisories = [
            {
                "region": "Saint Martin's Island & Coastal Cruises",
                "level": "Seasonal Advisory",
                "summary": "Tourist ferries operate primarily November–March subject to BIWTA sea-state clearance and daily eco-visitor limits.",
            },
            {
                "region": "Chattogram Hill Tracts (Sajek, Bandarban, Rangamati)",
                "level": "Checkpoint Protocol",
                "summary": "Carry original NID/Passport. Foreign nationals require DC/Ministry clearance for restricted Bandarban/Rangamati frontier zones.",
            },
            {
                "region": "Sundarbans Mangrove Reserve",
                "level": "Permit & Guide Mandatory",
                "summary": "Forest Department pass and armed forest guard escort are required for overnight eco-cruises.",
            },
        ]

        return Response({
            "helplines": helplines,
            "advisories": advisories,
            "facilities": SafetyFacilitySerializer(qs, many=True).data,
        })


class MapHubsAndDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        places = PlaceListSerializer(Place.objects.select_related("category").all(), many=True).data
        hotels = HotelSerializer(Hotel.objects.all(), many=True).data
        restaurants = RestaurantSerializer(Restaurant.objects.all(), many=True).data
        safety = SafetyFacilitySerializer(SafetyFacility.objects.all(), many=True).data
        hubs = [
            {"name": name, "latitude": coords[0], "longitude": coords[1]}
            for name, coords in STARTING_HUBS.items()
        ]
        return Response({
            "hubs": hubs,
            "places": places,
            "hotels": hotels,
            "restaurants": restaurants,
            "safety": safety,
        })


class RoutePlanView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        start = request.query_params.get("start", "Dhaka")
        dest_slug = request.query_params.get("destination")
        place = (
            get_object_or_404(Place, slug=dest_slug)
            if dest_slug
            else Place.objects.first()
        )
        if not place:
            return Response({"detail": "No destinations found."}, status=404)
        return Response(calculate_route(start, place))


class AIChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        prompt = (request.data.get("prompt") or request.data.get("message") or "").strip()
        if not prompt:
            return Response({"detail": "Please provide a travel question or request."}, status=400)
        result = generate_ai_response(prompt, user=request.user)
        return Response(result)


class AIFeedbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        log_id = request.data.get("log_id")
        vote = request.data.get("vote")
        if log_id and vote in (1, -1, "1", "-1"):
            AIQueryLog.objects.filter(id=log_id).update(helpful_vote=int(vote))
        return Response({"detail": "Thank you for rating the assistant response."})


class TranslatorPhrasesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get("category")
        phrases = TRAVEL_PHRASES
        if category and category != "All":
            phrases = [p for p in TRAVEL_PHRASES if p["category"] == category]
        return Response({
            "languages": SUPPORTED_LANGUAGES,
            "categories": sorted(list({p["category"] for p in TRAVEL_PHRASES})),
            "phrases": phrases,
        })


class TranslateTextView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get("text", "")
        source_lang = request.data.get("source_lang", "en")
        target_lang = request.data.get("target_lang", "bn")
        return Response(translate_text(text, source_lang, target_lang))


class TranslatorTTSView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        text = (request.query_params.get("text") or "").strip()[:220]
        lang = (request.query_params.get("lang") or "bn").split("-")[0].lower()
