import re
from django.db.models import Q
from tourism.models import Place

CITY_SYNONYMS = {
    "dhaka": ["Dhaka", "Narayanganj"],
    "old dhaka": ["Dhaka"],
    "chittagong": ["Chattogram", "Cox's Bazar", "Bandarban", "Rangamati"],
    "chattogram": ["Chattogram", "Cox's Bazar", "Bandarban", "Rangamati"],
    "cox": ["Cox's Bazar"],
    "coxs bazar": ["Cox's Bazar"],
    "sylhet": ["Sylhet", "Moulvibazar", "Sunamganj"],
    "sreemangal": ["Moulvibazar", "Sylhet"],
    "khulna": ["Khulna", "Bagerhat"],
    "sundarbans": ["Khulna", "Bagerhat"],
    "rajshahi": ["Rajshahi", "Bogura", "Naogaon"],
    "bogra": ["Bogura"],
    "bogura": ["Bogura"],
    "barishal": ["Barishal", "Patuakhali", "Jhalokathi"],
    "barisal": ["Barishal", "Patuakhali", "Jhalokathi"],
    "kuakata": ["Patuakhali"],
    "rangpur": ["Dinajpur", "Rangpur"],
    "bandarban": ["Bandarban"],
    "rangamati": ["Rangamati"],
    "sajek": ["Rangamati"],
    "cumilla": ["Cumilla"],
    "comilla": ["Cumilla"],
}

INTEREST_KEYWORDS = {
    "sea": ["sea", "beach", "island", "ocean", "coral", "coast", "sunset", "sunrise"],
    "nature": ["nature", "hill", "hills", "mountain", "cloud", "waterfall", "tea", "river", "haor", "lake", "green"],
    "wildlife": ["forest", "tiger", "wildlife", "mangrove", "gibbon", "bird", "jungle", "swamp"],
    "historical": ["history", "historical", "fort", "palace", "mughal", "ancient", "heritage", "museum", "archaeological"],
    "spiritual": ["mosque", "temple", "monastery", "buddhist", "religious", "shrine", "masjid"],
    "food": ["food", "eat", "biryani", "mezban", "tea", "cuisine", "restaurant", "street food", "culinary"],
    "adventure": ["trek", "hike", "boat", "kayak", "waterfall", "trail", "camping", "offbeat", "hidden"],
}


def parse_natural_language_query(raw_query: str):
    q = (raw_query or "").strip()
    lower = q.lower()

