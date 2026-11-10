import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"
ZIP_PATH = PROJECT_DIR.parent / "chologhuri.zip"


def verify_live_server():
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8099", "--noreload"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        ready = False
        for _ in range(25):
            try:
                r = requests.get("http://127.0.0.1:8099/api/health/", timeout=2)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.4)
        if not ready:
            raise RuntimeError("Django server failed to start on 127.0.0.1:8099")

        home = requests.get("http://127.0.0.1:8099/", timeout=5)
        foods = requests.get("http://127.0.0.1:8099/foods/", timeout=5)
        food_img = requests.get("http://127.0.0.1:8099/media/foods/kacchi-biryani.jpg", timeout=5)
        css = requests.get("http://127.0.0.1:8099/static/css/chologhuri.css", timeout=5)
        js = requests.get("http://127.0.0.1:8099/static/js/app.js", timeout=5)
        img = requests.get("http://127.0.0.1:8099/media/places/coxs-bazar.jpg", timeout=5)
        weather = requests.get("http://127.0.0.1:8099/api/places/coxs-bazar/weather/", timeout=8)
        nlp = requests.get("http://127.0.0.1:8099/api/places/?nlp=I+have+only+6+hours+in+Dhaka", timeout=5)
        trans_bn = requests.post("http://127.0.0.1:8099/api/translator/translate/", json={"text": "Where is Lalbagh Fort?", "source_lang": "en", "target_lang": "bn"}, timeout=8)
        tts_bn = requests.get("http://127.0.0.1:8099/api/translator/tts/?lang=bn&text=%E0%A6%A7%E0%A6%A8%E0%A7%8D%E0%A6%AF%E0%A6%AC%E0%A6%BE%E0%A6%A6", timeout=8)
        auth_page = requests.get("http://127.0.0.1:8099/auth/", timeout=5)
        hotel_page = requests.get("http://127.0.0.1:8099/hotels/sea-pearl-beach-resort-spa/", timeout=5)
        hotel_img = requests.get("http://127.0.0.1:8099/media/hotels/intercontinental-dhaka.jpg", timeout=5)

        print("LIVE CHECK HOME:", home.status_code, "Hero slides:", home.text.count("class=\"hero-slide"), "No hero-peek:", "hero-peek" not in home.text)
        print("LIVE CHECK FOODS:", foods.status_code, "Food Img:", food_img.status_code, len(food_img.content), "bytes")
        print("LIVE CHECK HOTEL:", hotel_page.status_code, "Hotel Img:", hotel_img.status_code, len(hotel_img.content), "bytes")
        print("LIVE CHECK CSS:", css.status_code, len(css.text), "bytes")
        print("LIVE CHECK JS:", js.status_code, len(js.text), "bytes")
        print("LIVE CHECK IMG:", img.status_code, img.headers.get("content-type"), len(img.content), "bytes")
        print("LIVE CHECK WEATHER:", weather.status_code, weather.json().get("current", {}).get("temperature_c"), "C", weather.json().get("source"))
        print("LIVE CHECK NLP 6H DHAKA:", nlp.status_code, "Matches:", nlp.json().get("count"))
        print("LIVE CHECK TRANSLATE BN:", trans_bn.status_code, trans_bn.json().get("provider"), "chars:", len(trans_bn.json().get("translated_text", "")), "| TTS:", tts_bn.status_code, tts_bn.headers.get("content-type"))
        print("LIVE CHECK AUTH CLEAN:", auth_page.status_code, "No Demo Admin:", "Demo Admin" not in auth_page.text)

        assert hotel_page.status_code == 200 and hotel_img.status_code == 200 and len(hotel_img.content) > 10000

        assert trans_bn.status_code == 200 and len(trans_bn.json().get("translated_text", "")) > 0
        assert tts_bn.status_code == 200 and "audio" in tts_bn.headers.get("content-type", "")
        assert "Demo Admin" not in auth_page.text and "AdminCholo2026" not in auth_page.text

        assert home.status_code == 200 and home.text.count("class=\"hero-slide") >= 6
        assert "Auto 5s" not in home.text and "Slide 1 /" not in home.text and "hero-peek" not in home.text and "hero-official-ribbon" not in home.text and "Developed by Fatema" in home.text
        assert foods.status_code == 200 and "1. Traditional Bangladeshi Main Dishes" in foods.text and "5. Traditional Bangladeshi Drinks" in foods.text
        assert food_img.status_code == 200 and len(food_img.content) > 10000
        # Verify every single food photo in FAMOUS_FOODS exists on disk
        sys.path.insert(0, str(BACKEND_DIR))
        from tourism.famous_foods import FAMOUS_FOODS
        for item in FAMOUS_FOODS:
            fpath = BACKEND_DIR / item["image_url"].lstrip("/")
            assert fpath.exists() and fpath.stat().st_size > 5000, f"Missing food image: {fpath}"
        print("VERIFIED ALL", len(FAMOUS_FOODS), "FOOD IMAGES ON DISK!")
        assert css.status_code == 200 and len(css.text) > 5000
        assert js.status_code == 200 and "3000" in js.text and "mt{s}.google.com" in js.text
        assert img.status_code == 200 and len(img.content) > 10000
        assert weather.status_code == 200
        assert nlp.status_code == 200 and nlp.json().get("count", 0) >= 3
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def create_project_zip():
    exclude_dirs = {"__pycache__", ".git", "node_modules", ".venv", "venv", "staticfiles"}
    count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith((".pyc", ".pyo", ".log")):
                    continue
                full_path = Path(root) / f
                arcname = Path("chologhuri") / full_path.relative_to(PROJECT_DIR)
                zf.write(full_path, arcname)
                count += 1
    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"ZIP CREATED: {ZIP_PATH} ({count} files, {size_mb:.2f} MB)")


if __name__ == "__main__":
    verify_live_server()
    create_project_zip()
