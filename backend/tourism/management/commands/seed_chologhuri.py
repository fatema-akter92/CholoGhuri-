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
        admin_user.is_superuser = True
        admin_user.save()
        TravelerProfile.objects.get_or_create(user=admin_user, defaults={"nationality": "Bangladesh"})

        traveler_user, _ = User.objects.get_or_create(
            username="traveler",
            defaults={
                "email": "traveler@chologhuri.bd",
                "first_name": "Aarav",
                "last_name": "Rahman",
            },
        )
        traveler_user.set_password("CholoGhuri2026!")
        traveler_user.save()
        TravelerProfile.objects.get_or_create(
            user=traveler_user,
            defaults={
                "nationality": "International / UK",
                "preferred_budget_tier": "mid",
                "dietary_preferences": ["halal"],
            },
        )

        # 2. Categories (Module A1 from Specification)
        categories_data = [
            ("Sea Beaches", "sea-beaches", "Waves", "Golden coastlines, coral islands, and dramatic Bay of Bengal sunsets.", 1),
            ("Hills & Nature", "hills-nature", "Mountain", "Cloud-kissed valleys, terraced tea gardens, and cascading hill rivers.", 2),
            ("Forests & Wildlife", "forests-wildlife", "Trees", "UNESCO mangrove ecosystems, freshwater swamps, and gibbon habitats.", 3),
            ("Historical Places", "historical-places", "Landmark", "Mughal forts, riverfront palaces, and ancient terracotta citadels.", 4),
            ("Archaeological & Cultural Sites", "archaeological-cultural", "Compass", "UNESCO mosque cities, lost merchant streets, and Buddhist viharas.", 5),
            ("Religious Tourism", "religious-tourism", "Sparkles", "Centuries-old mosques, ornate Hindu temples, and hilltop Buddhist shrines.", 6),
            ("Food Tourism", "food-tourism", "Utensils", "Authentic Old Dhaka biryani, Chattogram Mezban, and Sylheti culinary heritage.", 7),
            ("Hidden Gems", "hidden-gems", "Gem", "Serene haor wetlands, floating boat markets, and emerald canyon trails.", 8),
        ]
        cats = {}
        for name, slug, icon, desc, order in categories_data:
            obj, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "icon_name": icon, "description": desc, "display_order": order},
            )
            cats[slug] = obj

        today = date.today()

        # 3. 30 Iconic Bangladesh Destinations
        places_data = [
            # --- Sea Beaches ---
            {
                "slug": "coxs-bazar",
                "name": "Cox's Bazar Sea Beach",
                "cat": "sea-beaches",
                "tagline": "The world's longest unbroken natural sandy coastline stretching 120 km along the Bay of Bengal.",
                "division": "Chattogram",
                "district": "Cox's Bazar",
                "address": "Laboni & Kolatoli Beach, Marine Drive, Cox's Bazar",
                "lat": 21.4272,
                "lon": 91.9765,
                "desc": "Stretching 120 km without interruption, Cox's Bazar is Bangladesh's premier coastal gateway. From bustling Laboni and Kolatoli points to the scenic 80 km Marine Drive leading to Inani's coral boulders and Himchari waterfalls, visitors enjoy dramatic sunsets, coastal seafood, and ocean breezes.",
                "highlights": ["120 km unbroken shoreline", "Marine Drive coastal highway", "Inani Beach & Himchari Cliffs", "Dry fish market & Burmese Market"],
                "fee": 0,
                "fee_foreign": 0,
                "hours": "Open 24 Hours (Lifeguard duty 7:00 AM – 6:30 PM)",
                "dur": 8.0,
                "tier": "mid",
                "cost": 3800,
                "best": "November to March",
                "season": {"winter": 96, "summer": 72, "monsoon": 42},
                "indoor": False,
                "rain_note": "Visit Radiant Fish World aquarium, Cox's Bazar Cultural Center, or enjoy covered sea-view seafood restaurants.",
                "tips": ["Drive along Marine Drive toward Inani before sunset.", "Check tide tables and swim only inside lifeguard-flagged zones."],
                "safety": ["Avoid swimming during red-flag monsoon rip currents.", "Keep valuables secured while visiting crowded beach markets."],
                "restr": "Rough sea warnings issued occasionally June–September.",
                "advisory": "Verified active; Tourist Police booths operate along Laboni, Sugandha & Kolatoli.",
                "interests": ["sea", "nature", "food", "family", "photography"],
                "tags": ["weekend", "beach", "sunset", "flight-hub"],
                "hero": True,
                "hero_h": "THE HORIZON OF COX'S BAZAR",
                "hero_s": "120 km of golden Bay of Bengal shoreline & Marine Drive vistas",
                "views": 1840,
                "rating": 4.8,
            },
            {
                "slug": "saint-martins-island",
                "name": "Saint Martin's Island",
                "cat": "sea-beaches",
                "tagline": "Bangladesh's only coral island — crystal-clear turquoise waters, coconut groves, and starry skies.",
                "division": "Chattogram",
                "district": "Cox's Bazar",
                "address": "Teknaf Coast, Bay of Bengal (Narikel Jinjira)",
                "lat": 20.6276,
                "lon": 92.3233,
                "desc": "Locally known as Narikel Jinjira (Coconut Island), Saint Martin's is a tranquil 8 sq km coral island at Bangladesh's southernmost tip. Cycle around sandy lanes, walk across low-tide coral shelves to Chhera Dwip, and savor freshly grilled red snapper under clear night skies.",
                "highlights": ["Turquoise Bay of Bengal waters", "Chhera Dwip tidal coral extension", "Fresh beachside BBQ snapper", "No private cars — cycling & walking"],
                "fee": 0,
                "fee_foreign": 0,
                "hours": "Ferry departures 9:00 AM – 9:30 AM (Seasonal)",
                "dur": 24.0,
                "tier": "mid",
                "cost": 4800,
                "best": "November to February",
                "season": {"winter": 97, "summer": 45, "monsoon": 15},
                "indoor": False,
                "rain_note": "Ferries pause during monsoon; substitute with Inani Beach or Teknaf Nature Reserve.",
                "tips": ["Book government-approved tourist ship tickets 5–7 days in advance.", "Carry cash as ATMs are limited on the island."],
                "safety": ["Do not remove corals or shells (strictly protected ecological zone).", "Wear reef sandals when walking near rocky tidal pools."],
                "restr": "Tourist ferries closed Apr–Oct & subject to daily visitor cap regulations.",
                "advisory": "Ecological conservation zone: single-use plastics restricted.",
                "interests": ["sea", "nature", "adventure", "photography", "food"],
                "tags": ["island", "coral", "seasonal"],
                "hero": True,
                "hero_h": "CORAL SERENITY OF SAINT MARTIN'S",
                "hero_s": "Turquoise tides and coconut-fringed coral shores",
                "views": 1620,
                "rating": 4.9,
            },
            {
                "slug": "kuakata",
                "name": "Kuakata Sea Beach",
                "cat": "sea-beaches",
                "tagline": "Daughter of the Sea — rare panoramic beach offering both sunrise and sunset over the ocean.",
