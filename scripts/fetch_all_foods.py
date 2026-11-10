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
FOOD_MEDIA_DIR = BASE_DIR / "backend" / "media" / "foods"
MANIFEST_PATH = BASE_DIR / "scripts" / "food_all_manifest.json"

TARGETS = [
    {"slug": "kacchi-biryani", "wiki": ["Kacchi Biryani"], "queries": ["Kacchi Biryani Dhaka"]},
    {"slug": "beef-tehari", "wiki": ["Tehari", "Tahri (dish)"], "queries": ["Beef Tehari Dhaka", "Tehari rice"]},
    {"slug": "morog-polao", "wiki": ["Pilaf", "Chicken biryani"], "queries": ["Morog Polao", "Chicken pulao"]},
    {"slug": "shorshe-ilish", "wiki": ["Shorshe ilish"], "queries": ["Shorshe ilish"]},
    {"slug": "bhuna-khichuri", "wiki": ["Khichdi"], "queries": ["Bhuna khichuri"]},
    {"slug": "mezbani-beef", "wiki": ["Mezban"], "queries": ["Mezbani beef", "Beef curry Bangladesh"]},
    {"slug": "kala-bhuna", "wiki": ["Kala bhuna"], "queries": ["Kala bhuna"]},
    {"slug": "chui-jhal", "wiki": ["Chui jhal"], "queries": ["Mutton curry Bangladesh"]},
    {"slug": "bhorta-rice", "wiki": ["Bhorta"], "queries": ["Aloo bhorta", "Bangladeshi bhorta platter"]},
    {"slug": "prawn-malai-curry", "wiki": ["Chingri malai curry"], "queries": ["Chingri malai curry", "Prawn malai curry"]},
    {"slug": "beef-shatkora", "wiki": ["Shatkora"], "queries": ["Beef curry Bangladesh"]},
    {"slug": "panta-ilish", "wiki": ["Panta bhat"], "queries": ["Panta ilish"]},

    # Street Foods
    {"slug": "fuchka-chotpoti", "wiki": ["Panipuri"], "queries": ["Fuchka Bangladesh"]},
    {"slug": "chotpoti", "wiki": ["Chotpoti"], "queries": ["Chotpoti", "Chotpoti Bangladesh"]},
    {"slug": "jhalmuri", "wiki": ["Jhalmuri"], "queries": ["Jhalmuri", "Jhal muri"]},
    {"slug": "mughlai-paratha", "wiki": ["Mughlai paratha"], "queries": ["Mughlai paratha"]},
    {"slug": "bakarkhani", "wiki": ["Bakarkhani"], "queries": ["Bakarkhani"]},
    {"slug": "singara", "wiki": ["Samosa"], "queries": ["Bengali singara", "Singara"]},
    {"slug": "samosa", "wiki": ["Samosa"], "queries": ["Samosa crispy"]},
    {"slug": "haleem", "wiki": ["Haleem"], "queries": ["Haleem", "Shahi haleem"]},
    {"slug": "piyaju", "wiki": ["Pakora"], "queries": ["Piyaju Bangladesh", "Onion pakora"]},

    # Sweets & Desserts
    {"slug": "bogura-doi", "wiki": ["Mishti doi"], "queries": ["Mishti doi", "Bogura doi"]},
    {"slug": "comilla-roshmalai", "wiki": ["Rasmalai"], "queries": ["Rasmalai", "Roshmalai"]},
    {"slug": "tangail-chomchom", "wiki": ["Cham cham"], "queries": ["Chomchom", "Cham cham sweet"]},
    {"slug": "natore-kachagolla", "wiki": ["Kachagolla", "Sandesh (confectionery)"], "queries": ["Kachagolla", "Natore kachagolla", "Bengali sandesh"]},
    {"slug": "muktagacha-monda", "wiki": ["Monda (sweet)", "Peda"], "queries": ["Muktagacha Monda", "Monda sweet Bangladesh"]},
    {"slug": "rasgulla", "wiki": ["Rasgulla"], "queries": ["Rasgulla", "Roshogolla"]},
    {"slug": "kalojam", "wiki": ["Gulab jamun", "Kalojam"], "queries": ["Kalojam", "Kala jamun"]},
    {"slug": "sandesh", "wiki": ["Sandesh (confectionery)"], "queries": ["Sandesh Bengali sweet"]},
    {"slug": "jilapi", "wiki": ["Jalebi"], "queries": ["Jalebi", "Jilapi Bangladesh"]},

    # Pitha
    {"slug": "bhapa-pitha", "wiki": ["Bhapa pitha"], "queries": ["Bhapa pitha"]},
    {"slug": "patishapta", "wiki": ["Patishapta", "Pitha"], "queries": ["Patishapta", "Patishapta pitha"]},
    {"slug": "chitoi-pitha", "wiki": ["Chitoi pitha", "Pitha"], "queries": ["Chitoi pitha"]},
    {"slug": "puli-pitha", "wiki": ["Puli pitha", "Pitha"], "queries": ["Puli pitha", "Bhaja puli pitha"]},
    {"slug": "nakshi-pitha", "wiki": ["Nakshi pitha", "Pitha"], "queries": ["Nakshi pitha"]},
    {"slug": "dudh-puli", "wiki": ["Dudh puli", "Pitha"], "queries": ["Dudh puli pitha", "Dudh puli"]},
    {"slug": "teler-pitha", "wiki": ["Malpua", "Pitha"], "queries": ["Teler pitha", "Pakan pitha", "Poya pitha"]},

    # Drinks
    {"slug": "borhani", "wiki": ["Borhani"], "queries": ["Borhani", "Borhani Bangladesh"]},
    {"slug": "lassi", "wiki": ["Lassi"], "queries": ["Sweet lassi", "Lassi"]},
    {"slug": "sugarcane-juice", "wiki": ["Sugarcane juice"], "queries": ["Sugarcane juice"]},
    {"slug": "coconut-water", "wiki": ["Coconut water", "Coconut"], "queries": ["Green coconut water", "King coconut drink"]},
    {"slug": "seven-layer-tea", "wiki": ["Seven Color Tea"], "queries": ["Seven Color Tea"]},
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


def get_candidates(item):
    cands = []
    for t in item["wiki"]:
        u = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(t.replace(' ', '_'))}"
        try:
            r = requests.get(u, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                d = r.json()
                for k in ("originalimage", "thumbnail"):
                    im = d.get(k)
                    if im and is_good(im.get("source", "")):
                        cands.append(im["source"])
                        break
        except Exception:
            pass
    for q in item["queries"]:
        try:
            r = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {q}",
                    "gsrnamespace": 6,
                    "gsrlimit": 6,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime",
                    "iiurlwidth": 900,
                    "format": "json",
                },
                headers=HEADERS,
                timeout=12,
            )
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
                    info = (p.get("imageinfo") or [{}])[0]
                    if info.get("mime") in ("image/jpeg", "image/png", "image/webp") and info.get("width", 0) >= 400:
                        u = info.get("thumburl") or info.get("url")
                        if is_good(u):
                            cands.append(u)
        except Exception:
            pass
    return list(dict.fromkeys(cands))


def main():
    FOOD_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for item in TARGETS:
        slug = item["slug"]
        dest = FOOD_MEDIA_DIR / f"{slug}.jpg"
        if dest.exists() and dest.stat().st_size > 6000:
            manifest[slug] = f"/media/foods/{dest.name}"
            print(f"[SKIP] {slug}")
            continue
        saved = False
        for url in get_candidates(item):
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                r.raise_for_status()
                im = Image.open(BytesIO(r.content)).convert("RGB")
                w, h = im.size
                if w < 350 or h < 220:
                    continue
                if w > 1000:
                    im = im.resize((1000, int(h * (1000 / w))), Image.Resampling.LANCZOS)
                im.save(dest, format="JPEG", quality=85, optimize=True)
                manifest[slug] = f"/media/foods/{dest.name}"
                print(f"[SAVED] {slug}.jpg ({im.size[0]}x{im.size[1]})")
                saved = True
                break
            except Exception:
                continue
        if not saved:
            print(f"[MISSING] {slug}")
        time.sleep(0.15)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    missing = [t["slug"] for t in TARGETS if t["slug"] not in manifest]
    print(f"Done! Total: {len(manifest)}/{len(TARGETS)}, Missing: {missing}")


if __name__ == "__main__":
    main()
