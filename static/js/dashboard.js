document.addEventListener('DOMContentLoaded', () => {
    console.log('Unified Dashboard Initialized');
    
    // --- MAP INITIALIZATION ---
    let map;
    let heatLayer;

    function initMap() {
        try {
            map = L.map('map').setView([20, 0], 2);

            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);

            heatLayer = L.heatLayer([], {
                radius: 25,
                blur: 15,
                maxZoom: 10,
                max: 1.0,
                gradient: {0.1: 'blue', 0.3: 'lime', 0.5: 'yellow', 0.7: 'orange', 1.0: 'red'}
            }).addTo(map);
            
            console.log('Map initialized successfully.');
            fetchMapData();
        } catch (error) {
            console.error('Error initializing map:', error);
            document.getElementById('map').innerHTML = '<p class="text-red-500 text-center">Error al cargar el mapa.</p>';
        }
    }

    async function fetchMapData() {
        try {
            const response = await fetch('/api/v1/events/geojson');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const geojsonData = await response.json();
            
            const heatPoints = geojsonData.features.map(feature => {
                const [lon, lat] = feature.geometry.coordinates;
                const risk = feature.properties.risk_score || 50; // Default risk if not present
                return [lat, lon, risk / 100]; // Lat, Lng, Intensity
            });

            heatLayer.setLatLngs(heatPoints);
            console.log(`Heatmap updated with ${heatPoints.length} points.`);
        } catch (error) {
            console.error('Error fetching map data:', error);
        }
    }

    // --- DASHBOARD DATA LOADING ---
    async function fetchDashboardData() {
        try {
            const response = await fetch('/api/v1/dashboard-data');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            updateStatCards(data.stats);
            updateHighRiskArticles(data.high_risk_articles);
            updateRecentArticles(data.recent_articles);
            updateAiAnalysis(data.ai_analysis);
            
            // Placeholder for chart updates
            updateCharts(data);

            console.log('Dashboard data loaded and rendered.');
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    }

    function updateStatCards(stats) {
        document.getElementById('global-risk-index').textContent = (Math.random() * 100).toFixed(1); // Placeholder
        document.getElementById('critical-alerts-count').textContent = stats.critical_alerts;
        document.getElementById('ai-confidence').textContent = `${stats.ai_confidence}%`;
        document.getElementById('new-articles-count').textContent = stats.total_articles; // Assuming total is new for now
    }

    function createArticleHtml(article) {
        const riskColor = article.risk_score > 85 ? 'text-red-400' : (article.risk_score > 60 ? 'text-yellow-400' : 'text-green-400');
        return `
            <a href="${article.url}" target="_blank" class="block p-3 hover:bg-gray-800/50 rounded-lg transition-colors">
                <div class="flex justify-between items-start">
                    <p class="font-semibold text-sm">${article.title}</p>
                    <span class="text-xs ${riskColor} font-bold">${article.risk_score.toFixed(1)}</span>
                </div>
                <p class="text-xs text-gray-400">${article.source} - ${new Date(article.published_at).toLocaleDateString()}</p>
            </a>
        `;
    }

    function updateHighRiskArticles(articles) {
        const container = document.getElementById('high-risk-articles');
        if (!articles || articles.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center p-4">No hay eventos de alto riesgo.</p>';
            return;
        }
        container.innerHTML = articles.map(createArticleHtml).join('');
    }

    function updateRecentArticles(articles) {
        const container = document.getElementById('recent-articles');
        if (!articles || articles.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center p-4">No hay artículos recientes.</p>';
            return;
        }
        container.innerHTML = articles.map(createArticleHtml).join('');
    }

    function updateAiAnalysis(analysis) {
        const container = document.getElementById('ai-analysis-content');
        // Basic markdown-to-HTML conversion
        let content = analysis.content.replace(/\n/g, '<br>');
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        container.innerHTML = `<p>${content}</p>`;
    }
    
    function updateCharts(data) {
        // Placeholder for Risk Timeline Chart
        const timelineTrace = {
            x: [1, 2, 3, 4, 5, 6, 7], // Days
            y: [65, 59, 80, 81, 56, 55, 70], // Dummy risk scores
            type: 'scatter',
            mode: 'lines+markers',
            line: {color: '#3b82f6'},
        };
        Plotly.newPlot('risk-timeline-chart', [timelineTrace], {
            margin: { t: 20, b: 30, l: 30, r: 10 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#e0e0e0' }
        }, {responsive: true});

        // Placeholder for Risk Distribution Chart
        const distributionTrace = {
            x: ['Bajo', 'Medio', 'Alto', 'Crítico'],
            y: [20, 45, 25, 10], // Dummy distribution
            type: 'bar',
            marker: {color: ['#22c55e', '#f59e0b', '#ef4444', '#dc2626']}
        };
        Plotly.newPlot('risk-distribution-chart', [distributionTrace], {
            margin: { t: 20, b: 30, l: 30, r: 10 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#e0e0e0' }
        }, {responsive: true});
    }

    // --- ACTIONS ---
    const runIngestionBtn = document.getElementById('run-ingestion-btn');
    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    const actionsStatus = document.getElementById('actions-status');

    async function handleAction(url, button, statusText) {
        button.disabled = true;
        button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...`;
        actionsStatus.textContent = '';

        try {
            const response = await fetch(url, { method: 'POST' });
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Error desconocido');
            }
            
            actionsStatus.textContent = `${statusText}: ${result.articles_added ?? result.articles_processed} artículos.`;
            // Recargar datos del dashboard para reflejar los cambios
            fetchDashboardData();

        } catch (error) {
            actionsStatus.textContent = `Error: ${error.message}`;
            console.error(`Error en la acción ${url}:`, error);
        } finally {
            button.disabled = false;
            button.innerHTML = button.id === 'run-ingestion-btn' 
                ? '<i class="fas fa-rss mr-2"></i>Ejecutar Ingesta RSS' 
                : '<i class="fas fa-cogs mr-2"></i>Ejecutar Análisis NLP';
        }
    }

    runIngestionBtn.addEventListener('click', () => {
        handleAction('/api/v1/actions/run-ingestion', runIngestionBtn, 'Ingesta completada');
    });

    runAnalysisBtn.addEventListener('click', () => {
        handleAction('/api/v1/actions/run-analysis', runAnalysisBtn, 'Análisis completado');
    });


    // --- INITIALIZATION CALLS ---
    initMap();
    fetchDashboardData();

    // Set interval to refresh data every 5 minutes
    setInterval(fetchDashboardData, 300000);
});
