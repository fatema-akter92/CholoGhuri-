import json
from datetime import date, timedelta
from pathlib import Path
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import TravelerProfile
from tourism.models import (
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
from tourism.services.itinerary_engine import build_smart_itinerary


class Command(BaseCommand):
    help = "Seed CholoGhuri with verified Bangladesh tourism data, real photos, hotels, food, safety & analytics."

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[4]
        manifest_path = base_dir / "scripts" / "image_manifest.json"
        manifest = {}
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        def get_imgs(slug):
            entry = manifest.get(slug, {})
            files = entry.get("files") or [f"/media/places/{slug}.jpg"]
            attrs = entry.get("attributions") or []
            attr_str = (
                f"{attrs[0].get('title', slug)} ({attrs[0].get('license', 'Wikimedia Commons')})"
                if attrs
                else "Wikimedia Commons Verified"
            )
            return files[0], files, attr_str

        # 1. Demo Users (Traveler & Staff Admin)
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@chologhuri.bd",
                "first_name": "CholoGhuri",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("AdminCholo2026!")
        admin_user.is_staff = True
