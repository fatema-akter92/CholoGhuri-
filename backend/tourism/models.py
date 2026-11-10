import uuid
from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    icon_name = models.CharField(max_length=50, default="Compass")
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Place(models.Model):
    BUDGET_CHOICES = [
        ("low", "Budget-Friendly"),
        ("mid", "Mid-Range"),
        ("luxury", "Premium / Luxury"),
    ]

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    tagline = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="places")
    division = models.CharField(max_length=80)
    district = models.CharField(max_length=80)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    description = models.TextField()
    highlights = models.JSONField(default=list, blank=True)
    image_url = models.CharField(max_length=500)
    gallery_urls = models.JSONField(default=list, blank=True)
    image_attribution = models.CharField(max_length=255, blank=True)

    entry_fee_bdt = models.PositiveIntegerField(default=0)
    entry_fee_foreigner_bdt = models.PositiveIntegerField(default=0)
    opening_hours = models.CharField(max_length=140, default="Open 24 Hours")
    recommended_duration_hours = models.FloatField(default=4.0)
    budget_tier = models.CharField(max_length=15, choices=BUDGET_CHOICES, default="mid")
    estimated_daily_cost_bdt = models.PositiveIntegerField(default=2500)

    best_time_to_visit = models.CharField(max_length=160, default="November to March")
    seasonal_suitability = models.JSONField(
        default=dict,
        blank=True,
        help_text="Suitability scores (0-100) for winter, summer, monsoon",
    )
    is_indoor_friendly = models.BooleanField(default=False)
    rainy_day_alternative_note = models.TextField(blank=True)

    travel_tips = models.JSONField(default=list, blank=True)
    safety_tips = models.JSONField(default=list, blank=True)
    seasonal_restrictions = models.TextField(blank=True)
    verified_advisory = models.TextField(blank=True)

    interests = models.JSONField(default=list, blank=True)
    quick_tags = models.JSONField(default=list, blank=True)

    info_source = models.CharField(
        max_length=200, default="Bangladesh Tourism Board & Local Field Verification"
    )
    last_verified_date = models.DateField(null=True, blank=True)

    is_featured_hero = models.BooleanField(default=False)
    hero_headline = models.CharField(max_length=160, blank=True)
    hero_subtitle = models.CharField(max_length=220, blank=True)

    view_count = models.PositiveIntegerField(default=0)
    avg_rating = models.FloatField(default=4.7)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured_hero", "-view_count", "name"]

    def __str__(self):
        return f"{self.name} ({self.district})"


class Hotel(models.Model):
    TIER_CHOICES = [
        ("low", "Budget Stay"),
        ("mid", "Mid-Range Hotel"),
        ("luxury", "Luxury Resort"),
    ]
    LINK_STATUS_CHOICES = [
        ("active", "Verified Active"),
        ("needs_check", "Needs Verification"),
        ("broken", "Broken / Unreachable"),
    ]

