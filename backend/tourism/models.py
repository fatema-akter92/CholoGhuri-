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

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name="hotels")
    city = models.CharField(max_length=80)
    division = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    tier = models.CharField(max_length=15, choices=TIER_CHOICES, default="mid")
    price_per_night_bdt = models.PositiveIntegerField(default=3500)
    rating = models.FloatField(default=4.4)
    facilities = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    booking_url = models.URLField(blank=True)
    is_verified_business = models.BooleanField(default=True)
    link_status = models.CharField(max_length=20, choices=LINK_STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-rating", "price_per_night_bdt"]

    def __str__(self):
        return f"{self.name} — {self.city}"


class Restaurant(models.Model):
    PRICE_CHOICES = [
        ("budget", "Budget (৳150–৳400)"),
        ("moderate", "Moderate (৳400–৳1,000)"),
        ("fine", "Fine Dining (৳1,000+)"),
    ]

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name="restaurants")
    city = models.CharField(max_length=80)
    division = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    cuisine_type = models.CharField(max_length=120)
    regional_specialty = models.CharField(max_length=140, blank=True)
    price_range = models.CharField(max_length=20, choices=PRICE_CHOICES, default="moderate")
    avg_meal_bdt = models.PositiveIntegerField(default=450)
    rating = models.FloatField(default=4.5)
    menu_highlights = models.JSONField(default=list, blank=True)
    opening_hours = models.CharField(max_length=120, default="10:00 AM – 11:00 PM")
    contact_phone = models.CharField(max_length=50, blank=True)
    image_url = models.CharField(max_length=500, blank=True)

    is_halal_verified = models.BooleanField(default=True)
    is_vegetarian_friendly = models.BooleanField(default=False)
    is_nut_free_safe = models.BooleanField(default=True)
    is_dairy_free_safe = models.BooleanField(default=False)
    is_shellfish_free_safe = models.BooleanField(default=True)
    dietary_notes = models.CharField(max_length=255, blank=True)
    is_verified_business = models.BooleanField(default=True)

    class Meta:
        ordering = ["-rating", "avg_meal_bdt"]

    def __str__(self):
        return f"{self.name} ({self.city})"


class SafetyFacility(models.Model):
    FACILITY_TYPES = [
        ("hospital", "Hospital / Medical Center"),
        ("pharmacy", "24h / Verified Pharmacy"),
        ("tourist_police", "Tourist Police Unit"),
        ("police", "Local Police Station"),
        ("coast_guard", "Coast Guard / Rescue"),
    ]

    name = models.CharField(max_length=180)
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES)
    city = models.CharField(max_length=80)
    division = models.CharField(max_length=80)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name="safety_facilities")
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=60)
    emergency_24h = models.BooleanField(default=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    verified_notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["division", "city", "facility_type"]

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"


class LocalGuide(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("verified", "Verified Guide"),
        ("rejected", "Rejected"),
    ]

    full_name = models.CharField(max_length=140)
    city = models.CharField(max_length=80)
    division = models.CharField(max_length=80)
    languages = models.JSONField(default=list, blank=True)
    specialties = models.JSONField(default=list, blank=True)
    daily_rate_bdt = models.PositiveIntegerField(default=2000)
    phone = models.CharField(max_length=50)
    license_ref = models.CharField(max_length=100, blank=True)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.city})"


class Review(models.Model):
    VISIT_CHOICES = [
        ("solo", "Solo Traveler"),
        ("couple", "Couple"),
        ("family", "Family"),
        ("friends", "Friends Group"),
    ]

    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="place_reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=160)
    comment = models.TextField()
    photo_url = models.CharField(max_length=500, blank=True)
    visit_type = models.CharField(max_length=20, choices=VISIT_CHOICES, default="friends")
    is_reported = models.BooleanField(default=False)
    report_reason = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.place.name} — {self.rating}★ by {self.user.username}"


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)
