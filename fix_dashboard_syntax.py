#!/usr/bin/env python3
"""
Script para arreglar la sintaxis del dashboard
"""

def fix_dashboard_js():
    dashboard_path = r"src\web\templates\dashboard_BUENO.html"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar el inicio de la función generateMosaicTiles
    start_marker = "// Generate mosaic tiles\nasync function generateMosaicTiles(mode) {"
    end_marker = "// Get different news sets with perfect alignment\nfunction getNewsSet(setIndex) {"
    
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)
    
    if start_index == -1 or end_index == -1:
        print("❌ No se pudo encontrar la función generateMosaicTiles")
        return False
    
    # Nueva implementación completa de la función
    new_function = '''// Generate mosaic tiles
async function generateMosaicTiles(mode) {
    const container = document.getElementById('news-mosaic');
    let tilesHTML = '';
    let sampleArticles = [];
    
    try {
        // Cargar artículos deduplicados desde la API
        const response = await fetch('/api/articles/deduplicated?hours=24');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Error loading deduplicated articles');
        }
        
        sampleArticles = data.mosaic || [];
        
        // Si no hay suficientes artículos deduplicados, usar el fallback
        if (sampleArticles.length === 0) {
            console.warn('⚠️ No hay artículos deduplicados, usando datos de fallback');
            sampleArticles = getNewsSet(currentNewsSet);
        } else {
            console.log(`🎯 Cargados ${sampleArticles.length} artículos deduplicados`);
        }
        
    } catch (deduplicationError) {
        console.error('Error cargando artículos deduplicados:', deduplicationError);
        console.log('🔄 Usando datos de fallback por error de deduplicación');
        sampleArticles = getNewsSet(currentNewsSet);
    }
    
    console.log(`🎨 Generando mosaico con ${sampleArticles.length} artículos usando computer vision...`);
        
    // Pre-cargar análisis CV para todos los artículos
    const cvAnalysisPromises = sampleArticles.map(article => 
        article.id ? getImageAnalysis(article.id) : Promise.resolve(null)
    );
    
    try {
        const cvAnalyses = await Promise.all(cvAnalysisPromises);
        console.log(`🔍 Análisis CV obtenidos para ${cvAnalyses.filter(a => a).length} artículos`);
        
        sampleArticles.forEach((article, index) => {
            let sizeClass;
            
            if (currentNewsSet === 0) {
                // Set 1: Diseño original (7 noticias)
                sizeClass = `size-${(index % 12) + 1}`;
            } else if (currentNewsSet === 1) {
                // Set 2: NUEVO DISEÑO DEL USUARIO - Rejilla 3x4 (12 cuadrados) 
                const newUserPattern = [
                    'size-puzzle-single',  // Art 1: 1 cuadrado 
                    'size-puzzle-single',  // Art 2: 1 cuadrado  
                    'size-puzzle-single',  // Art 3: 1 cuadrado
                    'size-puzzle-single',  // Art 4: 1 cuadrado
                    'size-puzzle-big',     // Art 5: 4 cuadrados (grande)
                    'size-puzzle-wide',    // Art 6: 2 cuadrados (ancho)
                    'size-puzzle-wide'     // Art 7: 2 cuadrados (ancho)
                ];
                sizeClass = newUserPattern[index] || 'size-puzzle-single';
            } else if (currentNewsSet === 2) {
                // Set 3: Diseño puzzle anterior - Rejilla 3x4 (12 cuadrados) 
                const puzzlePattern = [
                    'size-puzzle-single',  // Art 1: 1 cuadrado (izquierda)
                    'size-puzzle-single',  // Art 2: 1 cuadrado (izquierda)
                    'size-puzzle-big',     // Art 3: 4 cuadrados (derecha)
                    'size-puzzle-single',  // Art 4: 1 cuadrado (izquierda)
                    'size-puzzle-single',  // Art 5: 1 cuadrado (izquierda)
                    'size-puzzle-wide',    // Art 6: 2 cuadrados (abajo)
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
            
            // Obtener la imagen optimizada o usar fallback
            const normalizedImage = normalizeImageUrl(article.image_url || article.image);
            let imageUrl = normalizedImage || article.image_url || article.image || `https://picsum.photos/400/300?random=${index}`;
            
            // Si hay análisis CV, usar imagen optimizada si está disponible
            if (cvAnalysis && cvAnalysis.optimized_url && cvAnalysis.optimized_url !== article.image_url) {
                imageUrl = normalizeImageUrl(cvAnalysis.optimized_url) || imageUrl;
                console.log(`🔧 Usando imagen optimizada CV para artículo ${article.id}:`, cvAnalysis.optimized_url);
            }
            
            // Agregar evento click para el modal
            const clickHandler = `onclick="openArticleModal({
                id: ${article.id || 'null'},
                title: '${(article.title || '').replace(/'/g, "\\\\'")}',
                auto_generated_summary: '${(article.auto_generated_summary || '').replace(/'/g, "\\\\'")}',
                summary: '${(article.summary || '').replace(/'/g, "\\\\'")}',
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
            const normalizedImage = normalizeImageUrl(article.image_url || article.image);
            const imageUrl = normalizedImage || article.image_url || article.image || `https://picsum.photos/400/300?random=${index}`;
            
            const clickHandler = `onclick="openArticleModal({
                id: ${article.id || 'null'},
                title: '${(article.title || '').replace(/'/g, "\\\\'")}',
                auto_generated_summary: '${(article.auto_generated_summary || '').replace(/'/g, "\\\\'")}',
                summary: '${(article.summary || '').replace(/'/g, "\\\\'")}',
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
    
    // Show/hide load more button
    const loadMoreContainer = document.getElementById('load-more-container');
    if (loadMoreContainer) {
        loadMoreContainer.style.display = 'flex';
    }
}

'''
    
    # Reemplazar la función completa
    new_content = content[:start_index] + new_function + content[end_index:]
    
    # Escribir el archivo actualizado
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Función generateMosaicTiles arreglada correctamente")
    print(f"📊 Longitud original: {len(content)} caracteres")
    print(f"📊 Longitud nueva: {len(new_content)} caracteres")
    
    return True

if __name__ == "__main__":
    fix_dashboard_js()
