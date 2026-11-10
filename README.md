# CholoGhuri — Smart Bangladesh Tourism Guide

"More Than a Travel Map — A Smarter Way to Explore Bangladesh."

![Django](https://img.shields.io/badge/DJANGO-6.1.1-092E20?style=for-the-badge&logo=django&logoColor=white) ![Python](https://img.shields.io/badge/PYTHON-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white) ![HTML5 & CSS3](https://img.shields.io/badge/HTML5_%26_CSS3-CYAN_OFFWHITE-06B6D4?style=for-the-badge&logo=html5&logoColor=white) ![Google Maps & Leaflet](https://img.shields.io/badge/GOOGLE_MAPS_%26_LEAFLET-1.9.4-2563EB?style=for-the-badge&logo=googlemaps&logoColor=white) ![DRF](https://img.shields.io/badge/REST_FRAMEWORK-3.18.1-A30000?style=for-the-badge&logo=django&logoColor=white) ![Bangladesh Coverage](https://img.shields.io/badge/COVERAGE-8_DIVISIONS-0284C7?style=for-the-badge&logo=openstreetmap&logoColor=white) ![Developer](https://img.shields.io/badge/DEVELOPED_BY-FATEMA-0E7490?style=for-the-badge)

---

#### Visit the Livelink: 

---

## 🎯 Overview

**Bangladesh** is a land of remarkable contrasts woven together by winding rivers, emerald plains, and timeless heritage. Within a single journey across its **eight divisions**, travelers can watch dawn break over the unbroken golden sands of **Cox's Bazar** and coral reefs of **Saint Martin's Island**, climb into drifting monsoon clouds above **Sajek Valley** and **Bandarban**, wander misty tea gardens in **Sreemangal**, glide across the mirrored wetlands of **Tanguar Haor** and the **Sundarbans** mangrove forest, and trace centuries of terracotta temples, Mughal forts, and Old Dhaka's vibrant culinary streets.

**CholoGhuri** is built to turn that richness into an effortless, confident travel experience. Crafted as a full-stack **Django + Django REST Framework + HTML5/CSS3 + Vanilla JavaScript** platform with a crisp **Cyan & Off-White** interface, it brings together **30 verified destinations** with authentic photography, **natural-language trip discovery**, **Open-Meteo live weather & rainy-day backups**, **Google Maps & Leaflet routing** with intercity fare estimates, **20 verified hotels with online booking**, **42 iconic Bangladeshi dishes across 5 regional sections**, **real-time Bengali translation with voice audio**, and **national `999` emergency safety support**—helping every visitor explore Bangladesh smarter.

---

## ✨ Key Features

- **Clean Fullscreen Bangladesh Showcase:** 3-second smooth auto-sliding hero photography featuring iconic Bangladesh landmarks in pure imagery without text clutter.
- **Smart Natural-Language Discovery:** Understands everyday queries such as `"I have only 6 hours in Dhaka"`, `"rainy day budget hill trip"`, or division-based filters.
- **Live Open-Meteo Weather & Rain Backups:** Displays live destination temperature, conditions, 5-day outlooks, and indoor/rain-safe alternatives when monsoon weather hits.
- **Google Maps & Leaflet Interactive Routing:** Explore verified tourist spots, hotels, restaurants, hospitals, and Tourist Police pins with intercity distance, travel time, and fare estimates (Bus, Train, Air, Launch, CNG).
- **Verified Stays & Online Hotel Booking:** Compare hotels side-by-side, inspect real hotel photography, book rooms online (`/hotels/<slug>/`), or jump directly to the official hotel website / booking page.
- **Famous Bangladeshi Foods Guide (`/foods/`):** 5 organized culinary sections (**Main Dishes**, **Street Foods**, **Sweets & Desserts**, **Traditional Pitha**, and **Drinks**) paired with local photography, origin divisions, and tourist tasting notes.
- **Multilingual Live Translator & Bengali TTS:** Real-time translation into clean Bengali and global languages with audio voice playback and a fullscreen **"Show Local"** card for drivers and vendors.
- **Smart Multi-Day Trip Planner & AI Assistant:** Build half-day to 7-day Bangladesh itineraries with itemized budget estimates, shareable public links (`/trips/shared/<code>/`), and conversational travel help.
- **Travel Safety Bar & Helpline (`999`):** Persistent safety header and district directory for Bangladesh Tourist Police, emergency hospitals, fire services, and solo/monsoon safety checklists.
- **Staff-Restricted Admin & Analytics Portal (`/admin-portal/`):** Search analytics, popular destination demand, AI query tracking, hotel booking records, and feedback moderation accessible strictly to authorized staff.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python `3.12+`, Django `6.1.1`, Django REST Framework `3.18.1` |
| **Frontend UI** | Semantic HTML5 Templates, Pure CSS3 (`chologhuri.css`), Vanilla JavaScript (`app.js`) |
| **Maps & Routing** | Leaflet `1.9.4` + Google Maps Tile Layers (`mt{s}.google.com`) + Haversine Route Engine |
| **Live Integrations** | Open-Meteo Weather API, Google Translate & Bengali TTS Proxy, Optional Gemini / OpenAI Keys |
| **Database & Static** | SQLite (pre-seeded `db.sqlite3`), WhiteNoise `6.7+`, Gunicorn `22.0+` |
| **Local Verified Media** | Wikimedia Commons curated photos (`backend/media/places/`, `foods/`, `hotels/`) |

---

## Core Routes & Modules

| Route | Module | Purpose |
| :--- | :--- | :--- |
| `/` | Homepage | Fullscreen destination hero carousel, NLP search bar & featured places |
| `/destinations/` | Destination Explorer | Filter 30 Bangladesh landmarks by division, budget, category, or weather safety |
| `/destinations/<slug>/` | Place Detail | Photo gallery, live weather, distance estimator, nearby stays & reviews |
| `/foods/` | Culinary Guide | 42 authentic Bangladeshi dishes grouped by category & famous regions |
| `/hotels-food/` | Hotels & Dining | Verified hotels, side-by-side comparison tray & halal/allergy food explorer |
| `/hotels/<slug>/` | Online Booking | Hotel room reservation checkout, amenities & official website link |
| `/planner/` | Smart Trip Planner | Multi-day schedule builder, cost breakdown & shareable trip URLs |
| `/map/` | Interactive Map | Searchable Google Maps / Leaflet directory across places, hotels & SOS pins |
| `/safety/` | Safety & 999 SOS | Emergency numbers, Tourist Police stations, hospitals & safety guides |
| `/translator/` | Live Translator | Clean Bengali & multilingual translator with voice audio & Show Local view |
| `/assistant/` | AI Travel Assistant | Conversational Bangladesh travel Q&A widget & dedicated assistant page |
| `/auth/` & `/dashboard/` | Traveler Account | Account registration/sign-in, saved itineraries, bookings & reviews |
| `/admin-portal/` | Admin Portal | Staff-only analytics, booking oversight & feedback moderation |

---- 

### Author

Developed by **Fatema**

----------

 #### "To travel through Bangladesh is to read a living poem of winding rivers, green hills, timeless heritage, and golden hospitality — every road leads to a story waiting to be discovered."*
 **— CholoGhuri | Explore Bangladesh Smarter**
