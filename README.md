# CholoGhuri — Smart Bangladesh Tourism Guide

**Discover Bangladesh. Travel Smarter. Explore Beyond the Ordinary.**

CholoGhuri is a full-stack **Django + HTML5 + CSS3 + Vanilla JavaScript** smart tourism platform built exclusively for Bangladesh. It combines real verified photography of 30 iconic Bangladesh destinations with a Japan-guide inspired 3-second auto-sliding homepage showcase, Cyan & Off-White aesthetic, natural-language search, Google Maps interactive routing, AI travel planning, live weather backups, multilingual Show-Local translation, and full Admin analytics.

---

## Project Architecture

- **Backend**: Django 6 + Django REST Framework + SQLite (pre-seeded with 30 destinations, 20 hotels, 12 restaurants, 14 emergency facilities & local guides)
- **Frontend**: Pure semantic HTML5 Templates + Custom CSS3 (`static/css/chologhuri.css`, Cyan & Off-White theme) + Vanilla JS (`static/js/app.js`) + Leaflet OpenStreetMap
- **Media**: 60 locally verified real photographs of Bangladesh landmarks downloaded from Wikimedia Commons (`backend/media/places/`)

---

## Quick Start (Running Process)

### 1. Prerequisites
- Python **3.10+** (`python --version`)

### 2. Install Dependencies
```bash
cd chologhuri/backend
pip install -r requirements.txt
```

### 3. Run Database Migrations & Seed Verified Data
*(Note: The SQLite database is already pre-seeded, so you can skip or re-run safely anytime—the seeder is idempotent!)*
```bash
python manage.py migrate
python manage.py seed_chologhuri
```

### 4. Start the Server
```bash
python manage.py runserver
```
Then open **http://127.0.0.1:8000** in your browser!
*(On Windows, you can also double-click `start_windows.bat` directly.)*

---

## Demo Accounts

| Role | Username | Password | Access |
| :--- | :--- | :--- | :--- |
| **Traveler** | `traveler` | `CholoGhuri2026!` | Wishlist, Saved Trips, Expense Tracker, Reviews |
| **Staff Admin** | `admin` | `AdminCholo2026!` | In-App Admin Portal (`/admin-portal/`), Django Admin (`/admin/`) |

---

## Key Features & URLs

- `/` — **Homepage**: 3-second auto-sliding Bangladesh hero showcase, natural-language search (`"I have only 6 hours in Dhaka"`), 8 categories, live Open-Meteo weather suitability check
- `/destinations/` — **Tourist Explorer**: Filter by category, division, budget tier, interest, rain-safe indoor picks, or natural language
- `/destinations/<slug>/` — **Place Detail**: Real gallery, local/foreign entry fees, opening hours, tips, live 5-day weather & rainy-day alternatives, nearby hotels/food/hospitals, reviews & correction reports
- `/map/` — **Interactive Map & Route Planner**: Toggle tourist spots, hotels, restaurants & medical/police pins + calculate distance, drive time & BD transport fares (Bus, Train, Flight, Ship, CNG)
- `/planner/` — **Smart Trip & Budget Planner**: Build Half-day to 7-day plans with transport/hotel/food estimates, shareable family links (`/trips/shared/<code>/`), and Estimated vs. Actual expense tracker
- `/hotels-food/` — **Hotels & Halal/Allergy Food Explorer**: Side-by-side hotel comparison + verified Halal, Vegetarian, Nut-Free, Dairy-Free, and Shellfish-Free food filters
- `/assistant/` — **AI Travel Assistant** (+ floating `"How can we help you?"` widget on every page)
- `/translator/` — **Multilingual Translator**: 7 languages + Bengali phonetic guide + Web Speech audio + `"Show Local"` full-screen display card
- `/safety/` — **Safety, 999 & Verified Guides**: Emergency numbers, hospital/police map, advisories & local guide applications
- `/admin-portal/` — **Admin Content & AI Analytics Dashboard**: Most viewed/saved places, search analytics, AI latency/cost/quality monitoring, data freshness & link health checks, moderation queues

---

## Publishing / Production Deployment

1. Set environment variables in `backend/.env` (see `backend/.env.example`):
   - `DJANGO_SECRET_KEY=<strong-random-key>`
   - `DJANGO_DEBUG=False`
   - `DJANGO_ALLOWED_HOSTS=your-domain.com`
   - Optional: `GEMINI_API_KEY` or `OPENAI_API_KEY` for live LLM responses (works 100% offline without keys).
2. Run `python manage.py collectstatic --noinput`
3. Serve with Gunicorn (`Procfile` included for Render / Railway / Heroku):
   ```bash
   gunicorn chologhuri_project.wsgi:application --bind 0.0.0.0:8000
   ```
