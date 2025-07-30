self.addEventListener('install',e=>{e.waitUntil(caches.open('risk-cache').then(c=>c.addAll(['/','/events_geojson','/historical.geojson'])))});
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))});
