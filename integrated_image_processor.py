#!/usr/bin/env python3
"""
Wrapper para integrar el extractor de imágenes en el proceso de ingesta de noticias
"""
import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent))

from news_image_extractor import NewsImageExtractor

logger = logging.getLogger(__name__)

class IntegratedImageProcessor:
    """
    Procesador de imágenes integrado que se puede usar en el flujo de ingesta
    """
    
    def __init__(self):
        self.extractor = NewsImageExtractor()
        logger.info("🖼️  Procesador de imágenes inicializado")
    
    def process_article_image(self, article_data):
        """
        Procesar imagen para un artículo durante la ingesta
        
        Args:
            article_data (dict): Datos del artículo con keys: id, url, title, etc.
            
        Returns:
            dict: article_data actualizado con image_url
        """
        try:
            article_id = article_data.get('id')
            article_url = article_data.get('url')
            
            if not article_id or not article_url:
                logger.warning(f"Artículo {article_id}: Faltan datos para extraer imagen")
                return article_data
            
            # Intentar extraer y descargar imagen
            local_path = self.extractor.process_article(article_id, article_url)
            
            if local_path:
                # Actualizar los datos del artículo
                article_data['image_url'] = local_path
                logger.info(f"✅ Imagen procesada para artículo {article_id}: {local_path}")
            else:
                logger.warning(f"⚠️  No se pudo extraer imagen para artículo {article_id}")
                
            return article_data
            
        except Exception as e:
            logger.error(f"Error procesando imagen para artículo {article_data.get('id', 'unknown')}: {e}")
            return article_data
    
    def batch_process_images(self, articles_data):
        """
        Procesar imágenes para un lote de artículos
        
        Args:
            articles_data (list): Lista de diccionarios con datos de artículos
            
        Returns:
            list: Lista actualizada con image_url
        """
        logger.info(f"🔄 Procesando imágenes para {len(articles_data)} artículos...")
        
        success_count = 0
        for i, article in enumerate(articles_data):
            logger.info(f"[{i+1}/{len(articles_data)}] Procesando: {article.get('title', 'Sin título')[:50]}...")
            
            updated_article = self.process_article_image(article)
            
            if updated_article.get('image_url') and updated_article['image_url'].startswith('/static/images/news/'):
                success_count += 1
            
            articles_data[i] = updated_article
        
        logger.info(f"✅ Procesamiento completado: {success_count}/{len(articles_data)} con imágenes extraídas")
        return articles_data


def enhance_rss_ingestion():
    """
    Función para mejorar el sistema de ingesta RSS existente
    """
    print("🔧 MEJORANDO SISTEMA DE INGESTA RSS")
    
    # Buscar archivos de ingesta RSS existentes
    rss_files = []
    
    search_patterns = [
        "rss_ingestion.py",
        "feed_ingestion.py", 
        "news_ingestion.py",
        "data_ingestion.py"
    ]
    
    current_dir = Path(".")
    for pattern in search_patterns:
        matches = list(current_dir.rglob(pattern))
        rss_files.extend(matches)
    
    if rss_files:
        print(f"📁 Archivos de ingesta encontrados:")
        for file in rss_files:
            print(f"   - {file}")
    else:
        print("❌ No se encontraron archivos de ingesta RSS")
    
    # Crear ejemplo de integración
    integration_code = '''
# INTEGRACIÓN CON EXTRACTOR DE IMÁGENES
# Agregar al final del archivo de ingesta RSS:

from integrated_image_processor import IntegratedImageProcessor

def enhanced_rss_ingestion():
    # ... código existente de RSS ...
    
    # Al final, después de guardar artículos en BD
    image_processor = IntegratedImageProcessor()
    
    # Obtener artículos recién insertados
    recent_articles = get_recent_articles_from_db()  # Implementar según tu estructura
    
    # Procesar imágenes
    updated_articles = image_processor.batch_process_images(recent_articles)
    
    print(f"✅ Ingesta completada con imágenes procesadas")

# EJEMPLO DE USO EN NUEVO ARTÍCULO:
def process_new_article(article_data):
    # ... guardar artículo en BD ...
    
    # Procesar imagen inmediatamente
    processor = IntegratedImageProcessor()
    updated_article = processor.process_article_image(article_data)
    
    return updated_article
'''
    
    with open("integration_example.py", "w", encoding="utf-8") as f:
        f.write(integration_code)
    
    print("✅ Ejemplo de integración guardado en 'integration_example.py'")

def test_integration():
    """Probar la integración con datos de prueba"""
    print("\n🧪 PROBANDO INTEGRACIÓN")
    
    # Datos de prueba
    test_articles = [
        {
            'id': 999,
            'title': 'Artículo de prueba',
            'url': 'https://www.bbc.com/news',
            'content': 'Contenido de prueba'
        }
    ]
    
    processor = IntegratedImageProcessor()
    results = processor.batch_process_images(test_articles)
    
    print(f"✅ Prueba completada: {len(results)} artículos procesados")
    return results[0] if results else None

def main():
    """Función principal"""
    print("🚀 SETUP: Integración de extractor de imágenes")
    print("=" * 60)
    
    # Paso 1: Mejorar ingesta existente
    enhance_rss_ingestion()
    
    # Paso 2: Probar integración
    test_result = test_integration()
    
    print("\n" + "=" * 60)
    print("📋 INSTRUCCIONES FINALES:")
    print("1. Revisar 'integration_example.py' para ver el código")
    print("2. Integrar el código en tus archivos de ingesta RSS") 
    print("3. Todas las nuevas noticias tendrán imágenes automáticamente")
    print("4. Ejecutar 'python news_image_extractor.py' para procesar artículos existentes")

if __name__ == "__main__":
    main()