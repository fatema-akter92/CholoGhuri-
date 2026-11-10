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

