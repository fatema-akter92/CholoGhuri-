from django.urls import path
from . import web_views

urlpatterns = [
    path("", web_views.home_view, name="home"),
    path("foods/", web_views.foods_view, name="foods"),
    path("festivals/", web_views.festivals_view, name="festivals"),
    path("destinations/", web_views.destinations_view, name="destinations"),
    path("destinations/<slug:slug>/", web_views.place_detail_view, name="place-detail-web"),
    path("map/", web_views.map_view, name="map"),
    path("planner/", web_views.planner_view, name="planner"),
    path("trips/shared/<str:share_code>/", web_views.trip_shared_view, name="trip-shared-web"),
    path("hotels-food/", web_views.hotels_food_view, name="hotels-food"),
    path("hotels/<slug:slug>/", web_views.hotel_detail_view, name="hotel-detail-web"),
    path("assistant/", web_views.assistant_view, name="assistant"),
    path("translator/", web_views.translator_view, name="translator"),
    path("safety/", web_views.safety_view, name="safety"),
    path("auth/", web_views.auth_view, name="auth"),
    path("logout/", web_views.logout_web_view, name="logout-web"),
    path("dashboard/", web_views.dashboard_view, name="dashboard"),
    path("admin-portal/", web_views.admin_portal_view, name="admin-portal"),
]
