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
