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
