import json
import re
import time
from django.conf import settings
import requests

from tourism.models import AIQueryLog, Hotel, Place, Restaurant, SafetyFacility
from tourism.services.itinerary_engine import build_smart_itinerary
from tourism.services.nlp_search import parse_natural_language_query, search_places_nlp


def _call_optional_llm(prompt: str, context_summary: str):
    """
    If GEMINI_API_KEY or OPENAI_API_KEY is configured in .env, enriches the response
    using real LLM APIs while staying strictly grounded in CholoGhuri's verified database.
    """
    gemini_key = getattr(settings, "GEMINI_API_KEY", "")
    openai_key = getattr(settings, "OPENAI_API_KEY", "")

    system_msg = (
        "You are CholoGhuri AI, the official Smart Bangladesh Tourism Guide assistant. "
        "Respond concisely in clear English for local and international tourists. "
        "Always ground recommendations in the verified Bangladesh facts below, include budget estimates in BDT, "
        "and mention safety/weather advice when relevant.\n\n"
        f"Verified Context:\n{context_summary}"
    )

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_msg}\n\nUser Question: {prompt}"}]}]
            }
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata", {})
                tokens = int(usage.get("totalTokenCount", 350))
                return text, "gemini-2.0-flash", tokens, round(tokens * 0.0000004, 6)
        except Exception:
            pass

    if openai_key:
