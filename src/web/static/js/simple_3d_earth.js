/**
 * Simple 3D Earth Background - Debug Version
 * Versión simplificada para testing y debugging
 */

console.log('🌍 Loading Simple 3D Earth Script...');

let earthScene, earthCamera, earthRenderer, earthModel;
let animationId = null;

function createSimple3DEarth() {
    console.log('🚀 Creating Simple 3D Earth...');
    
    // Get canvas element
    const canvas = document.getElementById('earth3d-canvas');
    if (!canvas) {
        console.error('❌ Canvas element not found!');
        return false;
    }
    
    try {
        // Scene
        earthScene = new THREE.Scene();
        console.log('✅ Scene created');
        
        // Camera
        earthCamera = new THREE.PerspectiveCamera(
            50, 
            window.innerWidth / window.innerHeight, 
            1, 
            1000
        );
        earthCamera.position.set(0, 0, 10);
        console.log('✅ Camera created and positioned');
        
        // Renderer
        earthRenderer = new THREE.WebGLRenderer({ 
            canvas: canvas,
            alpha: true,
            antialias: true
        });
        earthRenderer.setSize(window.innerWidth * 1.3, window.innerHeight * 1.3);
        earthRenderer.setClearColor(0x000000, 0); // Transparent
        console.log('✅ Renderer created');
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 2);
        earthScene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
        directionalLight.position.set(5, 5, 5);
        earthScene.add(directionalLight);
        console.log('✅ Lighting added');
        
        // Create visible Earth sphere
        const geometry = new THREE.SphereGeometry(4, 32, 32);
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x4488ff,
            transparent: true,
            opacity: 0.9
        });
        
        earthModel = new THREE.Mesh(geometry, material);
        earthScene.add(earthModel);
        console.log('✅ Earth sphere created and added to scene');
        
        // Start animation
        animateEarth();
        console.log('✅ Animation started');
        
        // Try to load texture
        loadEarthTexture();
        
        return true;
        
    } catch (error) {
        console.error('❌ Error creating 3D Earth:', error);
        return false;
    }
}

function loadEarthTexture() {
    const textureLoader = new THREE.TextureLoader();
    const textureUrl = 'https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg';
    
    console.log('🖼️ Loading Earth texture...');
    
    textureLoader.load(
        textureUrl,
        function(texture) {
            console.log('✅ Texture loaded successfully');
            if (earthModel) {
                earthModel.material.map = texture;
                earthModel.material.color.setHex(0xffffff);
                earthModel.material.needsUpdate = true;
            }
        },
        function(progress) {
            const percent = (progress.loaded / progress.total * 100).toFixed(1);
            console.log(`📈 Texture loading: ${percent}%`);
        },
        function(error) {
            console.warn('⚠️ Texture failed to load, using solid color:', error);
        }
    );
}

function animateEarth() {
    animationId = requestAnimationFrame(animateEarth);
    
    if (earthModel) {
        earthModel.rotation.y += 0.01;
    }
    
    if (earthRenderer && earthCamera && earthScene) {
        earthRenderer.render(earthScene, earthCamera);
    }
}

function resizeEarth() {
    if (earthCamera && earthRenderer) {
        earthCamera.aspect = window.innerWidth / window.innerHeight;
        earthCamera.updateProjectionMatrix();
        earthRenderer.setSize(window.innerWidth * 1.3, window.innerHeight * 1.3);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM Ready - Initializing Simple 3D Earth...');
    
    // Wait for Three.js to load
    setTimeout(() => {
        if (typeof THREE === 'undefined') {
            console.error('❌ Three.js not loaded!');
            return;
        }
        
        const success = createSimple3DEarth();
        
        if (success) {
            console.log('🎉 Simple 3D Earth initialized successfully!');
            
            // Add resize listener
            window.addEventListener('resize', resizeEarth);
            
            // Debug info after 2 seconds
            setTimeout(() => {
                console.log('🔍 Debug Info:');
                console.log('- Earth model exists:', !!earthModel);
                console.log('- Scene children:', earthScene ? earthScene.children.length : 0);
                console.log('- Animation running:', !!animationId);
            }, 2000);
        } else {
            console.error('❌ Failed to initialize Simple 3D Earth');
        }
    }, 500);
});

// Cleanup
window.addEventListener('beforeunload', function() {
    if (animationId) {
        cancelAnimationFrame(animationId);
    }
});
