#!/usr/bin/env python3
"""
Sistema de migración y unificación de base de datos
Consolida todas las tablas relacionadas con artículos en una sola tabla optimizada
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class DatabaseUnificationSystem:
    """Sistema para unificar y optimizar la estructura de la base de datos"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db'):
        self.db_path = db_path
        self.backup_path = f'{db_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
    def create_backup(self):
        """Crear backup de la base de datos actual"""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            print(f"✅ Backup creado: {self.backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False
    
    def design_unified_schema(self) -> str:
        """Diseña el esquema unificado optimizado"""
        
        unified_schema = """
        CREATE TABLE IF NOT EXISTS unified_articles (
            -- IDs y metadata básica
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Información del artículo
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            ai_summary TEXT,
            auto_generated_summary TEXT,
            
            -- URLs y fuentes
            url TEXT,
            image_url TEXT,
            original_image_url TEXT,
            video_url TEXT,
            
            -- Información de medios y fuente
            source TEXT,                    -- Nombre del medio (ej: CNN, BBC, Reuters)
            source_country TEXT,            -- País de origen del medio
            source_bias TEXT,               -- Sesgo político estimado (left/center/right)
            source_credibility REAL DEFAULT 0.5,  -- Credibilidad del medio (0.0-1.0)
            author TEXT,
            
            -- Fechas
            published_at DATETIME,
            original_published_date TEXT,
            enrichment_timestamp TIMESTAMP,
            
            -- Idioma y traducción
            language TEXT DEFAULT 'es',
            original_language TEXT,
            is_translated INTEGER DEFAULT 0,
            
            -- Ubicación y geografía
            country TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            location_extracted TEXT,        -- Ubicación extraída por NLP
            
            -- Análisis de riesgo y geopolítica
            risk_level TEXT,                -- alto/medio/bajo
            risk_score REAL DEFAULT 0.0,   -- Score numérico 0.0-1.0
            conflict_intensity REAL DEFAULT 0.0,  -- Intensidad del conflicto (0-100)
            conflict_probability REAL DEFAULT 0.0,
            geopolitical_relevance REAL DEFAULT 0.0,
            
            -- Análisis de sentimiento
            sentiment_score REAL DEFAULT 0.0,
            sentiment_label TEXT,
            ai_sentiment TEXT,
            
            -- Entidades extraídas por NLP
            countries_involved TEXT,        -- JSON array de países implicados
            politicians_involved TEXT,      -- JSON array de políticos (nombres completos)
            military_entities TEXT,         -- JSON array de entidades militares
            weapons_mentioned TEXT,         -- JSON array de armamento mencionado
            weapon_models TEXT,             -- JSON array de modelos específicos de armas
            organizations_involved TEXT,    -- JSON array de organizaciones
            
            -- Análisis NLP avanzado
            key_persons TEXT,              -- Personas clave mencionadas
            key_locations TEXT,            -- Ubicaciones clave
            entities_json TEXT,            -- Todas las entidades en JSON
            extracted_entities_json TEXT,
            keywords TEXT,                 -- Palabras clave extraídas
            topics TEXT,                   -- Temas identificados
            
            -- Tipos de conflicto y eventos
            conflict_type TEXT,            -- Tipo de conflicto identificado
            event_type TEXT,               -- Tipo de evento geopolítico
            conflict_indicators TEXT,      -- Indicadores de conflicto
            
            -- Análisis visual
            has_image BOOLEAN DEFAULT 0,
            image_source TEXT,
            visual_risk_score REAL,
            detected_objects TEXT,
            visual_analysis_json TEXT,
            
            -- Métricas de calidad
            quality_score REAL DEFAULT 0.0,
            validation_result TEXT,
            enrichment_confidence REAL DEFAULT 0.0,
            processing_confidence REAL DEFAULT 0.0,
            
            -- Estado de procesamiento
            processed INTEGER DEFAULT 0,
            enrichment_status TEXT DEFAULT 'pending',
            enrichment_version INTEGER DEFAULT 1,
            processing_time REAL,
            model_version TEXT,
            
            -- Control de duplicados y exclusiones
            semantic_hash TEXT,
            is_excluded INTEGER DEFAULT 0,
            exclusion_reason TEXT,
            
            -- Categorización
            category TEXT,
            tags TEXT,
            ai_tags TEXT,
            
            -- Importancia e impacto
            ai_importance REAL DEFAULT 0.0,
            impact_score REAL DEFAULT 0.0,
            urgency_level TEXT,
            
            -- Datos adicionales
            raw_data TEXT,                 -- Datos raw del RSS/API
            metadata_json TEXT,            -- Metadata adicional
            processing_notes TEXT,         -- Notas del procesamiento
            
            -- Índices para optimización
            last_enriched TEXT,
            last_processed TIMESTAMP
        );
        
        -- Crear índices para consultas optimizadas
        CREATE INDEX IF NOT EXISTS idx_unified_published_at ON unified_articles(published_at);
        CREATE INDEX IF NOT EXISTS idx_unified_risk_level ON unified_articles(risk_level);
        CREATE INDEX IF NOT EXISTS idx_unified_country ON unified_articles(country);
        CREATE INDEX IF NOT EXISTS idx_unified_source ON unified_articles(source);
        CREATE INDEX IF NOT EXISTS idx_unified_processed ON unified_articles(processed);
        CREATE INDEX IF NOT EXISTS idx_unified_geopolitical ON unified_articles(geopolitical_relevance);
        CREATE INDEX IF NOT EXISTS idx_unified_conflict_intensity ON unified_articles(conflict_intensity);
        CREATE INDEX IF NOT EXISTS idx_unified_semantic_hash ON unified_articles(semantic_hash);
        """
        
        return unified_schema
    
    def migrate_existing_data(self):
        """Migra datos existentes al nuevo esquema unificado"""
        
        if not os.path.exists(self.db_path):
            print(f"❌ Base de datos no encontrada: {self.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear nueva tabla unificada
            print("🔧 Creando esquema unificado...")
            cursor.executescript(self.design_unified_schema())
            
            # Migrar datos de la tabla articles
            print("📦 Migrando datos de la tabla 'articles'...")
            
            # Obtener columnas de la tabla original
            cursor.execute("PRAGMA table_info(articles);")
            original_columns = [col[1] for col in cursor.fetchall()]
            
            # Mapeo de campos entre tabla original y nueva
            field_mapping = self._get_field_mapping()
            
            # Construir query de migración
            select_fields = []
            insert_fields = []
            
            for old_field, new_field in field_mapping.items():
                if old_field in original_columns:
                    select_fields.append(old_field)
                    insert_fields.append(new_field)
            
            # Ejecutar migración
            select_query = f"SELECT {', '.join(select_fields)} FROM articles WHERE 1=1"
            insert_placeholders = ', '.join(['?' for _ in insert_fields])
            insert_query = f"INSERT INTO unified_articles ({', '.join(insert_fields)}) VALUES ({insert_placeholders})"
            
            cursor.execute(select_query)
            articles_data = cursor.fetchall()
            
            print(f"📊 Migrando {len(articles_data)} artículos...")
            
            for row in articles_data:
                cursor.execute(insert_query, row)
            
            # Migrar datos de processed_data si existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_data';")
            if cursor.fetchone():
                print("🧠 Integrando datos de análisis NLP existentes...")
                self._merge_processed_data(cursor)
            
            conn.commit()
            
            # Verificar migración
            cursor.execute("SELECT COUNT(*) FROM unified_articles;")
            migrated_count = cursor.fetchone()[0]
            
            print(f"✅ Migración completada: {migrated_count} artículos migrados")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error durante migración: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_field_mapping(self) -> Dict[str, str]:
        """Mapeo entre campos de tabla original y nueva tabla unificada"""
        return {
            'id': 'id',
            'title': 'title',
            'content': 'content',
            'url': 'url',
            'source': 'source',
            'published_at': 'published_at',
            'language': 'language',
            'created_at': 'created_at',
            'risk_level': 'risk_level',
            'country': 'country',
            'region': 'region',
            'summary': 'summary',
            'risk_score': 'risk_score',
            'sentiment_score': 'sentiment_score',
            'sentiment_label': 'sentiment_label',
            'conflict_type': 'conflict_type',
            'key_persons': 'key_persons',
            'key_locations': 'key_locations',
            'entities_json': 'entities_json',
            'conflict_indicators': 'conflict_indicators',
            'visual_risk_score': 'visual_risk_score',
            'detected_objects': 'detected_objects',
            'visual_analysis_json': 'visual_analysis_json',
            'image_url': 'image_url',
            'processed': 'processed',
            'processing_time': 'processing_time',
            'quality_score': 'quality_score',
            'validation_result': 'validation_result',
            'enrichment_status': 'enrichment_status',
            'enrichment_version': 'enrichment_version',
            'last_enriched': 'last_enriched',
            'enrichment_confidence': 'enrichment_confidence',
            'semantic_hash': 'semantic_hash',
            'auto_generated_summary': 'auto_generated_summary',
            'extracted_entities_json': 'extracted_entities_json',
            'conflict_probability': 'conflict_probability',
            'geopolitical_relevance': 'geopolitical_relevance',
            'is_excluded': 'is_excluded',
            'is_translated': 'is_translated',
            'original_language': 'original_language',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'video_url': 'video_url',
            'author': 'author',
            'tags': 'tags',
            'category': 'category',
            'ai_summary': 'ai_summary',
            'ai_tags': 'ai_tags',
            'ai_sentiment': 'ai_sentiment',
            'ai_importance': 'ai_importance',
            'enrichment_timestamp': 'enrichment_timestamp',
            'has_image': 'has_image',
            'image_source': 'image_source',
            'original_image_url': 'original_image_url'
        }
    
    def _merge_processed_data(self, cursor):
        """Integrar datos de la tabla processed_data"""
        try:
            # Obtener datos NLP procesados
            cursor.execute("""
                SELECT article_id, advanced_nlp, sentiment, keywords, topics, 
                       classification, confidence_score, processing_time
                FROM processed_data 
                WHERE article_id IS NOT NULL
            """)
            
            processed_rows = cursor.fetchall()
            
            for row in processed_rows:
                article_id, advanced_nlp, sentiment, keywords, topics, classification, confidence, proc_time = row
                
                # Actualizar registro en unified_articles
                cursor.execute("""
                    UPDATE unified_articles 
                    SET keywords = ?, topics = ?, processing_confidence = ?,
                        processing_notes = ?, model_version = 'legacy_nlp'
                    WHERE id = ?
                """, (keywords, topics, confidence or 0.0, advanced_nlp, article_id))
            
            print(f"🔗 Integrados datos NLP de {len(processed_rows)} artículos")
            
        except Exception as e:
            print(f"⚠️ Error integrando datos NLP: {e}")
    
    def verify_migration(self) -> bool:
        """Verificar que la migración fue exitosa"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar que la tabla existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unified_articles';")
            if not cursor.fetchone():
                print("❌ Tabla unified_articles no encontrada")
                return False
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM unified_articles;")
            unified_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles;")
            original_count = cursor.fetchone()[0]
            
            print(f"📊 Verificación de migración:")
            print(f"   Original: {original_count} artículos")
            print(f"   Migrados: {unified_count} artículos")
            
            # Verificar estructura
            cursor.execute("PRAGMA table_info(unified_articles);")
            columns = cursor.fetchall()
            print(f"   Columnas en tabla unificada: {len(columns)}")
            
            # Verificar datos críticos
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE title IS NOT NULL AND title != '';")
            with_title = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE image_url IS NOT NULL AND image_url != '';")
            with_image = cursor.fetchone()[0]
            
            print(f"   Con título: {with_title}")
            print(f"   Con imagen: {with_image}")
            
            success = unified_count == original_count and unified_count > 0
            
            if success:
                print("✅ Migración verificada exitosamente")
            else:
                print("❌ Problemas en la verificación de migración")
            
            conn.close()
            return success
            
        except Exception as e:
            print(f"❌ Error verificando migración: {e}")
            return False

def main():
    """Función principal para ejecutar la migración"""
    print("🔄 SISTEMA DE UNIFICACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    unifier = DatabaseUnificationSystem()
    
    # Crear backup
    if not unifier.create_backup():
        print("❌ No se pudo crear backup. Abortando migración.")
        return
    
    # Ejecutar migración
    if unifier.migrate_existing_data():
        # Verificar migración
        if unifier.verify_migration():
            print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print(f"📁 Backup disponible en: {unifier.backup_path}")
        else:
            print("\n❌ MIGRACIÓN COMPLETADA CON ERRORES")
    else:
        print("\n❌ MIGRACIÓN FALLÓ")

if __name__ == "__main__":
    main()