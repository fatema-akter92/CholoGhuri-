from django.contrib.auth.models import User
from rest_framework import serializers
from .models import TravelerProfile


class TravelerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelerProfile
        fields = [
            "phone",
            "nationality",
            "preferred_language",
            "preferred_budget_tier",
            "dietary_preferences",
            "emergency_contact_name",
            "emergency_contact_phone",
            "is_verified_guide",
            "updated_at",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = TravelerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "date_joined",
            "profile",
        ]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    nationality = serializers.CharField(max_length=80, required=False, default="International Visitor")
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        nationality = validated_data.pop("nationality", "International Visitor")
        phone = validated_data.pop("phone", "")
        password = validated_data.pop("password")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=password,
        )
        TravelerProfile.objects.create(
            user=user,
            nationality=nationality,
            phone=phone,
        )
        return user
