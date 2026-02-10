
// Configuración de endpoints para Riskmap A.I.
const RISKMAP_CONFIG = {
    API_BASE_URL: window.location.port === '5001' ? window.location.origin : 'http://localhost:5001',
    ENDPOINTS: {
        // Endpoint CORREGIDO - usa este para datos filtrados correctamente
        CONFLICTS: '/api/analytics/conflicts-corrected',
        
        // Endpoint original - puede tener problemas de filtrado
        CONFLICTS_ORIGINAL: '/api/analytics/conflicts',
        
        // Otros endpoints
        NEWS: '/api/news',
        SATELLITE: '/api/analytics/satellite-zones',
        GEOJSON: '/api/analytics/geojson'
    },
    
    // Configuración del mapa
    MAP_CONFIG: {
        DEFAULT_CENTER: [31.0461, 34.8516], // Israel (zona con más conflictos)
        DEFAULT_ZOOM: 6,
        CLUSTER_DISTANCE: 50
    },
    
    // Configuración de filtros
    FILTERS: {
        RISK_LEVELS: ['high', 'medium', 'low'],
        TIMEFRAMES: ['24h', '7d', '30d', '90d']
    }
};

// Función helper para obtener datos de conflictos
async function fetchConflicts(timeframe = '7d') {
    try {
        const response = await fetch(`${RISKMAP_CONFIG.API_BASE_URL}${RISKMAP_CONFIG.ENDPOINTS.CONFLICTS}?timeframe=${timeframe}`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Obtenidos ${data.conflicts.length} conflictos del sistema corregido`);
            return data;
        } else {
            console.error('❌ Error obteniendo conflictos:', data.error);
            return null;
        }
    } catch (error) {
        console.error('❌ Error de red obteniendo conflictos:', error);
        return null;
    }
}

// Función helper para obtener noticias filtradas
async function fetchFilteredNews(limit = 20) {
    try {
        const response = await fetch(`${RISKMAP_CONFIG.API_BASE_URL}${RISKMAP_CONFIG.ENDPOINTS.NEWS}?limit=${limit}&filtered=true`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Obtenidas ${data.articles.length} noticias geopolíticas filtradas`);
            return data;
        } else {
            console.error('❌ Error obteniendo noticias:', data.error);
            return null;
        }
    } catch (error) {
        console.error('❌ Error de red obteniendo noticias:', error);
        return null;
    }
}

console.log('🔧 Riskmap A.I. Config cargado con endpoints corregidos');
