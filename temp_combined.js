
// ===== BLOQUE 1 =====

// Cache buster: 2025-08-05-fix-v2
// Global variables
let currentFilter = 'all';
let mosaicData = [];
// Variables globales para el sistema de noticias
let currentNewsSet = 0; // Track which news set we're showing
let totalNewsSets = 4; // Total number of news sets available (4 diseños)
let currentNewsOffset = 0; // Para paginación real
let newsPageSize = 12; // Artículos por página
let allLoadedNews = []; // Almacenar todos los artículos cargados
let hasMoreNews = true; // Si hay más noticias para cargar

// 🖼️ Sistema Anti-Duplicados de Imágenes
let usedImages = new Set(); // Almacena URLs de imágenes ya utilizadas
let heroImageUrl = null;    // Imagen del artículo hero actual

// Function to reset used images (call when switching news sets)
function resetUsedImages() {
    usedImages.clear();
    heroImageUrl = null;
    console.log('🔄 Reset del sistema anti-duplicados');
}

// Function to check if image is already used and add to used list
function isImageUsed(imageUrl) {
    if (!imageUrl) return false;
    
    const normalizedUrl = normalizeImageUrl(imageUrl);
    if (!normalizedUrl) return false;
    
    return usedImages.has(normalizedUrl);
}

// Function to mark image as used
function markImageAsUsed(imageUrl, context = 'mosaic') {
    if (!imageUrl) return false;
    
    const normalizedUrl = normalizeImageUrl(imageUrl);
    if (!normalizedUrl) return false;
    
    usedImages.add(normalizedUrl);
    
    if (context === 'hero') {
        heroImageUrl = normalizedUrl;
    }
    
    console.log(`🏷️ Imagen marcada como usada (${context}):`, normalizedUrl);
    return true;
}

// Function to get alternative image for duplicates
// Sistema avanzado anti-duplicados para imágenes
class ImageDeduplicationSystem {
    constructor() {
        this.usedImageHashes = new Set();
        this.imageHashCache = new Map();
        this.fallbackImageIndex = 0;
        this.fallbackImages = [
            'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=300&fit=crop', // News
            'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400&h=300&fit=crop', // Conference
            'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=300&fit=crop', // World
            'https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9?w=400&h=300&fit=crop', // Security
            'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=400&h=300&fit=crop', // Politics
            'https://images.unsplash.com/photo-1459347268516-3ed71100e718?w=400&h=300&fit=crop', // International
            'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=300&fit=crop', // Global
            'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400&h=300&fit=crop', // Economy
        ];
        this.topicBasedImages = {
            'conflict': [
                'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9?w=400&h=300&fit=crop'
            ],
            'politics': [
                'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1459347268516-3ed71100e718?w=400&h=300&fit=crop'
            ],
            'economy': [
                'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=300&fit=crop'
            ],
            'international': [
                'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=300&fit=crop'
            ]
        };
    }
    
    async getImageHash(imageUrl) {
        if (this.imageHashCache.has(imageUrl)) {
            return this.imageHashCache.get(imageUrl);
        }
        
        try {
            // Crear hash basado en URL y contenido
            const urlHash = await this.createSimpleHash(imageUrl);
            
            // Intentar obtener hash del contenido real (si es accesible)
            try {
                const response = await fetch(imageUrl, { mode: 'cors' });
                if (response.ok) {
                    const arrayBuffer = await response.arrayBuffer();
                    const contentHash = await this.createHashFromBuffer(arrayBuffer);
                    const combinedHash = urlHash + '_' + contentHash;
                    this.imageHashCache.set(imageUrl, combinedHash);
                    return combinedHash;
                }
            } catch (e) {
                // Si no se puede acceder al contenido, usar solo URL hash
            }
            
            this.imageHashCache.set(imageUrl, urlHash);
            return urlHash;
            
        } catch (error) {
            console.warn('Error creando hash para imagen:', imageUrl, error);
            return imageUrl; // Usar URL como fallback
        }
    }
    
    async createSimpleHash(text) {
        const encoder = new TextEncoder();
        const data = encoder.encode(text);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
    }
    
    async createHashFromBuffer(buffer) {
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
    }
    
    async isImageUsed(imageUrl) {
        if (!imageUrl) return true;
        
        const hash = await this.getImageHash(imageUrl);
        return this.usedImageHashes.has(hash);
    }
    
    async markImageAsUsed(imageUrl) {
        if (!imageUrl) return;
        
        const hash = await this.getImageHash(imageUrl);
        this.usedImageHashes.add(hash);
        console.log(`📷 Imagen marcada como usada: ${imageUrl.substring(0, 50)}...`);
    }
    
    detectImageTopic(article) {
        const text = `${article.title || ''} ${article.content || ''} ${article.summary || ''}`.toLowerCase();
        
        const topicKeywords = {
            'conflict': ['conflict', 'war', 'military', 'army', 'battle', 'fight', 'violence', 'soldier'],
            'politics': ['politics', 'government', 'minister', 'president', 'election', 'vote', 'policy'],
            'economy': ['economy', 'economic', 'market', 'business', 'trade', 'finance', 'money', 'bank'],
            'international': ['international', 'global', 'world', 'country', 'nation', 'diplomatic']
        };
        
        let bestTopic = 'international';
        let maxMatches = 0;
        
        for (const [topic, keywords] of Object.entries(topicKeywords)) {
            const matches = keywords.filter(keyword => text.includes(keyword)).length;
            if (matches > maxMatches) {
                maxMatches = matches;
                bestTopic = topic;
            }
        }
        
        return bestTopic;
    }
    
    async getUniqueImageForArticle(article) {
        console.log(`🔍 Buscando imagen única para: ${article.title?.substring(0, 50)}...`);
        
        // 1. Intentar imagen original del artículo
        const originalImages = [
            article.image,
            article.image_url,
            article.featured_image,
            article.hero_image
        ].filter(Boolean);
        
        for (const imgUrl of originalImages) {
            const isUsed = await this.isImageUsed(imgUrl);
            if (!isUsed) {
                await this.markImageAsUsed(imgUrl);
                console.log('✅ Usando imagen original del artículo');
                return imgUrl;
            }
        }
        
        // 2. Buscar imagen por tema específico
        const topic = this.detectImageTopic(article);
        const topicImages = this.topicBasedImages[topic] || [];
        
        for (const imgUrl of topicImages) {
            const isUsed = await this.isImageUsed(imgUrl);
            if (!isUsed) {
                await this.markImageAsUsed(imgUrl);
                console.log(`✅ Usando imagen temática (${topic})`);
                return imgUrl;
            }
        }
        
        // 3. Usar imagen de fallback general (rotar)
        let attempts = 0;
        while (attempts < this.fallbackImages.length) {
            const imgUrl = this.fallbackImages[this.fallbackImageIndex];
            this.fallbackImageIndex = (this.fallbackImageIndex + 1) % this.fallbackImages.length;
            
            const isUsed = await this.isImageUsed(imgUrl);
            if (!isUsed) {
                await this.markImageAsUsed(imgUrl);
                console.log('✅ Usando imagen de fallback');
                return imgUrl;
            }
            
            attempts++;
        }
        
        // 4. Si todas están usadas, generar imagen dinámica única
        const dynamicImage = this.generateDynamicImage(article);
        console.log('✅ Generando imagen dinámica única');
        return dynamicImage;
    }
    
    generateDynamicImage(article) {
        // Crear URL única basada en el artículo
        const seed = this.hashCode(article.title || article.id || Math.random().toString());
        const size = 400 + (seed % 200); // Variar tamaño
        const color = this.getColorFromSeed(seed);
        
        return `https://picsum.photos/${size}/300?random=${Math.abs(seed)}&blur=1`;
    }
    
    hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash;
    }
    
    getColorFromSeed(seed) {
        const colors = ['blue', 'green', 'red', 'orange', 'purple', 'teal', 'brown'];
        return colors[Math.abs(seed) % colors.length];
    }
    
    resetUsedImages() {
        console.log('🔄 Reiniciando cache de imágenes usadas');
        this.usedImageHashes.clear();
        this.fallbackImageIndex = 0;
    }
    
    getUsageStats() {
        return {
            totalUsedImages: this.usedImageHashes.size,
            cacheSize: this.imageHashCache.size,
            fallbackIndex: this.fallbackImageIndex
        };
    }
}

// Instancia global del sistema anti-duplicados
const imageDeduplication = new ImageDeduplicationSystem();

// Función mejorada para obtener imagen alternativa
async function getAlternativeImage(article, excludeUrls = []) {
    console.log(`🔍 Obteniendo imagen alternativa para: ${article.title?.substring(0, 50)}...`);
    
    // Usar el sistema anti-duplicados avanzado
    try {
        const uniqueImage = await imageDeduplication.getUniqueImageForArticle(article);
        console.log('✅ Imagen única obtenida:', uniqueImage);
        return uniqueImage;
    } catch (error) {
        console.error('❌ Error obteniendo imagen única:', error);
        
        // Fallback básico si el sistema avanzado falla
        const basicFallbacks = [
            'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=300&fit=crop',
            'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400&h=300&fit=crop',
            'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=300&fit=crop'
        ];
        
        const randomIndex = Math.floor(Math.random() * basicFallbacks.length);
        return basicFallbacks[randomIndex];
    }
}

// Function to normalize image URLs for local images
function normalizeImageUrl(url) {
    console.log('🔍 normalizeImageUrl llamada con:', url);
    if (!url) {
        console.log('⚠️ URL es null/undefined');
        return null;
    }
    
    // Lista de URLs de imágenes problemáticas que deben evitarse
    const badImagePatterns = [
        'texture', 'black', 'negro', 'fallback', 'placeholder', 
        'default', '1x1', 'pixel', 'transparent', 'blank', 'empty',
        'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP', // 1x1 transparent GIF
        'loading', 'spinner'
    ];
    
    // Verificar si la URL contiene patrones problemáticos
    const urlLower = url.toLowerCase();
    for (const pattern of badImagePatterns) {
        if (urlLower.includes(pattern)) {
            console.log('⚠️ Imagen problemática detectada:', pattern, 'en', url);
            return null;
        }
    }
    
    // Si es una imagen local (comienza con data\images o data/images)
    if (url.startsWith('data\\images\\') || url.startsWith('data/images/')) {
        // Extraer solo el nombre del archivo
        const filename = url.replace(/^data[\\\/]images[\\\/]/, '');
        const normalized = `/data/images/${filename}`;
        console.log('✅ URL normalizada:', url, '→', normalized);
        return normalized;
    }
    
    // Si ya es una URL completa, devolverla tal como está
    console.log('ℹ️ URL no necesita normalización:', url);
    return url;
}

// Function to get smart fallback images based on content
function getSmartFallbackImage(article) {
    const title = (article.title || '').toLowerCase();
    const source = (article.source || '').toLowerCase();
    
    // Fallback específico por fuente
    const sourceFallbacks = {
        'ap news': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop',
        'financial times': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop',
        'axios': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?w=800&h=600&fit=crop',
        'reuters': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800&h=600&fit=crop',
        'cnn': 'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=800&h=600&fit=crop',
        'bbc': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?w=800&h=600&fit=crop'
    };
    
    for (const [sourceKey, fallbackUrl] of Object.entries(sourceFallbacks)) {
        if (source.includes(sourceKey)) {
            return fallbackUrl;
        }
    }
    
    // Fallback basado en contenido del título
    if (title.includes('war') || title.includes('guerra') || title.includes('conflict') || title.includes('fighting')) {
        return 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop';
    } else if (title.includes('economy') || title.includes('economia') || title.includes('market') || title.includes('financial')) {
        return 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop';
    } else if (title.includes('politics') || title.includes('political') || title.includes('gobierno') || title.includes('government')) {
        return 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop';
    } else if (title.includes('tech') || title.includes('technology') || title.includes('digital') || title.includes('cyber')) {
        return 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=600&fit=crop';
    }
    
    // Fallback general
    return 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop';
}

// Function to validate and improve image URLs
function validateAndImproveImage(imageUrl, article) {
    const normalizedUrl = normalizeImageUrl(imageUrl);
    
    if (!normalizedUrl) {
        console.log('🔄 Imagen no válida, usando fallback inteligente para:', article.title);
        return getSmartFallbackImage(article);
    }
    
    return normalizedUrl;
}

// Function to detect if text is in English
function detectEnglish(text) {
    if (!text || text.length < 10) return false;
    
    // English indicators
    const englishWords = [
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'with',
        'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time',
        'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many',
        'over', 'such', 'take', 'than', 'them', 'well', 'were', 'into', 'that',
        'have', 'will', 'would', 'could', 'should', 'about', 'after', 'before'
    ];
    
    const words = text.toLowerCase().split(/\s+/).slice(0, 20); // First 20 words
    const englishMatches = words.filter(word => englishWords.includes(word)).length;
    
    // Also check for common English patterns
    const englishPatterns = [/\b(ing\b|ed\b|tion\b|ly\b)/g, /\bthe\s+\w+/g, /\band\s+/g];
    let patternMatches = 0;
    englishPatterns.forEach(pattern => {
        const matches = (text.match(pattern) || []).length;
        patternMatches += matches;
    });
    
    // Consider it English if we have enough indicators
    return (englishMatches >= 2) || (patternMatches >= 3);
}

// Function to translate text on the fly
async function translateText(text, sourceElement = null) {
    if (!text || text.length < 3) return text;
    
    try {
        // Show loading indicator if element provided
        if (sourceElement) {
            sourceElement.style.opacity = '0.7';
            sourceElement.style.filter = 'blur(1px)';
        }
        
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                source_lang: 'auto',
                target_lang: 'es'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.translated_text) {
            console.log('✅ Traducción exitosa:', text.substring(0, 50) + '... → ' + data.translated_text.substring(0, 50) + '...');
            return data.translated_text;
        } else {
            console.warn('⚠️ Error en traducción:', data.error);
            return text; // Return original if translation fails
        }
        
    } catch (error) {
        console.error('❌ Error al traducir:', error);
        return text; // Return original if translation fails
    } finally {
        // Remove loading indicator
        if (sourceElement) {
            sourceElement.style.opacity = '1';
            sourceElement.style.filter = 'none';
        }
    }
}

// Function to translate and update element content
async function translateAndUpdateElement(element, originalText) {
    if (!element || !originalText) return;
    
    if (detectEnglish(originalText)) {
        console.log('🔄 Detectado inglés, traduciendo:', originalText.substring(0, 50) + '...');
        const translatedText = await translateText(originalText, element);
        if (translatedText && translatedText !== originalText) {
            element.textContent = translatedText;
            element.title = `Original: ${originalText.substring(0, 100)}...`;
        }
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar sistema anti-duplicados
    resetUsedImages();
    
    loadRealNewsData();  // Cargar datos reales primero
    loadHeroArticle();
    loadMosaic('importance', null);  // Pass null for initial load
    loadAiAnalysis();   // Cargar análisis periodístico por IA
    updateStatistics();
    
    // Initialize fallback indicators for dashboard
    if (window.FallbackManager) {
        window.FallbackManager.initializePageIndicators('dashboard');
        
        // Mark analytics section after charts are loaded
        setTimeout(() => {
            const analyticsGrid = document.getElementById('analytics-grid');
            if (analyticsGrid) {
                window.FallbackManager.markContainerAsFallback(analyticsGrid, 'ANÁLISIS EN TIEMPO REAL');
            }
        }, 1000);
    }
    
    // Auto-refresh every 5 minutes
    setInterval(function() {
        loadRealNewsData();  // Recargar datos reales
        updateStatistics();
        loadHeroArticle();
        refreshLatest();
        loadAiAnalysis();  // Recargar análisis de IA
    }, 300000);
    
    // Initialize analytics after a delay to ensure main content loads first
    setTimeout(() => {
        initializeAnalytics();
        loadAnalytics('overview', null);
    }, 2000);
});

// Cargar datos reales de la API
function loadRealNewsData() {
    fetch('/api/articles?limit=40')  // Cargar suficientes artículos para 4+ sets
        .then(response => response.json())
        .then(data => {
            if (data.success && data.articles) {
                window.realNewsData = data.articles;
                console.log(`✅ Cargados ${data.articles.length} artículos reales de la base de datos`);
                
                // Iniciar análisis de computer vision en background para artículos con imágenes
                const articlesWithImages = data.articles.filter(article => article.image_url);
                if (articlesWithImages.length > 0) {
                    console.log(`🔍 Iniciando análisis CV en background para ${articlesWithImages.length} artículos con imágenes`);
                    
                    // Llamar al endpoint de análisis en batch de forma asíncrona
                    fetch('/api/vision/analyze-article-images', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            article_ids: articlesWithImages.map(a => a.id).slice(0, 20) // Limitar a 20 para no sobrecargar
                        })
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            console.log(`🎯 Análisis CV iniciado para ${result.started_count || 0} artículos`);
                            
                            // Mostrar notificación al usuario
                            showCVAnalysisNotification(`Análisis de computer vision iniciado para ${result.started_count || 0} imágenes`);
                        } else {
                            console.warn('No se pudo iniciar análisis CV:', result.error);
                        }
                    })
                    .catch(error => {
                        console.warn('Error iniciando análisis CV:', error);
                    });
                }
            } else {
                console.warn('No se pudieron cargar artículos reales, usando datos mock');
                window.realNewsData = [];
            }
        })
        .catch(error => {
            console.error('Error cargando datos reales:', error);
            window.realNewsData = [];
        });
}

// Mostrar notificación de análisis CV
function showCVAnalysisNotification(message) {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(34, 197, 94, 0.9);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 1000;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    notification.innerHTML = `
        <i class="fas fa-robot" style="margin-right: 8px;"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Load AI analysis content
function loadAiAnalysis() {
    const aiContent = document.getElementById('aiArticleContent');
    
    // Show loading state
    aiContent.innerHTML = `
        <div class="ai-loading">
            <i class="fas fa-brain fa-spin"></i>
            <div>Generando análisis periodístico con IA...</div>
        </div>
    `;
    
    // Fetch AI analysis from backend
    fetch('/api/groq/analysis')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.analysis) {
                // Asegurar que analysis es una string o un objeto con estructura
                let analysisContent = '';
                
                if (typeof data.analysis === 'object' && data.analysis.title) {
                    // Formato estructurado con title, subtitle, content
                    analysisContent = `
                        <div class="ai-analysis-article">
                            <h1>${data.analysis.title || 'Análisis Geopolítico Global'}</h1>
                            ${data.analysis.subtitle ? `<h2 class="analysis-subtitle">${data.analysis.subtitle}</h2>` : ''}
                            <div class="article-content">
                                ${(data.analysis.content || data.analysis.analysis || 'Análisis no disponible').replace(/\n/g, '</div><div class="article-paragraph">')}
                            </div>
                            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                                <i class="fas fa-robot"></i> Análisis generado automáticamente basado en ${data.articles_count || 'múltiples'} artículos
                                <br><i class="fas fa-clock"></i> ${data.timestamp ? new Date(data.timestamp).toLocaleString('es-ES') : 'Ahora'}
                            </div>
                        </div>
                    `;
                } else {
                    // Formato simple de texto
                    const analysisText = typeof data.analysis === 'string' ? data.analysis : 
                                       typeof data.analysis === 'object' ? JSON.stringify(data.analysis, null, 2) :
                                       String(data.analysis);
                    
                    analysisContent = `
                        <div class="ai-analysis-article">
                            <h1>Análisis Geopolítico Global</h1>
                            <div class="article-paragraph">
                                ${analysisText.replace(/\n/g, '</div><div class="article-paragraph">')}
                            </div>
                            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                                <i class="fas fa-robot"></i> Análisis generado automáticamente basado en ${data.articles_count || 'múltiples'} artículos
                                <br><i class="fas fa-clock"></i> ${data.timestamp ? new Date(data.timestamp).toLocaleString('es-ES') : 'Ahora'}
                            </div>
                        </div>
                    `;
                }
                
                aiContent.innerHTML = analysisContent;
            } else {
                // Show fallback content if analysis fails
                aiContent.innerHTML = `
                    <div class="ai-analysis-article">
                        <h1>Análisis Geopolítico Global</h1>
                        <div class="article-paragraph">
                            ${data.fallback_analysis || 'El análisis geopolítico está siendo generado en segundo plano. Recarga la página en unos minutos para ver el contenido actualizado.'}
                        </div>
                        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                            <i class="fas fa-exclamation-triangle"></i> Estado: Generando análisis...
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error cargando análisis AI:', error);
            // Show error state
            aiContent.innerHTML = `
                <div class="ai-analysis-article">
                    <h1>Análisis Geopolítico Global</h1>
                    <div class="article-paragraph">
                        El sistema de análisis por IA está procesando los últimos eventos geopolíticos. 
                        Este proceso puede tardar varios minutos en completarse debido a la complejidad del análisis.
                    </div>
                    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                        <i class="fas fa-sync-alt fa-spin"></i> El análisis se está generando en segundo plano
                        <br><button onclick="loadAiAnalysis()" style="margin-top: 10px; padding: 8px 16px; background: rgba(0,212,255,0.3); border: 1px solid rgba(0,212,255,0.5); color: white; border-radius: 5px; cursor: pointer;">
                            <i class="fas fa-refresh"></i> Intentar recargar
                        </button>
                    </div>
                </div>
            `;
        });
}

// Load hero article (most important news)
function loadHeroArticle() {
    console.log('🏆 Cargando artículo héroe...');
    
    // Fetch real data from our API
    fetch('/api/hero-article')
        .then(response => response.json())
        .then(async data => {
            if (data.success && data.article) {
                const heroArticle = data.article;
                console.log('📰 Artículo héroe obtenido:', heroArticle.title);
                
                // Store hero article data globally for modal
                window.currentHeroArticle = heroArticle;
                
                // Update hero article content
                const titleElement = document.getElementById('hero-title');
                const textElement = document.getElementById('hero-text');
                const locationElement = document.getElementById('hero-location-text');
                
                // ASEGURAR QUE SIEMPRE ESTÉ EN ESPAÑOL
                console.log('🌐 Verificando y traduciendo contenido del héroe...');
                
                // Traducir título si es necesario
                let finalTitle = heroArticle.title;
                if (needsTranslation(heroArticle.title)) {
                    console.log('🔄 Traduciendo título del héroe...');
                    finalTitle = await translateText(heroArticle.title);
                }
                
                // Traducir texto/resumen si es necesario
                let finalText = heroArticle.text || heroArticle.auto_generated_summary || heroArticle.summary;
                if (needsTranslation(finalText)) {
                    console.log('🔄 Traduciendo texto del héroe...');
                    finalText = await translateText(finalText);
                }
                
                // Traducir ubicación si es necesario
                let finalLocation = heroArticle.location;
                if (needsTranslation(finalLocation)) {
                    console.log('🔄 Traduciendo ubicación del héroe...');
                    finalLocation = await translateText(finalLocation);
                }
                
                // Actualizar contenido en DOM
                titleElement.textContent = finalTitle;
                textElement.textContent = finalText;
                locationElement.textContent = finalLocation;
                
                // Update risk badge
                const riskBadge = document.getElementById('hero-risk-badge');
                const risk = heroArticle.risk_level || heroArticle.risk || 'medium';
                riskBadge.className = `hero-risk-badge ${risk}`;
                riskBadge.textContent = risk.toUpperCase().replace('_', ' ') + ' RIESGO';
                
                // ASEGURAR IMAGEN DE ALTA CALIDAD
                console.log('🖼️ Optimizando imagen del héroe...');
                let heroImageUrl = await getOptimizedHeroImage(heroArticle);
                
                // Aplicar la imagen final
                const heroElement = document.getElementById('hero-article');
                heroElement.style.backgroundImage = `url('${heroImageUrl}')`;
                
                console.log('✅ Héroe cargado exitosamente:', finalTitle);
                
            } else {
                console.warn('⚠️ No se pudo cargar el artículo héroe, usando datos de fallback');
                await loadHeroArticleFallback();
            }
        })
        .catch(async error => {
            console.error('❌ Error cargando artículo héroe:', error);
            await loadHeroArticleFallback();
        });
}

// Función para obtener imagen optimizada para el héroe
async function getOptimizedHeroImage(article) {
    console.log('🔍 Optimizando imagen para héroe...');
    
    // 1. Verificar si hay análisis CV disponible
    if (article.id) {
        try {
            const cvAnalysis = await getImageAnalysis(article.id);
            if (cvAnalysis && cvAnalysis.optimized_url && cvAnalysis.quality_score > 0.6) {
                console.log('✨ Usando imagen optimizada por CV:', cvAnalysis.optimized_url);
                return cvAnalysis.optimized_url;
            }
        } catch (cvError) {
            console.warn('⚠️ Error obteniendo análisis CV para héroe:', cvError);
        }
    }
    
    // 2. Usar imagen original si es de buena calidad
    const originalImage = article.image_url || article.image;
    if (originalImage && isHighQualityImage(originalImage)) {
        console.log('📸 Usando imagen original de alta calidad');
        return originalImage;
    }
    
    // 3. Buscar imagen alternativa de alta calidad
    const alternativeImage = getAlternativeImage(article, [], true); // true = solo alta calidad
    if (alternativeImage) {
        console.log('🔄 Usando imagen alternativa de alta calidad');
        return alternativeImage;
    }
    
    // 4. Fallback a imagen de stock de alta calidad
    const stockImage = getHighQualityStockImage(article.location || 'global');
    console.log('🎨 Usando imagen de stock de alta calidad');
    return stockImage;
}

// Función para verificar si una imagen es de alta calidad
function isHighQualityImage(imageUrl) {
    if (!imageUrl) return false;
    
    // Criterios de alta calidad:
    // - No es placeholder (no contiene 'placeholder', 'default', etc.)
    // - Resolución aparentemente alta (basado en URL)
    // - Fuente confiable
    
    const lowQualityIndicators = [
        'placeholder',
        'default',
        'thumbnail',
        'small',
        '150x',
        '200x',
        '300x',
        'picsum.photos/300',
        'picsum.photos/400'
    ];
    
    const urlLower = imageUrl.toLowerCase();
    return !lowQualityIndicators.some(indicator => urlLower.includes(indicator));
}

// Función para obtener imagen de stock de alta calidad
function getHighQualityStockImage(location) {
    const stockImages = {
        'europa': 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1920&h=800&fit=crop',
        'asia': 'https://images.unsplash.com/photo-1536431311719-398b6704d4cc?w=1920&h=800&fit=crop',
        'africa': 'https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?w=1920&h=800&fit=crop',
        'america': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920&h=800&fit=crop',
        'medio oriente': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1920&h=800&fit=crop',
        'global': 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=1920&h=800&fit=crop'
    };
    
    const locationKey = Object.keys(stockImages).find(key => 
        location.toLowerCase().includes(key)
    ) || 'global';
    
    return stockImages[locationKey];
}

async function loadHeroArticleFallback() {
    console.log('🔄 Usando datos de fallback para héroe (ya en español)');
    
    // Fallback data - YA EN ESPAÑOL Y CON IMÁGENES DE ALTA CALIDAD
    const heroArticles = [
        {
            title: "Crisis diplomática se intensifica en Europa Oriental con repercusiones globales",
            text: "Los últimos desarrollos han escalado las tensiones internacionales, con movimientos militares estratégicos que señalan una posible reconfiguración del orden geopolítico en la región.",
            location: "Europa Oriental",
            risk: "high",
            image: "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1920&h=800&fit=crop&q=80"
        },
        {
            title: "Tensiones comerciales amenazan la estabilidad económica mundial",
            text: "Las nuevas restricciones comerciales han generado ondas de choque en los mercados globales, elevando las preocupaciones sobre una posible guerra comercial de consecuencias devastadoras.",
            location: "Global",
            risk: "high", 
            image: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920&h=800&fit=crop&q=80"
        },
        {
            title: "Desarrollos críticos en Medio Oriente alteran el equilibrio regional",
            text: "Los eventos recientes han reconfigurado las alianzas tradicionales en la región, con implicaciones significativas para la seguridad energética global y la estabilidad internacional.",
            location: "Medio Oriente",
            risk: "critical",
            image: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1920&h=800&fit=crop&q=80"
        },
        {
            title: "Escalada de tensiones en el Mar del Sur de China preocupa a la comunidad internacional",
            text: "Las maniobras militares recientes han elevado significativamente el riesgo de conflicto en una de las rutas comerciales más importantes del mundo.",
            location: "Asia-Pacífico",
            risk: "critical",
            image: "https://images.unsplash.com/photo-1536431311719-398b6704d4cc?w=1920&h=800&fit=crop&q=80"
        },
        {
            title: "Crisis humanitaria se agrava en África Subsahariana",
            text: "La situación humanitaria se ha deteriorado dramáticamente, con millones de personas en riesgo debido a la combinación de conflictos armados y crisis climática.",
            location: "África Subsahariana",
            risk: "high",
            image: "https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?w=1920&h=800&fit=crop&q=80"
        }
    ];
    
    // Seleccionar artículo héroe aleatorio
    const heroArticle = heroArticles[Math.floor(Math.random() * heroArticles.length)];
    
    // Actualizar contenido del héroe
    document.getElementById('hero-title').textContent = heroArticle.title;
    document.getElementById('hero-text').textContent = heroArticle.text;
    document.getElementById('hero-location-text').textContent = heroArticle.location;
    
    // Actualizar badge de riesgo
    const riskBadge = document.getElementById('hero-risk-badge');
    riskBadge.className = `hero-risk-badge ${heroArticle.risk}`;
    riskBadge.textContent = heroArticle.risk.toUpperCase().replace('_', ' ') + ' RIESGO';
    
    // Aplicar imagen de alta calidad
    const heroElement = document.getElementById('hero-article');
    heroElement.style.backgroundImage = `url('${heroArticle.image}')`;
    
    // Almacenar datos para modal
    window.currentHeroArticle = heroArticle;
    
    console.log('✅ Héroe fallback cargado:', heroArticle.title);
}

// High risk articles filtering
function filterHighRisk(category, buttonElement) {
    currentFilter = category;
    
    // Update button states
    document.querySelectorAll('.section-controls .btn-control').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
    
    // Filter articles
    const articles = document.querySelectorAll('.high-risk-card');
    articles.forEach(article => {
        const articleCategory = article.dataset.category || 'general';
        if (category === 'all' || articleCategory === category) {
            article.style.display = 'block';
        } else {
            article.style.display = 'none';
        }
    });
}

// Latest articles filtering
function filterLatest(timeframe, buttonElement) {
    const articles = document.querySelectorAll('.latest-article-card');
    const now = new Date();
    
    // Update button states
    if (buttonElement) {
        buttonElement.parentElement.querySelectorAll('.btn-control').forEach(btn => {
            btn.classList.remove('active');
        });
        buttonElement.classList.add('active');
    }
    
    articles.forEach(article => {
        const articleDate = new Date(article.dataset.date);
        let show = true;
        
        if (timeframe === 'today') {
            show = articleDate.toDateString() === now.toDateString();
        } else if (timeframe === 'week') {
            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            show = articleDate >= weekAgo;
        }
        
        article.style.display = show ? 'flex' : 'none';
    });
}

// Refresh latest articles
function refreshLatest() {
    // Show loading state
    const container = document.getElementById('latest-articles');
    container.innerHTML = '<div class="latest-article-card"><div class="latest-article-content"><h3 class="latest-article-title">Actualizando...</h3><p class="latest-article-description">Obteniendo las últimas noticias...</p></div></div>';
    
    // Simulate API call
    setTimeout(() => {
        location.reload();
    }, 1000);
}

// Load news mosaic
function loadMosaic(mode, buttonElement) {
    const container = document.getElementById('news-mosaic');
    
    // Reset news set counter when changing filter
    currentNewsSet = 0;
    
    // Update button states
    document.querySelectorAll('.mosaic-controls .btn-control').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to the clicked button
    if (buttonElement) {
        buttonElement.classList.add('active');
    } else {
        // Fallback: find button by mode
        const activeButton = document.querySelector(`.btn-control[onclick*="${mode}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }
    
    // Show loading
    container.innerHTML = `
        <div class="mosaic-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <div>Cargando mosaico ${mode}...</div>
        </div>
    `;
    
    // Hide load more button during initial load
    const loadMoreContainer = document.getElementById('load-more-container');
    loadMoreContainer.style.display = 'none';
    
    // Simulate loading and populate with sample data
    setTimeout(() => {
        generateMosaicTiles(mode);
    }, 1500);
}

// Computer Vision Integration for Image Optimization
async function getImageAnalysis(articleId) {
    try {
        const response = await fetch(`/api/vision/get-analysis/${articleId}`);
        if (response.ok) {
            const analysis = await response.json();
            console.log(`🔍 Análisis CV obtenido para artículo ${articleId}:`, analysis);
            return analysis;
        }
    } catch (error) {
        console.warn(`No se pudo obtener análisis CV para artículo ${articleId}:`, error);
    }
    return null;
}

function optimizeImagePositioning(imageElement, analysis) {
    if (!analysis || !analysis.positioning_recommendation) {
        console.log('No hay recomendaciones de posicionamiento CV disponibles');
        return;
    }

    const positioning = analysis.positioning_recommendation;
    const container = imageElement.closest('.mosaic-article');
    
    // Aplicar posicionamiento optimizado basado en análisis CV
    if (positioning.position) {
        const positions = {
            'top-left': '0% 0%',
            'top-center': '50% 0%',
            'top-right': '100% 0%',
            'center-left': '0% 50%',
            'center': '50% 50%',
            'center-right': '100% 50%',
            'bottom-left': '0% 100%',
            'bottom-center': '50% 100%',
            'bottom-right': '100% 100%'
        };
        
        const objectPosition = positions[positioning.position] || positions['center'];
        imageElement.style.objectPosition = objectPosition;
        console.log(`📍 Posicionamiento CV aplicado: ${positioning.position} (${objectPosition})`);
    }

    // Agregar indicador de calidad visual
    if (analysis.quality_score && container) {
        const existingIndicator = container.querySelector('.cv-quality-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        const qualityIndicator = document.createElement('div');
        qualityIndicator.className = 'cv-quality-indicator';
        qualityIndicator.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(0, 255, 0, 0.9);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            z-index: 20;
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        `;
        qualityIndicator.textContent = `CV: ${(analysis.quality_score * 100).toFixed(0)}%`;
        
        // Color basado en calidad
        if (analysis.quality_score >= 0.8) {
            qualityIndicator.style.background = 'rgba(34, 197, 94, 0.9)'; // Verde
        } else if (analysis.quality_score >= 0.6) {
            qualityIndicator.style.background = 'rgba(249, 115, 22, 0.9)'; // Naranja
        } else {
            qualityIndicator.style.background = 'rgba(239, 68, 68, 0.9)'; // Rojo
        }
        
        container.appendChild(qualityIndicator);
        console.log(`✨ Indicador de calidad CV añadido: ${(analysis.quality_score * 100).toFixed(0)}%`);
    }
}

async function applyComputerVisionOptimization(articleElement, article) {
    if (!article.id) {
        console.warn('Artículo sin ID, no se puede aplicar análisis CV');
        return;
    }

    try {
        // Obtener análisis CV para este artículo
        const cvAnalysis = await getImageAnalysis(article.id);
        
        if (cvAnalysis && !cvAnalysis.error) {
            // Encontrar la imagen en el elemento del artículo
            const imageDiv = articleElement.querySelector('.mosaic-article');
            
            if (imageDiv && article.image) {
                // Aplicar optimización de posicionamiento a background-image
                if (cvAnalysis.positioning_recommendation) {
                    const position = cvAnalysis.positioning_recommendation.position || 'center';
                    const positions = {
                        'top-left': '0% 0%',
                        'top-center': '50% 0%',
                        'top-right': '100% 0%',
                        'center-left': '0% 50%',
                        'center': '50% 50%',
                        'center-right': '100% 50%',
                        'bottom-left': '0% 100%',
                        'bottom-center': '50% 100%',
                        'bottom-right': '100% 100%'
                    };
                    
                    imageDiv.style.backgroundPosition = positions[position] || positions['center'];
                    console.log(`🎯 CV: Posición optimizada aplicada - ${position}`);
                }
                
                // Añadir indicador de calidad
                if (cvAnalysis.quality_score) {
                    const existingIndicator = imageDiv.querySelector('.cv-quality-indicator');
                    if (existingIndicator) {
                        existingIndicator.remove();
                    }

                    const qualityIndicator = document.createElement('div');
                    qualityIndicator.className = 'cv-quality-indicator';
                    qualityIndicator.style.cssText = `
                        position: absolute;
                        top: 8px;
                        right: 8px;
                        background: rgba(0, 255, 0, 0.9);
                        color: white;
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: bold;
                        z-index: 20;
                        backdrop-filter: blur(4px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                    `;
                    qualityIndicator.textContent = `CV: ${(cvAnalysis.quality_score * 100).toFixed(0)}%`;
                    
                    // Color basado en calidad
                    if (cvAnalysis.quality_score >= 0.8) {
                        qualityIndicator.style.background = 'rgba(34, 197, 94, 0.9)'; // Verde
                    } else if (cvAnalysis.quality_score >= 0.6) {
                        qualityIndicator.style.background = 'rgba(249, 115, 22, 0.9)'; // Naranja
                    } else {
                        qualityIndicator.style.background = 'rgba(239, 68, 68, 0.9)'; // Rojo
                    }
                    
                    imageDiv.appendChild(qualityIndicator);
                    console.log(`✨ Indicador de calidad CV añadido: ${(cvAnalysis.quality_score * 100).toFixed(0)}%`);
                }
            }
        } else {
            console.log(`ℹ️ No hay análisis CV disponible para artículo ${article.id}`);
        }
    } catch (error) {
        console.error(`Error aplicando optimización CV para artículo ${article.id}:`, error);
    }
}

// Generate mosaic tiles
async function generateMosaicTiles(mode) {
    const container = document.getElementById('news-mosaic');
    let tilesHTML = '';
    let sampleArticles = [];
    
    try {
        // Si es modo 'load_more', usar artículos ya cargados
        if (mode === 'load_more' && allLoadedNews.length > 0) {
            console.log(`🔄 Usando artículos cargados para "cargar más" (${allLoadedNews.length} artículos)`);
            sampleArticles = allLoadedNews.slice(); // Copiar array
        } else {
            // Intentar cargar artículos deduplicados primero
            console.log('🔄 Intentando cargar artículos deduplicados...');
            let response = await fetch('/api/articles/deduplicated?hours=24');
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.mosaic && data.mosaic.length > 0) {
                    sampleArticles = data.mosaic;
                    
                    // Inicializar array global con artículos iniciales
                    if (allLoadedNews.length === 0) {
                        allLoadedNews = [...sampleArticles];
                    }
                    
                    console.log(`✅ Cargados ${sampleArticles.length} artículos deduplicados`);
                } else {
                    throw new Error('No hay artículos deduplicados disponibles');
                }
            } else {
                throw new Error('Error en la respuesta del endpoint deduplicado');
            }
        }
    } catch (error) {
        console.warn('⚠️ Error cargando artículos deduplicados, usando endpoint estándar:', error.message);
        
        // Fallback al endpoint estándar solo si no tenemos artículos cargados
        if (allLoadedNews.length === 0) {
            try {
                const response = await fetch('/api/articles?limit=20');
                const data = await response.json();
                if (data.success && data.articles && data.articles.length > 0) {
                    sampleArticles = data.articles;
                    allLoadedNews = [...sampleArticles];
                    console.log(`📰 Fallback: cargados ${sampleArticles.length} artículos estándar`);
                } else {
                    console.error('❌ No se pudieron cargar artículos');
                    container.innerHTML = '<div class="error-message">Error cargando noticias</div>';
                    return;
                }
            } catch (fallbackError) {
                console.error('❌ Error en fallback:', fallbackError);
                container.innerHTML = '<div class="error-message">Error de conexión</div>';
                return;
            }
        } else {
            // Usar artículos ya cargados
            sampleArticles = allLoadedNews.slice();
        }
    }
    
    // Si no hay artículos, mostrar mensaje
    if (!sampleArticles || sampleArticles.length === 0) {
        container.innerHTML = '<div class="no-articles">No hay artículos disponibles</div>';
        return;
    }
    
    console.log(`🎨 Generando mosaico con ${sampleArticles.length} artículos`);
    
    // Resetear sistema anti-duplicados solo para primera carga
    if (mode !== 'load_more') {
        resetUsedImages();
    }
    
    // Generar patrones de layout según el modo o set actual
    if (mode === 'load_more') {
        // Para "cargar más", usar un patrón consistente
        sampleArticles.forEach((article, index) => {
            const patterns = ['normal', 'normal', 'wide', 'normal', 'tall', 'normal'];
            const sizeClass = patterns[index % patterns.length];
            const backgroundPosition = getBackgroundPosition(index);
            
            tilesHTML += generateArticleTile(article, sizeClass, backgroundPosition);
        });
    } else {
        // Lógica original para sets de diseño simplificada
        sampleArticles.forEach((article, index) => {
            let sizeClass = 'normal';
            let backgroundPosition = getBackgroundPosition(index);
            
            // Patrón simple basado en currentNewsSet
            if (currentNewsSet === 0) {
                const patterns = ['normal', 'wide', 'normal', 'tall', 'normal', 'normal'];
                sizeClass = patterns[index % patterns.length];
            } else if (currentNewsSet === 1) {
                const patterns = ['wide', 'normal', 'normal', 'wide', 'normal', 'tall'];
                sizeClass = patterns[index % patterns.length];
            } else {
                const patterns = ['normal', 'normal', 'wide', 'normal', 'tall', 'normal'];
                sizeClass = patterns[index % patterns.length];
            }
            
            tilesHTML += generateArticleTile(article, sizeClass, backgroundPosition);
        });
    }
    
    container.innerHTML = tilesHTML;
    
    // Translate mosaic content if in English
    setTimeout(async () => {
        await translateMosaicContent();
        
        // Apply computer vision optimization after translation
        setTimeout(() => {
            applyComputerVisionToMosaic();
        }, 500);
    }, 200);
}

// Función auxiliar para generar un tile individual
                    'size-puzzle-wide'     // Art 7: 2 cuadrados (abajo)
                ];
                sizeClass = puzzlePattern[index] || 'size-puzzle-single';
            } else if (currentNewsSet === 3) {
                // Set 4: Diseño esquema Paint - Rejilla 3x4 (12 cuadrados) según imagen
                const paintPattern = [
                    'size-puzzle-single',  // Art 1: Verde 1 (1 cuadrado)
                    'size-puzzle-single',  // Art 2: Verde 2 (1 cuadrado)  
                    'size-puzzle-big',     // Art 3: Azul grande (4 cuadrados)
                    'size-puzzle-single',  // Art 4: Amarillo 1 (1 cuadrado)
                    'size-puzzle-single',  // Art 5: Marrón (1 cuadrado)
                    'size-puzzle-wide',    // Art 6: Amarillo ancho (2 cuadrados)
                    'size-puzzle-single'   // Art 7: Rojo (1 cuadrado)
                ];
                sizeClass = paintPattern[index] || 'size-puzzle-single';
            } else {
                // Otros sets: usar sistema original
                sizeClass = `size-${(index % 12) + 1}`;
            }
            
            const riskClass = article.risk_level || article.risk || 'medium';
            const cvAnalysis = cvAnalyses[index];
            
            // Determinar posicionamiento de fondo basado en análisis CV
            let backgroundPosition = 'center center';
            if (cvAnalysis && cvAnalysis.positioning_recommendation) {
                const position = cvAnalysis.positioning_recommendation.position || 'center';
                const positions = {
                    'top-left': '0% 0%',
                    'top-center': '50% 0%',
                    'top-right': '100% 0%',
                    'center-left': '0% 50%',
                    'center': '50% 50%',
                    'center-right': '100% 50%',
                    'bottom-left': '0% 100%',
                    'bottom-center': '50% 100%',
                    'bottom-right': '100% 100%'
                };
                backgroundPosition = positions[position] || positions['center'];
            }
            
            // Generar indicador de calidad CV
            let cvIndicator = '';
            if (cvAnalysis && cvAnalysis.quality_score) {
                const qualityScore = (cvAnalysis.quality_score * 100).toFixed(0);
                let bgColor = 'rgba(34, 197, 94, 0.9)'; // Verde por defecto
                
                if (cvAnalysis.quality_score < 0.4) {
                    bgColor = 'rgba(239, 68, 68, 0.9)'; // Rojo
                } else if (cvAnalysis.quality_score < 0.7) {
                    bgColor = 'rgba(249, 115, 22, 0.9)'; // Naranja
                }
                
                cvIndicator = `
                    <div class="cv-quality-indicator" style="position: absolute; top: 8px; right: 8px; background: ${bgColor}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; z-index: 20;">CV: ${qualityScore}%</div>
                `;
            }
            
            // Obtener la imagen optimizada o usar fallback inteligente con sistema anti-duplicados
            let imageUrl = validateAndImproveImage(article.image_url || article.image, article);
            
            // Verificar si la imagen ya está en uso y buscar alternativa si es necesario
            if (isImageUsed(imageUrl)) {
                console.log(`🔄 Imagen duplicada detectada para artículo "${article.title}", buscando alternativa`);
                imageUrl = getAlternativeImage(article, [heroImageUrl]); // Excluir imagen del hero
            }
            
            // Si hay análisis CV, usar imagen optimizada si está disponible
            if (cvAnalysis && cvAnalysis.optimized_url && cvAnalysis.optimized_url !== article.image_url) {
                const optimizedUrl = validateAndImproveImage(cvAnalysis.optimized_url, article);
                if (optimizedUrl && !isImageUsed(optimizedUrl)) {
                    imageUrl = optimizedUrl;
                    console.log(`🔧 Usando imagen optimizada CV para artículo ${article.id}:`, cvAnalysis.optimized_url);
                }
            }
            
            // Marcar imagen como usada
            markImageAsUsed(imageUrl, 'mosaic');
            
            // Agregar evento click para el modal
            const clickHandler = `onclick="openArticleModal({
                id: ${article.id || 'null'},
                title: '${(article.title || '').replace(/'/g, "\\'")}',
                auto_generated_summary: '${(article.auto_generated_summary || '').replace(/'/g, "\\'")}',
                summary: '${(article.summary || '').replace(/'/g, "\\'")}',
                original_url: '${article.original_url || article.url || ''}',
                risk_level: '${article.risk_level || article.risk || 'medium'}'
            })"`;
            
            tilesHTML += `
                <div class="mosaic-article ${sizeClass}" style="background-image: url('${imageUrl}'); background-position: ${backgroundPosition}; cursor: pointer;" ${clickHandler}>
                    <div class="mosaic-content">
                        <div class="mosaic-meta">
                            <span class="mosaic-location"><i class="fas fa-map-marker-alt"></i> ${article.location || article.country || 'Global'}</span>
                            <span class="mosaic-risk-badge ${riskClass}">${(riskClass || 'medium').toUpperCase()}</span>
                        </div>
                        <h3 class="mosaic-title">${article.title || 'Noticia importante'}</h3>
                    </div>
                    ${cvIndicator}
                </div>
            `;
        });
        
        container.innerHTML = tilesHTML;
        
        // Translate mosaic content if in English
        setTimeout(async () => {
            const mosaicTitles = container.querySelectorAll('.mosaic-title');
            const mosaicLocations = container.querySelectorAll('.mosaic-location');
            
            // Translate titles
            for (let i = 0; i < mosaicTitles.length; i++) {
                const titleElement = mosaicTitles[i];
                const originalTitle = sampleArticles[i % sampleArticles.length]?.title;
                if (originalTitle) {
                    await translateAndUpdateElement(titleElement, originalTitle);
                }
            }
            
            // Translate locations (extract text without icon)
            for (let i = 0; i < mosaicLocations.length; i++) {
                const locationElement = mosaicLocations[i];
                const originalLocation = sampleArticles[i % sampleArticles.length]?.location || sampleArticles[i % sampleArticles.length]?.country;
                if (originalLocation) {
                    const textContent = locationElement.textContent.replace(/📍|🌍/, '').trim();
                    await translateAndUpdateElement(locationElement, textContent);
                }
            }
        }, 200);
        
        // Log de estadísticas CV
        const optimizedCount = cvAnalyses.filter(a => a && !a.error).length;
        console.log(`✅ Mosaico generado con computer vision: ${optimizedCount}/${sampleArticles.length} imágenes optimizadas`);
        
    } catch (cvError) {
        console.error('Error aplicando computer vision al mosaico:', cvError);
        
        // Fallback: generar mosaico sin CV
        sampleArticles.forEach((article, index) => {
            let sizeClass = `size-${(index % 12) + 1}`;
            const riskClass = article.risk_level || article.risk || 'medium';
            const imageUrl = validateAndImproveImage(article.image_url || article.image, article);
            
            const clickHandler = `onclick="openArticleModal({
                id: ${article.id || 'null'},
                title: '${(article.title || '').replace(/'/g, "\\'")}',
                auto_generated_summary: '${(article.auto_generated_summary || '').replace(/'/g, "\\'")}',
                summary: '${(article.summary || '').replace(/'/g, "\\'")}',
                original_url: '${article.original_url || article.url || ''}',
                risk_level: '${article.risk_level || article.risk || 'medium'}'
            })"`;
            
            tilesHTML += `
                <div class="mosaic-article ${sizeClass}" style="background-image: url('${imageUrl}'); cursor: pointer;" ${clickHandler}>
                    <div class="mosaic-content">
                        <div class="mosaic-meta">
                            <span class="mosaic-location"><i class="fas fa-map-marker-alt"></i> ${article.location || article.country || 'Global'}</span>
                            <span class="mosaic-risk-badge ${riskClass}">${(riskClass || 'medium').toUpperCase()}</span>
                        </div>
                        <h3 class="mosaic-title">${article.title || 'Noticia importante'}</h3>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = tilesHTML;
    }
    
// Función auxiliar para generar un tile individual
function generateArticleTile(article, sizeClass, backgroundPosition) {
    // Determinar clase de riesgo
    const riskClass = article.risk_level || article.risk || 'medium';
    
    // Obtener la imagen optimizada o usar fallback inteligente con sistema anti-duplicados
    let imageUrl = validateAndImproveImage(article.image_url || article.image, article);
    
    // Verificar si la imagen ya está en uso y buscar alternativa si es necesario
    if (isImageUsed(imageUrl)) {
        console.log(`🔄 Imagen duplicada detectada para artículo "${article.title}", buscando alternativa`);
        imageUrl = getAlternativeImage(article, []); // Sin excluir hero por ahora
    }
    
    // Marcar imagen como usada
    markImageAsUsed(imageUrl, 'mosaic');
    
    // Agregar evento click para el modal
    const clickHandler = `onclick="openArticleModal({
        id: ${article.id || 'null'},
        title: '${(article.title || '').replace(/'/g, "\\'")}',
        auto_generated_summary: '${(article.auto_generated_summary || '').replace(/'/g, "\\'")}',
        summary: '${(article.summary || '').replace(/'/g, "\\'")}',
        original_url: '${article.original_url || article.url || ''}',
        risk_level: '${riskClass}'
    })"`;
    
    return `
        <div class="mosaic-article ${sizeClass}" style="background-image: url('${imageUrl}'); background-position: ${backgroundPosition}; cursor: pointer;" ${clickHandler}>
            <div class="mosaic-content">
                <div class="mosaic-meta">
                    <span class="mosaic-location"><i class="fas fa-map-marker-alt"></i> ${article.location || article.country || 'Global'}</span>
                    <span class="mosaic-risk-badge ${riskClass}">${riskClass.toUpperCase()}</span>
                </div>
                <h3 class="mosaic-title">${article.title || 'Noticia importante'}</h3>
            </div>
        </div>
    `;
}

// Función auxiliar para obtener posición de fondo
function getBackgroundPosition(index) {
    const positions = ['center', 'top', 'bottom', 'left', 'right'];
    return positions[index % positions.length];
}

    // Show/hide load more button
    const loadMoreContainer = document.getElementById('load-more-container');
    if (loadMoreContainer) {
        loadMoreContainer.style.display = 'flex';
    }
}

// Get different news sets with perfect alignment
function getNewsSet(setIndex) {
    // Verificar si tenemos datos reales cargados
    if (window.realNewsData && window.realNewsData.length > 0) {
        return getRealNewsForSet(setIndex);
    }
    
    // Fallback a datos mock si no hay datos reales
    return getMockNewsSet(setIndex);
}

// Obtener datos reales organizados por sets
function getRealNewsForSet(setIndex) {
    const articlesPerSet = 7; // Cada set tiene 7 artículos
    const startIndex = setIndex * articlesPerSet;
    const endIndex = startIndex + articlesPerSet;
    
    // Obtener slice de artículos reales para este set
    const realArticles = window.realNewsData.slice(startIndex, endIndex);
    
    // Si no hay suficientes artículos reales, completar con mock
    if (realArticles.length < articlesPerSet) {
        const mockArticles = getMockNewsSet(setIndex);
        const needed = articlesPerSet - realArticles.length;
        realArticles.push(...mockArticles.slice(0, needed));
    }
    
    return realArticles;
}

// Función para obtener datos mock (como respaldo)
function getMockNewsSet(setIndex) {
    const newsSets = [
        // Set 1: 7 articles - DISEÑO ORIGINAL QUE FUNCIONABA BIEN
        [
            {
                title: "Tensiones geopolíticas se intensifican en Europa Oriental",
                location: "Europa Oriental",
                risk: "high",
                image: "https://picsum.photos/400/300?random=1"
            },
            {
                title: "Crisis diplomática en Asia-Pacífico",
                location: "Asia-Pacífico",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=2"
            },
            {
                title: "Movimientos económicos estratégicos en Medio Oriente",
                location: "Medio Oriente",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=3"
            },
            {
                title: "Desarrollos significativos en América Latina",
                location: "América Latina",
                risk: "low",
                image: "https://picsum.photos/400/300?random=4"
            },
            {
                title: "Cambios en las alianzas africanas",
                location: "África",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=5"
            },
            {
                title: "Nuevas políticas en América del Norte",
                location: "América del Norte",
                risk: "low",
                image: "https://picsum.photos/400/300?random=6"
            },
            {
                title: "Desarrollos en el Ártico",
                location: "Ártico",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=7"
            }
        ],
        // Set 2: 7 articles - NUEVO DISEÑO DEL USUARIO (3x4 = 12 cuadrados completos)
        [
            {
                title: "Reformas estratégicas en el Sudeste Asiático",
                location: "Sudeste Asiático",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=23"
            },
            {
                title: "Alianzas energéticas en Europa Central",
                location: "Europa Central",
                risk: "high",
                image: "https://picsum.photos/400/300?random=24"
            },
            {
                title: "Desarrollos tecnológicos en Asia Oriental",
                location: "Asia Oriental",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=25"
            },
            {
                title: "Negociaciones comerciales en el Mediterráneo",
                location: "Mediterráneo",
                risk: "low",
                image: "https://picsum.photos/400/300?random=26"
            },
            {
                title: "Crisis migratoria intensifica tensiones regionales",
                location: "Europa del Sur",
                risk: "high",
                image: "https://picsum.photos/400/300?random=27"
            },
            {
                title: "Acuerdos de cooperación en el Atlántico Norte",
                location: "Atlántico Norte",
                risk: "low",
                image: "https://picsum.photos/400/300?random=28"
            },
            {
                title: "Reformas políticas en América Andina",
                location: "América Andina",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=29"
            }
        ],
        // Set 3: 7 articles - DISEÑO PUZZLE ANTERIOR (3x4 = 12 cuadrados completos)
        [
            {
                title: "Escalada de conflictos en el Sudeste Asiático",
                location: "Sudeste Asiático",
                risk: "high",
                image: "https://picsum.photos/400/300?random=8"
            },
            {
                title: "Nuevas sanciones económicas globales",
                location: "Global",
                risk: "high",
                image: "https://picsum.photos/400/300?random=9"
            },
            {
                title: "Cambios en la política energética europea",
                location: "Europa",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=10"
            },
            {
                title: "Desarrollos en el Cáucaso",
                location: "Cáucaso",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=11"
            },
            {
                title: "Situación en el Cuerno de África",
                location: "África Oriental",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=12"
            },
            {
                title: "Acuerdos comerciales en el Pacífico",
                location: "Pacífico",
                risk: "low",
                image: "https://picsum.photos/400/300?random=13"
            },
            {
                title: "Reformas políticas en América Central",
                location: "América Central",
                risk: "low",
                image: "https://picsum.photos/400/300?random=14"
            }
        ],
        // Set 4: 8 articles - DISEÑO ESQUEMA PAINT (3x4 = 12 cuadrados completos)
        [
            {
                title: "Tensiones diplomáticas en Asia Central",
                location: "Asia Central",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=15"
            },
            {
                title: "Crisis energética en Europa del Norte",
                location: "Europa del Norte",
                risk: "high",
                image: "https://picsum.photos/400/300?random=16"
            },
            {
                title: "Desarrollos militares en el Indo-Pacífico",
                location: "Indo-Pacífico",
                risk: "high",
                image: "https://picsum.photos/400/300?random=17"
            },
            {
                title: "Negociaciones comerciales en África Occidental",
                location: "África Occidental",
                risk: "low",
                image: "https://picsum.photos/400/300?random=18"
            },
            {
                title: "Reformas políticas en el Mediterráneo Oriental",
                location: "Mediterráneo Oriental",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=19"
            },
            {
                title: "Cooperación internacional en la Antártida",
                location: "Antártida",
                risk: "low",
                image: "https://picsum.photos/400/300?random=20"
            },
            {
                title: "Disputas territoriales en el Mar del Sur de China",
                location: "Mar del Sur de China",
                risk: "high",
                image: "https://picsum.photos/400/300?random=21"
            },
            {
                title: "Alianzas estratégicas en América del Sur",
                location: "América del Sur",
                risk: "medium",
                image: "https://picsum.photos/400/300?random=22"
            }
        ]
    ];
    
    return newsSets[setIndex] || [];
}

// Load more news function
async function loadMoreNews() {
    if (!hasMoreNews) {
        console.log('📰 No hay más noticias para cargar');
        return;
    }
    
    console.log('📰 Cargando más noticias...');
    
    const loadMoreBtn = document.querySelector('.btn-load-more');
    const originalText = loadMoreBtn.textContent;
    
    // Mostrar estado de carga
    loadMoreBtn.disabled = true;
    loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
    
    try {
        // Calcular el offset basado en artículos ya cargados
        const offset = allLoadedNews.length;
        
        const response = await fetch(`/api/articles?limit=${newsPageSize}&offset=${offset}`);
        const data = await response.json();
        
        if (data.success && data.articles && data.articles.length > 0) {
            // Agregar nuevos artículos al array global
            allLoadedNews = [...allLoadedNews, ...data.articles];
            
            // Verificar si hay más artículos
            hasMoreNews = data.articles.length === newsPageSize;
            
            // Regenerar el mosaico con todos los artículos cargados
            await generateMosaicTiles('load_more');
            
            console.log(`✅ ${data.articles.length} noticias adicionales cargadas. Total: ${allLoadedNews.length}`);
            
            // Si no hay más artículos, ocultar el botón
            if (!hasMoreNews) {
                loadMoreBtn.style.display = 'none';
                
                // Mostrar mensaje opcional
                const container = document.getElementById('news-mosaic');
                const endMessage = document.createElement('div');
                endMessage.className = 'mosaic-end-message';
                endMessage.style.cssText = 'grid-column: 1 / -1; text-align: center; padding: 20px; color: #666; font-style: italic;';
                endMessage.textContent = 'No hay más noticias disponibles';
                container.appendChild(endMessage);
            }
        } else {
            hasMoreNews = false;
            loadMoreBtn.style.display = 'none';
            console.log('📰 No hay más noticias disponibles');
        }
        
    } catch (error) {
        console.error('❌ Error cargando más noticias:', error);
        
        // Mostrar mensaje de error
        const container = document.getElementById('news-mosaic');
        const errorMessage = document.createElement('div');
        errorMessage.className = 'mosaic-error-message';
        errorMessage.style.cssText = 'grid-column: 1 / -1; text-align: center; padding: 20px; color: #ff4444; background: rgba(255,68,68,0.1); border-radius: 8px; margin: 10px 0;';
        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error cargando más noticias. Intenta de nuevo.';
        container.appendChild(errorMessage);
        
        // Remover mensaje de error después de 5 segundos
        setTimeout(() => {
            if (errorMessage.parentNode) {
                errorMessage.remove();
            }
        }, 5000);
    } finally {
        // Restaurar botón
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = originalText;
    }
}

// Update statistics
function updateStatistics() {
    // Fetch real statistics from API
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.statistics;
                document.getElementById('total-articles').textContent = stats.total_articles || 0;
                document.getElementById('high-risk-count').textContent = stats.risk_alerts || 0;
                document.getElementById('countries-monitored').textContent = stats.countries_monitored || 0;
                document.getElementById('sources-count').textContent = stats.data_sources || 0;
                
                console.log('✅ Estadísticas actualizadas desde la base de datos');
            } else {
                console.warn('Error obteniendo estadísticas, usando valores mock');
                updateStatisticsFallback();
            }
        })
        .catch(error => {
            console.error('Error cargando estadísticas:', error);
            updateStatisticsFallback();
        });
}

function updateStatisticsFallback() {
    // Fallback statistics if API fails
    const stats = {
        totalArticles: Math.floor(Math.random() * 1000) + 500,
        highRiskCount: Math.floor(Math.random() * 20) + 5,
        countriesMonitored: Math.floor(Math.random() * 50) + 120,
        sourcesCount: Math.floor(Math.random() * 100) + 50
    };
    
    document.getElementById('total-articles').textContent = stats.totalArticles;
    document.getElementById('high-risk-count').textContent = stats.highRiskCount;
    document.getElementById('countries-monitored').textContent = stats.countriesMonitored;
    document.getElementById('sources-count').textContent = stats.sourcesCount;
}

// ===========================================
// ANALYTICS SECTION FUNCTIONS
// ===========================================

// Global analytics variables
let analyticsCharts = {};
let conflictHeatmapData = [];
let currentAnalyticsMode = 'overview';

// Initialize analytics components
function initializeAnalytics() {
    // Load Chart.js library if not already loaded
    if (typeof Chart === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = () => {
            console.log('✅ Chart.js loaded for analytics');
            createAnalyticsCharts();
        };
        document.head.appendChild(script);
    } else {
        createAnalyticsCharts();
    }
    
    // Initialize conflict heatmap
    initializeConflictHeatmap();
    
    // Update analytics data
    fetchAnalyticsData();
    
    // Set up auto-refresh
    setInterval(fetchAnalyticsData, 300000); // Refresh every 5 minutes
}

// Load analytics based on selected mode
function loadAnalytics(mode, buttonElement) {
    currentAnalyticsMode = mode;
    
    // Update button states
    document.querySelectorAll('.btn-analytics').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
    
    // Show relevant charts based on mode
    showAnalyticsForMode(mode);
    
    console.log(`📊 Loading analytics for mode: ${mode}`);
}

// Show analytics components based on mode
function showAnalyticsForMode(mode) {
    const containers = {
        'risk-distribution-chart': ['overview', 'conflicts'],
        'temporal-trends-chart': ['overview', 'trends'],
        'geographic-analysis': ['overview', 'conflicts'],
        'conflict-categories': ['conflicts', 'trends'],
        'prediction-model': ['predictions', 'overview'],
        'news-analysis': ['overview', 'trends']
    };
    
    Object.keys(containers).forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            if (containers[containerId].includes(mode)) {
                container.style.display = 'block';
            } else {
                container.style.display = 'none';
            }
        }
    });
}

// Create analytics charts
function createAnalyticsCharts() {
    // Risk Distribution Chart (Doughnut)
    const riskCtx = document.getElementById('riskDistributionCanvas');
    if (riskCtx) {
        analyticsCharts.riskDistribution = new Chart(riskCtx, {
            type: 'doughnut',
            data: {
                labels: ['Alto Riesgo', 'Riesgo Medio', 'Bajo Riesgo'],
                datasets: [{
                    data: [25, 45, 30],
                    backgroundColor: ['#f44336', '#ff9800', '#4caf50'],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
    
    // Temporal Trends Chart (Line)
    const temporalCtx = document.getElementById('temporalTrendsCanvas');
    if (temporalCtx) {
        const labels = generateDateLabels(7);
        analyticsCharts.temporalTrends = new Chart(temporalCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Conflictos Activos',
                        data: generateRandomData(7, 10, 50),
                        borderColor: '#ff4757',
                        backgroundColor: 'rgba(255, 71, 87, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Tensiones',
                        data: generateRandomData(7, 20, 80),
                        borderColor: '#ffa726',
                        backgroundColor: 'rgba(255, 167, 38, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Estabilidad',
                        data: generateRandomData(7, 60, 90),
                        borderColor: '#26c6da',
                        backgroundColor: 'rgba(38, 198, 218, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // We use custom legend
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#fff' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    x: {
                        ticks: { color: '#fff' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }
                }
            }
        });
    }
    
    // Conflict Categories Chart (Bar)
    const categoriesCtx = document.getElementById('conflictCategoriesCanvas');
    if (categoriesCtx) {
        analyticsCharts.conflictCategories = new Chart(categoriesCtx, {
            type: 'bar',
            data: {
                labels: ['Territorial', 'Económico', 'Político', 'Religioso', 'Étnico'],
                datasets: [{
                    data: [15, 23, 18, 12, 8],
                    backgroundColor: [
                        '#ff4757',
                        '#ff6b81',
                        '#ffa726',
                        '#ffcc02',
                        '#26c6da'
                    ],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#fff' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    x: {
                        ticks: { color: '#fff' },
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    // Sources Chart (Pie)
    const sourcesCtx = document.getElementById('sourcesCanvas');
    if (sourcesCtx) {
        analyticsCharts.sources = new Chart(sourcesCtx, {
            type: 'pie',
            data: {
                labels: ['Agencias Oficiales', 'Medios Locales', 'Redes Sociales', 'Think Tanks'],
                datasets: [{
                    data: [40, 30, 20, 10],
                    backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#9c27b0'],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            font: { size: 10 }
                        }
                    }
                }
            }
        });
    }
    
    console.log('📊 Analytics charts created successfully');
}

// Initialize conflict heatmap with REAL AI data using Leaflet
function initializeConflictHeatmap() {
    console.log('🗺️ Initializing REAL AI-powered conflict heatmap with Leaflet...');
    
    const heatmapContainer = document.getElementById('conflict-heatmap');
    if (!heatmapContainer) {
        console.error('❌ Heatmap container not found!');
        return;
    }
    
    // Load Leaflet if not already loaded
    if (typeof L === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
        script.crossOrigin = '';
        script.onload = () => {
            console.log('✅ Leaflet loaded, initializing map...');
            initializeLeafletMap();
        };
        document.head.appendChild(script);
    } else {
        initializeLeafletMap();
    }
}

function initializeLeafletMap() {
    // Show loading state
    const heatmapContainer = document.getElementById('conflict-heatmap');
    heatmapContainer.innerHTML = `
        <div id="map-loading" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: white; position: absolute; z-index: 1000; background: rgba(26, 35, 126, 0.9); width: 100%; border-radius: 15px;">
            <i class="fas fa-satellite-dish fa-3x" style="color: #00d4ff; margin-bottom: 20px; animation: spin 2s linear infinite;"></i>
            <h3>🛰️ Generando mapa satelital...</h3>
            <p>Analizando conflictos y preparando zonas para monitoreo satelital</p>
            <div class="loading-spinner" style="margin-top: 20px;"></div>
        </div>
        <div id="leaflet-map" style="width: 100%; height: 100%; border-radius: 15px;"></div>
    `;
    
    // Initialize Leaflet map
    const map = L.map('leaflet-map', {
        center: [20, 0],
        zoom: 2,
        zoomControl: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        keyboard: true
    });
    
    // Add dark tile layer
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y},
            {r}.png', {
        attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
        maxZoom: 20
    }).addTo(map);
    
    // Store map globally for satellite analysis
    window.conflictMap = map;
    window.conflictMarkers = [];
    window.satelliteZones = [];
    
    // Fetch CONFLICTS from NEWS ANALYSIS ONLY (no satellites)
    fetch('/api/news/conflicts')
        .then(response => response.json())
        .then(data => {
            // Hide loading
            const loadingDiv = document.getElementById('map-loading');
            if (loadingDiv) loadingDiv.style.display = 'none';
            
            if (data.success && data.conflicts && data.conflicts.length > 0) {
                console.log(`✅ ${data.conflicts.length} conflictos de noticias detectados (sin satélites)`);
                renderNewsConflictsOnMap(map, data.conflicts, data.statistics);
            } else if (data.success && data.conflicts.length === 0) {
                console.log('📰 No hay conflictos de noticias recientes');
                showMapMessage(map, 'No hay conflictos detectados en las noticias recientes', 'info');
            } else {
                console.error('❌ Error cargando conflictos de noticias:', data.error);
                showMapMessage(map, 'Error cargando datos de conflictos', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Error conectando con API de noticias:', error);
            const loadingDiv = document.getElementById('map-loading');
            if (loadingDiv) loadingDiv.style.display = 'none';
            showMapMessage(map, 'Error de conexión con el servidor', 'error');
        });
}

function renderNewsConflictsOnMap(map, conflicts, statistics) {
    console.log('📰 Renderizando conflictos de NOTICIAS en el mapa (sin satélites)');
    console.log(`📊 Procesando ${conflicts.length} conflictos de noticias`);
    
    // Clear existing markers
    window.conflictMarkers.forEach(marker => map.removeLayer(marker));
    window.conflictMarkers = [];
    
    // Add news conflict markers
    conflicts.forEach(conflict => {
        try {
            // Color by risk level
            const markerColor = getRiskColor(conflict.risk_level);
            
            // Create marker
            const marker = L.circleMarker([conflict.latitude, conflict.longitude], {
                radius: 8,
                fillColor: markerColor,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            });
            
            // Popup content for news conflict
            const popupContent = `
                <div class="conflict-popup news-conflict">
                    <div class="popup-header">
                        <h4>${conflict.title}</h4>
                        <span class="risk-badge ${conflict.risk_level}">${conflict.risk_level?.toUpperCase()}</span>
                    </div>
                    <div class="popup-content">
                        <p><strong>📍 Ubicación:</strong> ${conflict.location}</p>
                        <p><strong>🎯 Riesgo:</strong> ${(conflict.risk_score * 100).toFixed(1)}%</p>
                        <p><strong>📰 Fuente:</strong> ${conflict.source}</p>
                        ${conflict.summary ? `<p><strong>📝 Resumen:</strong> ${conflict.summary.substring(0, 200)}...</p>` : ''}
                        <div class="popup-actions">
                            <a href="${conflict.url}" target="_blank" class="btn-popup">Ver Artículo</a>
                        </div>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent);
            marker.addTo(map);
            window.conflictMarkers.push(marker);
            
        } catch (error) {
            console.error('Error adding news conflict marker:', error);
        }
    });
    
    // Update map statistics display
    updateMapStatistics(statistics);
    
    console.log(`✅ ${conflicts.length} marcadores de noticias agregados al mapa`);
}

function showMapMessage(map, message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `map-message ${type}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to map overlay
    messageDiv.style.position = 'absolute';
    messageDiv.style.top = '50%';
    messageDiv.style.left = '50%';
    messageDiv.style.transform = 'translate(-50%, -50%)';
    messageDiv.style.zIndex = '1000';
    messageDiv.style.background = type === 'error' ? '#ff4444' : '#4488ff';
    messageDiv.style.color = 'white';
    messageDiv.style.padding = '15px';
    messageDiv.style.borderRadius = '8px';
    messageDiv.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
    
    map.getContainer().appendChild(messageDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

function renderConflictsOnMap(map, conflicts, statistics, satelliteZones = []) {
    console.log('🎯 Rendering conflicts on Leaflet map');
    console.log(`📊 Processing ${conflicts.length} conflicts and ${satelliteZones.length} satellite zones`);
    
    // Clear existing markers
    window.conflictMarkers.forEach(marker => map.removeLayer(marker));
    window.satelliteZones.forEach(zone => map.removeLayer(zone));
    window.conflictMarkers = [];
    window.satelliteZones = [];
    
    // Add conflict markers
    conflicts.forEach((conflict, index) => {
        if (conflict.latitude && conflict.longitude) {
            const riskColor = getRiskColor(conflict.risk_level);
            const markerSize = getRiskSize(conflict.risk_level);
            
            // Create custom marker
            const marker = L.circleMarker([conflict.latitude, conflict.longitude], {
                radius: markerSize,
                fillColor: riskColor,
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8,
                className: `conflict-marker ${conflict.risk_level}`
            });
            
            // Create popup content
            const popupContent = `
                <div style="color: #333; min-width: 250px;">
                    <h4 style="margin: 0 0 10px 0; color: ${riskColor}; font-size: 1.1rem;">
                        🚨 ${conflict.title || 'Zona de Conflicto'}
                    </h4>
                    <p style="margin: 5px 0;"><strong>Ubicación:</strong> ${conflict.location || 'No especificada'}</p>
                    <p style="margin: 5px 0;"><strong>Nivel de Riesgo:</strong> 
                        <span style="background: ${riskColor}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8rem;">
                            ${conflict.risk_level.toUpperCase()}
                        </span>
                    </p>
                    <p style="margin: 5px 0;"><strong>Confianza IA:</strong> ${(conflict.confidence * 100).toFixed(1)}%</p>
                    <p style="margin: 5px 0;"><strong>Artículos:</strong> ${conflict.articles_count || 1}</p>
                    ${conflict.description ? `<p style="margin: 5px 0;"><strong>Descripción:</strong> ${conflict.description}</p>` : ''}
                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                        <button onclick="requestSatelliteImage(${conflict.latitude}, ${conflict.longitude}, '${conflict.location}')" 
                                style="background: #00d4ff; color: white; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">
                            🛰️ Analizar con Satélite
                        </button>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent);
            marker.addTo(map);
            window.conflictMarkers.push(marker);
        }
    });
    
    // Add satellite zones if available
    if (satelliteZones && satelliteZones.length > 0) {
        satelliteZones.forEach(zone => {
            if (zone.coordinates && zone.coordinates.length >= 4) {
                // Create polygon for satellite zone
                const polygon = L.polygon(zone.coordinates, {
                    color: '#00d4ff',
                    weight: 2,
                    opacity: 0.8,
                    fillColor: '#00d4ff',
                    fillOpacity: 0.1,
                    dashArray: '5, 5',
                    className: 'satellite-zone'
                });
                
                polygon.bindPopup(`
                    <div style="color: #333;">
                        <h4 style="margin: 0 0 10px 0; color: #00d4ff;">🛰️ Zona Satelital</h4>
                        <p><strong>Área:</strong> ${zone.area_km2 ? zone.area_km2.toFixed(2) + ' km²' : 'Calculando...'}</p>
                        <p><strong>Precisión:</strong> ${zone.precision || 'Alta'}</p>
                        <p><strong>Estado:</strong> ${zone.status || 'Listo para análisis'}</p>
                    </div>
                `);
                
                polygon.addTo(map);
                window.satelliteZones.push(polygon);
            }
        });
    }
    
    // Fit map to show all conflicts
    if (window.conflictMarkers.length > 0) {
        const group = new L.featureGroup(window.conflictMarkers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
    
    // Update legend
    updateMapLegend(statistics);
    
    // Add event listeners to conflict zones
    const conflictZones = document.querySelectorAll('.real-conflict-zone');
    conflictZones.forEach(zone => {
        zone.addEventListener('mouseenter', function() {
            this.style.opacity = '1';
            this.style.transform = 'scale(1.2)';
            this.style.filter = 'drop-shadow(0 0 15px rgba(255,255,255,0.8))';
            
            showRealConflictTooltip(this);
        });
        
        zone.addEventListener('mouseleave', function() {
            this.style.opacity = '0.8';
            this.style.transform = 'scale(1)';
            this.style.filter = 'none';
            hideTooltip();
        });
        
        zone.addEventListener('click', function() {
            const title = this.getAttribute('data-title');
            console.log(`🎯 Opening article: ${title}`);
            // Aquí podrías abrir el artículo específico
        });
    });
    
    console.log('✅ Real AI conflict map rendered successfully!');
}

function getRiskColor(riskLevel) {
    switch(riskLevel) {
        case 'high': return '#ef4444';
        case 'medium': return '#f59e0b';
        case 'low': return '#22c55e';
        default: return '#6b7280';
    }
}

function getRiskSize(riskLevel) {
    switch(riskLevel) {
        case 'high': return 15;
        case 'medium': return 12;
        case 'low': return 9;
        default: return 8;
    }
}

function updateMapLegend(statistics) {
    const legendContainer = document.querySelector('.heatmap-legend');
    if (legendContainer && statistics) {
        legendContainer.innerHTML = `
            <div class="legend-title">Distribución de Conflictos (IA)</div>
            <div class="legend-items" style="display: flex; gap: 20px; align-items: center;">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 12px; height: 12px; background: #ef4444; border-radius: 50%;"></div>
                    <span style="font-size: 0.9rem;">Alto Riesgo (${statistics.high_risk || 0})</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 12px; height: 12px; background: #f59e0b; border-radius: 50%;"></div>
                    <span style="font-size: 0.9rem;">Medio Riesgo (${statistics.medium_risk || 0})</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 12px; height: 12px; background: #22c55e; border-radius: 50%;"></div>
                    <span style="font-size: 0.9rem;">Bajo Riesgo (${statistics.low_risk || 0})</span>
                </div>
                <div style="margin-left: auto;">
                    <span style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">
                        Confianza IA: ${statistics.average_confidence ? (statistics.average_confidence * 100).toFixed(1) + '%' : 'N/A'}
                    </span>
                </div>
            </div>
        `;
    }
}
function showNoConflictsOnMap(map, suggestion) {
    console.log('ℹ️ No conflicts detected by AI');
    L.popup()
        .setLatLng([20, 0])
        .setContent(`
            <div style="text-align: center; color: #333; padding: 10px;">
                <h4 style="color: #22c55e; margin: 0 0 10px 0;">✅ No hay conflictos detectados</h4>
                <p style="margin: 5px 0;">La IA no encontró zonas de conflicto activo.</p>
                ${suggestion ? `<p style="font-style: italic; color: #666;">${suggestion}</p>` : ''}
            </div>
        `)
        .openOn(map);
}

function showAIErrorOnMap(map, error, suggestion) {
    console.log('❌ AI analysis error');
    L.popup()
        .setLatLng([20, 0])
        .setContent(`
            <div style="text-align: center; color: #333; padding: 10px;">
                <h4 style="color: #ef4444; margin: 0 0 10px 0;">⚠️ Error en análisis IA</h4>
                <p style="margin: 5px 0;">${error || 'Error desconocido'}</p>
                ${suggestion ? `<p style="font-style: italic; color: #666;">${suggestion}</p>` : ''}
            </div>
        `)
        .openOn(map);
}

function showConnectionErrorOnMap(map) {
    console.log('❌ Connection error');
    L.popup()
        .setLatLng([20, 0])
        .setContent(`
            <div style="text-align: center; color: #333; padding: 10px;">
                <h4 style="color: #ef4444; margin: 0 0 10px 0;">📡 Error de conexión</h4>
                <p style="margin: 5px 0;">No se pudo conectar con el sistema de análisis IA.</p>
                <button onclick="location.reload()" style="margin-top: 10px; padding: 5px 10px; background: #00d4ff; color: white; border: none; border-radius: 3px; cursor: pointer;">
                    🔄 Reintentar
                </button>
            </div>
        `)
        .openOn(map);
}


function showRealConflictTooltip(element) {
    const location = element.getAttribute('data-location');
    const intensity = element.getAttribute('data-intensity');
    const confidence = element.getAttribute('data-confidence');
    const type = element.getAttribute('data-type');
    const title = element.getAttribute('data-title');
    const reasoning = element.getAttribute('data-reasoning');
    
    let tooltip = document.getElementById('real-conflict-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'real-conflict-tooltip';
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0,0,0,0.95);
            color: white;
            padding: 15px;
            border-radius: 10px;
            font-size: 13px;
            z-index: 1000;
            pointer-events: none;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 212, 255, 0.5);
            box-shadow: 0 8px 25px rgba(0,0,0,0.8);
            max-width: 300px;
        `;
        document.body.appendChild(tooltip);
    }
    
    // Determine intensity color
    let intensityColor;
    if (intensity === 'high') {
        intensityColor = '#ff4757';
    } else if (intensity === 'medium') {
        intensityColor = '#ffa726';
    } else {
        intensityColor = '#26c6da';
    }
    
    tooltip.innerHTML = `
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <i class="fas fa-robot" style="color: #00d4ff; margin-right: 8px;"></i>
            <strong style="color: #00d4ff;">Análisis IA</strong>
        </div>
        <div style="margin-bottom: 10px;">
            <strong>${location}</strong>
        </div>
        <div style="margin-bottom: 5px;">
            <span style="color: ${intensityColor};">●</span> ${intensity.toUpperCase()} 
            (${(confidence * 100).toFixed(1)}% confianza)
        </div>
        <div style="margin-bottom: 5px;">Tipo: ${type}</div>
        <div style="margin-bottom: 8px; font-size: 11px; opacity: 0.8;">
            "${title.length > 60 ? title.substring(0, 60) + '...' : title}"
        </div>
        <div style="font-size: 11px; opacity: 0.7; font-style: italic;">
            ${reasoning.length > 100 ? reasoning.substring(0, 100) + '...' : reasoning}
        </div>
    `;
    tooltip.style.display = 'block';
}

function hideTooltip() {
    const tooltip = document.getElementById('real-conflict-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

function showNoConflictsMessage(suggestion) {
    const heatmapContainer = document.getElementById('conflict-heatmap');
    heatmapContainer.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: white; text-align: center; padding: 20px;">
            <i class="fas fa-peace" style="color: #4caf50; font-size: 4rem; margin-bottom: 20px;"></i>
            <h3 style="color: #4caf50; margin-bottom: 15px;">✅ No se detectaron conflictos activos</h3>
            <p style="opacity: 0.8; margin-bottom: 10px;">La IA analizó los artículos recientes y no encontró zonas de conflicto significativas.</p>
            <p style="opacity: 0.6; font-size: 14px;">${suggestion}</p>
        </div>
    `;
}

function showAIError(error, suggestion) {
    const heatmapContainer = document.getElementById('conflict-heatmap');
    heatmapContainer.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: white; text-align: center; padding: 20px;">
            <i class="fas fa-exclamation-triangle" style="color: #ff6b6b; font-size: 4rem; margin-bottom: 20px;"></i>
            <h3 style="color: #ff6b6b; margin-bottom: 15px;">❌ Error en Análisis de IA</h3>
            <p style="opacity: 0.8; margin-bottom: 15px; background: rgba(255,107,107,0.1); padding: 10px; border-radius: 8px;">
                ${error}
            </p>
            <p style="opacity: 0.7; font-size: 14px; color: #00d4ff;">${suggestion}</p>
            <button onclick="initializeConflictHeatmap()" 
                    style="margin-top: 15px; padding: 10px 20px; background: #00d4ff; border: none; border-radius: 8px; color: white; cursor: pointer;">
                🔄 Reintentar Análisis
            </button>
        </div>
    `;
}

function showConnectionError() {
    const heatmapContainer = document.getElementById('conflict-heatmap');
    heatmapContainer.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: white; text-align: center; padding: 20px;">
            <i class="fas fa-wifi" style="color: #ff6b6b; font-size: 4rem; margin-bottom: 20px;"></i>
            <h3 style="color: #ff6b6b; margin-bottom: 15px;">❌ Error de Conexión</h3>
            <p style="opacity: 0.8; margin-bottom: 15px;">No se pudo conectar al servidor de análisis de conflictos.</p>
            <button onclick="initializeConflictHeatmap()" 
                    style="margin-top: 15px; padding: 10px 20px; background: #00d4ff; border: none; border-radius: 8px; color: white; cursor: pointer;">
                🔄 Reintentar Conexión
            </button>
        </div>
    `;
}

// Fetch analytics data from API
function fetchAnalyticsData() {
    // Fetch conflict zones data
    fetch('/api/analytics/conflicts')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateConflictAnalytics(data.conflicts);
                updateAnalyticsStats(data.statistics);
                console.log('✅ Analytics data updated from API');
                
                // Auto-trigger satellite analysis for high-priority zones
                if (data.conflicts && data.conflicts.length > 0) {
                    const satelliteZones = data.conflicts
                        .filter(c => c.risk_level === 'high' || c.criticality >= 7)
                        .map(c => ({
                            center_latitude: c.latitude,
                            center_longitude: c.longitude,
                            location: c.location,
                            radius_km: c.radius_km || 5,
                            risk_level: c.risk_level,
                            criticality: c.criticality
                        }));
                    
                    if (satelliteZones.length > 0) {
                        console.log(`🛰️ Auto-triggering satellite analysis for ${satelliteZones.length} high-priority zones`);
                        setTimeout(() => {
                            triggerSatelliteAnalysis(satelliteZones);
                        }, 3000); // Give time for UI updates
                    }
                }
            } else {
                console.warn('Analytics API failed, using mock data');
                updateAnalyticsWithMockData();
            }
        })
        .catch(error => {
            console.error('Error fetching analytics data:', error);
            updateAnalyticsWithMockData();
        });
    
    // Update last update timestamp
    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
}

// Update analytics with conflict data
function updateConflictAnalytics(conflicts) {
    // Update stats
    const highRisk = conflicts.filter(c => c.risk_level === 'high').length;
    const mediumRisk = conflicts.filter(c => c.risk_level === 'medium').length;
    
    document.getElementById('high-risk-regions').textContent = highRisk;
    document.getElementById('medium-risk-regions').textContent = mediumRisk;
    
    // Update categories
    updateConflictCategories(conflicts);
    
    // Update prediction model
    updatePredictionModel(conflicts);
}

// Update analytics stats
function updateAnalyticsStats(stats) {
    if (stats) {
        document.getElementById('total-sources').textContent = stats.total_sources || 0;
        document.getElementById('active-sources').textContent = stats.active_sources || 0;
        document.getElementById('reliability-score').textContent = (stats.reliability_score || 0) + '%';
    }
}

// Update analytics with mock data (fallback)
function updateAnalyticsWithMockData() {
    // Mock statistics
    document.getElementById('high-risk-regions').textContent = Math.floor(Math.random() * 10) + 5;
    document.getElementById('medium-risk-regions').textContent = Math.floor(Math.random() * 15) + 10;
    document.getElementById('total-sources').textContent = Math.floor(Math.random() * 50) + 100;
    document.getElementById('active-sources').textContent = Math.floor(Math.random() * 30) + 50;
    document.getElementById('reliability-score').textContent = Math.floor(Math.random() * 20) + 75 + '%';
    
    // Mock categories
    const mockCategories = [
        { name: 'Territorial', count: Math.floor(Math.random() * 20) + 10 },
        { name: 'Económico', count: Math.floor(Math.random() * 15) + 15 },
        { name: 'Político', count: Math.floor(Math.random() * 10) + 8 },
        { name: 'Religioso', count: Math.floor(Math.random() * 8) + 5 },
        { name: 'Étnico', count: Math.floor(Math.random() * 6) + 3 }
    ];
    
    updateConflictCategoriesDisplay(mockCategories);
    
    // Mock prediction
    const accuracy = Math.floor(Math.random() * 20) + 75;
    updatePredictionDisplay(accuracy);
}

// Update conflict categories display
function updateConflictCategories(conflicts) {
    const categories = {};
    conflicts.forEach(conflict => {
        const category = conflict.category || 'Otros';
        categories[category] = (categories[category] || 0) + 1;
    });
    
    const categoriesArray = Object.entries(categories).map(([name, count]) => ({ name, count }));
    updateConflictCategoriesDisplay(categoriesArray);
}

// Update conflict categories display
function updateConflictCategoriesDisplay(categories) {
    const container = document.getElementById('categories-list');
    if (container) {
        container.innerHTML = categories.map(cat => `
            <div class="category-item">
                <span class="category-name">${cat.name}</span>
                <span class="category-count">${cat.count}</span>
            </div>
        `).join('');
    }
}

// Update prediction model
function updatePredictionModel(conflicts) {
    const accuracy = Math.floor((conflicts.length / (conflicts.length + 5)) * 100);
    updatePredictionDisplay(accuracy);
}

// Update prediction display
function updatePredictionDisplay(accuracy) {
    const scoreElement = document.querySelector('.score-value');
    const circleElement = document.querySelector('.score-circle');
    
    if (scoreElement) {
        scoreElement.textContent = accuracy + '%';
    }
    
    if (circleElement) {
        circleElement.style.setProperty('--score-percentage', accuracy + '%');
    }
    
    // Update factors
    const factors = [
        { name: 'Análisis de Sentimientos', impact: 'Alto', color: '#f44336' },
        { name: 'Geolocalización', impact: 'Medio', color: '#ff9800' },
        { name: 'Tendencias Históricas', impact: 'Alto', color: '#4caf50' },
        { name: 'Redes Sociales', impact: 'Medio', color: '#2196f3' }
    ];
    
    const factorsContainer = document.getElementById('factors-list');
    if (factorsContainer) {
        factorsContainer.innerHTML = factors.map(factor => `
            <div class="factor-item" style="--factor-color: ${factor.color};">
                <span class="factor-name">${factor.name}</span>
                <span class="factor-impact">${factor.impact}</span>
            </div>
        `).join('');
    }
}

// Update analytics based on timeframe
function updateAnalytics() {
    const timeframe = document.getElementById('timeframe-select').value;
    console.log(`📊 Updating analytics for timeframe: ${timeframe}`);
    
    // Re-fetch data with new timeframe
    fetchAnalyticsData();
}

// Toggle map layers
function toggleMapLayer(layer, buttonElement) {
    // Update button states
    document.querySelectorAll('.map-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
    
    // Update map display based on layer
    const conflictZones = document.querySelectorAll('.conflict-zone');
    conflictZones.forEach(zone => {
        const intensity = zone.getAttribute('data-intensity');
        if (layer === 'all' || layer === 'conflicts' || intensity === layer) {
            zone.style.display = 'block';
        } else {
            zone.style.display = 'none';
        }
    });
    
    console.log(`🗺️ Map layer changed to: ${layer}`);
}

// Export GeoJSON data
function exportGeoJSON() {
    console.log('📥 Exporting GeoJSON data...');
    
    // Fetch GeoJSON data from API
    fetch('/api/analytics/geojson')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.geojson) {
                downloadGeoJSON(data.geojson, true); // true = user download
            } else {
                // Generate mock GeoJSON if API fails
                const mockGeoJSON = generateMockGeoJSON();
                downloadGeoJSON(mockGeoJSON, true);
            }
        })
        .catch(error => {
            console.error('Error exporting GeoJSON:', error);
            const mockGeoJSON = generateMockGeoJSON();
            downloadGeoJSON(mockGeoJSON, true);
        });
}

// Save GeoJSON internally for system use
function saveGeoJSONInternally() {
    console.log('💾 Saving GeoJSON data internally...');
    
    fetch('/api/analytics/geojson')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.geojson) {
                // Store in localStorage for internal use
                localStorage.setItem('conflictZonesGeoJSON', JSON.stringify(data.geojson));
                localStorage.setItem('conflictZonesTimestamp', new Date().toISOString());
                
                // Also save to internal storage via API
                fetch('/api/analytics/save-geojson', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        geojson: data.geojson,
                        timestamp: new Date().toISOString()
                    })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        document.getElementById('geojson-auto-status').textContent = 
                            `GeoJSON guardado automáticamente (${new Date().toLocaleTimeString()})`;
                        console.log('✅ GeoJSON saved internally successfully');
                    }
                })
                .catch(error => {
                    console.warn('Warning saving GeoJSON internally:', error);
                    document.getElementById('geojson-auto-status').textContent = 
                        'GeoJSON guardado localmente';
                });
            } else {
                // Save mock data internally
                const mockGeoJSON = generateMockGeoJSON();
                localStorage.setItem('conflictZonesGeoJSON', JSON.stringify(mockGeoJSON));
                localStorage.setItem('conflictZonesTimestamp', new Date().toISOString());
                document.getElementById('geojson-auto-status').textContent = 
                    'GeoJSON mock guardado localmente';
            }
        })
        .catch(error => {
            console.error('Error saving GeoJSON internally:', error);
            const mockGeoJSON = generateMockGeoJSON();
            localStorage.setItem('conflictZonesGeoJSON', JSON.stringify(mockGeoJSON));
            localStorage.setItem('conflictZonesTimestamp', new Date().toISOString());
            document.getElementById('geojson-auto-status').textContent = 
                'GeoJSON de respaldo guardado';
        });
}

// Generate mock GeoJSON for conflict zones
function generateMockGeoJSON() {
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Europa Oriental",
                    "risk_level": "high",
                    "conflict_type": "territorial",
                    "intensity": 0.8,
                    "articles_count": 25
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [30.0, 50.0]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "name": "Medio Oriente",
                    "risk_level": "medium",
                    "conflict_type": "political",
                    "intensity": 0.6,
                    "articles_count": 18
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [45.0, 30.0]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "name": "Mar del Sur de China",
                    "risk_level": "high",
                    "conflict_type": "territorial",
                    "intensity": 0.9,
                    "articles_count": 32
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [115.0, 15.0]
                }
            }
        ]
    };
}

// Download GeoJSON file
function downloadGeoJSON(geoJsonData, isUserDownload = false) {
    const blob = new Blob([JSON.stringify(geoJsonData, null, 2)], {
        type: 'application/json'
    });
    
    if (isUserDownload) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `conflict_zones_${new Date().toISOString().split('T')[0]}.geojson`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log('✅ GeoJSON file downloaded successfully for user');
    } else {
        console.log('✅ GeoJSON prepared for internal use');
    }
}

// Helper functions for chart data generation
function generateDateLabels(days) {
    const labels = [];
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' }));
    }
    return labels;
}

function generateRandomData(length, min, max) {
    return Array.from({ length }, () => Math.floor(Math.random() * (max - min + 1)) + min);
}

// Article Modal Functions
let currentArticleUrl = '';

// Sistema de traducción automática para artículos
class ArticleTranslator {
    constructor() {
        this.translationCache = new Map();
        this.isTranslating = false;
        this.translatedArticles = new Set();
    }
    
    async translateArticleBeforeDisplay(articleData) {
        if (!articleData || this.isTranslating) return articleData;
        
        const articleId = articleData.id || articleData.title;
        if (this.translatedArticles.has(articleId)) {
            return articleData; // Ya está traducido
        }
        
        // Detectar si necesita traducción
        if (this.needsTranslation(articleData)) {
            console.log('📝 Traduciendo artículo:', articleData.title?.substring(0, 50));
            
            try {
                this.isTranslating = true;
                const translatedData = await this.translateArticleContent(articleData);
                this.translatedArticles.add(articleId);
                this.isTranslating = false;
                
                return translatedData;
            } catch (error) {
                console.error('❌ Error traduciendo artículo:', error);
                this.isTranslating = false;
                return articleData;
            }
        }
        
        return articleData;
    }
    
    needsTranslation(articleData) {
        const textToCheck = `${articleData.title || ''} ${articleData.content || ''} ${articleData.summary || ''}`;
        
        // Palabras indicadoras de español
        const spanishIndicators = [
            'el', 'la', 'los', 'las', 'de', 'en', 'un', 'una', 'que', 'con',
            'por', 'para', 'del', 'al', 'se', 'no', 'es', 'son', 'fue', 'han',
            'pero', 'como', 'más', 'todo', 'ser', 'año', 'día', 'tras', 'país'
        ];
        
        const words = textToCheck.toLowerCase().split(/\s+/).slice(0, 50);
        const spanishCount = words.filter(word => spanishIndicators.includes(word)).length;
        
        // Si menos del 30% son palabras en español, necesita traducción
        const spanishRatio = spanishCount / Math.max(words.length, 1);
        return spanishRatio < 0.3 && words.length > 5;
    }
    
    async translateArticleContent(articleData) {
        try {
            const fieldsToTranslate = ['title', 'content', 'summary', 'description'];
            const translatedData = { ...articleData };
            
            for (const field of fieldsToTranslate) {
                if (articleData[field] && typeof articleData[field] === 'string') {
                    const original = articleData[field];
                    const translated = await this.translateText(original);
                    
                    if (translated && translated !== original) {
                        translatedData[field] = translated;
                        translatedData[`original_${field}`] = original;
                        translatedData.is_translated = true;
                    }
                }
            }
            
            // Marcar como traducido
            if (translatedData.is_translated) {
                translatedData.translation_timestamp = new Date().toISOString();
                console.log('✅ Artículo traducido exitosamente');
            }
            
            return translatedData;
            
        } catch (error) {
            console.error('Error en translateArticleContent:', error);
            return articleData;
        }
    }
    
    async translateText(text) {
        if (!text || typeof text !== 'string' || text.length < 3) {
            return text;
        }
        
        // Verificar cache
        const cacheKey = this.getTextHash(text);
        if (this.translationCache.has(cacheKey)) {
            return this.translationCache.get(cacheKey);
        }
        
        try {
            // Llamar al backend para traducir
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    target_language: 'es'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.translated_text) {
                    // Guardar en cache
                    this.translationCache.set(cacheKey, result.translated_text);
                    return result.translated_text;
                }
            }
            
            console.warn('No se pudo traducir texto, usando original');
            return text;
            
        } catch (error) {
            console.error('Error en translateText:', error);
            return text;
        }
    }
    
    getTextHash(text) {
        // Simple hash para cache
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash.toString();
    }
}

// Instancia global del traductor
const articleTranslator = new ArticleTranslator();

// Función mejorada para abrir modal con traducción automática
async function openArticleModal(articleData) {
    console.log('🔍 Abriendo modal para artículo:', articleData);
    
    // Traducir artículo antes de mostrar si es necesario
    const translatedArticle = await articleTranslator.translateArticleBeforeDisplay(articleData);
    
    // Set modal content with safe defaults
    document.getElementById('modal-title').textContent = translatedArticle.title || 'Artículo sin título';
    document.getElementById('modal-location').textContent = translatedArticle.location || 
                                                          translatedArticle.country || 
                                                          translatedArticle.region || 
                                                          'Ubicación no especificada';
    
    // Mostrar indicador de traducción si aplica
    const titleElement = document.getElementById('modal-title');
    if (translatedArticle.is_translated) {
        titleElement.innerHTML = `
            <span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-right: 8px;">
                🌐 TRADUCIDO
            </span>
            ${translatedArticle.title || 'Artículo sin título'}
        `;
    }
    
    // Set risk badge with safe handling
    const riskBadge = document.getElementById('modal-risk');
    const riskLevel = translatedArticle.risk_level || translatedArticle.risk || 'medium';
    riskBadge.className = `modal-risk-badge ${riskLevel}`;
    riskBadge.textContent = `${riskLevel.toUpperCase()} RIESGO`;
    
    // Store original URL for later use
    currentArticleUrl = translatedArticle.original_url || translatedArticle.url || '#';
    
    // Load summary with priority: auto_generated_summary > summary > default
    const summaryToLoad = translatedArticle.auto_generated_summary || 
                         translatedArticle.summary || 
                         null;
    
    loadArticleSummary(translatedArticle.id, summaryToLoad);
    
    // Show modal with animation
    const modal = document.getElementById('article-modal');
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function openArticleModal(articleData) {
    console.log('🔍 Abriendo modal para artículo:', articleData);
    
    // Set modal content with safe defaults
    document.getElementById('modal-title').textContent = articleData.title || 'Artículo sin título';
    document.getElementById('modal-location').textContent = articleData.location || 
                                                          articleData.country || 
                                                          articleData.region || 
                                                          'Ubicación no especificada';
    
    // Set risk badge with safe handling
    const riskBadge = document.getElementById('modal-risk');
    const riskLevel = articleData.risk_level || articleData.risk || 'medium';
    riskBadge.className = `modal-risk-badge ${riskLevel}`;
    riskBadge.textContent = `${riskLevel.toUpperCase()} RIESGO`;
    
    // Store original URL for later use
    currentArticleUrl = articleData.original_url || articleData.url || '#';
    
    // Load summary with priority: auto_generated_summary > summary > default
    const summaryToLoad = articleData.auto_generated_summary || 
                         articleData.summary || 
                         null;
    
    loadArticleSummary(articleData.id, summaryToLoad);
    
    // Show modal with animation
    const modal = document.getElementById('article-modal');
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closeArticleModal() {
    const modal = document.getElementById('article-modal');
    modal.classList.remove('show');
    
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }, 300);
}

function loadArticleSummary(articleId, summary) {
    const summaryElement = document.getElementById('modal-summary-content');
    
    if (summary && summary.trim()) {
        summaryElement.textContent = summary;
        
        // Translate summary if in English
        setTimeout(async () => {
            await translateAndUpdateElement(summaryElement, summary);
        }, 100);
    } else {
        // Try to fetch summary from API if not provided
        summaryElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando resumen...';
        
        fetch(`/api/article/${articleId}/summary`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.summary) {
                    summaryElement.textContent = data.summary;
                    
                    // Translate if in English
                    setTimeout(async () => {
                        await translateAndUpdateElement(summaryElement, data.summary);
                    }, 100);
                } else {
                    summaryElement.textContent = 'No hay resumen disponible para este artículo.';
                }
            })
            .catch(error => {
                console.error('Error loading summary:', error);
                summaryElement.textContent = 'Error al cargar el resumen. Por favor, intente más tarde.';
            });
    }
}

function openOriginalArticle() {
    if (currentArticleUrl && currentArticleUrl !== '#') {
        window.open(currentArticleUrl, '_blank');
    } else {
        alert('URL del artículo original no disponible.');
    }
}

// Function to open hero article modal
function openHeroArticleModal() {
    if (window.currentHeroArticle) {
        openArticleModal(window.currentHeroArticle);
    } else {
        // Fallback data if hero article not loaded
        openArticleModal({
            id: 'hero',
            title: document.getElementById('hero-title').textContent || 'Artículo Destacado',
            location: document.getElementById('hero-location-text').textContent || 'Ubicación no disponible',
            risk: 'high',
            auto_generated_summary: 'Este es el artículo destacado del momento. Para ver el resumen completo, visite la fuente original.',
            original_url: '#'
        });
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('article-modal');
    if (event.target === modal) {
        closeArticleModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('article-modal');
        if (modal && modal.classList.contains('show')) {
            closeArticleModal();
        }
    }
});

// Satellite Analysis Functions
async function requestSatelliteImage(lat, lon, location) {
    console.log(`🛰️ LEGACY: Requesting satellite image for ${location} at ${lat}, ${lon} (uso deprecado)`);
    
    try {
        const response = await fetch('/api/satellite/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latitude: lat,
                longitude: lon,
                location: location,
                analysis_type: 'conflict_monitoring'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Satellite analysis initiated (legacy mode)');
            
            // Usar el nuevo sistema de notificaciones en lugar del modal
            const locationKey = `${lat}_${lon}_${Date.now()}`;
            showSatelliteAnalysisModal({
                ...data,
                latitude: lat,
                longitude: lon,
                location: location,
                locationKey: locationKey,
                isLegacy: true
            });
        } else {
            console.error('❌ Satellite analysis failed:', data.error);
            showErrorNotification(`Error en análisis satelital: ${data.error}`);
        }
    } catch (error) {
        console.error('❌ Satellite request error:', error);
        showErrorNotification('Error conectando con el sistema satelital');
    }
}

// 🛰️ NOTIFICACIÓN ESPECÍFICA PARA ZONAS DE CONFLICTO
function showSatelliteZoneNotification(data) {
    const { zone_id, location, priority, task_id, message } = data;
    
    // Crear notificación específica para zona
    const notification = document.createElement('div');
    notification.className = `notification zone-notification priority-${priority}`;
    notification.innerHTML = `
        <div class="notification-header">
            <div class="notification-icon">
                <i class="fas fa-satellite-dish" style="color: #00d4ff;"></i>
            </div>
            <div class="notification-title">
                Análisis Satelital - Zona de Conflicto
            </div>
            <div class="notification-priority ${priority}">
                ${priority.toUpperCase()}
            </div>
        </div>
        <div class="notification-content">
            <div class="zone-info">
                <strong>Zona:</strong> ${location}<br>
                <strong>ID:</strong> ${zone_id}<br>
                <strong>Estado:</strong> <span class="status processing">Procesando...</span>
            </div>
            <div class="progress-container">
                <div class="progress-bar" style="width: 0%"></div>
            </div>
        </div>
        <div class="notification-actions">
            <button onclick="closeNotification(this)" class="btn-close">×</button>
        </div>
    `;
    
    // Agregar al contenedor de notificaciones
    const container = document.getElementById('notifications-container') || createNotificationsContainer();
    container.appendChild(notification);
    
    // Animar progreso (simulado)
    setTimeout(() => animateZoneProgress(notification, task_id), 1000);
    
    // Auto-remover después de 30 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 30000);
    
    console.log(`📧 Notificación creada para zona ${zone_id}: ${location}`);
}

function animateZoneProgress(notification, task_id) {
    const progressBar = notification.querySelector('.progress-bar');
    const statusSpan = notification.querySelector('.status');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        
        progressBar.style.width = `${progress}%`;
        
        if (progress >= 100) {
            clearInterval(interval);
            statusSpan.textContent = 'Completado';
            statusSpan.className = 'status completed';
            progressBar.style.backgroundColor = '#00ff88';
        }
    }, 1500);
}

// 🛰️ SISTEMA DE NOTIFICACIONES SATELITALES MEJORADO
let activeSatelliteNotifications = new Map(); // Track active notifications
let satelliteProgressCounters = new Map(); // Track progress for each analysis

function showSatelliteAnalysisModal(data) {
    // Extraer datos de ubicación
    const lat = data.coordinates?.latitude || data.lat || 'N/A';
    const lon = data.coordinates?.longitude || data.lon || 'N/A';
    const location = data.location || data.zone || 'Zona de conflicto';
    
    // Evitar múltiples notificaciones para la misma ubicación
    const locationKey = `${lat}_${lon}`;
    if (activeSatelliteNotifications.has(locationKey)) {
        console.log('🚫 Notificación satelital ya activa para esta ubicación');
        return;
    }

    // Crear notificación compacta en esquina inferior derecha
    const notification = document.createElement('div');
    notification.id = `satellite-notification-${locationKey}`;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        max-width: 350px;
        min-width: 300px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        border: 1px solid rgba(0, 212, 255, 0.3);
        transition: all 0.3s ease;
        transform: translateX(100%);
        font-family: 'Orbitron', monospace;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-satellite-dish" style="color: #00d4ff; font-size: 1.1rem;"></i>
                <span style="font-weight: 600; font-size: 0.9rem;">Análisis Satelital</span>
            </div>
            <button onclick="closeSatelliteNotification('${locationKey}')" 
                    style="background: none; border: none; color: rgba(255,255,255,0.7); 
                           font-size: 1.2rem; cursor: pointer; padding: 0; line-height: 1;">×</button>
        </div>
        
        <div style="font-size: 0.8rem; margin-bottom: 8px; opacity: 0.9;">
            📍 <strong>${location}</strong>
        </div>
        
        <div id="satellite-status-${locationKey}" style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <i class="fas fa-spinner fa-spin" style="color: #00d4ff; font-size: 0.9rem;"></i>
                <span style="font-size: 0.8rem;">Iniciando descarga...</span>
            </div>
            <div style="background: rgba(255,255,255,0.2); height: 4px; border-radius: 2px; overflow: hidden;">
                <div id="satellite-progress-${locationKey}" 
                     style="background: #00d4ff; height: 100%; width: 0%; transition: width 0.3s ease;"></div>
            </div>
        </div>
        
        <div style="display: flex; gap: 8px;">
            <button onclick="window.open('/satellite-analysis', '_blank')" 
                    style="background: rgba(0,212,255,0.2); color: #00d4ff; border: 1px solid rgba(0,212,255,0.5); 
                           padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 0.75rem; flex: 1;">
                📷 Galería
            </button>
            <button onclick="minimizeSatelliteNotification('${locationKey}')" 
                    style="background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.3); 
                           padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 0.75rem;">
                📌 Minimizar
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Registrar notificación activa
    activeSatelliteNotifications.set(locationKey, notification);
    
    // Inicializar contador de progreso
    satelliteProgressCounters.set(locationKey, {
        attempts: 0,
        maxAttempts: 20, // Reducido de 60 a 20 (2 minutos máximo)
        startTime: Date.now(),
        timeout: 2 * 60 * 1000 // 2 minutos timeout
    });
    
    // Track real progress con límites mejorados
    if (data.task_id) {
        trackSatelliteAnalysisProgressImproved(data.task_id, locationKey);
    }
}

// Función mejorada para trackear progreso con manejo de errores
async function trackSatelliteAnalysisProgressImproved(taskId, locationKey) {
    console.log(`📡 Tracking satellite analysis: ${taskId} (${locationKey})`);
    
    const progressData = satelliteProgressCounters.get(locationKey);
    if (!progressData) return;
    
    const notification = activeSatelliteNotifications.get(locationKey);
    if (!notification) return;
    
    const progressBar = document.getElementById(`satellite-progress-${locationKey}`);
    const statusDiv = document.getElementById(`satellite-status-${locationKey}`);
    
    const checkProgress = async () => {
        progressData.attempts++;
        
        // Verificar timeout
        if (Date.now() - progressData.startTime > progressData.timeout) {
            handleSatelliteTimeout(locationKey);
            return;
        }
        
        // Verificar límite de intentos
        if (progressData.attempts > progressData.maxAttempts) {
            handleSatelliteTimeout(locationKey);
            return;
        }
        
        try {
            console.log(`🔍 Verificando progreso satelital (intento ${progressData.attempts}/${progressData.maxAttempts})`);
            
            const response = await fetch('/api/satellite/results?limit=10');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.analyses && data.analyses.length > 0) {
                const recentAnalysis = data.analyses[0];
                
                if (recentAnalysis.status === 'processing') {
                    updateSatelliteProgress(locationKey, 'processing', progressData.attempts);
                    setTimeout(checkProgress, 6000); // Aumentado a 6 segundos
                    
                } else if (recentAnalysis.status === 'completed') {
                    updateSatelliteProgress(locationKey, 'completed', 100, recentAnalysis);
                    
                } else if (recentAnalysis.status === 'failed') {
                    updateSatelliteProgress(locationKey, 'failed', 0, recentAnalysis);
                }
            } else {
                // No hay análisis disponibles, continuar esperando
                updateSatelliteProgress(locationKey, 'waiting', progressData.attempts);
                setTimeout(checkProgress, 6000);
            }
            
        } catch (error) {
            console.warn(`⚠️ Error en progreso satelital (${progressData.attempts}/${progressData.maxAttempts}):`, error);
            
            // Si hay muchos errores consecutivos, considerar fallo
            if (progressData.attempts > 10) {
                updateSatelliteProgress(locationKey, 'connection_error', 0);
                setTimeout(() => closeSatelliteNotification(locationKey), 5000);
            } else {
                setTimeout(checkProgress, 8000); // Aumentar intervalo en caso de error
            }
        }
    };
    
    // Iniciar verificación después de un breve delay
    setTimeout(checkProgress, 3000);
}

function updateSatelliteProgress(locationKey, status, progress, data = null) {
    const progressBar = document.getElementById(`satellite-progress-${locationKey}`);
    const statusDiv = document.getElementById(`satellite-status-${locationKey}`);
    
    if (!progressBar || !statusDiv) return;
    
    switch (status) {
        case 'processing':
            const calcProgress = Math.min(10 + (progress * 3), 85);
            progressBar.style.width = `${calcProgress}%`;
            statusDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <i class="fas fa-satellite-dish fa-spin" style="color: #00d4ff; font-size: 0.9rem;"></i>
                    <span style="font-size: 0.8rem;">Analizando zona (${progress}/20)...</span>
                </div>
                <div style="background: rgba(255,255,255,0.2); height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: #00d4ff; height: 100%; width: ${calcProgress}%; transition: width 0.3s ease;"></div>
                </div>
            `;
            break;
            
        case 'waiting':
            const waitProgress = Math.min(5 + (progress * 2), 50);
            progressBar.style.width = `${waitProgress}%`;
            statusDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <i class="fas fa-clock" style="color: #ffa726; font-size: 0.9rem;"></i>
                    <span style="font-size: 0.8rem;">Preparando análisis...</span>
                </div>
                <div style="background: rgba(255,255,255,0.2); height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: #ffa726; height: 100%; width: ${waitProgress}%; transition: width 0.3s ease;"></div>
                </div>
            `;
            break;
            
        case 'completed':
            progressBar.style.width = '100%';
            const detections = data?.cv_detections ? JSON.parse(data.cv_detections).length : 0;
            statusDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <i class="fas fa-check-circle" style="color: #22c55e; font-size: 0.9rem;"></i>
                    <span style="font-size: 0.8rem;">✅ Completado (${detections} detecciones)</span>
                </div>
                <div style="background: rgba(255,255,255,0.2); height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: #22c55e; height: 100%; width: 100%; transition: width 0.3s ease;"></div>
                </div>
            `;
            // Auto-cerrar después de 8 segundos
            setTimeout(() => closeSatelliteNotification(locationKey), 8000);
            break;
            
        case 'failed':
        case 'connection_error':
            progressBar.style.width = '100%';
            progressBar.style.background = '#ef4444';
            const errorMsg = status === 'connection_error' ? 'Error de conexión' : 'Análisis falló';
            statusDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <i class="fas fa-exclamation-triangle" style="color: #ef4444; font-size: 0.9rem;"></i>
                    <span style="font-size: 0.8rem;">❌ ${errorMsg}</span>
                </div>
                <div style="background: rgba(255,255,255,0.2); height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: #ef4444; height: 100%; width: 100%; transition: width 0.3s ease;"></div>
                </div>
            `;
            break;
    }
}

function handleSatelliteTimeout(locationKey) {
    console.log(`⏰ Timeout en análisis satelital para ${locationKey}`);
    updateSatelliteProgress(locationKey, 'connection_error', 0);
    setTimeout(() => closeSatelliteNotification(locationKey), 5000);
}

function closeSatelliteNotification(locationKey) {
    const notification = activeSatelliteNotifications.get(locationKey);
    if (notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
        
        activeSatelliteNotifications.delete(locationKey);
        satelliteProgressCounters.delete(locationKey);
    }
}

function minimizeSatelliteNotification(locationKey) {
    const notification = activeSatelliteNotifications.get(locationKey);
    if (notification) {
        const isMinimized = notification.getAttribute('data-minimized') === 'true';
        
        if (isMinimized) {
            // Restaurar
            notification.style.height = 'auto';
            notification.style.overflow = 'visible';
            notification.setAttribute('data-minimized', 'false');
            notification.querySelector('button[onclick*="minimizar"]').textContent = '📌 Minimizar';
        } else {
            // Minimizar
            notification.style.height = '60px';
            notification.style.overflow = 'hidden';
            notification.setAttribute('data-minimized', 'true');
            notification.querySelector('button[onclick*="minimizar"]').textContent = '📌 Expandir';
        }
    }
}

// Función anterior mantenida para compatibilidad (deprecada)
async function trackSatelliteAnalysisProgress(taskId, modal) {
    console.log(`📡 [DEPRECADO] Usando trackSatelliteAnalysisProgress - migrar a trackSatelliteAnalysisProgressImproved`);
    
    // Limpiar el modal inmediatamente para evitar interferencias
    if (modal && modal.parentNode) {
        modal.parentNode.removeChild(modal);
    }
    
    // Redirigir a la nueva función si es posible
    if (taskId) {
        const locationKey = `${Date.now()}_legacy`;
        activeSatelliteNotifications.set(locationKey, { remove: () => {} });
        satelliteProgressCounters.set(locationKey, {
            attempts: 0,
            maxAttempts: 10,
            startTime: Date.now(),
            timeout: 60 * 1000
        });
        
        // Mostrar notificación simple que la función anterior ha sido reemplazada
        console.log('🔄 Sistema satelital ha sido mejorado - no se mostrará modal completo');
    }
}

async function triggerSatelliteAnalysis(satelliteZones) {
    console.log(`🛰️ PIPELINE CORRECTO: Analizando ${satelliteZones.length} zonas de conflicto consolidadas`);
    
    // Procesar solo las zonas de mayor prioridad (máximo 5)
    const priorityZones = satelliteZones
        .sort((a, b) => {
            const priorityOrder = { 'critical': 3, 'high': 2, 'medium': 1, 'low': 0 };
            return (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0);
        })
        .slice(0, 5);
    
    for (let i = 0; i < priorityZones.length; i++) {
        const zone = priorityZones[i];
        
        // Validar que sea una zona de conflicto del pipeline
        if (!zone.zone_id || !zone.geojson) {
            console.warn(`⚠️ Zona inválida, saltando: ${zone.location || 'Sin nombre'}`);
            continue;
        }
        
        setTimeout(async () => {
            console.log(`🛰️ Procesando zona ${i+1}/${priorityZones.length}: ${zone.location} (${zone.priority})`);
            
            try {
                const response = await fetch('/api/satellite/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        zone_id: zone.zone_id,
                        geojson: zone.geojson,
                        location: zone.location,
                        priority: zone.priority,
                        analysis_type: 'conflict_zone_monitoring'
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    console.log(`✅ Análisis satelital iniciado para zona: ${zone.location}`);
                    
                    // Mostrar notificación específica para zona de conflicto
                    showSatelliteZoneNotification({
                        zone_id: zone.zone_id,
                        location: zone.location,
                        priority: zone.priority,
                        task_id: result.task_id,
                        message: result.message
                    });
                } else {
                    console.error(`❌ Error en análisis satelital para zona ${zone.location}:`, result.error);
                    showErrorNotification(`Error satelital en ${zone.location}: ${result.error}`);
                }
                
            } catch (error) {
                console.error(`❌ Error de red para zona ${zone.location}:`, error);
                showErrorNotification(`Error de conexión para análisis satelital de ${zone.location}`);
            }
            
        }, i * 3000); // Espaciar requests 3 segundos
    }
    
    // Mostrar resumen
    showNotification(`🛰️ Análisis satelital iniciado para ${priorityZones.length} zonas de conflicto`, 'info');
}

// Function to improve images using the new extractor
async function improveImages() {
    const button = event.target;
    const originalText = button.innerHTML;
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mejorando...';
        button.disabled = true;
        
        console.log('🖼️ Iniciando mejora de imágenes...');
        
        const response = await fetch('/api/improve-images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ Imágenes mejoradas exitosamente:', result);
            
            // Mostrar notificación de éxito
            showNotification(`✅ Imágenes mejoradas: ${result.cleaned} limpiadas, ${result.updated} actualizadas`, 'success');
            
            // Recargar el mosaico para ver las mejoras
            setTimeout(() => {
                if (typeof loadMosaic === 'function') {
                    loadMosaic('real');
                }
                if (typeof loadRealNewsData === 'function') {
                    loadRealNewsData();
                }
            }, 2000);
            
        } else {
            console.error('❌ Error mejorando imágenes:', result.error);
            showNotification(`❌ Error mejorando imágenes: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ Error en la solicitud de mejora de imágenes:', error);
        showNotification('❌ Error de conexión al mejorar imágenes', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Function to show notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 400px;
        font-size: 14px;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Fade in
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// ===== FIN BLOQUE 1 =====
