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
