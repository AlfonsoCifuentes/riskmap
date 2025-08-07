// Historical Dashboard Expanded - Complete JavaScript Module
// This file handles all functionality for the expanded historical analysis dashboard

// Global variables
let globalData = {};
let chartsInstances = {};
let mapsInstances = {};
let filtersState = {
    dateFrom: null,
    dateTo: null,
    country: null,
    category: null,
    severity: null
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Historical Dashboard Expanded...');
    initializeDashboard();
});

// Main initialization function
async function initializeDashboard() {
    try {
        // Load initial data
        await loadDashboardData();
        
        // Initialize all tabs
        initializeAllTabs();
        
        // Set up event listeners
        setupEventListeners();
        
        // Load default view (overview)
        await loadOverviewTab();
        
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showErrorMessage('Error al inicializar el dashboard');
    }
}

// Load dashboard data from API
async function loadDashboardData() {
    try {
        const [dashboardData, filtersData] = await Promise.all([
            fetch('/api/historical/dashboard').then(r => r.json()),
            fetch('/api/historical/filters').then(r => r.json())
        ]);
        
        globalData = {
            ...dashboardData,
            filters: filtersData
        };
        
        // Populate filter dropdowns
        populateFilters(filtersData);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        throw error;
    }
}

// Populate filter dropdowns
function populateFilters(filtersData) {
    const countrySelect = document.getElementById('country');
    const categorySelect = document.getElementById('category');
    
    if (countrySelect && filtersData.countries) {
        countrySelect.innerHTML = '<option value="">Todos los países</option>';
        filtersData.countries.forEach(country => {
            countrySelect.innerHTML += `<option value="${country}">${country}</option>`;
        });
    }
    
    if (categorySelect && filtersData.categories) {
        categorySelect.innerHTML = '<option value="">Todas las categorías</option>';
        filtersData.categories.forEach(category => {
            categorySelect.innerHTML += `<option value="${category}">${category}</option>`;
        });
    }
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all content areas
    document.querySelectorAll('.content-area').forEach(area => {
        area.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected content area
    const selectedArea = document.getElementById(tabName + 'Tab');
    if (selectedArea) {
        selectedArea.classList.add('active');
    }
    
    // Add active class to selected tab button
    event.target.classList.add('active');
    
    // Load specific tab content
    loadTabContent(tabName);
}

// Load content for specific tab
async function loadTabContent(tabName) {
    try {
        switch(tabName) {
            case 'overview':
                await loadOverviewTab();
                break;
            case 'timeline':
                await loadTimelineTab();
                break;
            case 'events':
                await loadEventsTab();
                break;
            case 'patterns':
                await loadPatternsTab();
                break;
            case 'geography':
                await loadGeographyTab();
                break;
            case 'predictions':
                await loadPredictionsTab();
                break;
            case 'intelligence':
                await loadIntelligenceTab();
                break;
            case 'datasets':
                await loadDatasetsTab();
                break;
            case 'comparisons':
                await loadComparisonsTab();
                break;
            case 'scenarios':
                await loadScenariosTab();
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} tab:`, error);
        showErrorMessage(`Error al cargar la pestaña ${tabName}`);
    }
}

// ==================== TAB LOADERS ====================

// Overview Tab
async function loadOverviewTab() {
    console.log('Loading overview tab...');
    
    // Load global timeline chart
    if (globalData.timeline_data) {
        createGlobalTimelineChart();
    }
    
    // Load conflict intensity chart
    if (globalData.intensity_data) {
        createConflictIntensityChart();
    }
    
    // Load regional distribution chart
    if (globalData.regional_data) {
        createRegionalDistributionChart();
    }
    
    // Load sentiment trends chart
    if (globalData.sentiment_data) {
        createSentimentTrendsChart();
    }
    
    // Load overview map
    createOverviewMap();
    
    // Load executive summary
    loadExecutiveSummary();
}

// Timeline Tab
async function loadTimelineTab() {
    console.log('Loading timeline tab...');
    
    // Create interactive timeline
    createInteractiveTimeline();
    
    // Load events by period chart
    createEventsByPeriodChart();
    
    // Load temporal correlation chart
    createTemporalCorrelationChart();
    
    // Load detailed timeline
    loadDetailedTimeline();
}

// Events Tab
async function loadEventsTab() {
    console.log('Loading events tab...');
    
    // Create events time chart
    createEventsTimeChart();
    
    // Create category chart
    createCategoryChart();
    
    // Create events map
    createEventsMap();
    
    // Load events table
    loadEventsTable();
    
    // Load impact analysis
    loadImpactAnalysis();
}

// Patterns Tab
async function loadPatternsTab() {
    console.log('Loading patterns tab...');
    
    // Create cyclical patterns chart
    createCyclicalPatternsChart();
    
    // Create anomalies chart
    createAnomaliesChart();
    
    // Create emerging trends chart
    createEmergingTrendsChart();
    
    // Create frequency analysis chart
    createFrequencyAnalysisChart();
    
    // Load identified patterns
    loadIdentifiedPatterns();
}

// Geography Tab
async function loadGeographyTab() {
    console.log('Loading geography tab...');
    
    // Create geography map
    createGeographyMap();
    
    // Create regional heatmap chart
    createRegionalHeatmapChart();
    
    // Create migration flows chart
    createMigrationFlowsChart();
    
    // Create stability indices chart
    createStabilityIndicesChart();
    
    // Create geopolitical connections chart
    createGeopoliticalConnectionsChart();
}

// Predictions Tab
async function loadPredictionsTab() {
    console.log('Loading predictions tab...');
    
    // Create predictive models chart
    createPredictiveModelsChart();
    
    // Create scenario probabilities chart
    createScenarioProbabilitiesChart();
    
    // Create future trends chart
    createFutureTrendsChart();
    
    // Create risk factors chart
    createRiskFactorsChart();
    
    // Load AI predictions
    loadAIPredictions();
}

// Intelligence Tab
async function loadIntelligenceTab() {
    console.log('Loading intelligence tab...');
    
    // Create AI sentiment chart
    createAISentimentChart();
    
    // Create entity extraction chart
    createEntityExtractionChart();
    
    // Load high risk articles
    loadHighRiskArticles();
    
    // Load latest articles
    loadLatestArticles();
}

// Datasets Tab
async function loadDatasetsTab() {
    console.log('Loading datasets tab...');
    
    // Update statistics
    updateDatasetStatistics();
    
    // Create source coverage chart
    createSourceCoverageChart();
    
    // Create data quality chart
    createDataQualityChart();
    
    // Load data sources status
    loadDataSourcesStatus();
}

// Comparisons Tab
async function loadComparisonsTab() {
    console.log('Loading comparisons tab...');
    
    // Initialize comparison controls
    initializeComparisonControls();
    
    // Create comparative analysis chart
    createComparativeAnalysisChart();
    
    // Create performance metrics chart
    createPerformanceMetricsChart();
}

// Scenarios Tab
async function loadScenariosTab() {
    console.log('Loading scenarios tab...');
    
    // Initialize scenario controls
    initializeScenarioControls();
    
    // Create projected impact chart
    createProjectedImpactChart();
    
    // Create scenario timeline chart
    createScenarioTimelineChart();
    
    // Load mitigation recommendations
    loadMitigationRecommendations();
}

// ==================== CHART CREATORS ====================

function createGlobalTimelineChart() {
    const container = document.getElementById('globalTimelineChart');
    if (!container) return;
    
    // Sample data for demonstration
    const data = {
        labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        datasets: [{
            label: 'Eventos Globales',
            data: [12, 19, 8, 15, 25, 14],
            borderColor: '#00d4ff',
            backgroundColor: 'rgba(0, 212, 255, 0.1)',
            tension: 0.4
        }]
    };
    
    if (chartsInstances.globalTimeline) {
        chartsInstances.globalTimeline.destroy();
    }
    
    const ctx = createCanvas(container);
    chartsInstances.globalTimeline = new Chart(ctx, {
        type: 'line',
        data: data,
        options: getChartOptions('Eventos por Mes')
    });
}

function createConflictIntensityChart() {
    const container = document.getElementById('conflictIntensityChart');
    if (!container) return;
    
    const data = {
        labels: ['Muy Bajo', 'Bajo', 'Medio', 'Alto', 'Muy Alto'],
        datasets: [{
            data: [15, 25, 30, 20, 10],
            backgroundColor: [
                '#66bb6a',
                '#ffa726',
                '#ffcc02',
                '#ff7043',
                '#ff4757'
            ]
        }]
    };
    
    if (chartsInstances.conflictIntensity) {
        chartsInstances.conflictIntensity.destroy();
    }
    
    const ctx = createCanvas(container);
    chartsInstances.conflictIntensity = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: getChartOptions('Distribución de Intensidad')
    });
}

function createRegionalDistributionChart() {
    const container = document.getElementById('regionalDistributionChart');
    if (!container) return;
    
    const data = {
        labels: ['África', 'Asia', 'Europa', 'América', 'Oceanía'],
        datasets: [{
            label: 'Eventos por Región',
            data: [45, 38, 22, 28, 5],
            backgroundColor: 'rgba(0, 212, 255, 0.7)',
            borderColor: '#00d4ff',
            borderWidth: 1
        }]
    };
    
    if (chartsInstances.regionalDistribution) {
        chartsInstances.regionalDistribution.destroy();
    }
    
    const ctx = createCanvas(container);
    chartsInstances.regionalDistribution = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: getChartOptions('Eventos por Región')
    });
}

function createSentimentTrendsChart() {
    const container = document.getElementById('sentimentTrendsChart');
    if (!container) return;
    
    const data = {
        labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        datasets: [{
            label: 'Positivo',
            data: [5, 8, 6, 9, 12, 10],
            borderColor: '#66bb6a',
            backgroundColor: 'rgba(102, 187, 106, 0.1)'
        }, {
            label: 'Neutral',
            data: [15, 12, 18, 14, 16, 20],
            borderColor: '#ffa726',
            backgroundColor: 'rgba(255, 167, 38, 0.1)'
        }, {
            label: 'Negativo',
            data: [25, 30, 22, 28, 18, 15],
            borderColor: '#ff4757',
            backgroundColor: 'rgba(255, 71, 87, 0.1)'
        }]
    };
    
    if (chartsInstances.sentimentTrends) {
        chartsInstances.sentimentTrends.destroy();
    }
    
    const ctx = createCanvas(container);
    chartsInstances.sentimentTrends = new Chart(ctx, {
        type: 'line',
        data: data,
        options: getChartOptions('Tendencias de Sentimiento')
    });
}

// Helper functions for charts
function createCanvas(container) {
    container.innerHTML = '<canvas></canvas>';
    return container.querySelector('canvas').getContext('2d');
}

function getChartOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#ffffff'
                }
            },
            title: {
                display: true,
                text: title,
                color: '#00d4ff'
            }
        },
        scales: {
            x: {
                ticks: {
                    color: '#ffffff'
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            },
            y: {
                ticks: {
                    color: '#ffffff'
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        }
    };
}

// ==================== MAP CREATORS ====================

function createOverviewMap() {
    const container = document.getElementById('overviewMap');
    if (!container) return;
    
    // Initialize Leaflet map
    if (mapsInstances.overview) {
        mapsInstances.overview.remove();
    }
    
    mapsInstances.overview = L.map('overviewMap').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(mapsInstances.overview);
    
    // Add sample markers
    addSampleMarkers(mapsInstances.overview);
}

function createEventsMap() {
    const container = document.getElementById('eventsMap');
    if (!container) return;
    
    if (mapsInstances.events) {
        mapsInstances.events.remove();
    }
    
    mapsInstances.events = L.map('eventsMap').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(mapsInstances.events);
    
    addSampleMarkers(mapsInstances.events);
}

function createGeographyMap() {
    const container = document.getElementById('geographyMap');
    if (!container) return;
    
    if (mapsInstances.geography) {
        mapsInstances.geography.remove();
    }
    
    mapsInstances.geography = L.map('geographyMap').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(mapsInstances.geography);
    
    addSampleMarkers(mapsInstances.geography);
}

function addSampleMarkers(map) {
    const sampleLocations = [
        { lat: 40.7128, lng: -74.0060, title: 'New York', risk: 'medium' },
        { lat: 51.5074, lng: -0.1278, title: 'London', risk: 'low' },
        { lat: 35.6762, lng: 139.6503, title: 'Tokyo', risk: 'low' },
        { lat: -33.8688, lng: 151.2093, title: 'Sydney', risk: 'low' },
        { lat: 33.9391, lng: 67.7100, title: 'Kabul', risk: 'high' }
    ];
    
    sampleLocations.forEach(location => {
        const color = location.risk === 'high' ? 'red' : 
                     location.risk === 'medium' ? 'orange' : 'green';
        
        L.circleMarker([location.lat, location.lng], {
            radius: 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7
        }).addTo(map).bindPopup(`<b>${location.title}</b><br>Riesgo: ${location.risk}`);
    });
}

// ==================== CONTENT LOADERS ====================

function loadExecutiveSummary() {
    const container = document.getElementById('executiveSummary');
    if (!container) return;
    
    container.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <h4 style="color: #00d4ff; margin-bottom: 0.5rem;">Resumen Ejecutivo - Últimas 24 Horas</h4>
            <p style="color: #ccc; line-height: 1.6;">
                Se han detectado <strong style="color: #ff4757;">12 eventos de alto impacto</strong> en las últimas 24 horas, 
                con un incremento del <strong style="color: #ffa726;">15%</strong> en la actividad geopolítica respecto al período anterior.
            </p>
            <p style="color: #ccc; line-height: 1.6;">
                Las regiones de <strong style="color: #00d4ff;">Medio Oriente</strong> y 
                <strong style="color: #00d4ff;">Europa Oriental</strong> muestran la mayor actividad, 
                con indicadores de tensión elevados en <strong style="color: #ff4757;">3 países</strong>.
            </p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
            <div style="text-align: center; padding: 1rem; background: rgba(255, 71, 87, 0.1); border-radius: 8px;">
                <div style="font-size: 2rem; color: #ff4757; font-weight: bold;">12</div>
                <div style="color: #ccc; font-size: 0.9rem;">Eventos Críticos</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: rgba(255, 167, 38, 0.1); border-radius: 8px;">
                <div style="font-size: 2rem; color: #ffa726; font-weight: bold;">87</div>
                <div style="color: #ccc; font-size: 0.9rem;">Alertas Activas</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: rgba(0, 212, 255, 0.1); border-radius: 8px;">
                <div style="font-size: 2rem; color: #00d4ff; font-weight: bold;">256</div>
                <div style="color: #ccc; font-size: 0.9rem;">Artículos Analizados</div>
            </div>
        </div>
    `;
}

function loadHighRiskArticles() {
    const container = document.getElementById('highRiskArticlesGrid');
    if (!container) return;
    
    const sampleArticles = [
        {
            title: 'Escalada de Tensiones en Región X',
            source: 'Reuters',
            date: '2024-01-15',
            riskScore: 85,
            summary: 'Aumento significativo en la actividad militar...'
        },
        {
            title: 'Crisis Económica Emergente',
            source: 'BBC',
            date: '2024-01-15',
            riskScore: 78,
            summary: 'Indicadores económicos muestran deterioro...'
        },
        {
            title: 'Conflicto Fronterizo Activo',
            source: 'CNN',
            date: '2024-01-14',
            riskScore: 92,
            summary: 'Reportes de enfrentamientos en la frontera...'
        }
    ];
    
    container.innerHTML = sampleArticles.map(article => `
        <div class="article-card">
            <div class="article-title">${article.title}</div>
            <div class="article-meta">${article.source} • ${article.date}</div>
            <p style="color: #ccc; font-size: 0.9rem; margin: 0.5rem 0;">${article.summary}</p>
            <div class="article-risk-score">Riesgo: ${article.riskScore}%</div>
        </div>
    `).join('');
}

function loadLatestArticles() {
    const container = document.getElementById('latestArticlesList');
    if (!container) return;
    
    const sampleArticles = [
        { title: 'Análisis de Estabilidad Regional', time: 'Hace 15 min', severity: 'medium' },
        { title: 'Reporte de Actividad Diplomática', time: 'Hace 32 min', severity: 'low' },
        { title: 'Alerta de Seguridad Nacional', time: 'Hace 1 hora', severity: 'high' },
        { title: 'Actualización Económica Global', time: 'Hace 2 horas', severity: 'medium' },
        { title: 'Monitoreo de Conflictos Activos', time: 'Hace 3 horas', severity: 'high' }
    ];
    
    container.innerHTML = sampleArticles.map(article => `
        <div class="article-item">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <div style="color: #fff; font-weight: 500; margin-bottom: 0.3rem;">${article.title}</div>
                    <div style="color: #ccc; font-size: 0.8rem;">${article.time}</div>
                </div>
                <div class="alert-severity severity-${article.severity}">
                    ${article.severity === 'high' ? 'Alta' : article.severity === 'medium' ? 'Media' : 'Baja'}
                </div>
            </div>
        </div>
    `).join('');
}

function updateDatasetStatistics() {
    const stats = {
        articlesCount: '12,456',
        gdeltRecords: '1.2M',
        acledEvents: '45,789',
        gprIndicators: '892'
    };
    
    Object.keys(stats).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            element.textContent = stats[key];
        }
    });
}

function loadDataSourcesStatus() {
    const container = document.getElementById('dataSourcesStatus');
    if (!container) return;
    
    const sources = [
        { name: 'GDELT', status: 'online', lastUpdate: '5 min ago', records: '1.2M' },
        { name: 'ACLED', status: 'online', lastUpdate: '10 min ago', records: '45.7K' },
        { name: 'RSS Feeds', status: 'warning', lastUpdate: '2 hours ago', records: '12.4K' },
        { name: 'News APIs', status: 'online', lastUpdate: '1 min ago', records: '8.9K' }
    ];
    
    container.innerHTML = sources.map(source => `
        <div class="source-status-card">
            <div class="source-status-header">
                <div class="source-name">${source.name}</div>
                <div class="status-indicator ${source.status}"></div>
            </div>
            <div class="source-metrics">
                <div class="metric-item">Última actualización: <span class="metric-value">${source.lastUpdate}</span></div>
                <div class="metric-item">Registros: <span class="metric-value">${source.records}</span></div>
            </div>
        </div>
    `).join('');
}

// ==================== UTILITY FUNCTIONS ====================

function setupEventListeners() {
    // Filter change listeners
    ['dateFrom', 'dateTo', 'country', 'category', 'severity'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', applyFilters);
        }
    });
}

function applyFilters() {
    // Update filters state
    filtersState = {
        dateFrom: document.getElementById('dateFrom')?.value,
        dateTo: document.getElementById('dateTo')?.value,
        country: document.getElementById('country')?.value,
        category: document.getElementById('category')?.value,
        severity: document.getElementById('severity')?.value
    };
    
    console.log('Filters applied:', filtersState);
    // Reload current tab with new filters
    // Implementation would refresh current data with filters
}

async function triggerETLUpdate() {
    try {
        showLoadingMessage('Actualizando datos...');
        const response = await fetch('/api/historical/etl/trigger', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            showSuccessMessage('Datos actualizados correctamente');
            await loadDashboardData();
            // Reload current active tab
            const activeTab = document.querySelector('.tab-button.active');
            if (activeTab) {
                const tabName = activeTab.textContent.trim().toLowerCase();
                await loadTabContent(tabName);
            }
        } else {
            showErrorMessage('Error al actualizar datos');
        }
    } catch (error) {
        console.error('Error triggering ETL update:', error);
        showErrorMessage('Error al actualizar datos');
    }
}

function exportData() {
    // Implementation for data export
    console.log('Exporting data...');
    showInfoMessage('Función de exportación en desarrollo');
}

// Message display functions
function showErrorMessage(message) {
    console.error(message);
    // Could implement toast notifications here
}

function showSuccessMessage(message) {
    console.log(message);
    // Could implement toast notifications here
}

function showInfoMessage(message) {
    console.info(message);
    // Could implement toast notifications here
}

function showLoadingMessage(message) {
    console.log(message);
    // Could implement loading overlay here
}

// Initialize all tabs placeholder functions (to be implemented)
function initializeAllTabs() {
    console.log('Initializing all tabs...');
}

// Timeline specific functions
function setTimeRange(range) {
    console.log('Setting time range:', range);
    // Update timeline view based on range
    
    // Remove active class from all buttons
    document.querySelectorAll('.time-range-selector button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

function createInteractiveTimeline() {
    const container = document.getElementById('interactiveTimeline');
    if (!container) return;
    
    container.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: #ccc;">
            <i class="fas fa-clock" style="font-size: 3rem; color: #00d4ff; margin-bottom: 1rem;"></i>
            <p>Línea temporal interactiva cargando...</p>
        </div>
    `;
}

// Additional chart creators for missing tabs
function createEventsTimeChart() {
    const container = document.getElementById('eventsTimeChart');
    if (!container) return;
    createPlaceholderChart(container, 'Cronología de Eventos');
}

function createCategoryChart() {
    const container = document.getElementById('categoryChart');
    if (!container) return;
    createPlaceholderChart(container, 'Distribución por Categoría');
}

function createPlaceholderChart(container, title) {
    const ctx = createCanvas(container);
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
            datasets: [{
                label: 'Datos',
                data: [12, 19, 8, 15, 25],
                backgroundColor: 'rgba(0, 212, 255, 0.7)'
            }]
        },
        options: getChartOptions(title)
    });
}

// Export functions to global scope
window.switchTab = switchTab;
window.setTimeRange = setTimeRange;
window.triggerETLUpdate = triggerETLUpdate;
window.exportData = exportData;
