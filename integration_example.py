
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
