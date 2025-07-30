// Geopolitical Particles Background - City Lights Effect

document.addEventListener('DOMContentLoaded', function() {
    // Initialize particles.js if available
    if (typeof particlesJS !== 'undefined') {
        initializeParticles();
    } else {
        // Fallback to custom particle system
        initializeCustomParticles();
    }
    
    // Initialize additional effects
    initializeFloatingElements();
    initializeDataStream();
    initializeScanLine();
});

function initializeParticles() {
    particlesJS('particles-js', {
        particles: {
            number: {
                value: 120,
                density: {
                    enable: true,
                    value_area: 800
                }
            },
            color: {
                value: ['#00d4ff', '#667eea', '#764ba2', '#4ecdc4']
            },
            shape: {
                type: 'circle',
                stroke: {
                    width: 0,
                    color: '#000000'
                }
            },
            opacity: {
                value: 0.6,
                random: true,
                anim: {
                    enable: true,
                    speed: 1,
                    opacity_min: 0.1,
                    sync: false
                }
            },
            size: {
                value: 3,
                random: true,
                anim: {
                    enable: true,
                    speed: 2,
                    size_min: 0.1,
                    sync: false
                }
            },
            line_linked: {
                enable: true,
                distance: 150,
                color: '#00d4ff',
                opacity: 0.2,
                width: 1
            },
            move: {
                enable: true,
                speed: 1.5,
                direction: 'none',
                random: true,
                straight: false,
                out_mode: 'out',
                bounce: false,
                attract: {
                    enable: true,
                    rotateX: 600,
                    rotateY: 1200
                }
            }
        },
        interactivity: {
            detect_on: 'canvas',
            events: {
                onhover: {
                    enable: true,
                    mode: 'grab'
                },
                onclick: {
                    enable: true,
                    mode: 'push'
                },
                resize: true
            },
            modes: {
                grab: {
                    distance: 200,
                    line_linked: {
                        opacity: 0.5
                    }
                },
                bubble: {
                    distance: 400,
                    size: 40,
                    duration: 2,
                    opacity: 8,
                    speed: 3
                },
                repulse: {
                    distance: 200,
                    duration: 0.4
                },
                push: {
                    particles_nb: 4
                },
                remove: {
                    particles_nb: 2
                }
            }
        },
        retina_detect: true
    });
}

function initializeCustomParticles() {
    console.log('Initializing custom particle system...');
    
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
    
    // Insert canvas into particles container
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
    
    // Particle system
    const particles = [];
    const particleCount = 80;
    const connectionDistance = 150;
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = (Math.random() - 0.5) * 2;
            this.radius = Math.random() * 3 + 1;
            this.opacity = Math.random() * 0.6 + 0.2;
            this.color = this.getRandomColor();
        }
        
        getRandomColor() {
            const colors = ['#00d4ff', '#667eea', '#764ba2', '#4ecdc4'];
            return colors[Math.floor(Math.random() * colors.length)];
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            // Bounce off edges
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
            
            // Keep particles in bounds
            this.x = Math.max(0, Math.min(canvas.width, this.x));
            this.y = Math.max(0, Math.min(canvas.height, this.y));
        }
        
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.globalAlpha = this.opacity;
            ctx.fill();
        }
    }
    
    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    // Draw connections between particles
    function drawConnections() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < connectionDistance) {
                    const opacity = (1 - distance / connectionDistance) * 0.3;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = '#00d4ff';
                    ctx.globalAlpha = opacity;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
    }
    
    // Animation loop
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Update and draw particles
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        // Draw connections
        drawConnections();
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

function initializeFloatingElements() {
    const container = document.createElement('div');
    container.className = 'floating-elements';
    document.body.appendChild(container);
    
    // Create floating elements
    for (let i = 0; i < 15; i++) {
        const element = document.createElement('div');
        element.className = 'floating-element';
        element.style.left = Math.random() * 100 + '%';
        element.style.animationDelay = Math.random() * 20 + 's';
        element.style.animationDuration = (15 + Math.random() * 10) + 's';
        container.appendChild(element);
    }
}

function initializeDataStream() {
    const container = document.createElement('div');
    container.className = 'data-stream';
    document.body.appendChild(container);
    
    // Create data bits
    setInterval(() => {
        if (container.children.length < 50) {
            const bit = document.createElement('div');
            bit.className = 'data-bit';
            bit.style.left = Math.random() * 100 + '%';
            bit.style.animationDelay = '0s';
            bit.style.animationDuration = (6 + Math.random() * 4) + 's';
            container.appendChild(bit);
            
            // Remove bit after animation
            setTimeout(() => {
                if (bit.parentNode) {
                    bit.parentNode.removeChild(bit);
                }
            }, 10000);
        }
    }, 200);
}

function initializeScanLine() {
    const scanLine = document.createElement('div');
    scanLine.className = 'scan-line';
    document.body.appendChild(scanLine);
}

// Matrix rain effect
function initializeMatrixRain() {
    const container = document.createElement('div');
    container.className = 'matrix-rain';
    document.body.appendChild(container);
    
    setInterval(() => {
        if (container.children.length < 30) {
            const column = document.createElement('div');
            column.className = 'matrix-column';
            column.style.left = Math.random() * 100 + '%';
            column.style.animationDelay = '0s';
            column.style.animationDuration = (8 + Math.random() * 4) + 's';
            container.appendChild(column);
            
            // Remove column after animation
            setTimeout(() => {
                if (column.parentNode) {
                    column.parentNode.removeChild(column);
                }
            }, 12000);
        }
    }, 500);
}

// Circuit pattern
function initializeCircuitPattern() {
    const pattern = document.createElement('div');
    pattern.className = 'circuit-pattern';
    document.body.appendChild(pattern);
}

// Mouse interaction effects - DISABLED
function initializeMouseEffects() {
    // Mouse effects completely disabled to eliminate trail effect
    console.log('Mouse effects disabled');
}

// Performance monitoring
function monitorPerformance() {
    let frameCount = 0;
    let lastTime = performance.now();
    
    function checkFPS() {
        frameCount++;
        const currentTime = performance.now();
        
        if (currentTime - lastTime >= 1000) {
            const fps = frameCount;
            frameCount = 0;
            lastTime = currentTime;
            
            // Reduce effects if FPS is too low
            if (fps < 30) {
                console.log('Low FPS detected, reducing particle effects');
                reduceEffects();
            }
        }
        
        requestAnimationFrame(checkFPS);
    }
    
    checkFPS();
}

function reduceEffects() {
    // Reduce number of particles
    const particlesContainer = document.getElementById('particles-js');
    if (particlesContainer && window.pJSDom && window.pJSDom[0]) {
        window.pJSDom[0].pJS.particles.number.value = Math.max(30, window.pJSDom[0].pJS.particles.number.value * 0.7);
    }
    
    // Remove some floating elements
    const floatingElements = document.querySelectorAll('.floating-element');
    for (let i = floatingElements.length - 1; i >= floatingElements.length / 2; i--) {
        if (floatingElements[i].parentNode) {
            floatingElements[i].parentNode.removeChild(floatingElements[i]);
        }
    }
}

// Initialize all effects
function initializeAllEffects() {
    // CSS animations for ripple effect - DISABLED
    // const style = document.createElement('style');
    // style.textContent = `
    //     @keyframes ripple {
    //         0% {
    //             width: 10px;
    //             height: 10px;
    //             opacity: 1;
    //         }
    //         100% {
    //             width: 100px;
    //             height: 100px;
    //             opacity: 0;
    //         }
    //     }
    // `;
    // document.head.appendChild(style);
    
    // Initialize effects with delay to prevent performance issues
    setTimeout(() => initializeMatrixRain(), 1000);
    setTimeout(() => initializeCircuitPattern(), 2000);
    // Mouse effects disabled - setTimeout(() => initializeMouseEffects(), 3000);
    setTimeout(() => monitorPerformance(), 4000);
}

// Start all effects
initializeAllEffects();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    // Clear intervals and remove event listeners
    const containers = [
        '.floating-elements',
        '.data-stream',
        '.matrix-rain',
        '.scan-line',
        '.circuit-pattern'
    ];
    
    containers.forEach(selector => {
        const container = document.querySelector(selector);
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    });
});