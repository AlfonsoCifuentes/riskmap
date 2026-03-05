/* ============================================================
   RISKMAP V2 — Application Core
   Handles data fetching, rendering, maps, charts, interactions
   ============================================================ */

(function () {
  'use strict';

  // ── Config ──────────────────────────────────────────────
  const API = {
    articles:    '/api/articles',
    hero:        '/api/hero-article',
    status:      '/api/status',
    conflicts:   '/api/analytics/conflicts-corrected',
    geojson:     '/api/analytics/geojson',
    gdelt:       '/api/gdelt-events',
    satellite:   '/api/satellite/gallery',
    aiAnalysis:  '/api/ai/geopolitical-analysis',
    sentiment:   '/api/analytics/sentiment',
    stats:       '/api/dashboard/stats',
  };

  const STATE = {
    articles: [],
    heroId: null,
    offset: 0,
    limit: 12,
    filter: 'all',
    mapInstance: null,
    heatLayer: null,
    markers: [],
    charts: {},
    searchOpen: false,
  };

  // ── Boot ────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    setupIntro();
    setupNav();
    setupScrollEffects();
    setupTabs();
    setupCursorGlow();
    setupSearchModal();

    // Parallel data fetch
    Promise.allSettled([
      loadHero(),
      loadArticles(),
      loadStatus(),
      loadConflicts(),
      loadGdeltEvents(),
      loadSatelliteGallery(),
      requestAIAnalysis(),
    ]).then(() => {
      console.log('[RiskMap] All data loaded');
      showToast('Intelligence feed connected', 'success', 3000);
    });

    // Observe animations
    observeAnimations();
  }

  // ── Intro Overlay ───────────────────────────────────────
  function setupIntro() {
    const intro = document.getElementById('intro');
    if (!intro) return;
    setTimeout(() => {
      intro.classList.add('hidden');
      setTimeout(() => intro.remove(), 800);
    }, 1800);
  }

  // ── Cursor Glow (desktop only) ──────────────────────────
  function setupCursorGlow() {
    const glow = document.getElementById('cursorGlow');
    if (!glow || !matchMedia('(hover:hover) and (pointer:fine)').matches) {
      if (glow) glow.remove();
      return;
    }
    let rAF;
    document.addEventListener('mousemove', (e) => {
      if (rAF) cancelAnimationFrame(rAF);
      rAF = requestAnimationFrame(() => {
        glow.style.left = e.clientX + 'px';
        glow.style.top = e.clientY + 'px';
      });
    }, { passive: true });
  }

  // ── Navigation ──────────────────────────────────────────
  function setupNav() {
    const navbar = document.getElementById('navbar');
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    let lastScroll = 0;

    // Hamburger
    toggle?.addEventListener('click', () => {
      toggle.classList.toggle('open');
      links.classList.toggle('open');
      document.body.classList.toggle('no-scroll');
    });

    // Hide/show nav on scroll
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y > 100) navbar.classList.add('scrolled');
      else navbar.classList.remove('scrolled');

      if (y > lastScroll && y > 400) navbar.classList.add('hidden-nav');
      else navbar.classList.remove('hidden-nav');
      lastScroll = y;
    }, { passive: true });

    // Active link tracking
    const sections = document.querySelectorAll('section[id]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          document.querySelectorAll('.nav-links a').forEach(a => {
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          });
        }
      });
    }, { threshold: 0.3 });
    sections.forEach(s => observer.observe(s));
  }

  // ── Scroll Effects ──────────────────────────────────────
  function setupScrollEffects() {
    const progress = document.getElementById('scrollProgress');
    window.addEventListener('scroll', () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      const pct = (window.scrollY / h) * 100;
      if (progress) progress.style.width = pct + '%';
    }, { passive: true });
  }

  // ── Tabs ────────────────────────────────────────────────
  function setupTabs() {
    // News risk filter
    document.getElementById('newsTabs')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.tab-btn');
      if (!btn) return;
      document.querySelectorAll('#newsTabs .tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      STATE.filter = btn.dataset.filter;
      renderArticles();
    });

    // Map timeframe
    document.getElementById('mapTabs')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.tab-btn');
      if (!btn) return;
      document.querySelectorAll('#mapTabs .tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadConflicts(btn.dataset.timeframe);
    });
  }

  // ── Search Modal (CMD/CTRL+K) ──────────────────────────
  function setupSearchModal() {
    const modal = document.getElementById('searchModal');
    const input = document.getElementById('searchInput');
    const results = document.getElementById('searchResults');
    if (!modal || !input) return;

    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleSearch();
      }
      if (e.key === 'Escape' && STATE.searchOpen) {
        toggleSearch();
      }
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) toggleSearch();
    });

    let debounce;
    input.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        const q = input.value.trim().toLowerCase();
        if (q.length < 2) { results.innerHTML = ''; return; }
        const matches = STATE.articles.filter(a =>
          (a.title || '').toLowerCase().includes(q) ||
          (a.source || '').toLowerCase().includes(q) ||
          (a.country || '').toLowerCase().includes(q) ||
          (a.location || '').toLowerCase().includes(q)
        ).slice(0, 8);

        results.innerHTML = matches.length ? matches.map(a => `
          <div class="search-result-item" data-article-id="${parseInt(a.id, 10)}">
            <span class="risk-badge ${(a.risk || a.risk_level || 'medium').toLowerCase()}" style="flex-shrink:0">${(a.risk || a.risk_level || '?')[0]?.toUpperCase()}</span>
            <div>
              <div style="font-weight:600;font-size:.85rem">${escapeHtml(a.title)}</div>
              <div class="text-xs text-muted">${escapeHtml(a.source || '')} · ${escapeHtml(a.location || a.country || '')}</div>
            </div>
          </div>
        `).join('') : '<div style="padding:var(--s-lg);text-align:center;color:var(--text-muted)">No results found.</div>';
      }, 200);
    });

    // Event delegation for search result clicks
    results.addEventListener('click', (e) => {
      const item = e.target.closest('.search-result-item[data-article-id]');
      if (item) {
        const id = parseInt(item.dataset.articleId, 10);
        if (!isNaN(id)) {
          openArticle(id);
          toggleSearch();
        }
      }
    });

    function toggleSearch() {
      STATE.searchOpen = !STATE.searchOpen;
      modal.classList.toggle('open', STATE.searchOpen);
      if (STATE.searchOpen) {
        input.value = '';
        results.innerHTML = '';
        setTimeout(() => input.focus(), 100);
        document.body.classList.add('no-scroll');
      } else {
        document.body.classList.remove('no-scroll');
      }
    }
  }

  // ── Animation Observer ──────────────────────────────────
  function observeAnimations() {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          // Stagger children
          const stagger = entry.target.closest('[data-stagger]') || (entry.target.hasAttribute('data-stagger') ? entry.target : null);
          if (stagger) {
            Array.from(stagger.children).forEach((child, i) => {
              child.style.setProperty('--i', i);
            });
          }
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('[data-animate]').forEach(el => io.observe(el));
  }

  // ── Animated Counter ────────────────────────────────────
  function animateCounter(el, target) {
    if (!el || isNaN(target)) return;
    const duration = 1200;
    const start = performance.now();
    const initial = 0;

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(initial + (target - initial) * ease);
      el.textContent = current.toLocaleString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ── News Ticker ─────────────────────────────────────────
  function updateTicker(articles) {
    const ticker = document.getElementById('tickerContent');
    if (!ticker || !articles?.length) return;

    const items = articles.slice(0, 12).map(a => {
      const risk = (a.risk || a.risk_level || 'medium').toLowerCase();
      const dotColor = risk === 'high' || risk === 'critical' ? 'red' : risk === 'medium' ? 'gold' : 'teal';
      const loc = a.location || a.country || '';
      return `<span class="ticker-item"><span class="dot ${dotColor}"></span>${loc ? loc + ': ' : ''}${escapeHtml((a.title || '').substring(0, 80))}</span>`;
    }).join('');

    // Duplicate for seamless loop
    ticker.innerHTML = items + items;
  }

  // ── API Helpers ─────────────────────────────────────────
  async function fetchJSON(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn(`[RiskMap] Fetch failed: ${url}`, err);
      return null;
    }
  }

  // ── Hero Article ────────────────────────────────────────
  async function loadHero() {
    const data = await fetchJSON(API.hero);
    if (!data?.success || !data.article) {
      // Remove loading skeleton on failure
      document.querySelectorAll('.hero .skeleton, .hero .shimmer').forEach(el => el.remove());
      return;
    }

    const art = data.article;
    STATE.heroId = art.id;

    const titleEl = document.getElementById('heroTitle');
    const excerptEl = document.getElementById('heroExcerpt');
    const bgImg = document.getElementById('heroBgImage');
    const metaEl = document.getElementById('heroMeta');
    const ctaEl = document.getElementById('heroCta');
    const locEl = document.getElementById('heroLocation');
    const timeEl = document.getElementById('heroTime');
    const sourceEl = document.getElementById('heroSource');
    const riskEl = document.getElementById('heroRiskBadge');
    const badgeText = document.getElementById('heroBadgeText');

    // Word-by-word reveal animation
    const title = art.title || 'Intelligence Report';
    titleEl.innerHTML = title.split(' ').map((w, i) =>
      `<span class="title-word" style="animation-delay:${0.3 + i * 0.06}s">${escapeHtml(w)}</span>`
    ).join(' ');

    const excerpt = art.auto_generated_summary || art.text || '';
    excerptEl.innerHTML = '';
    excerptEl.textContent = excerpt.substring(0, 280) + (excerpt.length > 280 ? '...' : '');

    if (art.image) {
      bgImg.src = art.image;
      bgImg.alt = art.title || '';
    }

    locEl.textContent = art.location || 'Global';
    timeEl.textContent = formatTimeAgo(art.published_at || art.date);
    sourceEl.textContent = art.source || 'OSINT';

    if (art.risk) {
      riskEl.textContent = art.risk.toUpperCase();
      riskEl.className = 'risk-badge ' + art.risk;
      riskEl.style.display = '';
    }

    const riskLabel = { high: 'Critical Alert', medium: 'Active Monitoring', low: 'Intelligence Brief' };
    badgeText.textContent = riskLabel[art.risk] || 'Breaking Intelligence';

    metaEl.style.display = '';

    if (art.original_url || art.url) {
      ctaEl.href = art.original_url || art.url;
      ctaEl.style.display = '';
    }
  }

  // ── Articles Feed ───────────────────────────────────────
  async function loadArticles(append = false) {
    const data = await fetchJSON(`${API.articles}?limit=${STATE.limit}&offset=${STATE.offset}`);
    if (!data?.success) return;

    if (append) {
      STATE.articles = STATE.articles.concat(data.articles || []);
    } else {
      STATE.articles = data.articles || [];
    }

    renderArticles();

    const loadMore = document.getElementById('loadMoreBtn');
    if (loadMore) {
      loadMore.style.display = (data.articles?.length >= STATE.limit) ? '' : 'none';
      loadMore.onclick = () => {
        STATE.offset += STATE.limit;
        loadArticles(true);
      };
    }
  }

  function renderArticles() {
    const grid = document.getElementById('newsGrid');
    if (!grid) return;

    let filtered = STATE.articles;
    if (STATE.filter !== 'all') {
      filtered = filtered.filter(a => (a.risk || a.risk_level || '').toLowerCase() === STATE.filter);
    }

    if (filtered.length === 0) {
      grid.innerHTML = '<p class="text-muted" style="grid-column:1/-1;text-align:center;padding:var(--s-3xl)">No intelligence reports match this filter.</p>';
      return;
    }

    // Populate ticker from first load
    updateTicker(STATE.articles);

    // Build timeline chart from loaded articles
    buildTimelineChart();

    grid.innerHTML = filtered.map((art, i) => {
      const risk = (art.risk || art.risk_level || 'medium').toLowerCase();
      const riskLabel = risk.charAt(0).toUpperCase() + risk.slice(1);
      const imgUrl = art.image || art.image_url || art.original_image_url || '';
      const excerpt = art.auto_generated_summary || art.summary || '';
      const location = art.location || art.country || 'Global';
      const source = art.source || 'OSINT';
      const dateStr = formatTimeAgo(art.published_at || art.date);
      const category = inferCategory(art);

      return `
        <article class="news-card${i === 0 && STATE.filter === 'all' ? ' featured' : ''}" 
                 onclick="openArticle(${art.id})" data-id="${art.id}" data-risk="${risk}"
                 role="button" tabindex="0"
                 onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();openArticle(${art.id})}"
                 style="--i:${i}">
          <div class="news-card-image">
            ${imgUrl ? `<img src="${escapeHtml(imgUrl)}" alt="${escapeHtml(art.title)}" loading="lazy" onerror="this.parentElement.classList.add('no-img')">` : ''}
            <span class="risk-badge ${risk}">${riskLabel}</span>
          </div>
          <div class="news-card-body">
            <div style="display:flex;align-items:center;gap:var(--s-xs);flex-wrap:wrap;margin-bottom:var(--s-xs)">
              <span class="news-card-source">${escapeHtml(source)}</span>
              ${category ? `<span class="chip ${category}">${category}</span>` : ''}
            </div>
            <h3 class="news-card-title">${escapeHtml(art.title)}</h3>
            <p class="news-card-excerpt">${escapeHtml(excerpt.substring(0, 200))}</p>
          </div>
          <div class="news-card-footer">
            <span class="location">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/></svg>
              ${escapeHtml(location)}
            </span>
            <span>${dateStr}</span>
          </div>
        </article>`;
    }).join('');
  }

  // Infer category from article content/tags
  function inferCategory(art) {
    const text = ((art.title || '') + ' ' + (art.conflict_type || '') + ' ' + (art.ai_tags || '')).toLowerCase();
    if (/war|conflict|militar|attack|strike|weapon|combat|missile|bomb|offensive/.test(text)) return 'conflict';
    if (/earthquake|flood|hurricane|tsunami|wildfire|disaster|storm|volcano/.test(text)) return 'disaster';
    if (/diplom|treaty|summit|negotiat|peace|agreement|alliance|sanction/.test(text)) return 'diplomacy';
    if (/refugee|humanitarian|crisis|famine|aid|relief|displace|evacuat/.test(text)) return 'humanitarian';
    return '';
  }

  // ── System Status ───────────────────────────────────────
  async function loadStatus() {
    const data = await fetchJSON(API.status);
    if (!data) return;

    // Animated counters for stat values
    const statsMap = {
      statArticles: data.total_articles ?? 0,
      statAlerts:   data.critical_alerts ?? 0,
      statRegions:  data.regions_in_conflict ?? 0,
      statSources:  data.active_sources ?? 0,
    };
    Object.entries(statsMap).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (!el) return;
      const counter = el.querySelector('.counter-value') || el;
      const num = parseInt(val, 10);
      if (!isNaN(num)) animateCounter(counter, num);
      else counter.textContent = val;
    });

    // Confidence from reliability_score or NLP system status
    const confEl = document.getElementById('statConfidence');
    if (confEl) {
      const counter = confEl.querySelector('.counter-value') || confEl;
      const confVal = data.reliability_score ?? (data.components?.nlp_system ? 87 : 0);
      animateCounter(counter, confVal);
    }

    setText('footerPing', `System: ${data.status || 'operational'} | ${data.total_articles || 0} reports`);

    // Pipeline status
    updatePipeline(data);
  }

  function updatePipeline(data) {
    const c = data.components || {};
    setStep('pipe-ingest', true);
    setStep('pipe-filter', true);
    setStep('pipe-nlp', c.nlp_system);
    setStep('pipe-rewrite', c.nlp_system);
    setStep('pipe-enrich', c.database);
    setStep('pipe-cv', c.visualization);
    setStep('pipe-dash', c.api);
  }

  function setStep(id, active) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('active', !!active);
  }

  // ── Conflicts / Map ─────────────────────────────────────
  async function loadConflicts(timeframe = '24h') {
    const data = await fetchJSON(`${API.conflicts}?timeframe=${timeframe}`);
    if (!data?.success) {
      initMap([]);
      return;
    }

    const conflicts = data.conflicts || [];
    initMap(conflicts);

    // Also load GeoJSON for heatmap
    const geoData = await fetchJSON(`${API.geojson}?timeframe=${timeframe}`);
    if (geoData?.success && geoData.geojson?.features) {
      addHeatData(geoData.geojson.features);
    }

    // Build risk distribution chart
    if (data.statistics) {
      buildRiskChart(data.statistics);
    }
  }

  function initMap(conflicts) {
    const container = document.getElementById('heatmap');
    if (!container) return;

    // Guard: Leaflet must be loaded
    if (typeof L === 'undefined') {
      console.warn('[RiskMap] Leaflet not loaded, skipping map init');
      container.innerHTML = '<p class="text-muted" style="text-align:center;padding:var(--s-2xl)">Map library failed to load.</p>';
      return;
    }

    // Create map once; reuse on subsequent calls
    if (!STATE.mapInstance) {
      const map = L.map('heatmap', {
        center: [25, 10],
        zoom: 2.5,
        minZoom: 2,
        maxZoom: 12,
        zoomControl: false,
        attributionControl: false,
        scrollWheelZoom: true,
      });

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
      }).addTo(map);

      STATE.mapInstance = map;
    } else {
      // Clear view for re-render
      STATE.mapInstance.setView([25, 10], 2.5);
    }

    // Clear existing markers
    STATE.markers.forEach(m => m.remove());
    STATE.markers = [];

    // Clear existing heat layer
    if (STATE.heatLayer) {
      STATE.mapInstance.removeLayer(STATE.heatLayer);
      STATE.heatLayer = null;
    }

    conflicts.forEach(c => {
      const lat = parseFloat(c.latitude);
      const lng = parseFloat(c.longitude);
      if (isNaN(lat) || isNaN(lng)) return;

      const riskColor = {
        high: '#ff3355', critical: '#ff2244', medium: '#ffaa22', low: '#00e5a0'
      }[c.risk_level || 'medium'] || '#ffaa22';

      const size = c.article_count ? Math.min(Math.max(c.article_count * 3, 8), 30) : 12;

      const marker = L.circleMarker([lat, lng], {
        radius: size,
        fillColor: riskColor,
        fillOpacity: 0.5,
        color: riskColor,
        weight: 1,
        opacity: 0.8,
      }).addTo(STATE.mapInstance);

      marker.bindPopup(`
        <div style="font-family:Inter,sans-serif;font-size:13px;min-width:200px">
          <strong style="font-size:14px">${escapeHtml(c.location || c.country || 'Unknown')}</strong><br>
          <span style="color:${riskColor};font-weight:600">${(c.risk_level || 'medium').toUpperCase()}</span><br>
          ${c.article_count ? `<span>Articles: ${c.article_count}</span><br>` : ''}
          ${c.avg_risk_score ? `<span>Risk Score: ${(c.avg_risk_score * 100).toFixed(0)}%</span>` : ''}
        </div>
      `);

      STATE.markers.push(marker);
    });
  }

  function addHeatData(features) {
    if (!STATE.mapInstance) return;

    const points = features
      .filter(f => f.geometry?.coordinates)
      .map(f => {
        const [lng, lat] = f.geometry.coordinates;
        const intensity = f.properties?.intensity || f.properties?.risk_score || 0.5;
        return [lat, lng, intensity];
      });

    if (STATE.heatLayer) STATE.mapInstance.removeLayer(STATE.heatLayer);

    if (points.length > 0 && typeof L.heatLayer === 'function') {
      STATE.heatLayer = L.heatLayer(points, {
        radius: 30,
        blur: 20,
        maxZoom: 12,
        gradient: {
          0.2: '#003d33',
          0.4: '#00e5a0',
          0.6: '#ffaa22',
          0.8: '#ff4466',
          1.0: '#ff2244'
        }
      }).addTo(STATE.mapInstance);
    }
  }

  // ── GDELT Events ────────────────────────────────────────
  async function loadGdeltEvents() {
    const data = await fetchJSON(API.gdelt);
    if (!data?.success) return;

    const events = (data.gdelt_events || []).slice(0, 10);
    const timeline = document.getElementById('gdeltTimeline');
    if (!timeline) return;

    if (events.length === 0) {
      timeline.innerHTML = '<p class="text-muted">No GDELT events available.</p>';
      return;
    }

    timeline.innerHTML = events.map(ev => {
      const risk = ev.goldstein_scale < -5 ? 'high' : ev.goldstein_scale < 0 ? 'medium' : '';
      return `
        <div class="timeline-event ${risk}">
          <div class="timeline-date">${escapeHtml(ev.date || '—')}</div>
          <div class="timeline-title">${escapeHtml(ev.description || ev.event_code || 'Event')}</div>
          <div class="timeline-desc">
            ${ev.actor1 ? `<span>${escapeHtml(ev.actor1)}</span>` : ''}
            ${ev.actor2 ? ` → <span>${escapeHtml(ev.actor2)}</span>` : ''}
            ${ev.country ? ` | <span>${escapeHtml(ev.country)}</span>` : ''}
            ${ev.tone != null ? ` | Tone: ${ev.tone.toFixed(1)}` : ''}
          </div>
        </div>`;
    }).join('');

    // GDELT chart
    buildGdeltChart(events);
  }

  // ── Satellite Gallery ───────────────────────────────────
  async function loadSatelliteGallery() {
    const data = await fetchJSON(API.satellite);
    const gallery = document.getElementById('satGallery');
    if (!gallery) return;

    let images = [];
    if (data?.success && data.images?.length) {
      images = data.images;
    } else if (data?.gallery?.length) {
      images = data.gallery;
    }

    if (images.length === 0) {
      gallery.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:var(--s-2xl) var(--s-lg);color:var(--text-muted)">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="margin-bottom:var(--s-sm);opacity:.5"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          <p style="font-weight:600;margin-bottom:var(--s-xs)">No satellite imagery available</p>
          <p style="font-size:.85rem">Satellite data will appear here when conflict zones are monitored.</p>
        </div>`;
      return;
    }

    gallery.innerHTML = images.slice(0, 8).map(img => {
      const src = img.url || img.image_url || img.image_path || img.thumbnail || '';
      const loc = img.location || img.zone_name || img.zone_id || 'Unknown Zone';
      const date = img.date || img.captured_at || img.created_at || '';
      return `
        <div class="sat-card"${src ? ` data-href="${escapeHtml(src)}"` : ''} style="cursor:${src ? 'pointer' : 'default'}">
          <img src="${escapeHtml(src)}" alt="${escapeHtml(loc)}" loading="lazy" 
               onerror="this.style.display='none'">
          <div class="sat-card-overlay">
            <h4>${escapeHtml(loc)}</h4>
            <p>${escapeHtml(date)}</p>
          </div>
        </div>`;
    }).join('');

    // Event delegation for satellite card clicks
    if (!gallery._satClickBound) {
      gallery.addEventListener('click', (e) => {
        const card = e.target.closest('.sat-card[data-href]');
        if (card) window.open(card.dataset.href, '_blank', 'noopener');
      });
      gallery._satClickBound = true;
    }
  }

  // ── AI Analysis ─────────────────────────────────────────
  async function requestAIAnalysis() {
    const panel = document.getElementById('aiAnalysisContent');
    const scanLine = document.getElementById('aiScanLine');
    if (!panel) return;

    try {
      // Send recent articles for contextualized AI analysis
      const articlePayload = STATE.articles.length > 0
        ? STATE.articles.slice(0, 10).map(a => ({
            title: a.title || '',
            summary: a.summary || a.auto_generated_summary || '',
            country: a.country || a.location || '',
            risk_level: a.risk || a.risk_level || ''
          }))
        : [];

      const res = await fetch(API.aiAnalysis, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ articles: articlePayload })
      });

      const data = await res.json();
      if (scanLine) scanLine.style.display = 'none';

      if (data?.success && (data.analysis || data.content)) {
        const text = data.analysis || data.content;
        const paragraphs = text.split('\n').filter(p => p.trim());
        panel.innerHTML = paragraphs.map(p =>
          `<div class="ai-insight">${escapeHtml(p)}</div>`
        ).join('');
      } else {
        // Fallback: load from status
        const status = await fetchJSON(API.status);
        panel.innerHTML = `
          <div class="ai-insight">
            System monitoring ${status?.total_articles || 'multiple'} intelligence reports across 
            ${status?.regions_in_conflict || 'multiple'} active conflict regions. 
            AI analysis engine ${status?.components?.nlp_system ? 'operational' : 'initializing'}.
            ${status?.active_sources || 'Multiple'} OSINT sources under active collection.
          </div>
          <div class="ai-insight" style="border-left-color:var(--accent-gold)">
            Real-time threat assessment is continuously updated. Pipeline processes incoming 
            intelligence through NLP classification, entity extraction, geocoding, and risk scoring 
            before cross-referencing with GDELT and ACLED databases.
          </div>`;
      }
    } catch (e) {
      if (scanLine) scanLine.style.display = 'none';
      panel.innerHTML = `
        <div class="ai-insight" style="border-left-color:var(--accent-gold)">
          AI analysis engine is processing. The system continuously ingests and analyzes 
          geopolitical intelligence from global OSINT sources, cross-referencing with GDELT 
          and ACLED databases for verification.
        </div>`;
    }
  }

  // ── Charts ──────────────────────────────────────────────
  function buildRiskChart(stats) {
    const ctx = document.getElementById('riskDistChart');
    if (!ctx) return;
    if (STATE.charts.risk) STATE.charts.risk.destroy();

    // Compute risk counts from statistics or fallback to STATE.articles
    let highRisk = stats.high_risk || stats.critical_alerts || 0;
    let medRisk = stats.medium_risk || 0;
    let lowRisk = stats.low_risk || 0;

    // If backend doesn't provide risk breakdown, compute from loaded articles
    if (highRisk === 0 && medRisk === 0 && lowRisk === 0 && STATE.articles.length > 0) {
      STATE.articles.forEach(a => {
        const r = (a.risk || a.risk_level || 'medium').toLowerCase();
        if (r === 'high' || r === 'critical') highRisk++;
        else if (r === 'medium') medRisk++;
        else lowRisk++;
      });
    }

    STATE.charts.risk = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['High Risk', 'Medium Risk', 'Low Risk'],
        datasets: [{
          data: [highRisk, medRisk, lowRisk],
          backgroundColor: ['#ff3355', '#ffaa22', '#00e5a0'],
          borderColor: '#111a22',
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#8898aa', font: { family: 'Inter', size: 12 }, padding: 16 }
          },
          title: {
            display: true,
            text: 'Conflict Risk Distribution',
            color: '#eaeef3',
            font: { family: 'Space Grotesk', size: 16, weight: 600 },
            padding: { bottom: 16 }
          }
        }
      }
    });
  }

  // ── Timeline Chart (article volume over time) ───────────
  function buildTimelineChart() {
    const ctx = document.getElementById('timelineChart');
    if (!ctx || STATE.articles.length === 0) return;
    if (STATE.charts.timeline) STATE.charts.timeline.destroy();

    // Group articles by day
    const dayCounts = {};
    STATE.articles.forEach(a => {
      const dateStr = a.published_at || a.date || a.created_at;
      if (!dateStr) return;
      const day = dateStr.substring(0, 10); // YYYY-MM-DD
      dayCounts[day] = (dayCounts[day] || 0) + 1;
    });

    const sorted = Object.entries(dayCounts).sort((a, b) => a[0].localeCompare(b[0]));
    if (sorted.length === 0) return;

    const labels = sorted.map(([d]) => {
      const dt = new Date(d);
      return dt.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    });
    const counts = sorted.map(([, c]) => c);

    STATE.charts.timeline = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Reports',
          data: counts,
          borderColor: '#00e5a0',
          backgroundColor: 'rgba(0,229,160,.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#00e5a0',
          pointBorderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: 'rgba(255,255,255,.04)' }, ticks: { color: '#556677', font: { size: 11 } } },
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,.04)' }, ticks: { color: '#556677', font: { size: 11 }, stepSize: 1 } }
        },
        plugins: {
          legend: { display: false },
          title: {
            display: true,
            text: 'Intelligence Report Volume',
            color: '#eaeef3',
            font: { family: 'Space Grotesk', size: 16, weight: 600 },
            padding: { bottom: 8 }
          }
        }
      }
    });
  }

  function buildGdeltChart(events) {
    const ctx = document.getElementById('gdeltChart');
    if (!ctx) return;
    if (STATE.charts.gdelt) STATE.charts.gdelt.destroy();

    const labels = events.map(e => e.country || e.actor1 || '?').slice(0, 8);
    const tones = events.map(e => e.tone || 0).slice(0, 8);
    const goldstein = events.map(e => e.goldstein_scale || 0).slice(0, 8);

    STATE.charts.gdelt = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Tone',
            data: tones,
            backgroundColor: tones.map(t => t < 0 ? 'rgba(255,51,85,.6)' : 'rgba(0,229,160,.6)'),
            borderRadius: 4,
          },
          {
            label: 'Goldstein Scale',
            data: goldstein,
            backgroundColor: 'rgba(51,153,255,.4)',
            borderRadius: 4,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        scales: {
          x: { grid: { color: 'rgba(255,255,255,.04)' }, ticks: { color: '#556677', font: { size: 11 } } },
          y: { grid: { display: false }, ticks: { color: '#8898aa', font: { size: 11 } } }
        },
        plugins: {
          legend: { labels: { color: '#8898aa', font: { size: 11 } } },
          title: {
            display: true,
            text: 'GDELT Event Sentiment',
            color: '#eaeef3',
            font: { family: 'Space Grotesk', size: 16, weight: 600 },
            padding: { bottom: 8 }
          }
        }
      }
    });
  }

  // ── Article Modal ───────────────────────────────────────
  window.openArticle = function (id) {
    const art = STATE.articles.find(a => a.id === id);
    if (!art) return;

    const modal = document.getElementById('articleModal');
    setText('modalTitle', art.title);
    setText('modalContent', art.auto_generated_summary || art.summary || art.content || '');

    const img = document.getElementById('modalImage');
    const imgUrl = art.image || art.image_url || art.original_image_url;
    if (imgUrl) { img.src = imgUrl; img.style.display = ''; }
    else { img.style.display = 'none'; }

    const meta = document.getElementById('modalMeta');
    const risk = art.risk || art.risk_level || 'medium';
    meta.innerHTML = `
      <span class="risk-badge ${risk}">${risk.toUpperCase()}</span>
      <span class="text-sm text-muted">${escapeHtml(art.location || art.country || 'Global')}</span>
      <span class="text-sm text-muted">${escapeHtml(art.source || '')}</span>
      <span class="text-sm text-muted">${formatTimeAgo(art.published_at || art.date)}</span>`;

    const link = document.getElementById('modalLink');
    if (art.original_url || art.url) {
      link.href = art.original_url || art.url;
      link.style.display = '';
    } else {
      link.style.display = 'none';
    }

    modal.classList.add('open');
    document.body.classList.add('no-scroll');
  };

  window.closeModal = function () {
    document.getElementById('articleModal')?.classList.remove('open');
    document.body.classList.remove('no-scroll');
  };

  document.getElementById('articleModal')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !STATE.searchOpen) closeModal();
  });

  // ── Toast Notifications ─────────────────────────────────
  window.showToast = function (message, type = 'success', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ⓘ' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <div style="flex-shrink:0;font-size:1.1rem">${icons[type] || icons.info}</div>
      <div style="flex:1">
        <div style="font-weight:600;font-size:.85rem;margin-bottom:2px">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div style="font-size:.8rem;color:var(--text-secondary)">${escapeHtml(message)}</div>
      </div>
      <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem;padding:0">&times;</button>`;

    container.appendChild(toast);
    requestAnimationFrame(() => toast.style.opacity = '1');
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(120%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  };

  // ── Utilities ───────────────────────────────────────────
  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatTimeAgo(dateStr) {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      const now = new Date();
      const diff = (now - d) / 1000;
      if (diff < 60) return 'Just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
      return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  }

  // ── Auto-refresh with visibility check ──────────────────
  function startAutoRefresh() {
    setInterval(() => {
      if (!document.hidden) loadStatus();
    }, 60000);

    setInterval(() => {
      if (!document.hidden) {
        loadHero();
        // Only refresh articles if user hasn't paginated
        if (STATE.offset === 0) loadArticles();
      }
    }, 300000);
  }
  startAutoRefresh();

})();
