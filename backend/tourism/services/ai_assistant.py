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
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 550,
                },
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                text = data["choices"][0]["message"]["content"]
                tokens = int(data.get("usage", {}).get("total_tokens", 380))
                return text, "openai-gpt-4o-mini", tokens, round(tokens * 0.0000006, 6)
        except Exception:
            pass

    return None, "chologhuri-engine", 0, 0.0


def generate_ai_response(prompt: str, user=None):
    t0 = time.perf_counter()
    clean_prompt = (prompt or "").strip()
    lower = clean_prompt.lower()
    intent = parse_natural_language_query(clean_prompt)

    is_trip_request = bool(
        intent["duration_days"]
        or intent["budget_bdt"]
        or any(w in lower for w in ("itinerary", "plan", "schedule", "days", "day trip", "trip"))
    )
    is_weather_or_closed = any(
        w in lower for w in ("rain", "weather", "closed", "monsoon", "alternative", "storm", "cyclone")
    )
    is_safety_query = any(
        w in lower for w in ("safe", "safety", "emergency", "hospital", "police", "999", "scam", "permit")
    )
    is_food_query = any(
        w in lower for w in ("food", "eat", "biryani", "mezban", "halal", "vegetarian", "allergy", "restaurant")
    )

    _, _, matched_places = search_places_nlp(clean_prompt)
    top_places = matched_places[:4] if matched_places else list(Place.objects.all()[:4])

    plan_payload = None
    if is_trip_request:
        days = intent["duration_days"] or (0.5 if intent["duration_hours"] and intent["duration_hours"] <= 6 else 3)
        budget = intent["budget_bdt"] or (8000 if days <= 1 else days * 5500)
        tier = intent["budget_tier"] or ("low" if (budget / max(1, days)) < 3200 else "luxury" if (budget / max(1, days)) > 9500 else "mid")
        label = "half day" if days < 1 else f"{int(days)} days"
        plan_payload = build_smart_itinerary(
            start_city=intent["locations"][0] if intent["locations"] else "Dhaka",
            duration_days=days,
            duration_label=label,
            budget_bdt=budget,
            budget_tier=tier,
            interests=intent["interests"] or ["nature", "historical", "food"],
            weather_aware=True,
        )

    # Build grounded deterministic response
    lines = []
    if plan_payload:
        bd = plan_payload["estimated_breakdown"]
        lines.append(
            f"Here is a personalized **{plan_payload['duration_label']} Bangladesh smart itinerary** "
            f"tailored to your **৳{plan_payload['budget_bdt']:,} BDT** budget ({plan_payload['budget_tier']} tier):"
        )
        for day in plan_payload["itinerary"]:
            lines.append(
                f"• **{day['title']}** — Stay: {day['hotel']['name'] if day['hotel'] else 'Day trip'} | "
                f"Food: {day['restaurant']['name'] if day['restaurant'] else 'Local dining'} "
                f"(Est. ৳{day['estimated_day_cost_bdt']:,})"
            )
        lines.append(
            f"\n**Estimated Total:** ৳{bd['total_bdt']:,} "
            f"(Transport ৳{bd['transport_bdt']:,} • Hotels ৳{bd['hotel_bdt']:,} • "
            f"Food ৳{bd['food_bdt']:,} • Entry Fees ৳{bd['entry_fees_bdt']:,})."
        )
        lines.append(
            "\n*Weather & Backup Note:* If heavy rain affects outdoor spots, indoor heritage sites like "
            "Ahsan Manzil, Star Mosque, or regional culinary trails are included as instant swaps."
        )
    elif is_weather_or_closed:
        indoor_places = list(Place.objects.filter(is_indoor_friendly=True)[:4])
        lines.append("If rain or seasonal closures affect outdoor coastal/hill attractions in Bangladesh, here are verified alternatives:")
        for p in indoor_places:
            lines.append(f"• **{p.name} ({p.district})**: {p.rainy_day_alternative_note or p.tagline}")
        lines.append("\n**Tip:** Always verify sea-crossing advisories before Saint Martin's Island (open mainly Nov–Mar) and carry waterproof gear in Sylhet during monsoon.")
    elif is_safety_query:
        lines.append("**Bangladesh Tourist Safety & Emergency Quick Guide:**")
        lines.append("• **National Emergency (Police / Ambulance / Fire):** Dial **999** (24/7 toll-free)")
        lines.append("• **Tourist Police Control Room:** **01320-222222** (Cox's Bazar, Dhaka, Sylhet & major hubs)")
        facilities = list(SafetyFacility.objects.filter(emergency_24h=True)[:3])
        for f in facilities:
            lines.append(f"• **{f.name} ({f.city})** — {f.get_facility_type_display()}: `{f.phone}`")
        lines.append("\n*Reminder:* Carry passport/NID copies when traveling to Sajek Valley, Bandarban, or Rangamati security checkpoints.")
    elif is_food_query:
        rests = list(Restaurant.objects.all()[:4])
        lines.append("**Top Verified Regional Food & Dietary-Safe Picks in Bangladesh:**")
        for r in rests:
            flags = []
            if r.is_halal_verified:
                flags.append("Halal Verified")
            if r.is_vegetarian_friendly:
                flags.append("Veg Friendly")
            if r.is_nut_free_safe:
                flags.append("Nut-Free Safe")
            lines.append(
                f"• **{r.name} ({r.city})** — {r.cuisine_type} (~৳{r.avg_meal_bdt}/meal) | "
                f"Highlights: {', '.join(r.menu_highlights[:2])} [{', '.join(flags)}]"
            )
    else:
        lines.append(f"Here are the best verified Bangladesh picks for your query:")
        for p in top_places:
            fee_txt = "Free entry" if p.entry_fee_bdt == 0 else f"৳{p.entry_fee_bdt} local / ৳{p.entry_fee_foreigner_bdt} foreign"
            lines.append(
                f"• **{p.name} ({p.district}, {p.division})** — {p.tagline} "
                f"(Best time: {p.best_time_to_visit} • {fee_txt})"
            )
        lines.append("\nAsk me to build a day-by-day budget itinerary, check rainy-day backups, or find nearby verified hotels & hospitals!")

    fallback_reply = "\n".join(lines)

    context_summary = "\n".join(
        [
            f"- {p.name} ({p.district}, {p.category.name}): fee {p.entry_fee_bdt} BDT, daily cost ~{p.estimated_daily_cost_bdt} BDT, best {p.best_time_to_visit}."
