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

    intent = {
        "raw_query": q,
        "duration_hours": None,
        "duration_days": None,
        "budget_bdt": None,
        "budget_tier": None,
        "locations": [],
        "interests": [],
        "indoor_only": False,
        "keywords": [],
    }

    # Extract hours e.g. "6 hours", "only 4 hrs", "half day"
    hr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)\b", lower)
    if hr_match:
        intent["duration_hours"] = float(hr_match.group(1))
    elif "half day" in lower or "half-day" in lower:
        intent["duration_hours"] = 5.0

    # Extract days e.g. "5 days", "3 day", "weekend"
    day_match = re.search(r"(\d+)\s*(?:day|days)\b", lower)
    if day_match:
        intent["duration_days"] = int(day_match.group(1))
        if intent["duration_hours"] is None:
            intent["duration_hours"] = int(day_match.group(1)) * 10.0
    elif "weekend" in lower:
        intent["duration_days"] = 2

    # Extract budget in BDT (e.g. "30,000", "30000 tk", "5000 taka", "15k")
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", lower)
    bdt_match = re.search(r"(\d[\d,]{2,})\s*(?:bdt|tk|taka|৳)?", lower)
    if k_match:
        intent["budget_bdt"] = int(float(k_match.group(1)) * 1000)
    elif bdt_match:
        val = int(bdt_match.group(1).replace(",", ""))
        if val >= 200:
            intent["budget_bdt"] = val

    if any(w in lower for w in ("cheap", "low cost", "low-cost", "budget", "backpacker", "free")):
        intent["budget_tier"] = "low"
    elif any(w in lower for w in ("luxury", "resort", "premium", "5 star", "5-star")):
        intent["budget_tier"] = "luxury"

    if any(w in lower for w in ("rain", "rainy", "monsoon", "indoor", "wet")):
        intent["indoor_only"] = True

    # Location hints
    for key, mapped_districts in CITY_SYNONYMS.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            for d in mapped_districts:
                if d not in intent["locations"]:
                    intent["locations"].append(d)

    # Interests
    for interest, words in INTEREST_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(w)}\b", lower) for w in words):
            intent["interests"].append(interest)

    # Remaining meaningful keywords
    stop_words = {
        "i", "have", "only", "in", "at", "for", "with", "my", "is", "the", "a", "an", "and",
        "or", "to", "of", "on", "near", "best", "places", "place", "visit", "want", "travel",
        "bangladesh", "trip", "tour", "hours", "hour", "hrs", "days", "day", "budget", "taka", "bdt",
        "love", "like", "show", "me", "find", "good", "top", "around",
    }
    tokens = [t for t in re.findall(r"[a-z0-9']+", lower) if t not in stop_words and len(t) > 2]
    intent["keywords"] = tokens[:8]
    return intent


def search_places_nlp(raw_query: str, queryset=None):
    qs = queryset if queryset is not None else Place.objects.select_related("category").all()
    intent = parse_natural_language_query(raw_query)

    if not raw_query.strip():
        return intent, "Showing all verified destinations across Bangladesh.", qs

    filtered = qs
    notes = []

    if intent["locations"]:
        loc_q = Q()
        for loc in intent["locations"]:
            loc_q |= (
                Q(division__icontains=loc)
                | Q(district__icontains=loc)
                | Q(address__icontains=loc)
            )
        loc_matches = filtered.filter(loc_q)
