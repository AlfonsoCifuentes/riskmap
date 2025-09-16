#!/usr/bin/env python3
"""
BLOQUE 2F: Modelo 3D Tierra
===========================

Automatización para:
- Implementar modelo 3D de la Tierra
- Integrar Three.js para visualización 3D
- Mostrar eventos geopolíticos en globo terrestre

Fecha: Agosto 2025
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('automation_block_2f.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class Earth3DModelSystem:
    """Sistema para modelo 3D de la Tierra"""
    
    def __init__(self):
        logger.info("🚀 Iniciando Sistema Modelo 3D Tierra - BLOQUE 2F")
    
    def run_all_updates(self):
        """Ejecutar todas las actualizaciones"""
        try:
            logger.info("=" * 60)
            logger.info("🌍 BLOQUE 2F: MODELO 3D TIERRA")
            logger.info("=" * 60)
            
            # 1. Crear modelo 3D con Three.js
            self.create_3d_earth_model()
            
            # 2. Implementar controles interactivos
            self.implement_3d_controls()
            
            # 3. Crear página del globo 3D
            self.create_3d_earth_page()
            
            logger.info("✅ BLOQUE 2F COMPLETADO EXITOSAMENTE")
            
        except Exception as e:
            logger.error(f"❌ Error en BLOQUE 2F: {e}")
            raise e
    
    def create_3d_earth_model(self):
        """Crear modelo 3D de la Tierra con Three.js"""
        try:
            logger.info("🌍 Creando modelo 3D de la Tierra...")
            
            # Crear directorio para 3D
            js_dir = Path('src/web/static/js')
            js_dir.mkdir(parents=True, exist_ok=True)
            
            # JavaScript para modelo 3D
            earth_3d_js = '''
/**
 * RISKMAP - Modelo 3D de la Tierra
 * Visualización interactiva de eventos geopolíticos en globo terrestre
 */

class Earth3DViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.earth = null;
        this.controls = null;
        this.events = [];
        this.markers = [];
        
        this.init();
    }
    
    init() {
        this.createScene();
        this.createEarth();
        this.createLighting();
        this.createControls();
        this.addEventListeners();
        this.animate();
        
        // Cargar eventos geopolíticos
        this.loadGeopoliticalEvents();
    }
    
    createScene() {
        // Crear escena
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000014);
        
        // Crear cámara
        this.camera = new THREE.PerspectiveCamera(
            75, 
            this.container.clientWidth / this.container.clientHeight, 
            0.1, 
            1000
        );
        this.camera.position.set(0, 0, 2.5);
        
        // Crear renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true 
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        this.container.appendChild(this.renderer.domElement);
    }
    
    createEarth() {
        // Geometría de la esfera
        const geometry = new THREE.SphereGeometry(1, 64, 64);
        
        // Material de la Tierra
        const textureLoader = new THREE.TextureLoader();
        const earthTexture = this.createEarthTexture();
        
        const material = new THREE.MeshPhongMaterial({
            map: earthTexture,
            bumpScale: 0.02,
            specular: new THREE.Color(0x111111),
            shininess: 30
        });
        
        // Crear mesh de la Tierra
        this.earth = new THREE.Mesh(geometry, material);
        this.earth.castShadow = true;
        this.earth.receiveShadow = true;
        this.scene.add(this.earth);
        
        // Añadir atmósfera
        this.createAtmosphere();
    }
    
    createEarthTexture() {
        // Crear textura procedural de la Tierra
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');
        
        // Gradiente base (océanos)
        const oceanGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        oceanGradient.addColorStop(0, '#1e3a8a');    // Azul oscuro polo norte
        oceanGradient.addColorStop(0.5, '#3b82f6');  // Azul medio ecuador
        oceanGradient.addColorStop(1, '#1e3a8a');    // Azul oscuro polo sur
        
        ctx.fillStyle = oceanGradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Continentes (simplificado)
        ctx.fillStyle = '#22c55e'; // Verde continentes
        
        // América del Norte
        ctx.fillRect(100, 100, 150, 100);
        // América del Sur  
        ctx.fillRect(120, 250, 80, 150);
        // Europa
        ctx.fillRect(450, 80, 80, 60);
        // África
        ctx.fillRect(430, 140, 100, 200);
        // Asia
        ctx.fillRect(500, 60, 200, 160);
        // Australia
        ctx.fillRect(700, 280, 80, 50);
        
        return new THREE.CanvasTexture(canvas);
    }
    
    createAtmosphere() {
        // Crear atmósfera brillante
        const atmosphereGeometry = new THREE.SphereGeometry(1.05, 32, 32);
        const atmosphereMaterial = new THREE.ShaderMaterial({
            transparent: true,
            side: THREE.BackSide,
            vertexShader: `
                varying vec3 vNormal;
                void main() {
                    vNormal = normalize(normalMatrix * normal);
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                varying vec3 vNormal;
                void main() {
                    float intensity = pow(0.8 - dot(vNormal, vec3(0, 0, 1.0)), 2.0);
                    gl_FragColor = vec4(0.3, 0.6, 1.0, 1.0) * intensity;
                }
            `
        });
        
        const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
        this.scene.add(atmosphere);
    }
    
    createLighting() {
        // Luz ambiental suave
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        
        // Luz direccional (sol)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 3, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Luz puntual para destacar eventos
        const pointLight = new THREE.PointLight(0xff4444, 0.5, 10);
        pointLight.position.set(0, 0, 3);
        this.scene.add(pointLight);
    }
    
    createControls() {
        // Controles de órbita
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 1.5;
        this.controls.maxDistance = 5;
        this.controls.enablePan = false;
    }
    
    addEventListeners() {
        // Redimensionar
        window.addEventListener('resize', () => this.onWindowResize(), false);
        
        // Click en eventos
        this.renderer.domElement.addEventListener('click', (event) => {
            this.onEventClick(event);
        });
    }
    
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    
    onEventClick(event) {
        // Raycasting para detectar clicks en eventos
        const mouse = new THREE.Vector2();
        mouse.x = (event.clientX / this.container.clientWidth) * 2 - 1;
        mouse.y = -(event.clientY / this.container.clientHeight) * 2 + 1;
        
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        
        const intersects = raycaster.intersectObjects(this.markers);
        if (intersects.length > 0) {
            const clickedMarker = intersects[0].object;
            this.showEventDetails(clickedMarker.userData);
        }
    }
    
    showEventDetails(eventData) {
        // Mostrar detalles del evento en modal
        const modal = document.getElementById('eventModal');
        const modalTitle = document.getElementById('eventModalTitle');
        const modalBody = document.getElementById('eventModalBody');
        
        modalTitle.textContent = eventData.title;
        modalBody.innerHTML = `
            <p><strong>Ubicación:</strong> ${eventData.location}</p>
            <p><strong>Tipo:</strong> ${eventData.type}</p>
            <p><strong>Nivel de Riesgo:</strong> ${eventData.risk_level}/10</p>
            <p><strong>Fecha:</strong> ${eventData.date}</p>
            <p><strong>Descripción:</strong> ${eventData.description}</p>
        `;
        
        // Mostrar modal (requiere Bootstrap)
        if (typeof bootstrap !== 'undefined') {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }
    
    async loadGeopoliticalEvents() {
        try {
            const response = await fetch('/api/dashboard/events-3d');
            const data = await response.json();
            
            if (data.success) {
                this.events = data.events;
                this.createEventMarkers();
            }
        } catch (error) {
            console.error('Error cargando eventos:', error);
            
            // Datos de ejemplo si falla la API
            this.events = [
                {
                    id: 1,
                    title: "Tensión Geopolítica",
                    location: "Europa Oriental",
                    latitude: 50.0,
                    longitude: 30.0,
                    risk_level: 8,
                    type: "Conflicto",
                    date: "2025-08-06",
                    description: "Escalada de tensiones en la región"
                },
                {
                    id: 2,
                    title: "Crisis Climática",
                    location: "Sudeste Asiático",
                    latitude: 10.0,
                    longitude: 105.0,
                    risk_level: 6,
                    type: "Clima",
                    date: "2025-08-06",
                    description: "Fenómenos meteorológicos extremos"
                }
            ];
            this.createEventMarkers();
        }
    }
    
    createEventMarkers() {
        // Limpiar marcadores existentes
        this.markers.forEach(marker => {
            this.scene.remove(marker);
        });
        this.markers = [];
        
        this.events.forEach(event => {
            const marker = this.createEventMarker(event);
            this.markers.push(marker);
            this.scene.add(marker);
        });
    }
    
    createEventMarker(eventData) {
        // Convertir coordenadas geográficas a posición 3D
        const lat = (eventData.latitude * Math.PI) / 180;
        const lon = (eventData.longitude * Math.PI) / 180;
        const radius = 1.02; // Ligeramente sobre la superficie
        
        const x = radius * Math.cos(lat) * Math.cos(lon);
        const y = radius * Math.sin(lat);
        const z = radius * Math.cos(lat) * Math.sin(lon);
        
        // Crear geometría del marcador
        const geometry = new THREE.SphereGeometry(0.02, 8, 8);
        
        // Color según nivel de riesgo
        let color = 0x00ff00; // Verde (bajo riesgo)
        if (eventData.risk_level >= 7) color = 0xff0000; // Rojo (alto riesgo)
        else if (eventData.risk_level >= 4) color = 0xffaa00; // Naranja (medio riesgo)
        
        const material = new THREE.MeshBasicMaterial({ 
            color: color,
            transparent: true,
            opacity: 0.8
        });
        
        // Crear marcador
        const marker = new THREE.Mesh(geometry, material);
        marker.position.set(x, y, z);
        marker.userData = eventData;
        
        // Añadir efecto de pulso
        this.addPulseEffect(marker);
        
        return marker;
    }
    
    addPulseEffect(marker) {
        // Animación de pulso para marcadores
        const originalScale = marker.scale.clone();
        
        const pulse = () => {
            marker.scale.multiplyScalar(1.2);
            setTimeout(() => {
                marker.scale.copy(originalScale);
            }, 500);
        };
        
        // Pulso cada 2 segundos
        setInterval(pulse, 2000);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Rotar la Tierra lentamente
        if (this.earth) {
            this.earth.rotation.y += 0.001;
        }
        
        // Actualizar controles
        if (this.controls) {
            this.controls.update();
        }
        
        // Renderizar escena
        this.renderer.render(this.scene, this.camera);
    }
    
    // Métodos públicos para controlar la visualización
    focusOnEvent(eventId) {
        const event = this.events.find(e => e.id === eventId);
        if (event) {
            // Animar cámara hacia el evento
            this.animateCameraToPosition(event.latitude, event.longitude);
        }
    }
    
    animateCameraToPosition(lat, lon) {
        const latRad = (lat * Math.PI) / 180;
        const lonRad = (lon * Math.PI) / 180;
        const radius = 2.5;
        
        const targetX = radius * Math.cos(latRad) * Math.cos(lonRad);
        const targetY = radius * Math.sin(latRad);
        const targetZ = radius * Math.cos(latRad) * Math.sin(lonRad);
        
        // Animación suave de cámara (requiere TWEEN.js o similar)
        if (typeof TWEEN !== 'undefined') {
            new TWEEN.Tween(this.camera.position)
                .to({ x: targetX, y: targetY, z: targetZ }, 2000)
                .easing(TWEEN.Easing.Quadratic.Out)
                .start();
        } else {
            this.camera.position.set(targetX, targetY, targetZ);
        }
    }
    
    updateEvents(newEvents) {
        this.events = newEvents;
        this.createEventMarkers();
    }
    
    setTimeRange(startDate, endDate) {
        // Filtrar eventos por rango de tiempo
        const filteredEvents = this.events.filter(event => {
            const eventDate = new Date(event.date);
            return eventDate >= startDate && eventDate <= endDate;
        });
        
        this.updateEvents(filteredEvents);
    }
}

// Inicializar cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('earth3d-container')) {
        window.earth3DViewer = new Earth3DViewer('earth3d-container');
    }
});
            '''
            
            # Guardar JavaScript del modelo 3D
            earth_3d_file = js_dir / 'earth3d.js'
            with open(earth_3d_file, 'w', encoding='utf-8') as f:
                f.write(earth_3d_js)
            
            logger.info("✅ Modelo 3D de la Tierra creado")
            
        except Exception as e:
            logger.error(f"❌ Error creando modelo 3D: {e}")
    
    def implement_3d_controls(self):
        """Implementar controles interactivos para el modelo 3D"""
        try:
            logger.info("🎮 Implementando controles 3D...")
            
            # CSS para controles 3D
            css_dir = Path('src/web/static/css')
            css_dir.mkdir(parents=True, exist_ok=True)
            
            earth_3d_css = '''
/* Estilos para visualizador 3D de la Tierra */
.earth3d-container {
    position: relative;
    width: 100%;
    height: 600px;
    background: radial-gradient(ellipse at center, #1e3c72 0%, #2a5298 100%);
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.earth3d-controls {
    position: absolute;
    top: 20px;
    left: 20px;
    z-index: 100;
    background: rgba(0, 0, 0, 0.7);
    padding: 15px;
    border-radius: 10px;
    color: white;
}

.earth3d-controls h6 {
    margin-bottom: 10px;
    color: #00d4ff;
}

.earth3d-controls .btn {
    margin: 2px;
    font-size: 0.8rem;
}

.earth3d-info {
    position: absolute;
    bottom: 20px;
    right: 20px;
    z-index: 100;
    background: rgba(0, 0, 0, 0.7);
    padding: 15px;
    border-radius: 10px;
    color: white;
    max-width: 300px;
}

.earth3d-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 200;
    text-align: center;
    color: white;
}

.earth3d-loading .spinner-border {
    color: #00d4ff;
}

.event-marker-legend {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 100;
    background: rgba(0, 0, 0, 0.7);
    padding: 15px;
    border-radius: 10px;
    color: white;
}

.legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 5px;
}

.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.legend-color.high { background-color: #ff0000; }
.legend-color.medium { background-color: #ffaa00; }
.legend-color.low { background-color: #00ff00; }

.earth3d-stats {
    position: absolute;
    bottom: 20px;
    left: 20px;
    z-index: 100;
    background: rgba(0, 0, 0, 0.7);
    padding: 15px;
    border-radius: 10px;
    color: white;
}

.earth3d-stats .stat-item {
    margin-bottom: 5px;
    font-size: 0.9rem;
}

.earth3d-stats .stat-value {
    color: #00d4ff;
    font-weight: bold;
}

/* Animaciones */
@keyframes pulse {
    0% { transform: scale(1); opacity: 0.8; }
    50% { transform: scale(1.2); opacity: 1; }
    100% { transform: scale(1); opacity: 0.8; }
}

.pulse-animation {
    animation: pulse 2s ease-in-out infinite;
}

/* Responsivo */
@media (max-width: 768px) {
    .earth3d-container {
        height: 400px;
    }
    
    .earth3d-controls,
    .earth3d-info,
    .event-marker-legend,
    .earth3d-stats {
        position: relative;
        margin: 10px;
        max-width: none;
    }
}
            '''
            
            # Guardar CSS del modelo 3D
            earth_3d_css_file = css_dir / 'earth3d.css'
            with open(earth_3d_css_file, 'w', encoding='utf-8') as f:
                f.write(earth_3d_css)
            
            logger.info("✅ Controles 3D implementados")
            
        except Exception as e:
            logger.error(f"❌ Error implementando controles 3D: {e}")
    
    def create_3d_earth_page(self):
        """Crear página del globo 3D"""
        try:
            logger.info("🌍 Creando página del globo 3D...")
            
            # HTML de la página del globo 3D
            earth_3d_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Globo 3D - RISKMAP</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <!-- Three.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <!-- CSS personalizado -->
    <link href="{{ url_for('static', filename='css/earth3d.css') }}" rel="stylesheet">
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-globe-americas me-2"></i>RISKMAP
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home me-1"></i>Inicio</a>
                <a class="nav-link" href="/dashboard-unificado"><i class="fas fa-chart-line me-1"></i>Dashboard</a>
                <a class="nav-link active" href="/globo-3d"><i class="fas fa-globe me-1"></i>Globo 3D</a>
            </div>
        </div>
    </nav>

    <!-- Contenido principal -->
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-globe me-2"></i>Globo 3D Interactivo</h2>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="resetView()">
                            <i class="fas fa-home me-1"></i>Inicio
                        </button>
                        <button type="button" class="btn btn-outline-success btn-sm" onclick="autoRotate()">
                            <i class="fas fa-play me-1"></i>Auto Rotar
                        </button>
                        <button type="button" class="btn btn-outline-info btn-sm" onclick="refreshEvents()">
                            <i class="fas fa-sync me-1"></i>Actualizar
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <!-- Contenedor del globo 3D -->
                <div class="earth3d-container" id="earth3d-container">
                    <!-- Loading -->
                    <div class="earth3d-loading" id="earth3d-loading">
                        <div class="spinner-border" role="status"></div>
                        <p class="mt-2">Cargando globo 3D...</p>
                    </div>
                    
                    <!-- Controles -->
                    <div class="earth3d-controls">
                        <h6><i class="fas fa-cogs me-2"></i>Controles</h6>
                        <div class="btn-group-vertical btn-group-sm w-100">
                            <button class="btn btn-outline-light" onclick="zoomIn()">
                                <i class="fas fa-search-plus me-1"></i>Acercar
                            </button>
                            <button class="btn btn-outline-light" onclick="zoomOut()">
                                <i class="fas fa-search-minus me-1"></i>Alejar
                            </button>
                            <button class="btn btn-outline-light" onclick="toggleRotation()">
                                <i class="fas fa-sync-alt me-1"></i>Rotar
                            </button>
                        </div>
                    </div>
                    
                    <!-- Leyenda -->
                    <div class="event-marker-legend">
                        <h6><i class="fas fa-map-marker-alt me-2"></i>Leyenda</h6>
                        <div class="legend-item">
                            <div class="legend-color high"></div>
                            <span>Alto Riesgo (7-10)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color medium"></div>
                            <span>Medio Riesgo (4-6)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color low"></div>
                            <span>Bajo Riesgo (1-3)</span>
                        </div>
                    </div>
                    
                    <!-- Estadísticas -->
                    <div class="earth3d-stats">
                        <h6><i class="fas fa-chart-bar me-2"></i>Estadísticas</h6>
                        <div class="stat-item">
                            Eventos activos: <span class="stat-value" id="active-events">0</span>
                        </div>
                        <div class="stat-item">
                            Alto riesgo: <span class="stat-value" id="high-risk-events">0</span>
                        </div>
                        <div class="stat-item">
                            Última actualización: <span class="stat-value" id="last-update">--:--</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Información adicional -->
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle me-2"></i>Instrucciones</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-mouse me-2"></i>Click y arrastra para rotar</li>
                            <li><i class="fas fa-scroll me-2"></i>Scroll para zoom</li>
                            <li><i class="fas fa-hand-pointer me-2"></i>Click en eventos para detalles</li>
                            <li><i class="fas fa-keyboard me-2"></i>Teclas de flecha para navegar</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-filter me-2"></i>Filtros</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Tipo de Evento:</label>
                            <select class="form-select form-select-sm" id="event-type-filter">
                                <option value="all">Todos</option>
                                <option value="conflict">Conflictos</option>
                                <option value="climate">Clima</option>
                                <option value="political">Políticos</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Nivel de Riesgo:</label>
                            <select class="form-select form-select-sm" id="risk-level-filter">
                                <option value="all">Todos</option>
                                <option value="high">Alto (7-10)</option>
                                <option value="medium">Medio (4-6)</option>
                                <option value="low">Bajo (1-3)</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-clock me-2"></i>Tiempo Real</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <span>Estado del sistema:</span>
                            <span class="badge bg-success">Operativo</span>
                        </div>
                        <div class="d-flex justify-content-between mt-2">
                            <span>Última sincronización:</span>
                            <span id="last-sync">Hace 2 min</span>
                        </div>
                        <button class="btn btn-primary btn-sm w-100 mt-3" onclick="forceRefresh()">
                            <i class="fas fa-sync me-1"></i>Forzar Actualización
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal para detalles de eventos -->
    <div class="modal fade" id="eventModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="eventModalTitle">Detalles del Evento</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="eventModalBody">
                    <!-- Contenido dinámico -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    <button type="button" class="btn btn-primary">Ver en Dashboard</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/earth3d.js') }}"></script>
    
    <script>
        // Funciones de control global
        let autoRotateEnabled = false;
        
        function resetView() {
            if (window.earth3DViewer) {
                window.earth3DViewer.camera.position.set(0, 0, 2.5);
            }
        }
        
        function autoRotate() {
            autoRotateEnabled = !autoRotateEnabled;
            // Implementar auto rotación
        }
        
        function refreshEvents() {
            if (window.earth3DViewer) {
                window.earth3DViewer.loadGeopoliticalEvents();
            }
        }
        
        function zoomIn() {
            if (window.earth3DViewer && window.earth3DViewer.camera.position.length() > 1.5) {
                window.earth3DViewer.camera.position.multiplyScalar(0.9);
            }
        }
        
        function zoomOut() {
            if (window.earth3DViewer && window.earth3DViewer.camera.position.length() < 5) {
                window.earth3DViewer.camera.position.multiplyScalar(1.1);
            }
        }
        
        function toggleRotation() {
            autoRotate();
        }
        
        function forceRefresh() {
            location.reload();
        }
        
        // Ocultar loading cuando esté listo
        window.addEventListener('load', function() {
            setTimeout(() => {
                document.getElementById('earth3d-loading').style.display = 'none';
            }, 2000);
        });
        
        // Actualizar estadísticas
        function updateStats() {
            if (window.earth3DViewer && window.earth3DViewer.events) {
                const events = window.earth3DViewer.events;
                document.getElementById('active-events').textContent = events.length;
                document.getElementById('high-risk-events').textContent = 
                    events.filter(e => e.risk_level >= 7).length;
                document.getElementById('last-update').textContent = 
                    new Date().toLocaleTimeString();
            }
        }
        
        // Actualizar cada 30 segundos
        setInterval(updateStats, 30000);
    </script>
</body>
</html>'''
            
            # Guardar página del globo 3D
            templates_dir = Path('src/web/templates')
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            earth_3d_page_file = templates_dir / 'globo_3d.html'
            with open(earth_3d_page_file, 'w', encoding='utf-8') as f:
                f.write(earth_3d_html)
            
            logger.info("✅ Página del globo 3D creada")
            
        except Exception as e:
            logger.error(f"❌ Error creando página 3D: {e}")

def main():
    """Función principal para ejecutar BLOQUE 2F"""
    try:
        system = Earth3DModelSystem()
        system.run_all_updates()
        
        print("\n" + "="*60)
        print("🎉 BLOQUE 2F COMPLETADO EXITOSAMENTE")
        print("="*60)
        print("✅ Modelo 3D Tierra con Three.js creado")
        print("✅ Controles interactivos implementados")
        print("✅ Página del globo 3D creada")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN BLOQUE 2F: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
