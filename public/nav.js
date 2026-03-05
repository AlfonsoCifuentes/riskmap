/* ═══════════════════════════════════════════════════════════
   RISKMAP A.I. — Navigation + UI Engine
   ═══════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  /* ── Route Aliases ── */
  var ROUTE_ALIASES = {
    "/": "/index.html",
    "/news-analysis": "/index.html",
    "/index.html": "/index.html",
    "/conflict-monitoring": "/conflict-monitoring.html",
    "/conflict-monitoring.html": "/conflict-monitoring.html",
    "/trends-analysis": "/trends-analysis.html",
    "/trends-analysis.html": "/trends-analysis.html",
    "/early-warning": "/early-warning.html",
    "/early-warning.html": "/early-warning.html",
    "/executive-reports": "/executive-reports.html",
    "/executive-reports.html": "/executive-reports.html",
    "/data-intelligence": "/data-intelligence.html",
    "/data-intelligence.html": "/data-intelligence.html",
    "/satellite-analysis": "/satellite-analysis.html",
    "/satellite-analysis.html": "/satellite-analysis.html",
    "/video-surveillance": "/video-surveillance.html",
    "/video-surveillance.html": "/video-surveillance.html",
    "/historical-analysis": "/historical-analysis.html",
    "/historical-analysis.html": "/historical-analysis.html",
    "/about": "/about.html",
    "/about.html": "/about.html",
    "/logs": "/logs.html",
    "/logs.html": "/logs.html",
    "/settings": "/settings.html",
    "/settings.html": "/settings.html"
  };

  function normalizePath(pathname) {
    if (!pathname) return "/";
    var p = pathname;
    if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
    return ROUTE_ALIASES[p] || p;
  }

  /* ── Menu State ── */
  function setMenuState(open) {
    var menu = document.getElementById("navMenu");
    var overlay = document.getElementById("navOverlay");
    var btn = document.getElementById("hamburgerBtn");
    if (menu) menu.classList.toggle("open", open);
    if (overlay) overlay.classList.toggle("active", open);
    if (btn) {
      btn.classList.toggle("open", open);
      btn.classList.toggle("active", open);
      btn.setAttribute("aria-expanded", String(open));
    }
    document.body.style.overflow = open ? "hidden" : "";
  }

  function toggleNav() {
    var menu = document.getElementById("navMenu");
    if (!menu) return;
    setMenuState(!menu.classList.contains("open"));
  }

  window.toggleNav = toggleNav;
  window.RiskMapRoutes = ROUTE_ALIASES;

  /* ── Active Link Detection ── */
  function markActiveLinks() {
    var current = normalizePath(window.location.pathname);
    document.querySelectorAll(".nav-link, .nav-menu-item").forEach(function (el) {
      var href = el.getAttribute("href") || "";
      var canonical = normalizePath(href);
      var isActive = canonical === current;
      el.classList.toggle("active", isActive);
      if (isActive) el.setAttribute("aria-current", "page");
      else el.removeAttribute("aria-current");
    });
  }

  function ensureCanonicalNavHrefs() {
    document.querySelectorAll(".nav-link, .nav-menu-item").forEach(function (el) {
      var href = el.getAttribute("href") || "";
      var canonical = normalizePath(href);
      if (canonical !== href) el.setAttribute("href", canonical);
    });
  }

  /* ── Scroll Progress Bar ── */
  function initScrollProgress() {
    var bar = document.getElementById("scrollProgress");
    if (!bar) {
      bar = document.createElement("div");
      bar.id = "scrollProgress";
      document.body.prepend(bar);
    }
    var nav = document.querySelector(".top-nav");
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var scrollTop = window.scrollY || document.documentElement.scrollTop;
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight > 0) {
          bar.style.width = Math.min(100, (scrollTop / docHeight) * 100) + "%";
        }
        if (nav) nav.classList.toggle("scrolled", scrollTop > 20);
        ticking = false;
      });
    }, { passive: true });
  }

  /* ── Grain Texture ── */
  function initGrain() {
    var el = document.getElementById("grain");
    if (el) return; // already exists
    var canvas = document.createElement("canvas");
    canvas.width = 256; canvas.height = 256;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;
    var img = ctx.createImageData(256, 256);
    for (var i = 0; i < img.data.length; i += 4) {
      var v = Math.random() * 255;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
      img.data[i + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    el = document.createElement("div");
    el.id = "grain";
    el.style.backgroundImage = "url(" + canvas.toDataURL("image/png") + ")";
    el.style.backgroundRepeat = "repeat";
    document.body.appendChild(el);
  }

  /* ── Scroll Reveal (IntersectionObserver) ── */
  function initScrollReveal() {
    if (!("IntersectionObserver" in window)) {
      // Fallback: just show everything
      document.querySelectorAll(".reveal, .reveal-left, .reveal-right, .reveal-scale, .stagger")
        .forEach(function (el) { el.classList.add("visible"); });
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -40px 0px" });

    document.querySelectorAll(".reveal, .reveal-left, .reveal-right, .reveal-scale, .stagger")
      .forEach(function (el) { observer.observe(el); });
  }

  /* ═══════════════════════════════════════════════════════════
     DOM READY
     ═══════════════════════════════════════════════════════════ */
  document.addEventListener("DOMContentLoaded", function () {
    ensureCanonicalNavHrefs();
    markActiveLinks();
    setMenuState(false);
    initScrollProgress();
    initGrain();

    // Delay reveal init slightly so elements are in the DOM
    requestAnimationFrame(function () {
      setTimeout(initScrollReveal, 50);
    });

    var btn = document.getElementById("hamburgerBtn");
    if (btn && !btn.hasAttribute("aria-label")) {
      btn.setAttribute("aria-label", "Abrir menú de navegación");
    }
    if (btn) btn.setAttribute("aria-expanded", "false");

    // Close menu on link click
    document.querySelectorAll(".nav-link, .nav-menu-item").forEach(function (item) {
      item.addEventListener("click", function () {
        setTimeout(function () { setMenuState(false); }, 100);
      });
    });

    // Escape key closes menu
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setMenuState(false);
    });
  });

  /* ═══════════════════════════════════════════════════════════
     GLOBAL UTILITIES
     ═══════════════════════════════════════════════════════════ */

  /** HTML escape — prevents XSS in dynamic content */
  window.escH = function (s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  };

  /** Toast notification */
  window.showToast = function (msg, type, duration) {
    var t = type || "info";
    var ms = duration || 3500;
    var root = document.getElementById("toast-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "toast-root";
      document.body.appendChild(root);
    }
    var toast = document.createElement("div");
    toast.className = "toast " + t;
    var icons = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" };
    toast.innerHTML = "<strong>" + (icons[t] || "ℹ") + "</strong> " + window.escH(msg);
    root.appendChild(toast);
    requestAnimationFrame(function () { toast.classList.add("show"); });
    setTimeout(function () {
      toast.classList.remove("show");
      setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 350);
    }, ms);
  };

  /** Fetch JSON with error handling */
  window.fetchJSON = async function (url, options) {
    try {
      var res = await fetch(url, options || {});
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch (err) {
      console.warn("[RiskMap] fetch error:", url, err.message);
      return null;
    }
  };

  /** Animated counter with cubic easing */
  window.animCount = function (el, to, duration) {
    if (!el) return;
    var target = Number(to) || 0;
    var ms = duration || 900;
    var start = performance.now();
    var from = Number((el.textContent || "0").replace(/[^\d.-]/g, "")) || 0;
    function frame(now) {
      var p = Math.min((now - start) / ms, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(from + (target - from) * eased).toLocaleString("es-ES");
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  };

  /** Relative time in Spanish */
  window.timeAgo = function (dateLike) {
    if (!dateLike) return "N/D";
    var dt = new Date(dateLike);
    if (Number.isNaN(dt.getTime())) return "N/D";
    var sec = Math.max(0, Math.floor((Date.now() - dt.getTime()) / 1000));
    if (sec < 60) return "Ahora";
    if (sec < 3600) return Math.floor(sec / 60) + "m";
    if (sec < 86400) return Math.floor(sec / 3600) + "h";
    if (sec < 604800) return Math.floor(sec / 86400) + "d";
    return dt.toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
  };

  /** Risk level badge HTML */
  window.riskBadge = function (riskLevel) {
    var r = (riskLevel || "unknown").toLowerCase();
    if (r === "critical") return '<span class="badge badge-critical">Crítico</span>';
    if (r === "high") return '<span class="badge badge-high">Alto</span>';
    if (r === "medium") return '<span class="badge badge-medium">Medio</span>';
    if (r === "low") return '<span class="badge badge-low">Bajo</span>';
    return '<span class="badge badge-unknown">Sin clasificar</span>';
  };

  /** Re-init scroll reveals (call after dynamic content insertion) */
  window.initReveals = function () {
    initScrollReveal();
  };

  /** Chart.js dark theme defaults */
  window.chartDefaults = function () {
    if (typeof Chart === "undefined") return;
    Chart.defaults.color = "#7e93bd";
    Chart.defaults.borderColor = "rgba(130,165,255,.1)";
    Chart.defaults.font.family = "'Sora', 'Inter', system-ui, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyleWidth = 8;
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(6,12,26,.92)";
    Chart.defaults.plugins.tooltip.borderColor = "rgba(130,165,255,.2)";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.titleFont = { weight: "600" };
    Chart.defaults.scale.grid = { color: "rgba(130,165,255,.06)" };
  };
})();
