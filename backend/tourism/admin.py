from django.contrib import admin
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

admin.site.site_header = "CholoGhuri Smart Tourism Administration"
admin.site.site_title = "CholoGhuri Admin"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "district", "division", "budget_tier", "entry_fee_bdt", "is_featured_hero", "last_verified_date")
    list_filter = ("category", "division", "budget_tier", "is_featured_hero", "is_indoor_friendly")
    search_fields = ("name", "district", "division", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "tier", "price_per_night_bdt", "rating", "is_verified_business", "link_status")
    list_filter = ("tier", "division", "is_verified_business", "link_status")
    search_fields = ("name", "city")


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "cuisine_type", "price_range", "avg_meal_bdt", "is_halal_verified", "is_vegetarian_friendly")
    list_filter = ("price_range", "is_halal_verified", "is_vegetarian_friendly", "division")
    search_fields = ("name", "city", "cuisine_type")


@admin.register(SafetyFacility)
class SafetyFacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "facility_type", "city", "phone", "emergency_24h")
    list_filter = ("facility_type", "division", "emergency_24h")


@admin.register(LocalGuide)
class LocalGuideAdmin(admin.ModelAdmin):
    list_display = ("full_name", "city", "daily_rate_bdt", "verification_status")
    list_filter = ("verification_status", "division")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "user", "rating", "visit_type", "is_reported", "is_approved", "created_at")
    list_filter = ("is_reported", "is_approved", "rating")


@admin.register(FeedbackCorrection)
class FeedbackCorrectionAdmin(admin.ModelAdmin):
    list_display = ("subject", "correction_type", "place", "status", "created_at")
    list_filter = ("status", "correction_type")


admin.site.register(HotelBooking)
admin.site.register(WishlistItem)
admin.site.register(TripPlan)
admin.site.register(TripExpense)
admin.site.register(SearchLog)
admin.site.register(AIQueryLog)
