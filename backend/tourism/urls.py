from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminAnalyticsView,
    AdminFeedbackViewSet,
    AdminGuideViewSet,
    AdminHotelViewSet,
    AdminPlaceViewSet,
    AdminRestaurantViewSet,
    AdminReviewModerationViewSet,
    AIChatView,
    AIFeedbackView,
    CategoryListView,
    FeedbackCorrectionView,
    HotelListView,
    LocalGuideListView,
    MapHubsAndDataView,
    PlaceDetailView,
    PlaceListView,
    PlaceReviewView,
    PlaceWeatherView,
    ReportReviewView,
    RestaurantListView,
    RoutePlanView,
    SafetySupportView,
    TranslateTextView,
    TranslatorPhrasesView,
    TranslatorTTSView,
    TripExpenseDeleteView,
    TripExpenseView,
    TripGenerateView,
    TripPlanDetailView,
    TripPlanListView,
    TripSharedView,
    WishlistToggleView,
    WishlistView,
)

admin_router = DefaultRouter()
admin_router.register(r"places", AdminPlaceViewSet, basename="admin-places")
admin_router.register(r"hotels", AdminHotelViewSet, basename="admin-hotels")
admin_router.register(r"restaurants", AdminRestaurantViewSet, basename="admin-restaurants")
admin_router.register(r"guides", AdminGuideViewSet, basename="admin-guides")
admin_router.register(r"reviews", AdminReviewModerationViewSet, basename="admin-reviews")
admin_router.register(r"feedback", AdminFeedbackViewSet, basename="admin-feedback")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("places/", PlaceListView.as_view(), name="place-list"),
    path("places/<slug:slug>/", PlaceDetailView.as_view(), name="place-detail"),
    path("places/<slug:slug>/weather/", PlaceWeatherView.as_view(), name="place-weather"),
    path("places/<slug:slug>/reviews/", PlaceReviewView.as_view(), name="place-reviews"),
    path("reviews/<int:pk>/report/", ReportReviewView.as_view(), name="review-report"),
    path("hotels/", HotelListView.as_view(), name="hotel-list"),
    path("restaurants/", RestaurantListView.as_view(), name="restaurant-list"),
    path("safety/", SafetySupportView.as_view(), name="safety-support"),
    path("map/data/", MapHubsAndDataView.as_view(), name="map-data"),
    path("routes/plan/", RoutePlanView.as_view(), name="route-plan"),
    path("ai/chat/", AIChatView.as_view(), name="ai-chat"),
    path("ai/feedback/", AIFeedbackView.as_view(), name="ai-feedback"),
    path("translator/phrases/", TranslatorPhrasesView.as_view(), name="translator-phrases"),
    path("translator/translate/", TranslateTextView.as_view(), name="translator-translate"),
    path("translator/tts/", TranslatorTTSView.as_view(), name="translator-tts"),
    path("trips/generate/", TripGenerateView.as_view(), name="trip-generate"),
    path("trips/", TripPlanListView.as_view(), name="trip-list"),
    path("trips/<int:pk>/", TripPlanDetailView.as_view(), name="trip-detail"),
    path("trips/shared/<str:share_code>/", TripSharedView.as_view(), name="trip-shared"),
    path("trips/<int:pk>/expenses/", TripExpenseView.as_view(), name="trip-expense-add"),
    path("trips/<int:pk>/expenses/<int:exp_id>/", TripExpenseDeleteView.as_view(), name="trip-expense-del"),
    path("wishlist/", WishlistView.as_view(), name="wishlist-list"),
    path("wishlist/toggle/", WishlistToggleView.as_view(), name="wishlist-toggle"),
    path("guides/", LocalGuideListView.as_view(), name="guide-list"),
    path("feedback/", FeedbackCorrectionView.as_view(), name="feedback-correction"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("admin/", include(admin_router.urls)),
]
