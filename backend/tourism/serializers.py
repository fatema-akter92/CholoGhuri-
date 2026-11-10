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
