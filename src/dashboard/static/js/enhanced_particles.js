// Enhanced Interconnected Particles Background with Space Dawn/Dusk Gradient
// Colors: Blue, Cyan, Green with mouse interaction (no click)

document.addEventListener('DOMContentLoaded', function() {
    initializeEnhancedParticles();
});

function initializeEnhancedParticles() {
    console.log('🌌 Initializing enhanced interconnected particles...');
    
    // Remove existing particles container if any
    const existingContainer = document.getElementById('particles-js');
    if (existingContainer) {
        existingContainer.innerHTML = '';
    }
    
    // Create canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas properties
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    canvas.style.pointerEvents = 'none';
    
    // Create gradient background
    canvas.style.background = `
        linear-gradient(
            180deg,
            #0a1a2e 0%,
            #16213e 25%,
            #0f3460 50%,
            #16537e 75%,
            #06b6d4 100%
        )
    `;
    
    // Insert canvas into particles container or body
    const particlesContainer = document.getElementById('particles-js');
    if (particlesContainer) {
        particlesContainer.appendChild(canvas);
    } else {
        document.body.appendChild(canvas);
    }
    
    // Resize canvas
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Particle system configuration
    const config = {
        particleCount: 80,
        connectionDistance: 120,
        maxConnections: 3,
        mouseInfluenceRadius: 150,
        mouseInfluenceStrength: 0.3,
        colors: [
            '#06b6d4', // Cyan
            '#3b82f6', // Blue
            '#10b981', // Green
            '#0ea5e9', // Sky blue
            '#14b8a6'  // Teal
        ]
    };
    
    // Mouse tracking
    let mouse = {
        x: 0,
        y: 0,
        isMoving: false
    };
    
    // Track mouse movement
    document.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.isMoving = true;
        
        // Reset moving flag after a delay
        clearTimeout(mouse.timeout);
        mouse.timeout = setTimeout(() => {
            mouse.isMoving = false;
        }, 100);
    });
    
    // Particle class
    class EnhancedParticle {
        constructor() {
            this.reset();
            this.baseSpeed = 0.3 + Math.random() * 0.7;
            this.pulsePhase = Math.random() * Math.PI * 2;
            this.pulseSpeed = 0.02 + Math.random() * 0.03;
        }
        
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * this.baseSpeed;
            this.vy = (Math.random() - 0.5) * this.baseSpeed;
            this.radius = 1.5 + Math.random() * 2;
            this.baseOpacity = 0.4 + Math.random() * 0.4;
            this.color = config.colors[Math.floor(Math.random() * config.colors.length)];
            this.connections = [];
        }
        
        update() {
            // Mouse influence
            if (mouse.isMoving) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < config.mouseInfluenceRadius) {
                    const force = (config.mouseInfluenceRadius - distance) / config.mouseInfluenceRadius;
                    const angle = Math.atan2(dy, dx);
                    
                    this.vx += Math.cos(angle) * force * config.mouseInfluenceStrength * 0.1;
                    this.vy += Math.sin(angle) * force * config.mouseInfluenceStrength * 0.1;
                }
            }
            
            // Apply velocity with damping
            this.x += this.vx;
            this.y += this.vy;
            
            // Velocity damping
            this.vx *= 0.99;
            this.vy *= 0.99;
            
            // Boundary wrapping
            if (this.x < -this.radius) this.x = canvas.width + this.radius;
            if (this.x > canvas.width + this.radius) this.x = -this.radius;
            if (this.y < -this.radius) this.y = canvas.height + this.radius;
            if (this.y > canvas.height + this.radius) this.y = -this.radius;
            
            // Update pulse phase
            this.pulsePhase += this.pulseSpeed;
        }
        
        draw() {
            // Calculate pulsing opacity
            const pulseOpacity = this.baseOpacity + Math.sin(this.pulsePhase) * 0.2;
            
            // Draw particle with glow effect
            ctx.save();
            
            // Outer glow
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius * 3, 0, Math.PI * 2);
            const gradient = ctx.createRadialGradient(
                this.x, this.y, 0,
                this.x, this.y, this.radius * 3
            );
            gradient.addColorStop(0, this.color + '40');
            gradient.addColorStop(1, this.color + '00');
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // Main particle
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color + Math.floor(pulseOpacity * 255).toString(16).padStart(2, '0');
            ctx.fill();
            
            // Inner bright core
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius * 0.5, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff' + Math.floor(pulseOpacity * 128).toString(16).padStart(2, '0');
            ctx.fill();
            
            ctx.restore();
        }
        
        findConnections(particles) {
            this.connections = [];
            let connectionCount = 0;
            
            for (let other of particles) {
                if (other === this || connectionCount >= config.maxConnections) continue;
                
                const dx = this.x - other.x;
                const dy = this.y - other.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < config.connectionDistance) {
                    this.connections.push({
                        particle: other,
                        distance: distance,
                        opacity: (config.connectionDistance - distance) / config.connectionDistance
                    });
                    connectionCount++;
                }
            }
        }
        
        drawConnections() {
            for (let connection of this.connections) {
                const other = connection.particle;
                const opacity = connection.opacity * 0.3;
                
                // Create gradient line
                const gradient = ctx.createLinearGradient(
                    this.x, this.y,
                    other.x, other.y
                );
                gradient.addColorStop(0, this.color + Math.floor(opacity * 255).toString(16).padStart(2, '0'));
                gradient.addColorStop(0.5, '#ffffff' + Math.floor(opacity * 128).toString(16).padStart(2, '0'));
                gradient.addColorStop(1, other.color + Math.floor(opacity * 255).toString(16).padStart(2, '0'));
                
                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                ctx.lineTo(other.x, other.y);
                ctx.strokeStyle = gradient;
                ctx.lineWidth = 1 + opacity;
                ctx.stroke();
                
                // Add subtle glow to connection
                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                ctx.lineTo(other.x, other.y);
                ctx.strokeStyle = '#ffffff' + Math.floor(opacity * 64).toString(16).padStart(2, '0');
                ctx.lineWidth = 3;
                ctx.stroke();
            }
        }
    }
    
    // Initialize particles
    const particles = [];
    for (let i = 0; i < config.particleCount; i++) {
        particles.push(new EnhancedParticle());
    }
    
    // Animation loop
    function animate() {
        // Clear canvas with slight trail effect
        ctx.fillStyle = 'rgba(10, 26, 46, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Update particles and find connections
        particles.forEach(particle => {
            particle.update();
            particle.findConnections(particles);
        });
        
        // Draw connections first (behind particles)
        particles.forEach(particle => {
            particle.drawConnections();
        });
        
        // Draw particles on top
        particles.forEach(particle => {
            particle.draw();
        });
        
        requestAnimationFrame(animate);
    }
    
    // Start animation
    animate();
    
    // Performance monitoring
    let frameCount = 0;
    let lastTime = performance.now();
    
    function monitorPerformance() {
        frameCount++;
        const currentTime = performance.now();
        
        if (currentTime - lastTime >= 1000) {
            const fps = frameCount;
            frameCount = 0;
            lastTime = currentTime;
            
            // Adjust particle count based on performance
            if (fps < 30 && particles.length > 40) {
                particles.splice(0, 10);
                console.log('🔧 Reduced particles for better performance');
            } else if (fps > 50 && particles.length < config.particleCount) {
                for (let i = 0; i < 5; i++) {
                    particles.push(new EnhancedParticle());
                }
            }
        }
        
        requestAnimationFrame(monitorPerformance);
    }
    
    monitorPerformance();
    
    console.log('✨ Enhanced particles initialized successfully');
}

// Cleanup function
window.addEventListener('beforeunload', () => {
    const canvas = document.querySelector('#particles-js canvas');
    if (canvas && canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
    }
});