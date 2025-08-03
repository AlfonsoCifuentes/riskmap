#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para enriquecimiento de pocos artículos
"""

import asyncio
from enriquecimiento_masivo_nuevo import MassiveEnrichmentProcessor

async def test_enrichment():
    """Ejecutar enriquecimiento de prueba con pocos artículos"""
    print("🧪 PRUEBA DE ENRIQUECIMIENTO")
    print("Pipeline: NLP → Computer Vision → Groq/Ollama")
    print("=" * 50)
    
    try:
        # Crear procesador
        processor = MassiveEnrichmentProcessor()
        
        # Mostrar información
        total_articles = processor.get_total_articles_count()
        articles_to_process = processor.get_articles_to_enrich(limit=5)
        
        print(f"📊 Total artículos en BD: {total_articles}")
        print(f"📝 Artículos a procesar: {len(articles_to_process)}")
        
        if len(articles_to_process) == 0:
            print("✅ No hay artículos pendientes de enriquecer")
            return
        
        print("\n🚀 Iniciando procesamiento de prueba...")
        
        # Procesar solo 3 artículos como prueba
        success = await processor.process_all_articles(limit=3)
        
        if success:
            print("\n✅ Prueba de enriquecimiento completada exitosamente")
        else:
            print("\n❌ Prueba completada con errores")
            
    except Exception as e:
        print(f"\n❌ Error en prueba: {e}")

if __name__ == "__main__":
    asyncio.run(test_enrichment())
