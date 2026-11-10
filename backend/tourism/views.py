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
        if lang not in {"bn", "en", "hi", "ar", "ja", "fr", "es"}:
            lang = "bn"
        if not text:
            return Response({"detail": "No text provided"}, status=400)
        try:
            r = requests.get(
                "https://translate.google.com/translate_tts",
                params={"ie": "UTF-8", "client": "tw-ob", "tl": lang, "q": text},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=6,
            )
            if r.status_code == 200 and r.content:
                return HttpResponse(r.content, content_type="audio/mpeg")
        except Exception:
            pass
        return Response({"detail": "Audio TTS unavailable"}, status=503)


class TripGenerateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        start_city = request.data.get("start_city", "Dhaka")
        duration_label = request.data.get("duration_label", "3 days")
        duration_map = {
            "half_day": 0.5,
            "half day": 0.5,
            "1_day": 1.0,
            "1 day": 1.0,
            "3_days": 3.0,
            "3 days": 3.0,
            "5_days": 5.0,
            "5 days": 5.0,
            "7_days": 7.0,
            "7 days": 7.0,
        }
        duration_days = float(
            request.data.get("duration_days")
            or duration_map.get(str(duration_label).lower(), 3.0)
        )
        budget_bdt = int(request.data.get("budget_bdt", 20000))
        budget_tier = request.data.get("budget_tier", "mid")
        traveler_type = request.data.get("traveler_type", "friends")
        interests = request.data.get("interests") or ["nature", "historical"]
        weather_aware = bool(request.data.get("weather_aware", True))

        plan_data = build_smart_itinerary(
            start_city=start_city,
            duration_days=duration_days,
            duration_label=duration_label.replace("_", " "),
            budget_bdt=budget_bdt,
            budget_tier=budget_tier,
            traveler_type=traveler_type,
            interests=interests,
            weather_aware=weather_aware,
        )

        save_plan = bool(request.data.get("save", False))
        saved_obj = None
        if save_plan:
            saved_obj = TripPlan.objects.create(
                user=request.user if request.user.is_authenticated else None,
                title=request.data.get("title") or plan_data["title"],
                start_city=start_city,
                duration_days=duration_days,
                duration_label=plan_data["duration_label"],
                budget_bdt=budget_bdt,
                budget_tier=budget_tier,
                traveler_type=traveler_type,
                interests=interests,
                itinerary_json=plan_data["itinerary"],
                estimated_breakdown_json=plan_data["estimated_breakdown"],
                weather_notes=plan_data["weather_notes"],
            )
            plan_data["saved_trip"] = TripPlanSerializer(saved_obj).data

        return Response(plan_data)


class TripPlanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = TripPlan.objects.filter(user=request.user).prefetch_related("expenses")
        return Response(TripPlanSerializer(trips, many=True).data)

    def post(self, request):
        data = request.data
        trip = TripPlan.objects.create(
            user=request.user,
            title=data.get("title", "My Bangladesh Trip"),
            start_city=data.get("start_city", "Dhaka"),
            duration_days=float(data.get("duration_days", 3)),
            duration_label=data.get("duration_label", "3 days"),
            budget_bdt=int(data.get("budget_bdt", 15000)),
            budget_tier=data.get("budget_tier", "mid"),
            traveler_type=data.get("traveler_type", "friends"),
            interests=data.get("interests", []),
            itinerary_json=data.get("itinerary_json", []),
            estimated_breakdown_json=data.get("estimated_breakdown_json", {}),
            weather_notes=data.get("weather_notes", ""),
        )
        return Response(TripPlanSerializer(trip).data, status=201)


class TripPlanDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        trip = get_object_or_404(TripPlan.objects.prefetch_related("expenses"), pk=pk)
        return Response(TripPlanSerializer(trip).data)

    def delete(self, request, pk):
        trip = get_object_or_404(TripPlan, pk=pk, user=request.user)
        trip.delete()
        return Response(status=204)


class TripSharedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, share_code):
        trip = get_object_or_404(TripPlan.objects.prefetch_related("expenses"), share_code=share_code)
        return Response(TripPlanSerializer(trip).data)


class TripExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        trip = get_object_or_404(TripPlan, pk=pk, user=request.user)
        expense = TripExpense.objects.create(
            trip=trip,
            category=request.data.get("category", "food"),
            title=(request.data.get("title") or "Trip Expense").strip()[:160],
            amount_bdt=int(request.data.get("amount_bdt", 0)),
            day_number=int(request.data.get("day_number", 1)),
        )
        return Response(TripExpenseSerializer(expense).data, status=201)


class TripExpenseDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, exp_id):
        expense = get_object_or_404(TripExpense, pk=exp_id, trip_id=pk, trip__user=request.user)
        expense.delete()
        return Response(status=204)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related("place", "place__category")
        return Response(
            WishlistItemSerializer(
                items,
                many=True,
                context={"wishlist_place_ids": _wishlist_ids_for(request)},
            ).data
        )


class WishlistToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        place_id = request.data.get("place_id")
        place = get_object_or_404(Place, pk=place_id)
        item = WishlistItem.objects.filter(user=request.user, place=place).first()
        if item:
            item.delete()
            return Response({"wishlisted": False, "place_id": place.id})
        WishlistItem.objects.create(user=request.user, place=place)
        return Response({"wishlisted": True, "place_id": place.id}, status=201)


class LocalGuideListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = LocalGuide.objects.filter(verification_status="verified")
        city = request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)
        return Response(LocalGuideSerializer(qs, many=True).data)

    def post(self, request):
        serializer = LocalGuideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(verification_status="pending")
        return Response(serializer.data, status=201)


class FeedbackCorrectionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user and request.user.is_authenticated:
            qs = FeedbackCorrection.objects.filter(user=request.user)
            return Response(FeedbackCorrectionSerializer(qs, many=True).data)
        return Response([])

    def post(self, request):
        serializer = FeedbackCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user if request.user.is_authenticated else None)
        return Response(serializer.data, status=201)


# ============================================================
# ADMIN & ANALYTICS VIEWS (Modules 16 & 18)
# ============================================================


class AdminAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        most_viewed = list(
            Place.objects.order_by("-view_count")
            .values("id", "name", "slug", "district", "view_count", "avg_rating")[:8]
        )
        most_saved = list(
            Place.objects.annotate(save_count=Count("wishlisted_by"))
            .order_by("-save_count", "-view_count")
            .values("id", "name", "slug", "district", "save_count")[:8]
        )
        popular_searches = list(
            SearchLog.objects.filter(is_failure=False)
            .values("query")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )
        failed_searches = list(
            SearchLog.objects.filter(is_failure=True)
            .values("query")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        ai_total = AIQueryLog.objects.count()
        ai_avg_latency = AIQueryLog.objects.aggregate(avg=Avg("latency_ms"))["avg"] or 0
        ai_total_tokens = AIQueryLog.objects.aggregate(total=Sum("tokens_used"))["total"] or 0
        ai_total_cost = AIQueryLog.objects.aggregate(total=Sum("estimated_cost_usd"))["total"] or 0.0
        ai_positive = AIQueryLog.objects.filter(helpful_vote=1).count()
        ai_negative = AIQueryLog.objects.filter(helpful_vote=-1).count()
        recent_ai_logs = AIQueryLogSerializer(AIQueryLog.objects.all()[:10], many=True).data

        trip_budgets = list(
            TripPlan.objects.values("budget_tier")
            .annotate(count=Count("id"), avg_budget=Avg("budget_bdt"))
            .order_by("-count")
        )
        trip_durations = list(
            TripPlan.objects.values("duration_label")
            .annotate(count=Count("id"))
            .order_by("-count")[:6]
        )

        stale_cutoff = date.today() - timedelta(days=90)
        stale_places = list(
            Place.objects.filter(Q(last_verified_date__isnull=True) | Q(last_verified_date__lt=stale_cutoff))
            .values("id", "name", "district", "last_verified_date")[:10]
        )
        broken_hotels = list(
            Hotel.objects.exclude(link_status="active").values("id", "name", "city", "link_status", "booking_url")
        )

        return Response({
            "overview": {
                "total_places": Place.objects.count(),
                "total_hotels": Hotel.objects.count(),
                "total_restaurants": Restaurant.objects.count(),
                "total_reviews": Review.objects.count(),
                "reported_reviews": Review.objects.filter(is_reported=True).count(),
                "pending_guides": LocalGuide.objects.filter(verification_status="pending").count(),
                "open_corrections": FeedbackCorrection.objects.filter(status="open").count(),
                "total_trips_planned": TripPlan.objects.count(),
            },
            "most_viewed_places": most_viewed,
            "most_saved_places": most_saved,
            "popular_searches": popular_searches,
            "failed_searches": failed_searches,
            "ai_monitoring": {
                "total_queries": ai_total,
                "avg_latency_ms": round(float(ai_avg_latency), 1),
                "total_tokens": ai_total_tokens,
                "estimated_cost_usd": round(float(ai_total_cost), 5),
                "helpful_votes": ai_positive,
                "unhelpful_votes": ai_negative,
                "recent_logs": recent_ai_logs,
            },
            "trip_analytics": {
                "budgets": trip_budgets,
                "durations": trip_durations,
            },
            "freshness_and_links": {
                "overdue_verification_places": stale_places,
                "flagged_hotel_links": broken_hotels,
            },
        })


class AdminPlaceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Place.objects.select_related("category").all()
    serializer_class = PlaceWriteSerializer


class AdminHotelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer


class AdminRestaurantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer


class AdminGuideViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LocalGuide.objects.all().order_by("-created_at")
    serializer_class = LocalGuideSerializer


class AdminReviewModerationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Review.objects.select_related("place", "user").all()
    serializer_class = ReviewSerializer


class AdminFeedbackViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = FeedbackCorrection.objects.select_related("user", "place").all()
    serializer_class = FeedbackCorrectionSerializer
