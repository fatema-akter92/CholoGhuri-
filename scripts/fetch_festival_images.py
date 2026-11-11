import json
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image

HEADERS = {
    "User-Agent": "CholoGhuriTourismApp/1.0 (https://chologhuri.example; chologhuribd@gmail.com)"
}

BASE_DIR = Path(__file__).resolve().parent.parent
FESTIVAL_MEDIA_DIR = BASE_DIR / "backend" / "media" / "festivals"
MANIFEST_PATH = BASE_DIR / "scripts" / "festival_image_manifest.json"

FESTIVAL_TARGETS = [
    {
        "slug": "rash-mela",
        "wiki": ["Rash Mela", "Dublar Char"],
        "queries": ["Rash Mela Bangladesh", "Dublar Char Bangladesh", "Sundarbans Bangladesh sunset river"],
    },
    {
        "slug": "nabanna-utsab",
        "wiki": ["Nabanna", "Paddy field Bangladesh"],
        "queries": ["Nabanna festival Bangladesh", "Paddy harvest Bangladesh", "Rice harvest Bangladesh rural"],
    },
    {
        "slug": "lalon-smaran-utsab",
        "wiki": ["Lalon", "Baul"],
        "queries": ["Lalon Akhra Kushtia", "Baul singer Bangladesh", "Lalon Mela Bangladesh"],
    },
    {
        "slug": "poush-mela",
        "wiki": ["Pitha"],
        "queries": ["Pitha festival Bangladesh", "Bhapa pitha Bangladesh", "Sonargaon folk Bangladesh"],
    },
    {
        "slug": "shakrain-festival",
        "wiki": ["Shakrain"],
        "queries": ["Shakrain Festival Dhaka", "Shakrain kite flying Old Dhaka", "Kite festival Bangladesh"],
    },
    {
        "slug": "ekushey-boi-mela",
        "wiki": ["Ekushey Book Fair", "Shaheed Minar, Dhaka"],
        "queries": ["Ekushey Book Fair Dhaka", "Amar Ekushey Book Fair", "Shaheed Minar Dhaka"],
    },
    {
        "slug": "basanta-utsab",
        "wiki": ["Pohela Falgun"],
        "queries": ["Pohela Falgun Dhaka", "Basanta Utsab Bangladesh", "Charukala Dhaka University"],
    },
    {
        "slug": "pahela-baishakh",
        "wiki": ["Pohela Boishakh", "Mangal Shobhajatra"],
        "queries": ["Mangal Shobhajatra", "Pahela Baishakh Dhaka", "Pohela Boishakh Bangladesh"],
    },
    {
        "slug": "boishabi-utsab",
        "wiki": ["Biju festival", "Chittagong Hill Tracts"],
        "queries": ["Boishabi festival Bangladesh", "Rangamati indigenous festival", "Bandarban Sangrai water festival"],
    },
    {
        "slug": "nouka-baich",
        "wiki": ["Nouka Baich"],
        "queries": ["Nouka Baich Bangladesh", "Boat race Bangladesh river"],
    },
    {
        "slug": "durga-puja",
        "wiki": ["Dhakeshwari Temple"],
        "queries": ["Durga Puja Dhaka Bangladesh", "Dhakeshwari Temple Dhaka", "Durga Puja pandal Bangladesh"],
    },
    {
        "slug": "eid-sholakia",
        "wiki": ["Sholakia"],
        "queries": ["Sholakia Eidgah Kishoreganj", "Eid-ul-Fitr Bangladesh mosque", "Baitul Mukarram Eid Bangladesh"],
    },
]


def is_good(url):
    if not url:
        return False
    low = url.lower()
    if any(ext in low for ext in (".svg", ".gif", ".pdf", ".tif", ".webm", ".ogv")):
        return False
    if any(bad in low for bad in ("flag_", "map_", "logo", "icon", "coat_of", "signature")):
        return False
    return True


def get_candidates(item):
    cands = []
    for title in item["wiki"]:
        u = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"
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
                    if info.get("mime") in ("image/jpeg", "image/png", "image/webp") and info.get("width", 0) >= 500:
                        u = info.get("thumburl") or info.get("url")
                        if is_good(u):
                            cands.append(u)
        except Exception:
            pass
    return list(dict.fromkeys(cands))


def main():
    FESTIVAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for item in FESTIVAL_TARGETS:
        slug = item["slug"]
        dest = FESTIVAL_MEDIA_DIR / f"{slug}.jpg"
        saved = False
        for url in get_candidates(item):
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                r.raise_for_status()
                im = Image.open(BytesIO(r.content)).convert("RGB")
                w, h = im.size
                if w < 450 or h < 280:
                    continue
                if w > 1100:
                    im = im.resize((1100, int(h * (1100 / w))), Image.Resampling.LANCZOS)
                im.save(dest, format="JPEG", quality=86, optimize=True)
                manifest[slug] = {"local_url": f"/media/festivals/{dest.name}", "source_url": url, "size": list(im.size)}
                print(f"[SAVED] {dest.name} ({im.size[0]}x{im.size[1]}) <- {url[:75]}")
                saved = True
                break
            except Exception as e:
                print(f"  skip {slug}: {e}")
        if not saved:
            print(f"[MISSING] {slug}")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Done! Total festival images: {len(manifest)}/{len(FESTIVAL_TARGETS)}")


if __name__ == "__main__":
    main()
