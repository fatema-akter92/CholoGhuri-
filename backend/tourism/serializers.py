from rest_framework import serializers
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


class CategorySerializer(serializers.ModelSerializer):
    place_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon_name", "description", "display_order", "place_count"]


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "place",
            "user",
            "username",
            "user_full_name",
            "rating",
            "title",
            "comment",
            "photo_url",
            "visit_type",
            "is_reported",
            "report_reason",
            "is_approved",
            "created_at",
        ]
        read_only_fields = ["user", "is_reported", "is_approved", "created_at"]

    def get_user_full_name(self, obj):
        full = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full or obj.user.username


class PlaceListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    review_count = serializers.IntegerField(read_only=True, default=0)
    is_wishlisted = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            "id",
            "name",
            "slug",
            "tagline",
            "category",
            "category_name",
            "category_slug",
            "division",
            "district",
            "latitude",
            "longitude",
            "image_url",
            "entry_fee_bdt",
            "entry_fee_foreigner_bdt",
            "opening_hours",
            "recommended_duration_hours",
            "budget_tier",
            "estimated_daily_cost_bdt",
            "best_time_to_visit",
            "is_indoor_friendly",
            "interests",
            "quick_tags",
            "is_featured_hero",
            "hero_headline",
            "hero_subtitle",
            "view_count",
            "avg_rating",
            "review_count",
            "is_wishlisted",
            "last_verified_date",
        ]

    def get_is_wishlisted(self, obj):
        wishlist_ids = self.context.get("wishlist_place_ids")
        if wishlist_ids is not None:
            return obj.id in wishlist_ids
        return False


class PlaceDetailSerializer(PlaceListSerializer):
    reviews = serializers.SerializerMethodField()

    class Meta(PlaceListSerializer.Meta):
