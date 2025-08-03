#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rápido del sistema de enriquecimiento masivo
Procesa solo 5 artículos para verificar que todo funciona
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_enriquecimiento.log')
    ]
)
logger = logging.getLogger(__name__)

# Importar servicios
from app_BUENA import get_database_path
from src.ai.unified_ai_service import unified_ai_service
from src.ai.ollama_service import ollama_service

class QuickEnrichmentTest:
    """Test rápido del sistema de enriquecimiento"""
    
    def __init__(self):
        # Ruta correcta de la base de datos
        self.db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
        
        # Verificar que la base de datos existe
        if not os.path.exists(self.db_path):
            logger.error(f"❌ Base de datos no encontrada: {self.db_path}")
            # Intentar con nombres alternativos comunes
            alt_paths = [
                "geopolitical_data.db",
                "data/geopolitical_data.db",
                "geopolitical_intel.db"
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    self.db_path = alt_path
                    logger.info(f"✅ Usando base de datos alternativa: {alt_path}")
                    break
            else:
                raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
        else:
            logger.info(f"✅ Base de datos encontrada: {self.db_path}")
    
    def check_services_status(self):
        """Verificar el estado de los servicios de AI"""
        logger.info("🔍 Verificando estado de servicios...")
        
        # Verificar Ollama
        try:
            ollama_status = ollama_service.check_service_health()
            logger.info(f"Ollama: {'✅' if ollama_status.get('available') else '❌'}")
            if ollama_status.get('available'):
                models = ollama_status.get('models', [])
                logger.info(f"  Modelos disponibles: {', '.join(models)}")
        except Exception as e:
            logger.warning(f"Error verificando Ollama: {e}")
        
        # Verificar servicio unificado
        try:
            unified_status = unified_ai_service.get_service_status()
            logger.info(f"Servicio unificado: {'✅' if unified_status.get('status') == 'healthy' else '❌'}")
            logger.info(f"  Estrategia: {unified_status.get('strategy', 'unknown')}")
            logger.info(f"  Fallback disponible: {'✅' if unified_status.get('fallback_available') else '❌'}")
        except Exception as e:
            logger.warning(f"Error verificando servicio unificado: {e}")
    
    def get_test_articles(self, limit=5):
        """Obtener artículos para test"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar artículos que no tengan análisis enriquecido
            cursor.execute("""
                SELECT id, title, content, url, risk_level
                FROM processed_data 
                WHERE (ai_summary IS NULL OR ai_summary = '' OR ai_summary = 'N/A')
                   OR (geopolitical_analysis IS NULL OR geopolitical_analysis = '' OR geopolitical_analysis = 'N/A')
                   OR (conflict_probability IS NULL OR conflict_probability = 0)
                ORDER BY published_date DESC
                LIMIT ?
            """, (limit,))
            
            articles = cursor.fetchall()
            conn.close()
            
            if not articles:
                logger.warning("⚠️ No se encontraron artículos sin enriquecer")
                return []
            
            logger.info(f"📰 Encontrados {len(articles)} artículos para test")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo artículos: {e}")
            return []
    
    def test_enrichment_single_article(self, article):
        """Test de enriquecimiento en un solo artículo"""
        article_id, title, content, url, risk_level = article
        
        logger.info(f"🔄 Procesando: {title[:60]}...")
        
        try:
            # Crear el texto completo para análisis
            full_text = f"Título: {title}\n\nContenido: {content}"
            
            # Solicitar análisis rápido
            logger.info("  📝 Solicitando resumen...")
            summary_result = unified_ai_service.get_fast_summary(
                text=full_text,
                max_length=150
            )
            
            if summary_result and summary_result.get('success'):
                summary = summary_result.get('summary', '')
                model_used = summary_result.get('model_used', 'unknown')
                logger.info(f"  ✅ Resumen generado con {model_used}")
                logger.info(f"  📝 {summary[:100]}...")
                
                # Intentar análisis geopolítico
                logger.info("  🌍 Solicitando análisis geopolítico...")
                analysis_result = unified_ai_service.get_deep_analysis(
                    text=full_text,
                    analysis_type="geopolitical"
                )
                
                if analysis_result and analysis_result.get('success'):
                    analysis = analysis_result.get('analysis', {})
                    model_used_analysis = analysis_result.get('model_used', 'unknown')
                    logger.info(f"  ✅ Análisis completado con {model_used_analysis}")
                    
                    # Extraer datos del análisis
                    risk_assessment = analysis.get('risk_assessment', {})
                    conflict_prob = risk_assessment.get('conflict_probability', 0)
                    
                    logger.info(f"  📊 Probabilidad de conflicto: {conflict_prob}")
                    return True
                else:
                    logger.warning("  ⚠️ Análisis geopolítico falló")
                    return False
            else:
                logger.warning("  ⚠️ Generación de resumen falló")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error procesando artículo {article_id}: {e}")
            return False
    
    def run_test(self):
        """Ejecutar test completo"""
        logger.info("🚀 Iniciando test rápido de enriquecimiento...")
        logger.info(f"📍 Base de datos: {self.db_path}")
        
        # Verificar servicios
        self.check_services_status()
        
        # Obtener artículos de prueba
        articles = self.get_test_articles(5)
        if not articles:
            logger.error("❌ No hay artículos para testear")
            return False
        
        # Procesar artículos
        success_count = 0
        for i, article in enumerate(articles, 1):
            logger.info(f"\n--- Test {i}/{len(articles)} ---")
            if self.test_enrichment_single_article(article):
                success_count += 1
        
        # Resultado final
        success_rate = (success_count / len(articles)) * 100
        logger.info(f"\n📊 RESULTADO DEL TEST:")
        logger.info(f"  ✅ Exitosos: {success_count}/{len(articles)}")
        logger.info(f"  📈 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 TEST APROBADO - Sistema listo para enriquecimiento masivo")
            return True
        else:
            logger.warning("⚠️ TEST PARCIAL - Revisar configuración antes del enriquecimiento masivo")
            return False

def main():
    """Función principal"""
    print("🧪 TEST RÁPIDO DE ENRIQUECIMIENTO MASIVO")
    print("=" * 50)
    
    try:
        # Crear y ejecutar test
        test = QuickEnrichmentTest()
        success = test.run_test()
        
        if success:
            print("\n✅ Test completado exitosamente")
            print("💡 Puedes ejecutar: python enriquecimiento_masivo.py")
        else:
            print("\n⚠️ Test completado con advertencias")
            print("💡 Revisar logs antes del enriquecimiento masivo")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
