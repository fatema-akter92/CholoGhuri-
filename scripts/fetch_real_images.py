import json
import os
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image

HEADERS = {
    "User-Agent": "CholoGhuriTourismApp/1.0 (https://chologhuri.example; contact@chologhuri.bd)"
}

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_PLACES_DIR = BASE_DIR / "backend" / "media" / "places"
MANIFEST_PATH = BASE_DIR / "scripts" / "image_manifest.json"

TARGETS = [
    {
        "slug": "coxs-bazar",
        "wiki_titles": ["Cox's Bazar", "Cox's Bazar Beach"],
        "commons_queries": ["Cox's Bazar sea beach sunset", "Cox's Bazar beach Bangladesh"],
    },
    {
        "slug": "saint-martins-island",
        "wiki_titles": ["St. Martin's Island"],
        "commons_queries": ["Saint Martin Island Bangladesh", "St Martin's Island beach Bangladesh"],
    },
    {
        "slug": "kuakata",
        "wiki_titles": ["Kuakata", "Kuakata Beach"],
        "commons_queries": ["Kuakata sea beach", "Kuakata Bangladesh"],
    },
    {
        "slug": "patenga",
        "wiki_titles": ["Patenga"],
        "commons_queries": ["Patenga Sea Beach", "Patenga Chattogram"],
    },
    {
        "slug": "sajek-valley",
        "wiki_titles": ["Sajek Valley"],
        "commons_queries": ["Sajek Valley", "Sajek clouds Bangladesh"],
    },
    {
        "slug": "bandarban",
        "wiki_titles": ["Nilgiri Tourist Center", "Boga Lake", "Bandarban District"],
        "commons_queries": ["Nilgiri Bandarban", "Boga Lake Bandarban"],
    },
    {
        "slug": "rangamati",
        "wiki_titles": ["Kaptai Lake", "Rangamati"],
        "commons_queries": ["Hanging Bridge Rangamati", "Kaptai Lake Rangamati"],
    },
    {
        "slug": "jaflong",
        "wiki_titles": ["Jaflong"],
        "commons_queries": ["Jaflong Sylhet", "Jaflong river Bangladesh"],
    },
    {
        "slug": "sreemangal",
        "wiki_titles": ["Sreemangal Upazila"],
        "commons_queries": ["Sreemangal tea garden", "Sylhet tea garden Bangladesh"],
    },
    {
        "slug": "ratargul",
        "wiki_titles": ["Ratargul Swamp Forest"],
        "commons_queries": ["Ratargul Swamp Forest", "Ratargul Sylhet"],
    },
    {
        "slug": "sundarbans",
        "wiki_titles": ["Sundarbans", "Sundarbans National Park"],
        "commons_queries": ["Sundarbans Bangladesh", "Sundarbans mangrove Bangladesh"],
    },
    {
        "slug": "lawachara",
        "wiki_titles": ["Lawachara National Park"],
        "commons_queries": ["Lawachara National Park", "Lawachara forest"],
    },
    {
        "slug": "lalbagh-fort",
        "wiki_titles": ["Lalbagh Fort"],
        "commons_queries": ["Lalbagh Fort Dhaka"],
    },
    {
        "slug": "ahsan-manzil",
        "wiki_titles": ["Ahsan Manzil"],
        "commons_queries": ["Ahsan Manzil Dhaka"],
    },
    {
        "slug": "mahasthangarh",
        "wiki_titles": ["Mahasthangarh"],
        "commons_queries": ["Mahasthangarh Bogra", "Mahasthangarh Bangladesh"],
    },
    {
        "slug": "paharpur",
        "wiki_titles": ["Somapura Mahavihara"],
        "commons_queries": ["Somapura Mahavihara Paharpur"],
    },
    {
        "slug": "shat-gambuj-mosque",
        "wiki_titles": ["Sixty Dome Mosque"],
        "commons_queries": ["Sixty Dome Mosque Bagerhat", "Shat Gambuj Mosque"],
    },
    {
        "slug": "sonargaon",
        "wiki_titles": ["Panam Nagar", "Sonargaon"],
        "commons_queries": ["Panam Nagar Sonargaon", "Sonargaon Folk Arts"],
    },
    {
        "slug": "mainamati",
        "wiki_titles": ["Shalban Vihara", "Mainamati"],
        "commons_queries": ["Shalban Vihara", "Mainamati Comilla"],
    },
    {
        "slug": "star-mosque",
        "wiki_titles": ["Star Mosque"],
        "commons_queries": ["Star Mosque Dhaka", "Tara Masjid Dhaka"],
    },
    {
        "slug": "dhakeshwari-temple",
        "wiki_titles": ["Dhakeshwari Temple"],
        "commons_queries": ["Dhakeshwari Temple Dhaka"],
    },
    {
        "slug": "kantajew-temple",
        "wiki_titles": ["Kantajew Temple"],
        "commons_queries": ["Kantajew Temple Dinajpur"],
    },
    {
        "slug": "buddha-dhatu-jadi",
        "wiki_titles": ["Buddha Dhatu Jadi"],
        "commons_queries": ["Buddha Dhatu Jadi Bandarban", "Golden Temple Bandarban"],
    },
    {
        "slug": "old-dhaka-food",
        "wiki_titles": ["Kacchi Biryani", "Dhakaiya cuisine", "Bangladeshi cuisine"],
        "commons_queries": ["Kacchi Biryani Dhaka", "Haji Biryani Dhaka", "Bangladeshi biryani"],
    },
    {
        "slug": "chattogram-mezban",
        "wiki_titles": ["Mezban", "Kala bhuna", "Bangladeshi cuisine"],
        "commons_queries": ["Kala bhuna", "Mezban Chittagong", "Bangladeshi curry"],
    },
    {
        "slug": "sylhet-tea-food",
        "wiki_titles": ["Seven Color Tea"],
        "commons_queries": ["Seven Color Tea", "Seven layer tea Sreemangal"],
    },
    {
        "slug": "tanguar-haor",
        "wiki_titles": ["Tanguar Haor"],
        "commons_queries": ["Tanguar Haor", "Tanguar Haor Sunamganj"],
    },
    {
        "slug": "nikli-haor",
        "wiki_titles": ["Nikli Upazila", "Mithamain Upazila"],
        "commons_queries": ["Nikli Haor", "Haor Kishoreganj Bangladesh"],
    },
    {
        "slug": "bhimruli-guava-market",
        "wiki_titles": ["Bhimruli"],
        "commons_queries": ["Bhimruli floating guava market", "Floating guava market Barishal"],
    },
    {
        "slug": "nafakhum-debotakhum",
        "wiki_titles": ["Nafakhum", "Amiakhum"],
        "commons_queries": ["Nafakhum waterfall", "Debotakhum Bandarban"],
    },
]


def is_good_photo_url(url: str) -> bool:
    if not url:
        return False
    lower = url.lower()
    bad_ext = (".svg", ".gif", ".pdf", ".tif", ".tiff", ".ogv", ".webm")
    if any(ext in lower for ext in bad_ext):
        return False
    bad_words = ("flag_of", "coat_of_arms", "map_of", "locator", "blank_map", "emblem", "logo", "icon")
    if any(w in lower for w in bad_words):
        return False
    return True


def fetch_wiki_summary_candidates(titles):
    candidates = []
    for title in titles:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                for key in ("originalimage", "thumbnail"):
                    img = data.get(key)
                    if img and is_good_photo_url(img.get("source", "")):
                        src = img["source"]
                        # Prefer <=1600px thumb if Wikimedia original is huge
                        candidates.append({
                            "url": src,
                            "source_page": data.get("content_urls", {}).get("desktop", {}).get("page", url),
                            "title": data.get("title", title),
                        })
                        break
        except Exception:
            pass
    return candidates


def fetch_commons_candidates(queries):
    candidates = []
    api = "https://commons.wikimedia.org/w/api.php"
    for q in queries:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {q}",
            "gsrnamespace": 6,
            "gsrlimit": 6,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1280,
            "format": "json",
        }
        try:
            r = requests.get(api, params=params, headers=HEADERS, timeout=15)
            if r.status_code == 200:
