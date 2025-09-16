
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
            