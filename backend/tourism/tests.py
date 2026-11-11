from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase


class CholoGhuriSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_chologhuri")

    def test_public_html_pages_render(self):
        client = Client()
        for url in [
            "/",
            "/foods/",
            "/festivals/",
            "/festivals/?season=winter-upcoming",
            "/foods/?section=main-dishes",
            "/foods/?section=street-foods",
            "/foods/?section=sweets-desserts",
            "/foods/?section=pitha",
            "/foods/?section=drinks",
            "/destinations/",
            "/destinations/?nlp=I+have+only+6+hours+in+Dhaka",
            "/destinations/coxs-bazar/",
            "/map/",
            "/planner/",
            "/hotels-food/",
            "/hotels-food/?tab=food&halal=1",
            "/hotels/sea-pearl-beach-resort-spa/",
            "/assistant/",
            "/translator/",
            "/translator/?lang=bn",
            "/translator/?lang=ar",
            "/translator/?lang=ja",
            "/translator/?lang=hi",
            "/translator/?lang=fr",
            "/translator/?lang=es",
            "/safety/",
            "/auth/",
            "/trips/shared/CHOLO5BD30/",
        ]:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200, f"Failed on {url}")
            self.assertNotIn("Module ", resp.content.decode("utf-8"), f"Found residual Module label on {url}")

        auth_html = client.get("/auth/").content.decode("utf-8")
        self.assertNotIn("Demo Admin", auth_html)
        self.assertNotIn("AdminCholo2026", auth_html)
        self.assertIn("chologhuribd@gmail.com", auth_html)
        home_html = client.get("/").content.decode("utf-8")
        self.assertIn("Seasonal &amp; Upcoming Festivals of Bangladesh", home_html)
        fest_html = client.get("/festivals/").content.decode("utf-8")
        for expected in (
            "Eid-ul-Fitr",
            "Eid-ul-Adha",
            "Dhaka International Trade Fair",
            "Jabbarer Boli Khela",
            "Nouka Baich",
            "Manipuri Rash Utsab",
            "Hason Raja Utsab",
            "Buddha Purnima",
            "Christmas in Bangladesh",
        ):
            self.assertIn(expected, fest_html)
        bn_html = client.get("/translator/?lang=bn").content.decode("utf-8")
        self.assertNotIn("<strong>HI:</strong>", bn_html)

        # Verify EN -> BN custom translation returns pure Bengali Unicode (no Hindi, no Banglish warning)
        from tourism.services.translator_service import translate_text
        for phrase in ("Good morning", "How are you?", "Where is the hotel?", "This food is delicious", "I want to go to Cox's Bazar"):
            out = translate_text(phrase, "en", "bn")["translated_text"]
            self.assertTrue(any("\u0980" <= c <= "\u09ff" for c in out), f"Missing Bengali script for {phrase}: {out}")
            self.assertFalse(any("\u0900" <= c <= "\u097f" for c in out), f"Hindi script leaked for {phrase}: {out}")
            self.assertNotIn("Offline phonetic guide", out)
            self.assertNotIn("ব্যাগোবো", out)

    def test_trip_planner_budget_ordering(self):
        from tourism.services.itinerary_engine import build_smart_itinerary

        for days in (0.5, 1.0, 3.0, 5.0, 7.0):
            for target_bdt in (10000, 30000, 90000):
                low = build_smart_itinerary("Dhaka", days, f"{days}d", target_bdt, "low")["estimated_breakdown"]["total_bdt"]
                mid = build_smart_itinerary("Dhaka", days, f"{days}d", target_bdt, "mid")["estimated_breakdown"]["total_bdt"]
                lux = build_smart_itinerary("Dhaka", days, f"{days}d", target_bdt, "luxury")["estimated_breakdown"]["total_bdt"]
                self.assertLess(low, mid, f"Expected low < mid for days={days}, target={target_bdt}")
                self.assertLess(mid, lux, f"Expected mid < luxury for days={days}, target={target_bdt}")

    def test_api_endpoints(self):
        client = Client()
        self.assertEqual(client.get("/api/health/").status_code, 200)
        places = client.get("/api/places/?nlp=6+hours+in+Dhaka").json()
        self.assertGreater(places["count"], 0)

        ai = client.post(
            "/api/ai/chat/",
            {"prompt": "5 days budget 30000 nature sea historical food"},
            content_type="application/json",
        )
        self.assertEqual(ai.status_code, 200)
        self.assertIn("generated_itinerary", ai.json())

        route = client.get("/api/routes/plan/?start=Dhaka&destination=coxs-bazar")
        self.assertEqual(route.status_code, 200)
        self.assertGreater(route.json()["road_distance_km"], 100)

        trans = client.post(
            "/api/translator/translate/",
            {"text": "Hello", "source_lang": "en", "target_lang": "bn"},
            content_type="application/json",
        )
        self.assertEqual(trans.status_code, 200)
        self.assertTrue(len(trans.json()["translated_text"]) > 0)

    def test_authenticated_user_and_admin_portal(self):
        client = Client()
        self.assertTrue(client.login(username="traveler", password="CholoGhuri2026!"))
        self.assertEqual(client.get("/dashboard/").status_code, 200)
        self.assertEqual(client.get("/admin-portal/").status_code, 302)  # redirects non-staff

        admin_client = Client()
        self.assertTrue(admin_client.login(username="admin", password="AdminCholo2026!"))
        self.assertEqual(admin_client.get("/admin-portal/").status_code, 200)
        self.assertEqual(admin_client.get("/api/admin/analytics/").status_code, 200)
