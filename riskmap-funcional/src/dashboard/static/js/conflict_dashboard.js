 // Conflict Analysis Dashboard Component

class ConflictDashboard {
    constructor() {
        this.conflictData = null;
        this.hotspots = [];
        this.timeline = [];
        this.actors = [];
        
        this.init();
    }
    
    async init() {
        console.log('🔍 Inicializando dashboard de conflictos...');
        await this.loadConflictData();
        this.createConflictSection();
        this.initializeConflictCharts();
    }
    
    async loadConflictData() {
        try {
            const response = await fetch('/api/conflicts/dashboard-data');
            const data = await response.json();
            
            if (data.success) {
                this.conflictData = data;
                this.hotspots = data.hotspots || [];
                this.timeline = data.timeline || [];
                this.actors = data.top_actors || [];
                
                console.log('✅ Datos de conflictos cargados:', data.summary);
            } else {
                console.error('❌ Error cargando datos de conflictos:', data.error);
            }
        } catch (error) {
            console.error('❌ Error en loadConflictData:', error);
        }
    }
    
    createConflictSection() {
        // Buscar el contenedor principal del dashboard
        const dashboardContainer = document.querySelector('.dashboard-container');
        if (!dashboardContainer) {
            console.error('No se encontró el contenedor del dashboard');
            return;
        }
        
        // Crear sección de análisis de conflictos
        const conflictSection = document.createElement('div');
        conflictSection.className = 'conflict-analysis-section';
        conflictSection.innerHTML = `
            <div class="section-header">
                <h2 class="section-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Análisis de Conflictos Globales
                </h2>
                <div class="section-controls">
                    <button class="btn-refresh" id="refreshConflicts">
                        <i class="fas fa-sync-alt"></i>
                        Actualizar
                    </button>
                </div>
            </div>
            
            <!-- Estadísticas de Conflictos -->
            <div class="conflict-stats-grid">
                <div class="conflict-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-fire"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="totalConflictEvents">-</div>
                        <div class="stat-label">Eventos Totales</div>
                        <div class="stat-trend" id="conflictTrend">-</div>
                    </div>
                </div>
                
                <div class="conflict-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-skull-crossbones"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="totalDeaths">-</div>
                        <div class="stat-label">Muertes Registradas</div>
                        <div class="stat-change">Datos históricos</div>
                    </div>
                </div>
                
                <div class="conflict-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-globe-americas"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="activeCountries">-</div>
                        <div class="stat-label">Países Afectados</div>
                        <div class="stat-change">Últimos 4 años</div>
                    </div>
                </div>
                
                <div class="conflict-stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="recentEvents">-</div>
                        <div class="stat-label">Eventos Recientes</div>
                        <div class="stat-change">2022-2024</div>
                    </div>
                </div>
            </div>
            
            <!-- Gráficos de Conflictos -->
            <div class="conflict-charts-grid">
                <div class="chart-card conflict-timeline-card">
                    <div class="chart-header">
                        <h3>Timeline de Conflictos</h3>
                        <div class="chart-controls">
                            <select id="timelineCountrySelect">
                                <option value="">Global</option>
                            </select>
                        </div>
                    </div>
                    <div class="chart-container">
                        <div id="conflictTimelineChart"></div>
                    </div>
                </div>
                
                <div class="chart-card conflict-hotspots-card">
                    <div class="chart-header">
                        <h3>Hotspots de Conflicto</h3>
                    </div>
                    <div class="chart-container">
                        <div id="conflictHotspotsChart"></div>
                    </div>
                </div>
            </div>
            
            <!-- Tabla de Actores Principales -->
            <div class="conflict-actors-section">
                <div class="section-header">
                    <h3>Actores Principales en Conflictos</h3>
                </div>
                <div class="actors-grid" id="conflictActorsGrid">
                    <!-- Se llenará dinámicamente -->
                </div>
            </div>
        `;
        
        // Insertar después de la sección de mapas
        const mapSection = document.querySelector('.map-section');
        if (mapSection) {
            mapSection.parentNode.insertBefore(conflictSection, mapSection.nextSibling);
        } else {
            dashboardContainer.appendChild(conflictSection);
        }
        
        // Actualizar estadísticas
        this.updateConflictStats();
        
        // Configurar event listeners
        this.setupEventListeners();
    }
    
    updateConflictStats() {
        if (!this.conflictData || !this.conflictData.summary) return;
        
        const summary = this.conflictData.summary;
        
        // Actualizar valores
        document.getElementById('totalConflictEvents').textContent = 
            summary.total_events.toLocaleString();
        document.getElementById('totalDeaths').textContent = 
            summary.total_deaths.toLocaleString();
        document.getElementById('activeCountries').textContent = 
            summary.active_countries.toLocaleString();
        document.getElementById('recentEvents').textContent = 
            summary.recent_events.toLocaleString();
        
        // Actualizar tendencia
        const trendElement = document.getElementById('conflictTrend');
        const trend = summary.trend;
        
        if (trend === 'increasing') {
            trendElement.innerHTML = '<i class="fas fa-arrow-up"></i> Incrementando';
            trendElement.className = 'stat-trend increasing';
        } else if (trend === 'decreasing') {
            trendElement.innerHTML = '<i class="fas fa-arrow-down"></i> Disminuyendo';
            trendElement.className = 'stat-trend decreasing';
        } else {
            trendElement.innerHTML = '<i class="fas fa-minus"></i> Estable';
            trendElement.className = 'stat-trend stable';
        }
    }
    
    initializeConflictCharts() {
        this.createTimelineChart();
        this.createHotspotsChart();
        this.createActorsGrid();
    }
    
    createTimelineChart() {
        if (!this.timeline || this.timeline.length === 0) {
            document.getElementById('conflictTimelineChart').innerHTML = 
                '<p class="no-data">No hay datos de timeline disponibles</p>';
            return;
        }
        
        const data = [{
            x: this.timeline.map(d => d.year),
            y: this.timeline.map(d => d.events),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Eventos',
            line: {
                color: '#ff4757',
                width: 3
            },
            marker: {
                color: '#ff4757',
                size: 8
            }
        }, {
            x: this.timeline.map(d => d.year),
            y: this.timeline.map(d => d.total_deaths),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Muertes',
            yaxis: 'y2',
            line: {
                color: '#ff6b6b',
                width: 2
            },
            marker: {
                color: '#ff6b6b',
                size: 6
            }
        }];
        
        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e8eaed' },
            xaxis: {
                gridcolor: '#2d3444',
                title: 'Año'
            },
            yaxis: {
                gridcolor: '#2d3444',
                title: 'Número de Eventos',
                side: 'left'
            },
            yaxis2: {
                title: 'Muertes',
                overlaying: 'y',
                side: 'right',
                gridcolor: '#2d3444'
            },
            legend: {
                x: 0,
                y: 1
            },
            margin: {
                l: 50,
                r: 50,
                t: 30,
                b: 50
            }
        };
        
        Plotly.newPlot('conflictTimelineChart', data, layout, {responsive: true});
    }
    
    createHotspotsChart() {
        if (!this.hotspots || this.hotspots.length === 0) {
            document.getElementById('conflictHotspotsChart').innerHTML = 
                '<p class="no-data">No hay datos de hotspots disponibles</p>';
            return;
        }
        
        const data = [{
            x: this.hotspots.map(d => d.event_count),
            y: this.hotspots.map(d => d.total_deaths),
            text: this.hotspots.map(d => d.country),
            mode: 'markers+text',
            type: 'scatter',
            marker: {
                size: this.hotspots.map(d => Math.sqrt(d.intensity_index) * 3),
                color: this.hotspots.map(d => d.intensity_index),
                colorscale: 'Reds',
                showscale: true,
                colorbar: {
                    title: 'Índice de Intensidad'
                }
            },
            textposition: 'top center'
        }];
        
        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e8eaed' },
            xaxis: {
                gridcolor: '#2d3444',
                title: 'Número de Eventos'
            },
            yaxis: {
                gridcolor: '#2d3444',
                title: 'Total de Muertes'
            },
            margin: {
                l: 50,
                r: 50,
                t: 30,
                b: 50
            }
        };
        
        Plotly.newPlot('conflictHotspotsChart', data, layout, {responsive: true});
    }
    
    createActorsGrid() {
        const grid = document.getElementById('conflictActorsGrid');
        if (!grid) return;
        
        if (!this.actors || this.actors.length === 0) {
            grid.innerHTML = '<p class="no-data">No hay datos de actores disponibles</p>';
            return;
        }
        
        grid.innerHTML = '';
        
        this.actors.forEach(actor => {
            const actorCard = document.createElement('div');
            actorCard.className = 'actor-card';
            
            const typeIcon = actor.type === 'Government/State' ? 
                'fas fa-university' : 'fas fa-users';
            
            actorCard.innerHTML = `
                <div class="actor-icon">
                    <i class="${typeIcon}"></i>
                </div>
                <div class="actor-info">
                    <div class="actor-name">${actor.actor}</div>
                    <div class="actor-type">${actor.type}</div>
                    <div class="actor-stats">
                        <span class="stat">
                            <i class="fas fa-calendar"></i>
                            ${actor.events} eventos
                        </span>
                        <span class="stat">
                            <i class="fas fa-skull"></i>
                            ${actor.deaths.toLocaleString()} muertes
                        </span>
                    </div>
                </div>
            `;
            
            grid.appendChild(actorCard);
        });
    }
    
    setupEventListeners() {
        // Botón de actualizar
        const refreshBtn = document.getElementById('refreshConflicts');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async () => {
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualizando...';
                await this.loadConflictData();
                this.updateConflictStats();
                this.initializeConflictCharts();
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualizar';
            });
        }
        
        // Selector de país para timeline
        const countrySelect = document.getElementById('timelineCountrySelect');
        if (countrySelect) {
            // Poblar con países de hotspots
            this.hotspots.forEach(hotspot => {
                const option = document.createElement('option');
                option.value = hotspot.country;
                option.textContent = hotspot.country;
                countrySelect.appendChild(option);
            });
            
            countrySelect.addEventListener('change', async (e) => {
                const country = e.target.value;
                await this.loadTimelineForCountry(country);
            });
        }
    }
    
    async loadTimelineForCountry(country) {
        try {
            const url = country ? 
                `/api/conflicts/timeline?country=${encodeURIComponent(country)}` :
                '/api/conflicts/timeline';
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                this.timeline = data.data;
                this.createTimelineChart();
            }
        } catch (error) {
            console.error('Error cargando timeline por país:', error);
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Esperar un poco para que el dashboard principal se inicialice
    setTimeout(() => {
        window.conflictDashboard = new ConflictDashboard();
    }, 2000);
});