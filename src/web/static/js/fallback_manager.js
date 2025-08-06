/**
 * Global Fallback Data Manager
 * Centralizes the display and management of fallback/simulated data indicators
 */

class FallbackManager {
    constructor() {
        this.indicators = new Map();
        this.init();
    }

    init() {
        // Add CSS if not already present
        if (!document.querySelector('#fallback-indicators-css')) {
            const link = document.createElement('link');
            link.id = 'fallback-indicators-css';
            link.rel = 'stylesheet';
            link.href = '/static/css/fallback_indicators.css';
            document.head.appendChild(link);
        }
    }

    /**
     * Create a fallback indicator element
     * @param {string} type - Type of indicator (warning, error, simulation)
     * @param {string} message - Message to display
     * @param {string} icon - FontAwesome icon class
     * @returns {HTMLElement} The indicator element
     */
    createIndicator(type = 'warning', message = 'Datos simulados', icon = 'fa-exclamation-triangle') {
        const indicator = document.createElement('div');
        indicator.className = `fallback-indicator ${type}`;
        indicator.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        return indicator;
    }

    /**
     * Create a status indicator for data sections
     * @param {string} status - Status type (real-data, fallback-data, simulated-data, error-data)
     * @param {string} message - Status message
     * @returns {HTMLElement} The status element
     */
    createDataStatus(status, message) {
        const statusEl = document.createElement('div');
        statusEl.className = `data-status ${status}`;
        
        let icon = 'fa-check-circle';
        if (status === 'fallback-data') icon = 'fa-exclamation-circle';
        else if (status === 'simulated-data') icon = 'fa-flask';
        else if (status === 'error-data') icon = 'fa-times-circle';
        
        statusEl.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        return statusEl;
    }

    /**
     * Mark a container as using fallback data
     * @param {HTMLElement} container - Container element
     * @param {string} badgeText - Text for the badge
     */
    markContainerAsFallback(container, badgeText = 'DATOS SIMULADOS') {
        if (!container) return;
        
        container.classList.add('fallback-container');
        
        // Remove existing badge if present
        const existingBadge = container.querySelector('.fallback-badge');
        if (existingBadge) existingBadge.remove();
        
        const badge = document.createElement('div');
        badge.className = 'fallback-badge';
        badge.textContent = badgeText;
        container.style.position = 'relative';
        container.appendChild(badge);
    }

    /**
     * Add fallback indicator to a section header
     * @param {HTMLElement} headerElement - Header element
     * @param {string} type - Indicator type
     * @param {string} message - Message
     */
    addToHeader(headerElement, type = 'warning', message = 'Datos no disponibles - Mostrando simulación') {
        if (!headerElement) return;
        
        const indicator = this.createIndicator(type, message, 'fa-database');
        
        // Create or update status container
        let statusContainer = headerElement.querySelector('.section-status');
        if (!statusContainer) {
            headerElement.classList.add('section-header-with-status');
            statusContainer = document.createElement('div');
            statusContainer.className = 'section-status';
            headerElement.appendChild(statusContainer);
        }
        
        statusContainer.appendChild(indicator);
    }

    /**
     * Add overlay indicator to widgets/charts
     * @param {HTMLElement} widget - Widget container
     * @param {string} type - Indicator type
     * @param {string} message - Message
     */
    addWidgetOverlay(widget, type = 'warning', message = 'SIMULADO') {
        if (!widget) return;
        
        widget.style.position = 'relative';
        
        const overlay = document.createElement('div');
        overlay.className = 'widget-fallback-overlay';
        
        const indicator = this.createIndicator(type, message, 'fa-flask');
        overlay.appendChild(indicator);
        
        widget.appendChild(overlay);
    }

    /**
     * Update statistics display with fallback indicators
     * @param {Object} stats - Statistics object
     * @param {HTMLElement} container - Container element
     */
    updateStatsWithIndicators(stats, container) {
        if (!container) return;
        
        // Add general indicator to container
        this.markContainerAsFallback(container, 'ESTADÍSTICAS SIMULADAS');
        
        // Update individual stat elements
        Object.keys(stats).forEach(key => {
            const element = container.querySelector(`#${key}, .${key}`);
            if (element) {
                // Add small indicator next to the value
                const indicator = document.createElement('span');
                indicator.className = 'fallback-indicator simulation';
                indicator.style.marginLeft = '0.5rem';
                indicator.style.fontSize = '0.6rem';
                indicator.innerHTML = '<i class="fas fa-flask"></i>';
                indicator.title = 'Dato simulado - API no disponible';
                
                element.appendChild(indicator);
            }
        });
    }

    /**
     * Show loading state with fallback warning
     * @param {HTMLElement} container - Container element
     * @param {string} message - Loading message
     */
    showLoadingWithFallbackWarning(container, message = 'Cargando datos...') {
        if (!container) return;
        
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="data-status fallback-data mb-3">
                    <i class="fas fa-wifi"></i>
                    <span>Conectando con APIs en tiempo real...</span>
                </div>
                <div class="spinner-border text-warning" role="status">
                    <span class="visually-hidden">${message}</span>
                </div>
                <p class="text-muted mt-2">${message}</p>
                <div class="fallback-indicator warning mt-2">
                    <i class="fas fa-info-circle"></i>
                    <span>Se mostrarán datos simulados si la conexión falla</span>
                </div>
            </div>
        `;
    }

    /**
     * Show error state with fallback explanation
     * @param {HTMLElement} container - Container element
     * @param {string} errorMessage - Error message
     * @param {boolean} hasSimulatedData - Whether simulated data is available
     */
    showErrorWithFallback(container, errorMessage = 'Error al cargar datos', hasSimulatedData = true) {
        if (!container) return;
        
        const simulatedInfo = hasSimulatedData ? `
            <div class="fallback-indicator simulation mt-3">
                <i class="fas fa-flask"></i>
                <span>Mostrando datos simulados como respaldo</span>
            </div>
        ` : '';
        
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="data-status error-data mb-3">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${errorMessage}</span>
                </div>
                <i class="fas fa-database fa-2x text-muted mb-2"></i>
                <p class="text-muted">API temporalmente no disponible</p>
                ${simulatedInfo}
            </div>
        `;
    }

    /**
     * Mark news/articles as using RSS fallback
     * @param {HTMLElement} container - News container
     */
    markNewsAsFallback(container) {
        if (!container) return;
        
        this.markContainerAsFallback(container, 'NOTICIAS REALES - RSS');
        
        // Add status to header if exists
        const header = container.querySelector('h1, h2, h3, h4, .section-title');
        if (header) {
            this.addToHeader(header, 'warning', 'Fuente: RSS feeds en tiempo real');
        }
    }

    /**
     * Mark video feeds as simulated
     * @param {HTMLElement} container - Video container
     */
    markVideoAsSimulated(container) {
        if (!container) return;
        
        this.markContainerAsFallback(container, 'VIDEO SIMULADO');
        
        // Add overlay to video elements
        const videos = container.querySelectorAll('video, img[src*="video"], .camera-feed');
        videos.forEach(video => {
            this.addWidgetOverlay(video, 'simulation', 'SIM');
        });
    }

    /**
     * Mark satellite images as simulated
     * @param {HTMLElement} container - Satellite container
     */
    markSatelliteAsSimulated(container) {
        if (!container) return;
        
        this.markContainerAsFallback(container, 'IMÁGENES SIMULADAS');
        
        // Add overlays to satellite images
        const images = container.querySelectorAll('.satellite-image, .satellite-gallery img');
        images.forEach(img => {
            this.addWidgetOverlay(img.parentElement || img, 'simulation', 'MUESTRA');
        });
    }

    /**
     * Mark financial/economic data as simulated
     * @param {HTMLElement} container - Economic data container
     */
    markEconomicAsSimulated(container) {
        if (!container) return;
        
        this.markContainerAsFallback(container, 'DATOS ECONÓMICOS SIMULADOS');
        
        // Add indicators to charts and metrics
        const charts = container.querySelectorAll('.chart-container, .metric-card, .economic-indicator');
        charts.forEach(chart => {
            this.addWidgetOverlay(chart, 'simulation', 'DEMO');
        });
    }

    /**
     * Initialize fallback indicators for a specific page
     * @param {string} pageType - Type of page (dashboard, video, satellite, etc.)
     */
    initializePageIndicators(pageType) {
        console.log(`🎭 Initializing fallback indicators for ${pageType} page`);
        
        switch (pageType) {
            case 'dashboard':
                this.initializeDashboardIndicators();
                break;
            case 'video':
                this.initializeVideoIndicators();
                break;
            case 'satellite':
                this.initializeSatelliteIndicators();
                break;
            case 'economic':
                this.initializeEconomicIndicators();
                break;
            default:
                this.initializeGenericIndicators();
        }
    }

    initializeDashboardIndicators() {
        // Mark news section
        const newsContainer = document.querySelector('#news-mosaic, .news-container, .news-section');
        if (newsContainer) {
            this.markNewsAsFallback(newsContainer);
        }
        
        // Mark statistics
        const statsContainer = document.querySelector('.stats-container, .statistics-section');
        if (statsContainer) {
            this.markContainerAsFallback(statsContainer, 'ESTADÍSTICAS EN TIEMPO REAL');
        }
        
        // Mark charts
        const chartContainers = document.querySelectorAll('.chart-container, #conflict-heatmap');
        chartContainers.forEach(chart => {
            this.markContainerAsFallback(chart, 'ANÁLISIS EN TIEMPO REAL');
        });
    }

    initializeVideoIndicators() {
        // Mark video feeds
        const videoContainer = document.querySelector('#camera-feeds, .camera-grid');
        if (videoContainer) {
            this.markVideoAsSimulated(videoContainer);
        }
        
        // Mark satellite gallery
        const satelliteGallery = document.querySelector('#satellite-gallery, .satellite-gallery');
        if (satelliteGallery) {
            this.markSatelliteAsSimulated(satelliteGallery);
        }
    }

    initializeSatelliteIndicators() {
        // Mark all satellite content
        const satelliteContainers = document.querySelectorAll('.satellite-container, .satellite-analysis');
        satelliteContainers.forEach(container => {
            this.markSatelliteAsSimulated(container);
        });
    }

    initializeEconomicIndicators() {
        // Mark economic data
        const economicContainers = document.querySelectorAll('.economic-data, .financial-metrics');
        economicContainers.forEach(container => {
            this.markEconomicAsSimulated(container);
        });
    }

    initializeGenericIndicators() {
        // Generic fallback for any page
        const mainContent = document.querySelector('main, .main-content, .dashboard-content');
        if (mainContent) {
            // Add general notice
            const notice = document.createElement('div');
            notice.className = 'data-status fallback-data mb-3';
            notice.innerHTML = `
                <i class="fas fa-info-circle"></i>
                <span>Sistema en modo demostración - Algunos datos pueden ser simulados</span>
            `;
            mainContent.insertBefore(notice, mainContent.firstChild);
        }
    }

    /**
     * Remove all fallback indicators from an element
     * @param {HTMLElement} element - Element to clean
     */
    removeFallbackIndicators(element) {
        if (!element) return;
        
        // Remove classes and badges
        element.classList.remove('fallback-container');
        element.querySelectorAll('.fallback-badge, .fallback-indicator, .widget-fallback-overlay').forEach(el => el.remove());
    }

    /**
     * Update data status when real data is received
     * @param {HTMLElement} container - Container element
     * @param {string} message - Success message
     */
    markAsRealData(container, message = 'Datos en tiempo real conectados') {
        if (!container) return;
        
        this.removeFallbackIndicators(container);
        
        const status = this.createDataStatus('real-data', message);
        container.insertBefore(status, container.firstChild);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (status.parentNode) {
                status.remove();
            }
        }, 3000);
    }
}

// Global instance
window.FallbackManager = new FallbackManager();

// Auto-initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Detect page type from URL or body class
    const path = window.location.pathname;
    let pageType = 'generic';
    
    if (path.includes('dashboard')) pageType = 'dashboard';
    else if (path.includes('video')) pageType = 'video';
    else if (path.includes('satellite')) pageType = 'satellite';
    else if (path.includes('economic') || path.includes('financial')) pageType = 'economic';
    
    window.FallbackManager.initializePageIndicators(pageType);
});

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FallbackManager;
}
