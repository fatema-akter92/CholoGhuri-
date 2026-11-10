import json
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
HOTEL_DIR = BASE_DIR / "backend" / "media" / "hotels"
MANIFEST_PATH = BASE_DIR / "scripts" / "hotel_image_manifest.json"

HOTEL_SEARCHES = [
    ("sea-pearl-beach-resort-spa", [], ["Sea Pearl Beach Resort", "Luxury beach resort Cox's Bazar", "Beach resort pool"]),
    ("sayeman-beach-resort", [], ["Sayeman Beach Resort", "Resort swimming pool ocean view"]),
    ("hotel-kollol-by-jz-group", [], ["Hotel building Cox's Bazar", "Modern hotel room"]),
    ("ocean-breeze-backpackers-stay", [], ["Hostel guesthouse bedroom", "Cozy budget hotel room"]),
    ("coral-view-resort-saint-martin", [], ["Tropical beach cottage palm trees", "Island beach resort bungalow"]),
    ("kuakata-grand-hotel-sea-resorts", [], ["Coastal hotel resort pool", "Seaside hotel exterior"]),
    ("megh-kabbo-eco-hill-resort", [], ["Sajek Valley cottage resort", "Wooden mountain cottage Bangladesh"]),
    ("sairu-hill-resort", [], ["Sairu Hill Resort Bandarban", "Hilltop infinity pool resort"]),
    ("hill-view-residential-hotel", [], ["Mountain town hotel building", "Hotel double bedroom"]),
    ("aronnyok-holiday-resort", [], ["Lakeside cottage resort", "Kaptai lake resort cottage"]),
    ("grand-sultan-tea-resort-golf", ["Grand Sultan Tea Resort"], ["Grand Sultan Sreemangal", "Luxury tea resort pool"]),
    ("balishira-resort", [], ["Eco resort garden cottage", "Tea garden cottage Sreemangal"]),
    ("rose-view-hotel-sylhet", [], ["Rose View Hotel Sylhet", "Boutique hotel lobby"]),
    ("jatra-flagship-hotel-khulna", [], ["Business hotel suite bedroom", "Modern hotel room interior"]),
    ("pashur-riverside-lodge-mongla", [], ["Riverside wooden lodge", "Forest eco lodge wooden"]),
    ("intercontinental-dhaka", ["InterContinental Dhaka"], ["InterContinental Dhaka", "Dhaka luxury hotel exterior"]),
    ("fars-hotel-resorts", [], ["Dhaka hotel building", "Deluxe hotel suite room"]),
    ("old-dhaka-heritage-guesthouse", [], ["Heritage boutique hotel room", "Vintage guesthouse interior"]),
    ("momo-inn-resort-bogura", [], ["Momo Inn Bogura", "Luxury resort exterior pool"]),
    ("bongotori-tanguar-houseboat", [], ["Tanguar Haor houseboat", "Wooden houseboat Bangladesh"]),
]


def is_good(url):
    if not url:
        return False
    low = url.lower()
    if any(ext in low for ext in (".svg", ".gif", ".pdf", ".tif", ".webm", ".ogv")):
        return False
    if any(bad in low for bad in ("flag_", "map_", "logo", "icon", "coat_of", "diagram")):
        return False
    return True


def fetch_urls(wiki_titles, queries):
    urls = []
    for t in wiki_titles:
        try:
            r = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(t.replace(' ', '_'))}",
                headers=HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                d = r.json()
                for k in ("originalimage", "thumbnail"):
                    im = d.get(k)
                    if im and is_good(im.get("source", "")):
                        urls.append(im["source"])
                        break
        except Exception:
            pass
    for q in queries:
        try:
            r = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {q}",
                    "gsrnamespace": 6,
                    "gsrlimit": 8,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime",
                    "iiurlwidth": 1100,
                    "format": "json",
                },
                headers=HEADERS,
                timeout=12,
            )
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
                    info = (p.get("imageinfo") or [{}])[0]
                    w, h = info.get("width", 0), info.get("height", 0)
                    if info.get("mime") in ("image/jpeg", "image/png", "image/webp") and w >= 550 and w >= h:
                        u = info.get("thumburl") or info.get("url")
                        if is_good(u):
                            urls.append(u)
        except Exception:
            pass
    return list(dict.fromkeys(urls))


def main():
    HOTEL_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    used_urls = set()

    for slug, wiki, queries in HOTEL_SEARCHES:
        dest = HOTEL_DIR / f"{slug}.jpg"
        if dest.exists() and dest.stat().st_size > 8000:
            manifest[slug] = f"/media/hotels/{dest.name}"
            print(f"[SKIP] {slug}")
            continue
        urls = fetch_urls(wiki, queries)
        saved = False
        ordered = [u for u in urls if u not in used_urls] + [u for u in urls if u in used_urls]
        for u in ordered:
            try:
                r = requests.get(u, headers=HEADERS, timeout=18)
                r.raise_for_status()
                im = Image.open(BytesIO(r.content)).convert("RGB")
                w, h = im.size
                if w < 450 or h < 280:
                    continue
                if w > 1200:
                    im = im.resize((1200, int(h * (1200 / w))), Image.Resampling.LANCZOS)
                im.save(dest, format="JPEG", quality=85, optimize=True)
                manifest[slug] = f"/media/hotels/{dest.name}"
                used_urls.add(u)
                print(f"[SAVED] {slug}.jpg ({im.size[0]}x{im.size[1]})")
                saved = True
                break
            except Exception:
                continue
        if not saved:
            print(f"[MISSING] {slug}")
        time.sleep(0.15)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Done! {len(manifest)}/{len(HOTEL_SEARCHES)}")


if __name__ == "__main__":
    main()
