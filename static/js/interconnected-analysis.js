// JavaScript para Análisis Interconectado
class InterconnectedAnalysis {
    constructor() {
        this.init();
        this.setupRealTimeUpdates();
        this.createNetworkVisualization();
        this.createCorrelationMatrix();
        this.createTrendsChart();
        this.loadInterconnectedData();
    }

    init() {
        console.log('🔗 Inicializando Análisis Interconectado...');
        this.updateMetrics();
        this.loadEventsTimeline();
        this.setupInterconnectedAlerts();
    }

    setupRealTimeUpdates() {
        // Actualizar cada 30 segundos
        setInterval(() => {
            this.updateMetrics();
            this.updateNetworkConnections();
            this.loadEventsTimeline();
        }, 30000);
    }

    updateMetrics() {
        // Simular métricas dinámicas
        const metrics = {
            activeConnections: Math.floor(Math.random() * 50) + 20,
            criticalCorrelations: Math.floor(Math.random() * 10) + 1,
            trendsDetected: Math.floor(Math.random() * 25) + 10,
            syncStatus: Math.floor(Math.random() * 5) + 95
        };

        Object.keys(metrics).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                if (key === 'syncStatus') {
                    element.textContent = metrics[key] + '%';
                } else {
                    element.textContent = metrics[key];
                }
                
                // Animación de actualización
                element.style.animation = 'none';
                element.offsetHeight; // Trigger reflow
                element.style.animation = 'pulse 0.5s';
            }
        });
    }

    createNetworkVisualization() {
        const width = 600;
        const height = 400;
        
        const svg = d3.select('#connectionNetwork')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Datos de nodos (sistemas conectados)
        const nodes = [
            { id: 'GDELT', group: 1, x: width/2, y: height/2 },
            { id: 'Artículos', group: 2, x: width/4, y: height/3 },
            { id: 'SentinelHub', group: 3, x: 3*width/4, y: height/3 },
            { id: 'Mapa Calor', group: 4, x: width/4, y: 2*height/3 },
            { id: 'Dashboard', group: 5, x: 3*width/4, y: 2*height/3 },
            { id: 'Alertas', group: 6, x: width/2, y: height/6 },
            { id: 'Reportes', group: 7, x: width/2, y: 5*height/6 }
        ];

        // Datos de enlaces (conexiones)
        const links = [
            { source: 'GDELT', target: 'Artículos' },
            { source: 'GDELT', target: 'SentinelHub' },
            { source: 'GDELT', target: 'Dashboard' },
            { source: 'Artículos', target: 'Mapa Calor' },
            { source: 'SentinelHub', target: 'Mapa Calor' },
            { source: 'Dashboard', target: 'Alertas' },
            { source: 'Mapa Calor', target: 'Reportes' },
            { source: 'Alertas', target: 'Reportes' }
        ];

        // Crear enlaces
        svg.selectAll('.link')
            .data(links)
            .enter()
            .append('line')
            .attr('class', 'connection-line')
            .attr('x1', d => nodes.find(n => n.id === d.source).x)
            .attr('y1', d => nodes.find(n => n.id === d.source).y)
            .attr('x2', d => nodes.find(n => n.id === d.target).x)
            .attr('y2', d => nodes.find(n => n.id === d.target).y);

        // Crear nodos
        const node = svg.selectAll('.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x},${d.y})`);

        node.append('circle')
            .attr('r', 20)
            .attr('class', 'network-node')
            .on('click', (event, d) => {
                this.showNodeDetails(d);
            });

        node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('font-size', '10px')
            .attr('fill', '#fff')
            .text(d => d.id);
    }

    createCorrelationMatrix() {
        const systems = ['GDELT', 'Artículos', 'SentinelHub', 'Mapa Calor', 'Dashboard'];
        const size = 60;
        const margin = 5;

        const svg = d3.select('#correlationMatrix')
            .append('svg')
            .attr('width', systems.length * (size + margin))
            .attr('height', systems.length * (size + margin));

        // Generar datos de correlación
        const correlationData = [];
        for (let i = 0; i < systems.length; i++) {
            for (let j = 0; j < systems.length; j++) {
                const correlation = i === j ? 1 : Math.random();
                correlationData.push({
                    x: i,
                    y: j,
                    value: correlation,
                    system1: systems[i],
                    system2: systems[j]
                });
            }
        }

        // Escala de colores
        const colorScale = d3.scaleSequential(d3.interpolateRdYlBu)
            .domain([0, 1]);

        // Crear celdas de la matriz
        svg.selectAll('.heatmap-cell')
            .data(correlationData)
            .enter()
            .append('rect')
            .attr('class', 'heatmap-cell')
            .attr('x', d => d.x * (size + margin))
            .attr('y', d => d.y * (size + margin))
            .attr('width', size)
            .attr('height', size)
            .attr('fill', d => colorScale(d.value))
            .on('mouseover', (event, d) => {
                this.showCorrelationTooltip(event, d);
            });

        // Etiquetas
        svg.selectAll('.row-label')
            .data(systems)
            .enter()
            .append('text')
            .attr('class', 'row-label')
            .attr('x', -5)
            .attr('y', (d, i) => i * (size + margin) + size/2)
            .attr('text-anchor', 'end')
            .attr('alignment-baseline', 'middle')
            .attr('font-size', '10px')
            .attr('fill', '#fff')
            .text(d => d);
    }

    createTrendsChart() {
        const ctx = document.getElementById('trendsChart').getContext('2d');
        
        // Generar datos de tendencias
        const labels = [];
        const riskData = [];
        const gdeltData = [];
        const articlesData = [];
        
        for (let i = 23; i >= 0; i--) {
            const date = new Date();
            date.setHours(date.getHours() - i);
            labels.push(date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }));
            
            riskData.push(Math.random() * 10);
            gdeltData.push(Math.random() * 100);
            articlesData.push(Math.floor(Math.random() * 50) + 10);
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Nivel de Riesgo',
                        data: riskData,
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Eventos GDELT',
                        data: gdeltData,
                        borderColor: '#4ecdc4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Artículos Procesados',
                        data: articlesData,
                        borderColor: '#45b7d1',
                        backgroundColor: 'rgba(69, 183, 209, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#fff' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#fff' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { color: '#fff' }
                    },
                    y2: {
                        type: 'linear',
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#fff' }
                    }
                }
            }
        });
    }

    loadEventsTimeline() {
        const timeline = document.getElementById('eventsTimeline');
        
        // Eventos simulados
        const events = [
            {
                time: '12:45',
                title: 'Correlación Alta Detectada',
                description: 'GDELT y Artículos muestran correlación de 0.89',
                type: 'high'
            },
            {
                time: '12:30',
                title: 'Nuevo Patrón Identificado',
                description: 'SentinelHub detecta cambios en zona de conflicto',
                type: 'medium'
            },
            {
                time: '12:15',
                title: 'Sincronización Completada',
                description: 'Todos los sistemas actualizados correctamente',
                type: 'low'
            },
            {
                time: '12:00',
                title: 'Alerta de Tendencia',
                description: 'Incremento en actividad geopolítica detectado',
                type: 'high'
            }
        ];

        timeline.innerHTML = events.map(event => `
            <div class="timeline-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${event.title}</h6>
                        <p class="mb-0 small">${event.description}</p>
                    </div>
                    <span class="badge bg-${event.type === 'high' ? 'danger' : event.type === 'medium' ? 'warning' : 'info'}">
                        ${event.time}
                    </span>
                </div>
            </div>
        `).join('');
    }

    setupInterconnectedAlerts() {
        const alertsContainer = document.getElementById('interconnectedAlerts');
        
        const alerts = [
            {
                id: 1,
                title: 'Correlación Crítica GDELT-Artículos',
                message: 'Se detectó una correlación del 94% entre eventos GDELT y artículos procesados',
                severity: 'high',
                systems: ['GDELT', 'Artículos'],
                timestamp: new Date().toISOString()
            },
            {
                id: 2,
                title: 'Patrón Satelital Confirmado',
                message: 'SentinelHub confirma cambios detectados por análisis de riesgo',
                severity: 'medium',
                systems: ['SentinelHub', 'Mapa Calor'],
                timestamp: new Date().toISOString()
            }
        ];

        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.severity === 'high' ? 'danger' : 'warning'} alert-dismissible fade show">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="alert-heading">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            ${alert.title}
                        </h6>
                        <p class="mb-1">${alert.message}</p>
                        <small class="text-muted">
                            Sistemas: ${alert.systems.join(', ')} | 
                            ${new Date(alert.timestamp).toLocaleString()}
                        </small>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            </div>
        `).join('');
    }

    loadInterconnectedData() {
        // Simular carga de datos desde APIs
        fetch('/api/analysis/interconnected')
            .then(response => response.json())
            .then(data => {
                console.log('📊 Datos interconectados cargados:', data);
                this.updateVisualizationsWithData(data);
            })
            .catch(error => {
                console.log('⚠️ Usando datos simulados para demostración');
                this.updateVisualizationsWithData(this.getSimulatedData());
            });
    }

    getSimulatedData() {
        return {
            connections: 42,
            correlations: 7,
            trends: 18,
            sync_status: 97,
            network_health: 'optimal',
            last_update: new Date().toISOString()
        };
    }

    updateVisualizationsWithData(data) {
        if (data.connections) {
            document.getElementById('activeConnections').textContent = data.connections;
        }
        if (data.correlations) {
            document.getElementById('criticalCorrelations').textContent = data.correlations;
        }
        if (data.trends) {
            document.getElementById('trendsDetected').textContent = data.trends;
        }
        if (data.sync_status) {
            document.getElementById('syncStatus').textContent = data.sync_status + '%';
        }
    }

    showNodeDetails(node) {
        alert(`Sistema: ${node.id}\nTipo: ${node.group}\nEstado: Activo`);
    }

    showCorrelationTooltip(event, data) {
        const tooltip = d3.select('body')
            .append('div')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '10px')
            .style('border-radius', '5px')
            .style('pointer-events', 'none')
            .html(`${data.system1} ↔ ${data.system2}<br>Correlación: ${(data.value * 100).toFixed(1)}%`)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');

        setTimeout(() => tooltip.remove(), 3000);
    }

    updateNetworkConnections() {
        // Animar conexiones activas
        d3.selectAll('.connection-line')
            .style('stroke-opacity', () => Math.random() * 0.5 + 0.5);
    }
}

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    new InterconnectedAnalysis();
});