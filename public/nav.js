/* nav.js — shared navigation for all RiskMap sub-pages */
(function () {
  'use strict';

  function toggleNav() {
    const menu = document.getElementById('navMenu');
    const overlay = document.getElementById('navOverlay');
    const btn = document.getElementById('hamburgerBtn');
    if (!menu) return;
    const open = menu.classList.contains('open');
    menu.classList.toggle('open', !open);
    if (overlay) overlay.classList.toggle('active', !open);
    if (btn) btn.classList.toggle('open', !open);
    document.body.style.overflow = open ? '' : 'hidden';
  }

  window.toggleNav = toggleNav;

  document.addEventListener('DOMContentLoaded', function () {
    // Mark active link
    const path = window.location.pathname.replace(/\/$/, '') || '/';
    document.querySelectorAll('.nav-link').forEach(function (a) {
      const href = (a.getAttribute('href') || '').replace(/\/$/, '') || '/';
      if (href === path || (path === '' && href === '/')) {
        a.classList.add('active');
      }
    });

    // Close nav after link click
    document.querySelectorAll('.nav-link').forEach(function (item) {
      item.addEventListener('click', function () {
        setTimeout(toggleNav, 100);
      });
    });

    // Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        const menu = document.getElementById('navMenu');
        if (menu && menu.classList.contains('open')) toggleNav();
      }
    });
  });

  // ── Toast helper ────────────────────────────────────────────
  window.showToast = function (msg, type, duration) {
    type = type || 'info';
    duration = duration || 4000;
    let root = document.getElementById('toast-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'toast-root';
      document.body.appendChild(root);
    }
    const t = document.createElement('div');
    t.className = 'toast ' + type;
    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
    t.innerHTML = '<span style="font-size:1.1rem">' + (icons[type] || icons.info) + '</span><span>' + escH(msg) + '</span>';
    root.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('show'); });
    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { t.remove(); }, 400);
    }, duration);
  };

  // ── Escape helper ────────────────────────────────────────────
  window.escH = function (s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  };

  // ── Animated counter ─────────────────────────────────────────
  window.animCount = function (el, to, dur) {
    if (!el) return;
    to = parseInt(to, 10) || 0;
    dur = dur || 1200;
    const from = 0;
    const start = performance.now();
    const step = function (now) {
      const p = Math.min((now - start) / dur, 1);
      const ease = p < .5 ? 2 * p * p : -1 + (4 - 2 * p) * p;
      el.textContent = Math.round(from + (to - from) * ease).toLocaleString();
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  // ── Time ago ─────────────────────────────────────────────────
  window.timeAgo = function (d) {
    if (!d) return '—';
    try {
      const diff = (Date.now() - new Date(d)) / 1000;
      if (diff < 60) return 'Ahora';
      if (diff < 3600) return Math.floor(diff / 60) + 'm';
      if (diff < 86400) return Math.floor(diff / 3600) + 'h';
      if (diff < 604800) return Math.floor(diff / 86400) + 'd';
      return new Date(d).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    } catch (_) { return d; }
  };

  // ── Risk badge HTML ───────────────────────────────────────────
  window.riskBadge = function (r) {
    r = (r || 'unknown').toLowerCase();
    const cls = r === 'high' || r === 'critical' ? 'badge-high' : r === 'medium' ? 'badge-medium' : r === 'low' ? 'badge-low' : 'badge-unknown';
    const lab = { high: '⚠ Alto', critical: '🔴 Crítico', medium: '● Medio', low: '✓ Bajo' }[r] || r;
    return '<span class="badge ' + cls + '">' + lab + '</span>';
  };

  // ── Fetch JSON helper ─────────────────────────────────────────
  window.fetchJSON = async function (url) {
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return await r.json();
    } catch (e) {
      console.warn('[RiskMap] fetch failed:', url, e);
      return null;
    }
  };
})();
