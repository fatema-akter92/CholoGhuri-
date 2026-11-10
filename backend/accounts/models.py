from django.contrib.auth.models import User
from django.db import models


class TravelerProfile(models.Model):
    BUDGET_CHOICES = [
        ("low", "Budget / Backpacker"),
        ("mid", "Mid-Range Comfort"),
        ("luxury", "Luxury / Resort"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True)
    nationality = models.CharField(max_length=80, default="Bangladesh")
    preferred_language = models.CharField(max_length=15, default="en")
    preferred_budget_tier = models.CharField(max_length=15, choices=BUDGET_CHOICES, default="mid")
    dietary_preferences = models.JSONField(default=list, blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    is_verified_guide = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"
