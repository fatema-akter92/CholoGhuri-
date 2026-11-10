/* CholoGhuri Core Interactions — Vanilla JS */

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

async function apiFetch(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
    ...(options.headers || {}),
  };
  const resp = await fetch(url, { ...options, headers });
  const text = await resp.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!resp.ok) {
    throw new Error(data?.detail || `Error ${resp.status}`);
  }
  return data;
}

/* 1. Mobile Navigation Drawer */
document.addEventListener("DOMContentLoaded", () => {
  const mobileBtn = document.getElementById("mobileMenuBtn");
  const mobileDrawer = document.getElementById("mobileDrawer");
  if (mobileBtn && mobileDrawer) {
    mobileBtn.addEventListener("click", () => {
      mobileDrawer.classList.toggle("open");
    });
  }

  /* 2. Top Utility Language Quick Jump */
  const navLangSelect = document.getElementById("navLangSelect");
  if (navLangSelect) {
    navLangSelect.addEventListener("change", (e) => {
      const code = e.target.value;
      if (code && code !== "en") {
        window.location.href = `/translator/?lang=${encodeURIComponent(code)}`;
      }
    });
  }

  /* 3. 3-Second Auto-Sliding Hero Carousel */
  const heroSlides = Array.from(document.querySelectorAll(".hero-slide"));
  const heroDots = Array.from(document.querySelectorAll(".hero-dot"));
  const heroWrapper = document.getElementById("heroCarousel");

  if (heroSlides.length > 0) {
    let current = 0;
    let paused = false;

    const showSlide = (idx) => {
      current = (idx + heroSlides.length) % heroSlides.length;
      heroSlides.forEach((s, i) => s.classList.toggle("active", i === current));
      heroDots.forEach((d, i) => d.classList.toggle("active", i === current));
    };

    document.getElementById("heroPrevBtn")?.addEventListener("click", () => showSlide(current - 1));
    document.getElementById("heroNextBtn")?.addEventListener("click", () => showSlide(current + 1));
    heroDots.forEach((dot, idx) => {
      dot.addEventListener("click", () => showSlide(idx));
    });

    if (heroWrapper) {
      heroWrapper.addEventListener("mouseenter", () => (paused = true));
      heroWrapper.addEventListener("mouseleave", () => (paused = false));
    }

    // Strict 3-second auto-slide interval
    setInterval(() => {
      if (!paused) {
        showSlide(current + 1);
      }
    }, 3000);
  }

  /* 4. Wishlist Heart Toggle */
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".wish-btn[data-place-id]");
    if (!btn) return;
    e.preventDefault();
    const placeId = parseInt(btn.getAttribute("data-place-id"), 10);
    try {
      const res = await apiFetch("/api/wishlist/toggle/", {
        method: "POST",
        body: JSON.stringify({ place_id: placeId }),
      });
      btn.classList.toggle("saved", res.wishlisted);
      btn.innerHTML = res.wishlisted ? "&#9829;" : "&#9825;";
      const badge = document.getElementById("navWishlistCount");
      if (badge) {
        const curr = parseInt(badge.textContent || "0", 10);
        badge.textContent = Math.max(0, curr + (res.wishlisted ? 1 : -1));
      }
    } catch {
      window.location.href = `/auth/?next=${encodeURIComponent(window.location.pathname)}`;
    }
  });

  /* 5. Floating AI Assistant Drawer */
  const aiToggle = document.getElementById("aiFabBtn");
  const aiDrawer = document.getElementById("aiDrawer");
  const aiClose = document.getElementById("aiDrawerClose");
  const aiForm = document.getElementById("aiDrawerForm");
  const aiInput = document.getElementById("aiDrawerInput");
  const aiMsgs = document.getElementById("aiDrawerMsgs");

  if (aiToggle && aiDrawer) {
    aiToggle.addEventListener("click", () => {
      aiDrawer.classList.toggle("open");
      if (aiDrawer.classList.contains("open")) aiInput?.focus();
    });
    aiClose?.addEventListener("click", () => aiDrawer.classList.remove("open"));
  }

  const appendFloatingMsg = (text, isUser = false, extraData = null) => {
    if (!aiMsgs) return;
    const div = document.createElement("div");
    div.className = `msg-bubble ${isUser ? "msg-user" : "msg-ai"}`;
    div.textContent = text;

    if (!isUser && extraData?.recommended_places?.length) {
      const links = document.createElement("div");
      links.style.marginTop = "8px";
      links.style.display = "flex";
      links.style.flexWrap = "wrap";
      links.style.gap = "5px";
      extraData.recommended_places.slice(0, 3).forEach((p) => {
        const a = document.createElement("a");
        a.href = `/destinations/${p.slug}/`;
        a.className = "badge badge-cyan";
        a.textContent = `${p.name} →`;
        links.appendChild(a);
      });
      div.appendChild(links);
    }

    aiMsgs.appendChild(div);
    aiMsgs.scrollTop = aiMsgs.scrollHeight;
  };

  if (aiForm && aiInput) {
    aiForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const q = aiInput.value.trim();
      if (!q) return;
      appendFloatingMsg(q, true);
      aiInput.value = "";
      const thinking = document.createElement("div");
      thinking.className = "msg-bubble msg-ai";
      thinking.textContent = "Planning your Bangladesh answer...";
      aiMsgs.appendChild(thinking);
      aiMsgs.scrollTop = aiMsgs.scrollHeight;

      try {
        const res = await apiFetch("/api/ai/chat/", {
          method: "POST",
          body: JSON.stringify({ prompt: q }),
        });
        thinking.remove();
        appendFloatingMsg(res.reply, false, res);
      } catch (err) {
        thinking.textContent = `Could not reach AI assistant: ${err.message}`;
      }
    });

    document.querySelectorAll("[data-ai-quick]").forEach((chip) => {
      chip.addEventListener("click", () => {
        aiInput.value = chip.getAttribute("data-ai-quick");
        aiForm.dispatchEvent(new Event("submit"));
      });
    });
  }
});

/* Helper: Native Pronunciation (Server MP3 Audio first so Bengali never falls back to Hindi, with Web Speech fallback) */
let activeTtsAudio = null;
function speakPhrase(text, langCode = "bn-BD") {
  if (!text) return;
  const shortLang = (langCode || "bn").split("-")[0].toLowerCase();
  try {
    if (activeTtsAudio) {
      activeTtsAudio.pause();
      activeTtsAudio = null;
    }
    const ttsUrl = `/api/translator/tts/?lang=${encodeURIComponent(shortLang)}&text=${encodeURIComponent(text)}`;
    const audio = new Audio(ttsUrl);
    activeTtsAudio = audio;
    audio.play().catch(() => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = langCode;
        utter.rate = 0.92;
        window.speechSynthesis.speak(utter);
      }
    });
  } catch {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = langCode;
      utter.rate = 0.92;
      window.speechSynthesis.speak(utter);
    }
  }
}

/* Helper: Open Show Local Modal */
function openShowLocalModal(nativeText, phoneticText, englishText) {
  const modal = document.getElementById("showLocalModal");
  if (!modal) return;
  document.getElementById("showLocalNative").textContent = nativeText || "";
  document.getElementById("showLocalPhonetic").textContent = phoneticText ? `Pronounce: ${phoneticText}` : "";
  document.getElementById("showLocalEnglish").textContent = englishText || "";
  modal.classList.add("open");
}

function closeShowLocalModal() {
  document.getElementById("showLocalModal")?.classList.remove("open");
}

/* Helper: Google Maps Powered Interactive Map (avoids OSM Access Denied) */
function initGoogleBaseMap(elementId, center = [23.685, 90.3563], zoom = 7, showLayerControl = true) {
  if (!window.L) return null;
  const map = L.map(elementId).setView(center, zoom);

  const googleRoad = L.tileLayer("https://mt{s}.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}", {
    subdomains: ["0", "1", "2", "3"],
    maxZoom: 20,
    attribution: "&copy; Google Maps",
  });

  const googleHybrid = L.tileLayer("https://mt{s}.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}", {
    subdomains: ["0", "1", "2", "3"],
    maxZoom: 20,
    attribution: "&copy; Google Satellite",
  });

  const googleTerrain = L.tileLayer("https://mt{s}.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}", {
    subdomains: ["0", "1", "2", "3"],
    maxZoom: 20,
    attribution: "&copy; Google Terrain",
  });

  const cartoLight = L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    subdomains: "abcd",
    maxZoom: 19,
    attribution: "&copy; CARTO",
  });

  googleRoad.addTo(map);
  if (showLayerControl) {
    L.control.layers(
      {
        "Google Maps (Road)": googleRoad,
        "Google Satellite": googleHybrid,
        "Google Terrain": googleTerrain,
        "Clean Map (Carto)": cartoLight,
      },
      null,
      { position: "topright" }
    ).addTo(map);
  }
  return map;
}
