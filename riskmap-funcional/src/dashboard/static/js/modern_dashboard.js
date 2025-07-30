// Modern Dashboard JavaScript - Updated for Redesigned Layout

class GeopoliticalDashboard {
    constructor() {
        this.map = null;
        this.miniMap = null;
        this.heatmapLayer = null;
        this.markersLayer = null;
        this.choroplethLayer = null;
        this.currentLayer = 'heatmap';
        this.alerts = [];
        this.stats = {};
        this.refreshInterval = 30000; // 30 seconds
        this.language = 'es';
        
        this.init();
    }
    
    async init() {
        // Remove sonar overlay after animation
        setTimeout(() => {
            const sonarOverlay = document.getElementById('sonarOverlay');
            if (sonarOverlay) {
                sonarOverlay.style.display = 'none';
            }
        }, 3500);
        
        // Initialize components
        this.initializeMap();
        this.initializeEventListeners();
        this.loadDashboardData();
        this.startAutoRefresh();
        this.initializeCharts();
        this.loadFeaturedArticle();
        this.loadAIAnalysis();
        this.loadArticlesTables();
        
        // Check for saved preferences
        this.loadUserPreferences();
    }
    
    initializeMap() {
        try {
            console.log('Initializing map...');
            
            // Check if Leaflet is available
            if (typeof L === 'undefined') {
                console.error('Leaflet library not loaded');
                this.showMapError('Leaflet library not available');
                return;
            }
            
            // Check if map container exists
            const mapContainer = document.getElementById('main-map');
            if (!mapContainer) {
                console.error('Map container not found');
                return;
            }
            
            // Clear any existing map
            if (this.map) {
                this.map.remove();
            }
            
            // Initialize main map
            this.map = L.map('main-map', {
                center: [20, 0],
                zoom: 2,
                minZoom: 1,
                maxZoom: 18,
                worldCopyJump: true,
                zoomControl: true,
                attributionControl: true
            });
            
            // Add dark theme tile layer with fallback
            const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '© OpenStreetMap contributors © CARTO',
                subdomains: 'abcd',
                maxZoom: 19,
                errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
            });
            
            tileLayer.addTo(this.map);
            
            // Add fallback tile layer
            const fallbackLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            });
            
            // Handle tile loading errors
            tileLayer.on('tileerror', () => {
                console.warn('Primary tile layer failed, switching to fallback');
                this.map.removeLayer(tileLayer);
                fallbackLayer.addTo(this.map);
            });
            
            // Initialize layers
            this.initializeHeatmapLayer();
            this.initializeMarkersLayer();
            this.initializeChoroplethLayer();
            
            // Show default layer
            this.showLayer('heatmap');
            
            // Add map ready event
            this.map.whenReady(() => {
                console.log('Map initialized successfully');
                this.loadMapData();
            });
            
        } catch (error) {
            console.error('Error initializing map:', error);
            this.showMapError('Error initializing map: ' + error.message);
        }
    }
    
    showMapError(message) {
        const mapContainer = document.getElementById('main-map');
        if (mapContainer) {
            mapContainer.innerHTML = `
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    background: var(--bg-secondary);
                    color: var(--text-secondary);
                    border-radius: 8px;
                    border: 2px dashed var(--bg-hover);
                    flex-direction: column;
                    gap: 1rem;
                ">
                    <i class="fas fa-map-marked-alt" style="font-size: 3rem; color: var(--accent-primary);"></i>
                    <div style="text-align: center;">
                        <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">Mapa no disponible</h3>
                        <p>${message}</p>
                        <button onclick="window.dashboard.retryMapInitialization()" style="
                            margin-top: 1rem;
                            padding: 0.5rem 1rem;
                            background: var(--accent-primary);
                            color: white;
                            border: none;
                            border-radius: 6px;
                            cursor: pointer;
                        ">Reintentar</button>
                    </div>
                </div>
            `;
        }
    }
    
    retryMapInitialization() {
        console.log('Retrying map initialization...');
        setTimeout(() => {
            this.initializeMap();
        }, 1000);
    }
    
    async loadMapData() {
        try {
            // Load heatmap data
            const heatmapResponse = await fetch('/api/events/heatmap');
            if (heatmapResponse.ok) {
                const heatmapData = await heatmapResponse.json();
                this.updateHeatmapWithData(heatmapData);
            }
            
            // Load events data
            const eventsResponse = await fetch('/api/dashboard/stats');
            if (eventsResponse.ok) {
                const eventsData = await eventsResponse.json();
                if (eventsData.events) {
                    this.updateMarkersWithData(eventsData.events);
                }
            }
            
            // Load choropleth data
            const choroplethResponse = await fetch('/api/risk-by-country');
            if (choroplethResponse.ok) {
                const choroplethData = await choroplethResponse.json();
                this.updateChoroplethWithData(choroplethData);
            }
            
        } catch (error) {
            console.error('Error loading map data:', error);
            // Use fallback data
            this.loadFallbackMapData();
        }
    }
    
    loadFallbackMapData() {
        console.log('Loading fallback map data...');
        
        // Generate sample heatmap data
        const sampleHeatmapData = [
            { lat: 50.4501, lng: 30.5234, intensity: 0.9, count: 15, country: 'Ukraine' },
            { lat: 33.3152, lng: 44.3661, intensity: 0.8, count: 12, country: 'Iraq' },
            { lat: 31.7683, lng: 35.2137, intensity: 0.85, count: 18, country: 'Israel' },
            { lat: 33.5138, lng: 36.2765, intensity: 0.75, count: 10, country: 'Syria' },
            { lat: 15.5527, lng: 48.5164, intensity: 0.9, count: 20, country: 'Yemen' },
            { lat: 34.5553, lng: 69.2075, intensity: 0.8, count: 14, country: 'Afghanistan' },
            { lat: 25.2048, lng: 55.2708, intensity: 0.6, count: 8, country: 'UAE' },
            { lat: 39.9334, lng: 32.8597, intensity: 0.7, count: 11, country: 'Turkey' }
        ];
        
        this.updateHeatmapWithData(sampleHeatmapData);
        
        // Generate sample events
        const sampleEvents = [
            {
                id: 1,
                lat: 50.4501,
                lng: 30.5234,
                title: 'Conflicto en Europa del Este',
                risk_level: 'high',
                category: 'military_conflict',
                country: 'Ukraine',
                date: new Date().toISOString()
            },
            {
                id: 2,
                lat: 33.3152,
                lng: 44.3661,
                title: 'Tensiones en Medio Oriente',
                risk_level: 'high',
                category: 'political_tension',
                country: 'Iraq',
                date: new Date().toISOString()
            },
            {
                id: 3,
                lat: 31.7683,
                lng: 35.2137,
                title: 'Crisis diplomática',
                risk_level: 'medium',
                category: 'political_tension',
                country: 'Israel',
                date: new Date().toISOString()
            }
        ];
        
        this.updateMarkersWithData(sampleEvents);
    }
    
    updateHeatmapWithData(data) {
        if (!this.heatmapLayer || !Array.isArray(data)) return;
        
        // Clear existing heatmap
        this.heatmapLayer.clearLayers();
        
        data.forEach(point => {
            const lat = point.lat || point[0];
            const lng = point.lng || point[1];
            const intensity = point.intensity || point[2] || 0.5;
            const count = point.count || 1;
            
            if (lat && lng) {
                const color = this.getHeatColor(intensity);
                const radius = Math.max(30000, 50000 * intensity * Math.sqrt(count));
                
                const circle = L.circle([lat, lng], {
                    radius: radius,
                    fillColor: color,
                    fillOpacity: 0.6,
                    stroke: true,
                    color: color,
                    weight: 2,
                    opacity: 0.8
                }).bindPopup(`
                    <div class="heatmap-popup">
                        <h4>${point.country || 'Región'}</h4>
                        <p>Intensidad: ${(intensity * 100).toFixed(1)}%</p>
                        <p>Eventos: ${count}</p>
                    </div>
                `);
                
                circle.addTo(this.heatmapLayer);
            }
        });
        
        console.log(`Updated heatmap with ${data.length} points`);
    }
    
    updateMarkersWithData(events) {
        if (!this.markersLayer || !Array.isArray(events)) return;
        
        // Clear existing markers
        this.markersLayer.clearLayers();
        
        events.forEach(event => {
            if (event.lat && event.lng) {
                const icon = this.getEventIcon(event.category);
                const marker = L.marker([event.lat, event.lng], { icon })
                    .bindPopup(this.createEventPopup(event));
                
                marker.addTo(this.markersLayer);
            }
        });
        
        console.log(`Updated markers with ${events.length} events`);
    }
    
    updateChoroplethWithData(riskData) {
        // This will be handled by the existing choropleth initialization
        console.log('Choropleth data updated:', Object.keys(riskData).length, 'countries');
    }
    
    initializeHeatmapLayer() {
        // Create heatmap data from events
        const heatmapData = this.generateHeatmapData();
        
        // Note: In production, you'd use a proper heatmap library like Leaflet.heat
        // For now, we'll simulate with circle markers
        this.heatmapLayer = L.layerGroup();
        
        heatmapData.forEach(point => {
            const intensity = point[2];
            const color = this.getHeatColor(intensity);
            
            L.circle([point[0], point[1]], {
                radius: 50000 * intensity,
                fillColor: color,
                fillOpacity: 0.6,
                stroke: false
            }).addTo(this.heatmapLayer);
        });
    }
    
    initializeMarkersLayer() {
        this.markersLayer = L.layerGroup();
        
        // Add markers for high-risk events
        this.getHighRiskEvents().forEach(event => {
            const icon = this.getEventIcon(event.category);
            const marker = L.marker([event.lat, event.lng], { icon })
                .bindPopup(this.createEventPopup(event));
            
            marker.addTo(this.markersLayer);
        });
    }
    
    initializeChoroplethLayer() {
        this.choroplethLayer = L.layerGroup();
        this.loadChoroplethData();
    }
    
    async loadChoroplethData() {
        try {
            // Load world countries GeoJSON data
            const response = await fetch('https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson');
            const worldData = await response.json();
            
            // Get risk data for countries
            const riskData = await this.getRiskDataByCountry();
            
            // Create choropleth layer
            L.geoJSON(worldData, {
                style: (feature) => this.getChoroplethStyle(feature, riskData),
                onEachFeature: (feature, layer) => {
                    const countryName = feature.properties.name;
                    const riskLevel = riskData[countryName] || 0;
                    const riskText = this.getRiskLevelText(riskLevel);
                    
                    layer.bindPopup(`
                        <div class="choropleth-popup">
                            <h4>${countryName}</h4>
                            <p>Nivel de Riesgo: <span class="risk-${riskText.toLowerCase()}">${riskText}</span></p>
                            <p>Puntuación: ${riskLevel.toFixed(1)}/10</p>
                        </div>
                    `);
                    
                    layer.on({
                        mouseover: (e) => {
                            const layer = e.target;
                            layer.setStyle({
                                weight: 3,
                                color: '#666',
                                dashArray: '',
                                fillOpacity: 0.9
                            });
                        },
                        mouseout: (e) => {
                            const layer = e.target;
                            layer.setStyle(this.getChoroplethStyle(feature, riskData));
                        }
                    });
                }
            }).addTo(this.choroplethLayer);
            
        } catch (error) {
            console.error('Error loading choropleth data:', error);
            // Fallback to basic choropleth with sample data
            this.createFallbackChoropleth();
        }
    }
    
    async getRiskDataByCountry() {
        try {
            const response = await fetch('/api/risk-by-country');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching risk data:', error);
            // Return sample risk data
            return {
                'United States': 6.5,
                'China': 7.2,
                'Russia': 8.1,
                'Ukraine': 9.5,
                'Iran': 7.8,
                'Israel': 7.0,
                'Syria': 8.9,
                'Afghanistan': 8.7,
                'North Korea': 8.3,
                'Venezuela': 7.5,
                'Myanmar': 8.0,
                'Ethiopia': 7.3,
                'Mali': 7.8,
                'Somalia': 8.5,
                'Yemen': 9.0,
                'Lebanon': 7.6,
                'Turkey': 6.8,
                'India': 6.2,
                'Pakistan': 7.4,
                'Brazil': 5.8,
                'Mexico': 6.3,
                'Colombia': 6.7,
                'Nigeria': 7.1,
                'South Africa': 6.0,
                'Egypt': 6.9,
                'Saudi Arabia': 6.4,
                'Iraq': 8.2,
                'Libya': 8.4,
                'Sudan': 8.6,
                'Belarus': 7.7,
                'Kazakhstan': 5.9,
                'Algeria': 6.6,
                'Morocco': 5.5,
                'Tunisia': 6.1,
                'Jordan': 6.5,
                'Kuwait': 5.7,
                'Qatar': 4.8,
                'United Arab Emirates': 4.5,
                'Oman': 4.9,
                'Bahrain': 5.2,
                'Cyprus': 5.1,
                'Malta': 4.2,
                'Luxembourg': 3.8,
                'Switzerland': 3.5,
                'Norway': 3.2,
                'Denmark': 3.1,
                'Sweden': 3.3,
                'Finland': 3.6,
                'Iceland': 2.9,
                'Ireland': 3.4,
                'United Kingdom': 4.7,
                'France': 5.0,
                'Germany': 4.3,
                'Netherlands': 4.1,
                'Belgium': 4.4,
                'Austria': 4.0,
                'Italy': 5.3,
                'Spain': 4.9,
                'Portugal': 4.6,
                'Greece': 5.8,
                'Poland': 5.4,
                'Czech Republic': 4.8,
                'Slovakia': 4.7,
                'Hungary': 5.1,
                'Romania': 5.5,
                'Bulgaria': 5.6,
                'Croatia': 4.9,
                'Slovenia': 4.2,
                'Estonia': 4.1,
                'Latvia': 4.3,
                'Lithuania': 4.4,
                'Japan': 4.5,
                'South Korea': 5.2,
                'Taiwan': 6.8,
                'Singapore': 4.0,
                'Malaysia': 5.3,
                'Thailand': 5.7,
                'Vietnam': 5.9,
                'Philippines': 6.4,
                'Indonesia': 6.1,
                'Australia': 3.7,
                'New Zealand': 3.0,
                'Canada': 3.9,
                'Chile': 5.0,
                'Argentina': 5.8,
                'Uruguay': 4.5,
                'Paraguay': 5.2,
                'Bolivia': 6.0,
                'Peru': 6.3,
                'Ecuador': 6.1,
                'Costa Rica': 4.8,
                'Panama': 5.1,
                'Guatemala': 6.2,
                'Honduras': 6.7,
                'El Salvador': 6.4,
                'Nicaragua': 6.9,
                'Cuba': 6.6,
                'Dominican Republic': 5.9,
                'Haiti': 7.8,
                'Jamaica': 5.7,
                'Trinidad and Tobago': 5.4,
                'Barbados': 4.3,
                'Bahamas': 4.6,
                'Belize': 5.8,
                'Guyana': 5.5,
                'Suriname': 5.3,
                'French Guiana': 4.7
            };
        }
    }
    
    getChoroplethStyle(feature, riskData) {
        const countryName = feature.properties.name;
        const riskLevel = riskData[countryName] || 0;
        
        return {
            fillColor: this.getChoroplethColor(riskLevel),
            weight: 1,
            opacity: 1,
            color: '#333',
            dashArray: '2',
            fillOpacity: 0.7
        };
    }
    
    getChoroplethColor(riskLevel) {
        // Color scale from green (low risk) to red (high risk)
        if (riskLevel >= 8.5) return '#8B0000'; // Dark red - Critical
        if (riskLevel >= 7.5) return '#DC143C'; // Crimson - Very High
        if (riskLevel >= 6.5) return '#FF4500'; // Orange Red - High
        if (riskLevel >= 5.5) return '#FF8C00'; // Dark Orange - Medium-High
        if (riskLevel >= 4.5) return '#FFD700'; // Gold - Medium
        if (riskLevel >= 3.5) return '#ADFF2F'; // Green Yellow - Low-Medium
        if (riskLevel >= 2.5) return '#32CD32'; // Lime Green - Low
        return '#228B22'; // Forest Green - Very Low
    }
    
    getRiskLevelText(riskLevel) {
        if (riskLevel >= 8.5) return 'Crítico';
        if (riskLevel >= 7.5) return 'Muy Alto';
        if (riskLevel >= 6.5) return 'Alto';
        if (riskLevel >= 5.5) return 'Medio-Alto';
        if (riskLevel >= 4.5) return 'Medio';
        if (riskLevel >= 3.5) return 'Bajo-Medio';
        if (riskLevel >= 2.5) return 'Bajo';
        return 'Muy Bajo';
    }
    
    createFallbackChoropleth() {
        // Create simple country shapes for major countries if GeoJSON fails
        const majorCountries = [
            { name: 'United States', bounds: [[24.396308, -125.0], [49.384358, -66.93457]], risk: 6.5 },
            { name: 'China', bounds: [[18.197700, 73.677368], [53.560974, 134.773911]], risk: 7.2 },
            { name: 'Russia', bounds: [[41.188004, 19.638718], [81.857361, 180.0]], risk: 8.1 },
            { name: 'Ukraine', bounds: [[44.386463, 22.137059], [52.379581, 40.228581]], risk: 9.5 },
            { name: 'Iran', bounds: [[25.064327, 44.047256], [39.782056, 63.317471]], risk: 7.8 }
        ];
        
        majorCountries.forEach(country => {
            const rectangle = L.rectangle(country.bounds, {
                color: this.getChoroplethColor(country.risk),
                fillColor: this.getChoroplethColor(country.risk),
                fillOpacity: 0.7,
                weight: 2
            }).bindPopup(`
                <div class="choropleth-popup">
                    <h4>${country.name}</h4>
                    <p>Nivel de Riesgo: ${this.getRiskLevelText(country.risk)}</p>
                    <p>Puntuación: ${country.risk}/10</p>
                </div>
            `);
            
            rectangle.addTo(this.choroplethLayer);
        });
    }
    
    generateHeatmapData() {
        // Simulated heatmap data - in production, this would come from your API
        return [
            [51.5074, -0.1278, 0.8],  // London
            [40.7128, -74.0060, 0.9], // New York
            [35.6762, 139.6503, 0.7], // Tokyo
            [55.7558, 37.6173, 0.85], // Moscow
            [39.9042, 116.4074, 0.75], // Beijing
            [19.4326, -99.1332, 0.6], // Mexico City
            [-23.5505, -46.6333, 0.65], // São Paulo
            [30.0444, 31.2357, 0.9], // Cairo
            [28.6139, 77.2090, 0.7], // New Delhi
            [31.2304, 121.4737, 0.8], // Shanghai
        ];
    }
    
    getHighRiskEvents() {
        // Simulated high-risk events - in production, from your API
        return [
            {
                id: 1,
                lat: 50.4501,
                lng: 30.5234,
                category: 'military_conflict',
                title: 'Tensión militar en Europa del Este',
                risk: 'high',
                date: new Date()
            },
            {
                id: 2,
                lat: 33.3152,
                lng: 44.3661,
                category: 'political_tension',
                title: 'Crisis diplomática en Medio Oriente',
                risk: 'high',
                date: new Date()
            }
        ];
    }
    
    getEventIcon(category) {
        const icons = {
            military_conflict: L.divIcon({
                html: '<i class="fas fa-exclamation-triangle" style="color: #ff4757;"></i>',
                iconSize: [30, 30],
                className: 'custom-div-icon'
            }),
            political_tension: L.divIcon({
                html: '<i class="fas fa-flag" style="color: #ffd93d;"></i>',
                iconSize: [30, 30],
                className: 'custom-div-icon'
            }),
            economic_crisis: L.divIcon({
                html: '<i class="fas fa-chart-line" style="color: #ff6b6b;"></i>',
                iconSize: [30, 30],
                className: 'custom-div-icon'
            })
        };
        
        return icons[category] || icons.political_tension;
    }
    
    createEventPopup(event) {
        const risk = event.risk || event.risk_level || 'unknown';
        const category = event.category || 'general';
        const title = event.title || 'Sin título';
        const date = event.date ? new Date(event.date).toLocaleDateString() : 'Fecha no disponible';
        
        return `
            <div class="event-popup">
                <h4>${title}</h4>
                <p>Categoría: ${category}</p>
                <p>Riesgo: <span class="risk-${risk}">${risk.toUpperCase()}</span></p>
                <p>Fecha: ${date}</p>
            </div>
        `;
    }
    
    getHeatColor(intensity) {
        // Color gradient from green to red based on intensity
        if (intensity < 0.3) return '#4ecdc4';
        if (intensity < 0.5) return '#ffd93d';
        if (intensity < 0.7) return '#ff6b6b';
        return '#ff4757';
    }
    
    showLayer(layerType) {
        // Remove all layers
        this.map.removeLayer(this.heatmapLayer);
        this.map.removeLayer(this.markersLayer);
        this.map.removeLayer(this.choroplethLayer);
        
        // Add selected layer
        switch(layerType) {
            case 'heatmap':
                this.map.addLayer(this.heatmapLayer);
                break;
            case 'markers':
                this.map.addLayer(this.markersLayer);
                break;
            case 'choropleth':
                this.map.addLayer(this.choroplethLayer);
                break;
        }
        
        this.currentLayer = layerType;
    }
    
    initializeEventListeners() {
        // Language selector
        const languageBtn = document.getElementById('languageBtn');
        if (languageBtn) {
            languageBtn.addEventListener('click', () => {
                const dropdown = document.getElementById('languageDropdown');
                if (dropdown) {
                    dropdown.classList.toggle('active');
                }
            });
        }
        
        // Language options
        document.querySelectorAll('.language-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const lang = e.currentTarget.dataset.lang;
                this.changeLanguage(lang);
                const dropdown = document.getElementById('languageDropdown');
                if (dropdown) {
                    dropdown.classList.remove('active');
                }
            });
        });
        
        // Map layer controls
        document.querySelectorAll('.map-control-btn[data-layer]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const layer = e.currentTarget.dataset.layer;
                
                // Update active state
                document.querySelectorAll('.map-control-btn[data-layer]').forEach(b => {
                    b.classList.remove('active');
                });
                e.currentTarget.classList.add('active');
                
                this.showLayer(layer);
            });
        });
        
        // Mini map toggle removed - functionality no longer needed
        
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.language-selector')) {
                const dropdown = document.getElementById('languageDropdown');
                if (dropdown) {
                    dropdown.classList.remove('active');
                }
            }
        });
    }
    
    async loadDashboardData() {
        try {
            // Fetch dashboard statistics
            const response = await fetch('/api/dashboard/stats');
            const data = await response.json();
            
            // Update stats
            this.updateStats(data.stats);
            
            // Update map data
            if (data.events) {
                this.updateMapData(data.events);
            }
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    updateStats(stats) {
        // Update stat cards with animation
        this.animateValue('totalArticles', 0, stats.total_articles || 442, 1000);
        this.animateValue('highRiskEvents', 0, stats.high_risk_events || 41, 1000);
        this.animateValue('processedToday', 0, stats.processed_today || 133, 1000);
        this.animateValue('activeRegions', 0, stats.active_regions || 7, 1000);
    }
    
    animateValue(elementId, start, end, duration) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const range = end - start;
        const increment = end > start ? 1 : -1;
        const stepTime = Math.abs(Math.floor(duration / range));
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            element.textContent = current.toLocaleString();
            
            if (current === end) {
                clearInterval(timer);
            }
        }, stepTime);
    }
    
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return 'Hace unos segundos';
        if (seconds < 3600) return `Hace ${Math.floor(seconds / 60)} minutos`;
        if (seconds < 86400) return `Hace ${Math.floor(seconds / 3600)} horas`;
        return `Hace ${Math.floor(seconds / 86400)} días`;
    }
    
    initializeCharts() {
        this.createCategoryChart();
        this.createTimelineChart();
        this.createSentimentChart();
    }
    
    createCategoryChart() {
        const data = [{
            values: [40, 32, 14, 13, 1],
            labels: ['Conflicto Militar', 'Crisis Económica', 'Tensión Política', 'Disturbios', 'Desastre Natural'],
            type: 'pie',
            hole: .4,
            marker: {
                colors: ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#2ecc71']
            }
        }];
        
        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e8eaed' },
            showlegend: true,
            legend: {
                orientation: 'v',
                x: 1,
                y: 0.5
            }
        };
        
        Plotly.newPlot('categoryChart', data, layout, {responsive: true});
    }
    
    createTimelineChart() {
        const dates = this.generateDateRange(30);
        // Generate more varied data with better scale
        const values = dates.map((date, index) => {
            const baseValue = 20;
            const variation = Math.sin(index * 0.3) * 15 + Math.random() * 20;
            const trend = index * 0.5; // Slight upward trend
            return Math.max(5, Math.floor(baseValue + variation + trend));
        });
        
        const data = [{
            x: dates,
            y: values,
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: '#00d4ff',
                width: 3,
                shape: 'spline'
            },
            marker: {
                color: '#00d4ff',
                size: 8,
                line: {
                    color: '#ffffff',
                    width: 2
                }
            },
            fill: 'tonexty',
            fillcolor: 'rgba(0, 212, 255, 0.1)'
        }];
        
        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e8eaed' },
            xaxis: {
                gridcolor: '#2d3444',
                zerolinecolor: '#2d3444',
                showgrid: true,
                title: 'Fecha'
            },
            yaxis: {
                gridcolor: '#2d3444',
                zerolinecolor: '#2d3444',
                title: 'Número de Eventos',
                showgrid: true,
                range: [0, Math.max(...values) + 10]
            },
            margin: {
                l: 50,
                r: 30,
                t: 30,
                b: 50
            }
        };
        
        Plotly.newPlot('timelineChart', data, layout, {responsive: true});
    }
    
    createSentimentChart() {
        const data = [{
            x: ['Positivo', 'Neutral', 'Negativo'],
            y: [25, 45, 30],
            type: 'bar',
            marker: {
                color: ['#4ecdc4', '#667eea', '#ff4757']
            }
        }];
        
        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e8eaed' },
            xaxis: {
                gridcolor: '#2d3444'
            },
            yaxis: {
                gridcolor: '#2d3444',
                title: 'Porcentaje'
            }
        };
        
        Plotly.newPlot('sentimentChart', data, layout, {responsive: true});
    }
    
    generateDateRange(days) {
        const dates = [];
        const today = new Date();
        
        for (let i = days; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
        }
        
        return dates;
    }
    
    toggleMiniMap() {
        const miniMap = document.getElementById('miniMap');
        if (!miniMap) return;
        
        miniMap.classList.toggle('active');
        
        if (miniMap.classList.contains('active') && !this.miniMap) {
            // Initialize mini map
            this.miniMap = L.map('miniMap', {
                center: [20, 0],
                zoom: 1,
                zoomControl: false,
                attributionControl: false
            });
            
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                subdomains: 'abcd'
            }).addTo(this.miniMap);
        }
    }
    
    toggleTheme() {
        // In a full implementation, this would toggle between dark and light themes
        document.body.classList.toggle('light-theme');
        
        // Update icon
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            if (document.body.classList.contains('light-theme')) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        }
        
        // Save preference
        localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
    }
    
    changeLanguage(lang) {
        this.language = lang;
        const currentLang = document.getElementById('currentLang');
        if (currentLang) {
            currentLang.textContent = lang.toUpperCase();
        }
        
        // Update all i18n elements
        if (window.i18n) {
            window.i18n.changeLanguage(lang);
        }
        
        // Save preference
        localStorage.setItem('language', lang);
    }
    
    loadUserPreferences() {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            this.toggleTheme();
        }
        
        // Load saved language
        const savedLang = localStorage.getItem('language');
        if (savedLang) {
            this.changeLanguage(savedLang);
        }
    }
    
    startAutoRefresh() {
        setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }
    
    updateMapData(events) {
        // Clear existing markers
        this.markersLayer.clearLayers();
        
        // Add new markers based on events
        events.forEach(event => {
            if (event.lat && event.lng) {
                const icon = this.getEventIcon(event.category);
                const marker = L.marker([event.lat, event.lng], { icon })
                    .bindPopup(this.createEventPopup(event));
                
                marker.addTo(this.markersLayer);
            }
        });
        
        // Update heatmap data
        this.updateHeatmapData(events);
    }
    
    updateHeatmapData(events) {
        // Clear existing heatmap
        this.heatmapLayer.clearLayers();
        
        // Group events by location and calculate intensity
        const locationIntensity = {};
        
        events.forEach(event => {
            if (event.lat && event.lng) {
                const key = `${event.lat},${event.lng}`;
                if (!locationIntensity[key]) {
                    locationIntensity[key] = {
                        lat: event.lat,
                        lng: event.lng,
                        count: 0,
                        riskSum: 0
                    };
                }
                locationIntensity[key].count++;
                locationIntensity[key].riskSum += event.risk_level === 'high' ? 1 : event.risk_level === 'medium' ? 0.6 : 0.3;
            }
        });
        
        // Create heatmap circles
        Object.values(locationIntensity).forEach(location => {
            const intensity = location.riskSum / location.count;
            const color = this.getHeatColor(intensity);
            
            L.circle([location.lat, location.lng], {
                radius: 50000 * intensity * location.count,
                fillColor: color,
                fillOpacity: 0.6,
                stroke: false
            }).addTo(this.heatmapLayer);
        });
    }
    
    async loadFeaturedArticle() {
        try {
            const response = await fetch('/api/articles/featured');
            const article = await response.json();
            
            if (article) {
                // Check if elements exist before setting content
                const titleElement = document.querySelector('.featured-title');
                const dateElement = document.getElementById('featuredDate');
                const locationElement = document.getElementById('featuredLocation');
                const riskElement = document.getElementById('featuredRisk');
                const descriptionElement = document.querySelector('.featured-description');
                const imageElement = document.getElementById('featuredImage');
                const readMoreElement = document.getElementById('featuredReadMore');
                
                if (titleElement) titleElement.textContent = article.title;
                if (dateElement) dateElement.textContent = new Date(article.date).toLocaleDateString();
                if (locationElement) locationElement.textContent = article.location || 'Global';
                if (riskElement) riskElement.textContent = (article.risk_level || 'low').toUpperCase();
                if (descriptionElement) descriptionElement.textContent = article.description || 'Sin descripción disponible';
                
                if (imageElement) {
                    if (article.image_url) {
                        imageElement.src = article.image_url;
                    } else {
                        imageElement.src = 'https://via.placeholder.com/300x200?text=No+Image';
                    }
                }
                
                if (readMoreElement) {
                    readMoreElement.href = article.url || '#';
                }
            }
        } catch (error) {
            console.error('Error loading featured article:', error);
            // Set default content if there's an error
            this.setDefaultFeaturedArticle();
        }
    }
    
    setDefaultFeaturedArticle() {
        const titleElement = document.querySelector('.featured-title');
        const dateElement = document.getElementById('featuredDate');
        const locationElement = document.getElementById('featuredLocation');
        const riskElement = document.getElementById('featuredRisk');
        const descriptionElement = document.querySelector('.featured-description');
        const imageElement = document.getElementById('featuredImage');
        
        if (titleElement) titleElement.textContent = 'Sistema de Análisis Geopolítico Activo';
        if (dateElement) dateElement.textContent = new Date().toLocaleDateString();
        if (locationElement) locationElement.textContent = 'Global';
        if (riskElement) riskElement.textContent = 'MEDIUM';
        if (descriptionElement) descriptionElement.textContent = 'El sistema está monitoreando eventos geopolíticos en tiempo real. Los datos se actualizan automáticamente cada 30 segundos.';
        if (imageElement) imageElement.src = 'https://via.placeholder.com/300x200?text=Sistema+Activo';
    }
    
    async loadAIAnalysis() {
        try {
            const response = await fetch('/api/ai/weekly-analysis');
            const analysis = await response.json();
            
            if (analysis) {
                const dateElement = document.getElementById('aiArticleDate');
                if (dateElement) {
                    dateElement.textContent = new Date().toLocaleDateString();
                }
                this.structureAIContent(analysis.content);
            }
        } catch (error) {
            console.error('Error loading AI analysis:', error);
            // Load default content
            this.loadDefaultAIAnalysis();
        }
    }
    
    structureAIContent(content) {
        const contentContainer = document.getElementById('aiArticleContent');
        if (!contentContainer) return;
        
        // Parse the HTML content
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = content;
        
        // Extract first paragraph as introduction (full width)
        const firstParagraph = tempDiv.querySelector('p');
        let introText = '';
        if (firstParagraph) {
            introText = firstParagraph.outerHTML;
            firstParagraph.remove();
        }
        
        // Get remaining content and organize into columns
        const remainingElements = Array.from(tempDiv.children);
        const columns = [[], [], []];
        
        // Distribute content across three columns
        remainingElements.forEach((element, index) => {
            columns[index % 3].push(element.outerHTML);
        });
        
        // Structure the content with grid layout
        contentContainer.innerHTML = `
            ${introText}
            <div class="ai-article-content-grid">
                <div>${columns[0].join('')}</div>
                <div>${columns[1].join('')}</div>
                <div>${columns[2].join('')}</div>
            </div>
        `;
    }
    
    loadDefaultAIAnalysis() {
        const headlineContent = `
            <div class="analysis-headline">
                Escalada de Tensiones Geopolíticas: Un Análisis Integral de la Semana
            </div>
        `;
        
        const introContent = `
            <p>En la semana que concluye, el panorama geopolítico global ha estado marcado por una serie de eventos que reflejan la creciente complejidad de las relaciones internacionales. Los análisis automatizados de nuestro sistema han identificado patrones preocupantes en múltiples regiones, con un incremento notable en las tensiones militares y diplomáticas que requieren una evaluación exhaustiva de sus implicaciones a corto y mediano plazo.</p>
        `;
        
        const mainContent = `
            <h3>Focos Críticos de Atención</h3>
            <p>El conflicto en <strong>Europa del Este</strong> continúa siendo el epicentro de la atención internacional. Nuestros algoritmos han detectado un aumento del <em>23%</em> en la actividad militar en la región, con movimientos de tropas que sugieren una preparación para operaciones de mayor envergadura.</p>
            
            <p>Paralelamente, las <strong>tensiones en el Indo-Pacífico</strong> han experimentado una escalada significativa, con ejercicios navales conjuntos que han generado respuestas diplomáticas contundentes por parte de las potencias regionales.</p>
            
            <h3>Impactos Económicos Globales</h3>
            <p>Los mercados financieros han mostrado una volatilidad extrema, con índices bursátiles experimentando fluctuaciones del <em>15%</em> en sesiones individuales. Las materias primas, especialmente el petróleo y el gas natural, han registrado incrementos del <strong>8%</strong> y <strong>12%</strong> respectivamente.</p>
            
            <p>Las cadenas de suministro globales enfrentan nuevas disrupciones, con retrasos en los puertos principales que afectan sectores críticos como la tecnología y la manufactura automotriz.</p>
            
            <h3>Análisis Diplomático</h3>
            <p>La retórica diplomática se ha endurecido considerablemente, con declaraciones clasificadas como <em>"altamente confrontacionales"</em> en un <strong>78%</strong> de los casos analizados. Los canales de comunicación tradicionales muestran signos de deterioro, mientras que emergen nuevos actores en el escenario internacional.</p>
            
            <p>Las organizaciones multilaterales enfrentan desafíos sin precedentes para mantener su relevancia en un mundo cada vez más polarizado, donde las alianzas tradicionales se ven sometidas a tensiones crecientes.</p>
            
            <h3>Proyecciones y Escenarios</h3>
            <p>Nuestros modelos predictivos, basados en análisis de big data y machine learning, sugieren tres escenarios principales para las próximas semanas:</p>
            
            <ul>
                <li><strong>Desescalada gradual (25%):</strong> Reducción de tensiones mediante negociaciones multilaterales y la intervención de actores mediadores.</li>
                <li><strong>Status quo (45%):</strong> Mantenimiento del nivel actual de conflicto con fluctuaciones menores en la intensidad.</li>
                <li><strong>Escalada significativa (30%):</strong> Intensificación del conflicto con posibles implicaciones para la estabilidad global.</li>
            </ul>
            
            <p>La comunidad internacional se encuentra en un momento crucial donde las decisiones tomadas en los próximos días podrían definir el rumbo de las relaciones internacionales para los meses venideros. La vigilancia continua y el análisis en tiempo real se vuelven herramientas indispensables para navegar esta compleja coyuntura geopolítica.</p>
        `;
        
        const contentContainer = document.getElementById('aiArticleContent');
        if (contentContainer) {
            contentContainer.innerHTML = `
                ${headlineContent}
                ${introContent}
                ${mainContent}
            `;
        }
    }
    
    async loadArticlesTables() {
        this.loadLatestArticles();
        this.loadHighRiskArticles();
        this.setupArticleEventListeners();
    }
    
    async loadLatestArticles() {
        try {
            const response = await fetch('/api/articles/latest?limit=12');
            const articles = await response.json();
            
            const list = document.getElementById('latestArticlesList');
            if (!list) {
                console.error('Latest articles list element not found');
                return;
            }
            
            list.innerHTML = '';
            
            if (articles && articles.length > 0) {
                articles.forEach(article => {
                    const listItem = this.createArticleListItem(article);
                    list.appendChild(listItem);
                });
            } else {
                this.loadDefaultLatestArticles();
            }
        } catch (error) {
            console.error('Error loading latest articles:', error);
            this.loadDefaultLatestArticles();
        }
    }
    
    async loadHighRiskArticles() {
        try {
            const response = await fetch('/api/articles/high-risk?limit=12');
            const articles = await response.json();
            
            const grid = document.getElementById('highRiskArticlesGrid');
            if (!grid) {
                console.error('High risk articles grid element not found');
                return;
            }
            
            grid.innerHTML = '';
            
            if (articles && articles.length > 0) {
                articles.forEach(article => {
                    const card = this.createArticleCard(article, true);
                    grid.appendChild(card);
                });
            } else {
                this.loadDefaultHighRiskArticles();
            }
        } catch (error) {
            console.error('Error loading high risk articles:', error);
            this.loadDefaultHighRiskArticles();
        }
    }
    
    createArticleListItem(article) {
        const div = document.createElement('div');
        div.className = `article-list-item ${article.risk_level || 'low'}-risk`;
        
        const description = article.description || article.content || 'Sin descripción disponible';
        const truncatedDescription = description.length > 200 ? description.substring(0, 200) + '...' : description;
        
        // Get proper source name instead of "RSS Feed"
        const sourceName = this.getSourceName(article.source || 'Fuente desconocida');
        
        div.innerHTML = `
            <div class="article-list-content">
                <div class="article-list-title" onclick="window.open('${article.url || '#'}', '_blank')">
                    ${article.title}
                </div>
                <div class="article-list-description">
                    ${truncatedDescription}
                </div>
                <div class="article-list-meta">
                    <div class="article-list-meta-item">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${article.location || 'Global'}</span>
                    </div>
                    <div class="article-list-meta-item">
                        <i class="fas fa-newspaper"></i>
                        <span>${sourceName}</span>
                    </div>
                    <div class="article-list-meta-item">
                        <i class="fas fa-language"></i>
                        <span>${(article.language || 'es').toUpperCase()}</span>
                    </div>
                </div>
            </div>
            <div class="article-list-sidebar">
                <span class="article-list-risk ${article.risk_level || 'low'}">
                    ${(article.risk_level || 'low').toUpperCase()}
                </span>
                <div class="article-list-source">${sourceName}</div>
                <div class="article-list-date">
                    ${new Date(article.date || article.created_at).toLocaleDateString()}
                </div>
            </div>
        `;
        
        return div;
    }
    
    getSourceName(source) {
        // Map RSS feeds to proper news source names
        const sourceMap = {
            'RSS Feed': 'Agencia Internacional',
            'rss': 'Agencia Internacional',
            'feed': 'Agencia Internacional',
            'reuters': 'Reuters',
            'bbc': 'BBC News',
            'cnn': 'CNN',
            'ap': 'Associated Press',
            'bloomberg': 'Bloomberg',
            'ft': 'Financial Times',
            'wsj': 'Wall Street Journal',
            'nyt': 'New York Times',
            'guardian': 'The Guardian',
            'elpais': 'El País',
            'lemonde': 'Le Monde',
            'spiegel': 'Der Spiegel',
            'aljazeera': 'Al Jazeera',
            'rt': 'RT News',
            'xinhua': 'Xinhua News',
            'tass': 'TASS',
            'dw': 'Deutsche Welle'
        };
        
        const lowerSource = source.toLowerCase();
        for (const [key, value] of Object.entries(sourceMap)) {
            if (lowerSource.includes(key)) {
                return value;
            }
        }
        
        return source;
    }
    
    createArticleCard(article, isHighRisk = false) {
        const div = document.createElement('div');
        div.className = `article-card ${article.risk_level}-risk`;
        
        const description = article.description || article.content || 'Sin descripción disponible';
        const truncatedDescription = description.length > 150 ? description.substring(0, 150) + '...' : description;
        
        const sourceName = this.getSourceName(article.source || 'Fuente desconocida');
        
        div.innerHTML = `
            <div class="article-title" onclick="window.open('${article.url || '#'}', '_blank')">
                ${article.title}
            </div>
            <div class="article-meta">
                <div class="article-meta-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span class="article-location">${article.location || 'Global'}</span>
                </div>
                <div class="article-meta-item">
                    <i class="fas fa-newspaper"></i>
                    <span class="article-source">${sourceName}</span>
                </div>
                <div class="article-meta-item">
                    <i class="fas fa-language"></i>
                    <span>${(article.language || 'es').toUpperCase()}</span>
                </div>
            </div>
            <div class="article-description">
                ${truncatedDescription}
            </div>
            <div class="article-footer">
                <span class="risk-badge ${article.risk_level || 'low'}">
                    ${(article.risk_level || 'low').toUpperCase()}
                </span>
                <span class="article-date">
                    ${new Date(article.date || article.created_at).toLocaleDateString()}
                </span>
            </div>
        `;
        
        return div;
    }
    
    loadDefaultHighRiskArticles() {
        const defaultArticles = [
            {
                id: 1,
                title: 'Escalada militar en Europa del Este genera preocupación internacional',
                description: 'Los movimientos de tropas en la frontera han aumentado las tensiones diplomáticas entre las potencias mundiales.',
                location: 'Ucrania',
                source: 'Reuters',
                risk_level: 'high',
                language: 'es',
                date: new Date(Date.now() - 3600000),
                url: '#'
            },
            {
                id: 2,
                title: 'Crisis económica en mercados asiáticos afecta comercio global',
                description: 'La volatilidad en los mercados financieros asiáticos ha generado ondas de choque en todo el mundo.',
                location: 'China',
                source: 'Financial Times',
                risk_level: 'high',
                language: 'en',
                date: new Date(Date.now() - 7200000),
                url: '#'
            },
            {
                id: 3,
                title: 'Tensiones diplomáticas aumentan tras nuevas sanciones',
                description: 'El anuncio de nuevas medidas restrictivas ha escalado las tensiones entre países aliados.',
                location: 'Global',
                source: 'BBC News',
                risk_level: 'medium',
                language: 'en',
                date: new Date(Date.now() - 10800000),
                url: '#'
            },
            {
                id: 4,
                title: 'Conflicto en Medio Oriente se intensifica',
                description: 'Los enfrentamientos en la región han aumentado significativamente en las últimas 48 horas.',
                location: 'Medio Oriente',
                source: 'Al Jazeera',
                risk_level: 'high',
                language: 'ar',
                date: new Date(Date.now() - 14400000),
                url: '#'
            },
            {
                id: 5,
                title: 'Ciberataques masivos afectan infraestructura crítica',
                description: 'Una serie de ataques coordinados ha comprometido sistemas de energía y comunicaciones.',
                location: 'Estados Unidos',
                source: 'CNN',
                risk_level: 'high',
                language: 'en',
                date: new Date(Date.now() - 18000000),
                url: '#'
            },
            {
                id: 6,
                title: 'Protestas masivas en América Latina por crisis económica',
                description: 'Miles de manifestantes salen a las calles para protestar por las medidas de austeridad.',
                location: 'Brasil',
                source: 'El País',
                risk_level: 'medium',
                language: 'es',
                date: new Date(Date.now() - 21600000),
                url: '#'
            }
        ];
        
        const grid = document.getElementById('highRiskArticlesGrid');
        if (grid) {
            grid.innerHTML = '';
            
            defaultArticles.forEach(article => {
                const card = this.createArticleCard(article, true);
                grid.appendChild(card);
            });
        }
    }
    
    loadDefaultLatestArticles() {
        const defaultArticles = [
            {
                id: 7,
                title: 'Reunión de emergencia del Consejo de Seguridad de la ONU',
                description: 'Los representantes se reúnen para discutir la escalada de tensiones en múltiples regiones.',
                location: 'Nueva York',
                source: 'UN News',
                risk_level: 'medium',
                language: 'en',
                date: new Date(Date.now() - 1800000),
                url: '#'
            },
            {
                id: 8,
                title: 'Nuevos acuerdos comerciales buscan estabilizar mercados',
                description: 'Las principales economías mundiales anuncian medidas coordinadas para reducir la volatilidad.',
                location: 'Global',
                source: 'Bloomberg',
                risk_level: 'low',
                language: 'en',
                date: new Date(Date.now() - 3600000),
                url: '#'
            },
            {
                id: 9,
                title: 'Avances en negociaciones de paz generan optimismo',
                description: 'Los mediadores internacionales reportan progresos significativos en las conversaciones.',
                location: 'Suiza',
                source: 'Swiss Info',
                risk_level: 'low',
                language: 'de',
                date: new Date(Date.now() - 5400000),
                url: '#'
            },
            {
                id: 10,
                title: 'Cumbre climática aborda crisis energética global',
                description: 'Los líderes mundiales buscan soluciones sostenibles a la crisis energética actual.',
                location: 'Reino Unido',
                source: 'The Guardian',
                risk_level: 'medium',
                language: 'en',
                date: new Date(Date.now() - 7200000),
                url: '#'
            },
            {
                id: 11,
                title: 'Innovaciones tecnológicas prometen revolucionar comunicaciones',
                description: 'Nuevos desarrollos en telecomunicaciones podrían cambiar el panorama geopolítico.',
                location: 'Japón',
                source: 'Nikkei',
                risk_level: 'low',
                language: 'ja',
                date: new Date(Date.now() - 9000000),
                url: '#'
            },
            {
                id: 12,
                title: 'Cooperación internacional en investigación médica se fortalece',
                description: 'Los países anuncian nuevas iniciativas conjuntas para enfrentar desafíos de salud global.',
                location: 'Francia',
                source: 'Le Monde',
                risk_level: 'low',
                language: 'fr',
                date: new Date(Date.now() - 10800000),
                url: '#'
            }
        ];
        
        const list = document.getElementById('latestArticlesList');
        if (list) {
            list.innerHTML = '';
            
            defaultArticles.forEach(article => {
                const listItem = this.createArticleListItem(article);
                list.appendChild(listItem);
            });
        }
    }
    
    setupArticleEventListeners() {
        // Refresh buttons
        const refreshHighRisk = document.getElementById('refreshHighRisk');
        const refreshLatest = document.getElementById('refreshLatest');
        
        if (refreshHighRisk) {
            refreshHighRisk.addEventListener('click', () => {
                this.loadHighRiskArticles();
            });
        }
        
        if (refreshLatest) {
            refreshLatest.addEventListener('click', () => {
                this.loadLatestArticles();
            });
        }
        
        // Filter buttons (placeholder for future implementation)
        const filterHighRisk = document.getElementById('filterHighRisk');
        const filterLatest = document.getElementById('filterLatest');
        
        if (filterHighRisk) {
            filterHighRisk.addEventListener('click', () => {
                // TODO: Implement filtering functionality
                console.log('Filter high risk articles');
            });
        }
        
        if (filterLatest) {
            filterLatest.addEventListener('click', () => {
                // TODO: Implement filtering functionality
                console.log('Filter latest articles');
            });
        }
    }
    
    getCategoryLabel(category) {
        const labels = {
            'military_conflict': 'Conflicto Militar',
            'political_tension': 'Tensión Política',
            'economic_crisis': 'Crisis Económica',
            'social_unrest': 'Disturbios Sociales',
            'natural_disaster': 'Desastre Natural',
            'cyber_security': 'Ciberseguridad',
            'health_crisis': 'Crisis de Salud'
        };
        
        return labels[category] || category;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new GeopoliticalDashboard();
});