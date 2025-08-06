// Script de debug para investigar el problema de URLs de imagen
// Este script puede ejecutarse en la consola del navegador

console.log('🔍 DEBUG: Iniciando investigación de URLs de imagen...');

// Función de normalización para testing
function testNormalizeImageUrl(url) {
    if (!url) return null;
    
    // Si es una imagen local (comienza con data\images o data/images)
    if (url.startsWith('data\\images\\') || url.startsWith('data/images/')) {
        // Extraer solo el nombre del archivo
        const filename = url.replace(/^data[\\\/]images[\\\/]/, '');
        return `/data/images/${filename}`;
    }
    
    // Si ya es una URL completa, devolverla tal como está
    return url;
}

// Casos de prueba
const testCases = [
    'data\\images\\article_2979_0af77df1.jpg',
    'data/images/article_2979_0af77df1.jpg',
    'https://example.com/image.jpg',
    'data\\images\\article_525_c9ab8b05.jpg'
];

console.log('📋 Probando casos de normalización:');
testCases.forEach(testCase => {
    const normalized = testNormalizeImageUrl(testCase);
    console.log(`Input: "${testCase}" → Output: "${normalized}"`);
});

// Verificar si hay elementos en el DOM con URLs problemáticas
console.log('🔎 Buscando elementos con URLs problemáticas...');
const allImages = document.querySelectorAll('[style*="background-image"]');
let problematicUrls = [];

allImages.forEach((element, index) => {
    const style = element.getAttribute('style');
    const urlMatch = style.match(/background-image:\s*url\(['"]([^'"]+)['"]\)/);
    if (urlMatch) {
        const url = urlMatch[1];
        console.log(`Elemento ${index}: URL = "${url}"`);
        
        // Detectar URLs problemáticas
        if (url.includes('dataimages') || url.includes('data\\images') && !url.startsWith('/')) {
            problematicUrls.push({
                element: element,
                url: url,
                index: index
            });
            console.warn(`⚠️ URL problemática encontrada: "${url}"`);
        }
    }
});

if (problematicUrls.length > 0) {
    console.error(`🚨 Se encontraron ${problematicUrls.length} URLs problemáticas:`);
    problematicUrls.forEach(item => {
        console.error(`- Elemento ${item.index}: "${item.url}"`);
    });
} else {
    console.log('✅ No se encontraron URLs problemáticas en el DOM');
}

// Verificar datos crudos de artículos si están disponibles
if (typeof articlesData !== 'undefined' && articlesData) {
    console.log('📊 Verificando datos de artículos...');
    const imageUrls = articlesData.map(article => article.image_url || article.image).filter(Boolean);
    console.log('URLs de imagen en datos:', imageUrls.slice(0, 5));
    
    const localImages = imageUrls.filter(url => url && (url.includes('data\\images') || url.includes('data/images')));
    console.log(`Encontradas ${localImages.length} imágenes locales:`, localImages.slice(0, 3));
}

console.log('🔍 DEBUG: Investigación completada');
