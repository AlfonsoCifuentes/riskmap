#!/usr/bin/env python3
"""
Script de procesamiento masivo con análisis NLP avanzado
Procesa todos los artículos de la base de datos unificada
"""

import sqlite3
import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime
import time

# Importar sistema NLP avanzado
from advanced_geopolitical_nlp import AdvancedGeopoliticalNLP

class MassArticleProcessor:
    """Procesador masivo de artículos con análisis NLP avanzado"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db'):
        self.db_path = db_path
        self.nlp_analyzer = None
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        
    def initialize_nlp_system(self):
        """Inicializar sistema NLP con Groq"""
        try:
            # Cargar API key de Groq si está disponible
            groq_client = None
            try:
                from groq import Groq
                import os
                from dotenv import load_dotenv
                
                load_dotenv()
                groq_api_key = os.getenv('GROQ_API_KEY')
                
                if groq_api_key:
                    groq_client = Groq(api_key=groq_api_key)
                    print("✅ Cliente Groq inicializado")
                else:
                    print("⚠️ GROQ_API_KEY no encontrada, usando análisis básico")
                    
            except ImportError:
                print("⚠️ Groq no disponible, usando análisis básico")
            
            # Inicializar analizador NLP
            self.nlp_analyzer = AdvancedGeopoliticalNLP(
                db_path=self.db_path,
                groq_client=groq_client
            )
            print("🧠 Sistema NLP avanzado inicializado")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando NLP: {e}")
            return False
    
    def get_articles_to_process(self) -> List[Dict[str, Any]]:
        """Obtener artículos que necesitan procesamiento NLP"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si existe la tabla unificada
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unified_articles';")
            if not cursor.fetchone():
                print("❌ Tabla unified_articles no encontrada. Ejecutar migración primero.")
                return []
            
            # Obtener artículos sin procesamiento avanzado o que necesiten actualización
            query = """
                SELECT id, title, content, source, published_at, country, region,
                       risk_level, image_url, url, language
                FROM unified_articles
                WHERE (model_version IS NULL OR model_version != 'advanced_nlp_v1.0')
                   AND title IS NOT NULL 
                   AND title != ''
                   AND length(title) > 10
                ORDER BY published_at DESC
                LIMIT 1000
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convertir a diccionarios
            articles = []
            columns = ['id', 'title', 'content', 'source', 'published_at', 'country', 
                      'region', 'risk_level', 'image_url', 'url', 'language']
            
            for row in rows:
                article = dict(zip(columns, row))
                articles.append(article)
            
            conn.close()
            
            print(f"📊 Encontrados {len(articles)} artículos para procesar")
            return articles
            
        except Exception as e:
            print(f"❌ Error obteniendo artículos: {e}")
            return []
    
    def update_article_analysis(self, article_id: int, analysis_data: Dict[str, Any]) -> bool:
        """Actualizar artículo con datos del análisis NLP"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construir query de actualización
            update_fields = []
            values = []
            
            # Campos a actualizar
            field_mapping = {
                'countries_involved': 'countries_involved',
                'politicians_involved': 'politicians_involved', 
                'weapons_mentioned': 'weapons_mentioned',
                'location_extracted': 'location_extracted',
                'conflict_intensity': 'conflict_intensity',
                'conflict_type': 'conflict_type',
                'source_country': 'source_country',
                'source_bias': 'source_bias',
                'source_credibility': 'source_credibility',
                'ai_summary': 'ai_summary',
                'urgency_level': 'urgency_level',
                'impact_score': 'impact_score',
                'processing_confidence': 'processing_confidence',
                'model_version': 'model_version',
                'last_processed': 'last_processed',
                'metadata_json': 'metadata_json'
            }
            
            for analysis_key, db_field in field_mapping.items():
                if analysis_key in analysis_data:
                    update_fields.append(f"{db_field} = ?")
                    values.append(analysis_data[analysis_key])
            
            # Actualizar timestamp
            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            
            # Agregar ID para WHERE clause
            values.append(article_id)
            
            # Ejecutar actualización
            query = f"""
                UPDATE unified_articles 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando artículo {article_id}: {e}")
            return False
    
    def process_single_article(self, article: Dict[str, Any]) -> bool:
        """Procesar un solo artículo con análisis NLP"""
        try:
            article_id = article['id']
            
            # Procesar con NLP avanzado
            analysis_data = self.nlp_analyzer.process_article(article)
            
            # Actualizar en base de datos
            if self.update_article_analysis(article_id, analysis_data):
                self.processed_count += 1
                
                # Log de progreso
                if self.processed_count % 10 == 0:
                    elapsed = time.time() - self.start_time
                    rate = self.processed_count / elapsed if elapsed > 0 else 0
                    print(f"✅ Procesados: {self.processed_count} | Rate: {rate:.2f}/s | Errores: {self.error_count}")
                
                return True
            else:
                self.error_count += 1
                return False
                
        except Exception as e:
            print(f"❌ Error procesando artículo {article.get('id', 'unknown')}: {e}")
            self.error_count += 1
            return False
    
    def process_all_articles(self, batch_size: int = 50):
        """Procesar todos los artículos en lotes"""
        print("🚀 INICIANDO PROCESAMIENTO MASIVO DE ARTÍCULOS")
        print("=" * 50)
        
        self.start_time = time.time()
        
        # Inicializar sistema NLP
        if not self.initialize_nlp_system():
            print("❌ No se pudo inicializar el sistema NLP. Abortando.")
            return
        
        # Obtener artículos a procesar
        articles = self.get_articles_to_process()
        
        if not articles:
            print("✅ No hay artículos para procesar")
            return
        
        total_articles = len(articles)
        print(f"📊 Total de artículos a procesar: {total_articles}")
        print(f"📦 Procesando en lotes de {batch_size}")
        print()
        
        # Procesar artículos en lotes
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(articles) + batch_size - 1) // batch_size
            
            print(f"🔄 Procesando lote {batch_num}/{total_batches} ({len(batch)} artículos)")
            
            for article in batch:
                # Mostrar info del artículo
                title_preview = (article['title'][:60] + '...') if len(article['title']) > 60 else article['title']
                print(f"   📰 {article['id']}: {title_preview}")
                
                # Procesar artículo
                self.process_single_article(article)
                
                # Pequeña pausa para no sobrecargar
                time.sleep(0.1)
            
            print(f"✅ Lote {batch_num} completado")
            print()
        
        # Resumen final
        elapsed_time = time.time() - self.start_time
        success_rate = (self.processed_count / total_articles) * 100 if total_articles > 0 else 0
        
        print("=" * 50)
        print("📊 RESUMEN DEL PROCESAMIENTO")
        print("=" * 50)
        print(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")
        print(f"✅ Artículos procesados: {self.processed_count}/{total_articles}")
        print(f"❌ Errores: {self.error_count}")
        print(f"📈 Tasa de éxito: {success_rate:.1f}%")
        print(f"🚀 Velocidad promedio: {self.processed_count / elapsed_time:.2f} artículos/seg")
        
        if self.processed_count > 0:
            print("\n✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        else:
            print("\n❌ PROCESAMIENTO COMPLETADO CON ERRORES")
    
    def generate_processing_report(self):
        """Generar reporte del estado de procesamiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print("📊 REPORTE DE ESTADO DE PROCESAMIENTO")
            print("=" * 40)
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM unified_articles;")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE model_version = 'advanced_nlp_v1.0';")
            processed_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE countries_involved IS NOT NULL AND countries_involved != '';")
            with_countries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE politicians_involved IS NOT NULL AND politicians_involved != '';")
            with_politicians = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE weapons_mentioned IS NOT NULL AND weapons_mentioned != '';")
            with_weapons = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE conflict_intensity IS NOT NULL AND conflict_intensity > 0;")
            with_intensity = cursor.fetchone()[0]
            
            print(f"Total de artículos: {total_articles}")
            print(f"Procesados con NLP avanzado: {processed_articles}")
            print(f"Con países identificados: {with_countries}")
            print(f"Con políticos identificados: {with_politicians}")
            print(f"Con armamento identificado: {with_weapons}")
            print(f"Con intensidad calculada: {with_intensity}")
            
            # Top países mencionados
            print("\n🌍 Países más mencionados:")
            cursor.execute("""
                SELECT countries_involved, COUNT(*) as count
                FROM unified_articles 
                WHERE countries_involved IS NOT NULL 
                AND countries_involved != ''
                AND countries_involved != '[]'
                GROUP BY countries_involved
                ORDER BY count DESC
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                try:
                    countries = json.loads(row[0])
                    if countries:
                        print(f"   {', '.join(countries[:3])}: {row[1]} artículos")
                except:
                    pass
            
            # Distribución de niveles de riesgo
            print("\n⚠️ Distribución de riesgo:")
            cursor.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM unified_articles 
                WHERE risk_level IS NOT NULL
                GROUP BY risk_level
                ORDER BY count DESC
            """)
            
            for risk_level, count in cursor.fetchall():
                print(f"   {risk_level}: {count} artículos")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")

def main():
    """Función principal"""
    processor = MassArticleProcessor()
    
    # Generar reporte inicial
    print("📋 ESTADO INICIAL:")
    processor.generate_processing_report()
    print()
    
    # Procesar artículos
    processor.process_all_articles(batch_size=25)
    
    # Generar reporte final
    print("\n📋 ESTADO FINAL:")
    processor.generate_processing_report()

if __name__ == "__main__":
    main()