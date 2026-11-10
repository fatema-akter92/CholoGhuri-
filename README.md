# CholoGhuri — Smart Bangladesh Tourism Guide

"More Than a Travel Map — A Smarter Way to Explore Bangladesh."

![Django](https://img.shields.io/badge/DJANGO-6.1.1-092E20?style=for-the-badge&logo=django&logoColor=white) ![Python](https://img.shields.io/badge/PYTHON-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white) ![HTML5 & CSS3](https://img.shields.io/badge/HTML5_%26_CSS3-CYAN_OFFWHITE-06B6D4?style=for-the-badge&logo=html5&logoColor=white) ![Google Maps & Leaflet](https://img.shields.io/badge/GOOGLE_MAPS_%26_LEAFLET-1.9.4-2563EB?style=for-the-badge&logo=googlemaps&logoColor=white) ![DRF](https://img.shields.io/badge/REST_FRAMEWORK-3.18.1-A30000?style=for-the-badge&logo=django&logoColor=white) ![Bangladesh Coverage](https://img.shields.io/badge/COVERAGE-8_DIVISIONS-0284C7?style=for-the-badge&logo=openstreetmap&logoColor=white) ![Developer](https://img.shields.io/badge/DEVELOPED_BY-FATEMA-0E7490?style=for-the-badge)

---

Visit the Livelink: https://chologhuri.onrender.com/ *(Render blueprint ready — replace with your live Render URL after deployment)*

---

## 🎯 Overview

**CholoGhuri** is a full-stack **Django + Django REST Framework + HTML5/CSS3 + Vanilla JavaScript** smart tourism platform designed exclusively for exploring **Bangladesh**. Built with a crisp **Cyan & Off-White** visual system, it brings together **30 iconic destinations**, **20 verified hotels & resorts with online reservation**, **42 curated traditional Bangladeshi foods across 5 sections**, **live weather forecasts**, **natural-language discovery**, **Google Maps-powered interactive routing**, **real-time Bengali translation with voice audio**, and **national 999 travel safety tools**.

---

## ✨ Key Features

- **🖼️ Clean Fullscreen Bangladesh Showcase:** 3-second smooth auto-sliding hero photography featuring iconic Bangladesh landmarks in pure imagery without text clutter.
- **🔎 Smart Natural-Language Discovery:** Understands everyday queries such as `"I have only 6 hours in Dhaka"`, `"rainy day budget hill trip"`, or division-based filters.
- **🌦️ Live Open-Meteo Weather & Rain Backups:** Displays live destination temperature, conditions, 5-day outlooks, and indoor/rain-safe alternatives when monsoon weather hits.
- **🗺️ Google Maps & Leaflet Interactive Routing:** Explore verified tourist spots, hotels, restaurants, hospitals, and Tourist Police pins with intercity distance, travel time, and fare estimates (Bus, Train, Air, Launch, CNG).
- **🏨 Verified Stays & Online Hotel Booking:** Compare hotels side-by-side, inspect real hotel photography, book rooms online (`/hotels/<slug>/`), or jump directly to the official hotel website / booking page.
- **🍛 Famous Bangladeshi Foods Guide (`/foods/`):** 5 organized culinary sections (**Main Dishes**, **Street Foods**, **Sweets & Desserts**, **Traditional Pitha**, and **Drinks**) paired with local photography, origin divisions, and tourist tasting notes.
- **🗣️ Multilingual Live Translator & Bengali TTS:** Real-time translation into clean Bengali and global languages with audio voice playback and a fullscreen **"Show Local"** card for drivers and vendors.
- **🧭 Smart Multi-Day Trip Planner & AI Assistant:** Build half-day to 7-day Bangladesh itineraries with itemized budget estimates, shareable public links (`/trips/shared/<code>/`), and conversational travel help.
- **🚨 Travel Safety Bar & Helpline (`999`):** Persistent safety header and district directory for Bangladesh Tourist Police, emergency hospitals, fire services, and solo/monsoon safety checklists.
- **📊 Staff-Restricted Admin & Analytics Portal (`/admin-portal/`):** Search analytics, popular destination demand, AI query tracking, hotel booking records, and feedback moderation accessible strictly to authorized staff.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python `3.12+`, Django `6.1.1`, Django REST Framework `3.18.1` |
| **Frontend UI** | Semantic HTML5 Templates, Pure CSS3 (`chologhuri.css`), Vanilla JavaScript (`app.js`) |
| **Maps & Routing** | Leaflet `1.9.4` + Google Maps Tile Layers (`mt{s}.google.com`) + Haversine Route Engine |
| **Live Integrations** | Open-Meteo Weather API, Google Translate & Bengali TTS Proxy, Optional Gemini / OpenAI Keys |
| **Database & Static** | SQLite (pre-seeded `db.sqlite3`), WhiteNoise `6.7+`, Gunicorn `22.0+` |
| **Local Verified Media** | Wikimedia Commons curated photos (`backend/media/places/`, `foods/`, `hotels/`) |

---

## 🧭 Core Routes & Modules

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

---

## 📂 Project Structure

```text
chologhuri/
├── Procfile                  # Gunicorn web command with migrate & collectstatic
├── render.yaml               # One-click Render Blueprint deployment config
├── runtime.txt               # Python 3.12.7 runtime pin
├── README.md                 # Project overview and documentation
├── start_windows.bat         # Quick Windows local server launcher
├── scripts/                  # Real photo fetchers, manifests & live verification runner
└── backend/
    ├── manage.py
    ├── requirements.txt
    ├── db.sqlite3            # Pre-seeded Bangladesh tourism database
    ├── chologhuri_project/   # Core Django settings, URLs, WSGI
    ├── accounts/             # Custom traveler & staff user authentication API
    ├── tourism/              # Models, famous_foods catalog, DRF APIs, web views & services
    │   ├── management/commands/seed_chologhuri.py
    │   ├── services/         # AI assistant, itinerary, NLP search, route, translator & weather
    │   └── migrations/
    ├── static/               # CSS3 stylesheet, Vanilla JS & vendored Leaflet 1.9.4
    ├── templates/            # Django HTML5 responsive templates
    └── media/                # Verified local photos (places/, foods/, hotels/)
```

---

## ⚙️ Quick Start (Local Development)

### 1. Prerequisites
- Python **3.10+** (`3.12+` recommended)

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/fatema-akter92/chologhuri.git
cd chologhuri/backend
pip install -r requirements.txt
```

### 3. Migrate & Verify Seeded Database
*(The SQLite database is pre-seeded with 30 places, 20 hotels, 12 restaurants, and 14 safety facilities; `seed_chologhuri` is idempotent and safe to re-run anytime.)*
```bash
python manage.py migrate
python manage.py seed_chologhuri
```

### 4. Run Tests & Start Server
```bash
python manage.py test -v 2
python manage.py runserver
```
Open **`http://127.0.0.1:8000`** in your browser *(or double-click `start_windows.bat` on Windows)*.

---

## 🚀 Deployment (Render Blueprint)

1. Push this repository to GitHub (`main` branch).
2. In **Render Dashboard**, choose **New + → Blueprint** and select your repository.
3. Render automatically reads [`render.yaml`](render.yaml), installs `backend/requirements.txt`, executes migrations and `collectstatic`, and boots Gunicorn with production `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
4. *(Optional)* Add `GEMINI_API_KEY` or `OPENAI_API_KEY` in environment variables for live LLM responses (works cleanly with built-in smart fallback even without external keys).

---

## 👩‍💻 Author

Developed by **Fatema**
