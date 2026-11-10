import json
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
MANIFEST_PATH = BASE_DIR / "scripts" / "food_image_manifest.json"

FOOD_TARGETS = [
    {"slug": "kacchi-biryani", "wiki": ["Kacchi Biryani", "Biryani"], "queries": ["Kacchi Biryani", "Mutton biryani Bangladesh"]},
    {"slug": "shorshe-ilish", "wiki": ["Ilish", "Shorshe ilish"], "queries": ["Shorshe ilish", "Ilish mach bhaja", "Hilsa fish curry"]},
    {"slug": "kala-bhuna", "wiki": ["Kala bhuna", "Mezban"], "queries": ["Kala bhuna", "Beef bhuna Bangladesh"]},
    {"slug": "bhuna-khichuri", "wiki": ["Khichdi", "Khichuri"], "queries": ["Bhuna khichuri", "Bengali khichuri"]},
    {"slug": "beef-shatkora", "wiki": ["Shatkora"], "queries": ["Beef curry Bangladesh", "Bangladeshi beef curry"]},
    {"slug": "seven-layer-tea", "wiki": ["Seven Color Tea"], "queries": ["Seven Color Tea", "Seven layer tea Bangladesh"]},
    {"slug": "fuchka-chotpoti", "wiki": ["Panipuri", "Chotpoti"], "queries": ["Fuchka Bangladesh", "Chotpoti Bangladesh", "Fuchka"]},
    {"slug": "bakarkhani", "wiki": ["Bakarkhani"], "queries": ["Bakarkhani", "Bakarkhani Dhaka"]},
    {"slug": "bogura-doi-roshmalai", "wiki": ["Mishti doi", "Rasmalai"], "queries": ["Mishti doi", "Bogura doi", "Rasmalai"]},
    {"slug": "panta-ilish", "wiki": ["Panta bhat"], "queries": ["Panta ilish", "Panta bhat ilish"]},
    {"slug": "bhapa-pitha", "wiki": ["Bhapa pitha", "Pitha"], "queries": ["Bhapa pitha", "Bengali pitha"]},
    {"slug": "chui-jhal", "wiki": ["Chui jhal"], "queries": ["Mutton curry Bangladesh", "Chui jhal"]},
]


def is_good(url):
    if not url:
        return False
    low = url.lower()
    if any(ext in low for ext in (".svg", ".gif", ".pdf", ".tif", ".webm", ".ogv")):
        return False
    if any(bad in low for bad in ("flag_", "map_", "logo", "icon", "coat_of")):
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
                    "gsrlimit": 5,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime",
                    "iiurlwidth": 1000,
                    "format": "json",
                },
                headers=HEADERS,
                timeout=12,
            )
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
                    info = (p.get("imageinfo") or [{}])[0]
                    if info.get("mime") in ("image/jpeg", "image/png", "image/webp") and info.get("width", 0) >= 500:
                        u = info.get("thumburl") or info.get("url")
                        if is_good(u):
                            cands.append(u)
        except Exception:
            pass
    return list(dict.fromkeys(cands))


def main():
    FOOD_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for item in FOOD_TARGETS:
        slug = item["slug"]
        dest = FOOD_MEDIA_DIR / f"{slug}.jpg"
        if dest.exists() and dest.stat().st_size > 8000:
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
                if w < 400 or h < 260:
                    continue
                if w > 1100:
                    im = im.resize((1100, int(h * (1100 / w))), Image.Resampling.LANCZOS)
                im.save(dest, format="JPEG", quality=85, optimize=True)
                manifest[slug] = f"/media/foods/{dest.name}"
                print(f"[SAVED] {slug}.jpg ({im.size[0]}x{im.size[1]})")
                saved = True
                break
            except Exception as e:
                print(f"  fail {slug}: {e}")
        if not saved:
            print(f"[MISSING] {slug}")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Done! Total foods:", len(manifest))


if __name__ == "__main__":
    main()
