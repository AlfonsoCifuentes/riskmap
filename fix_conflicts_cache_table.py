#!/usr/bin/env python3
"""
Script para crear la tabla de cache de conflictos detectados por IA
"""

import sqlite3
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_conflicts_cache_table():
    """Crear la tabla ai_detected_conflicts en la base de datos"""
    
    db_path = "./data/geopolitical_intel.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_detected_conflicts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    intensity TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    article_id INTEGER,
                    article_title TEXT,
                    article_summary TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    area_km REAL DEFAULT 1.0,
                    precision_level TEXT DEFAULT 'city',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Crear índices para consultas rápidas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_detected_at ON ai_detected_conflicts(detected_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_active ON ai_detected_conflicts(is_active);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_intensity ON ai_detected_conflicts(intensity);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_location ON ai_detected_conflicts(location_name);")
            
            conn.commit()
            logger.info("✅ Tabla ai_detected_conflicts creada correctamente")
            
            # Verificar que existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_detected_conflicts';")
            result = cursor.fetchone()
            
            if result:
                logger.info("✅ Tabla confirmada en la base de datos")
                
                # Mostrar estructura de la tabla
                cursor.execute("PRAGMA table_info(ai_detected_conflicts);")
                columns = cursor.fetchall()
                logger.info("📊 Estructura de la tabla:")
                for col in columns:
                    logger.info(f"   - {col[1]} ({col[2]})")
                
                # Verificar datos existentes
                cursor.execute("SELECT COUNT(*) FROM ai_detected_conflicts;")
                count = cursor.fetchone()[0]
                logger.info(f"📊 Conflictos en cache: {count}")
                
                if count > 0:
                    # Mostrar los más recientes
                    cursor.execute("""
                        SELECT location_name, intensity, confidence, detected_at 
                        FROM ai_detected_conflicts 
                        ORDER BY detected_at DESC 
                        LIMIT 5
                    """)
                    recent = cursor.fetchall()
                    logger.info("🔥 Conflictos más recientes:")
                    for conflict in recent:
                        logger.info(f"   - {conflict[0]}: {conflict[1]} (conf: {conflict[2]}) - {conflict[3]}")
                
            else:
                logger.error("❌ La tabla no se creó correctamente")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error creando tabla: {e}")
        return False
    
    return True

def test_cache_availability():
    """Probar si el cache puede ser usado para respuestas rápidas"""
    
    db_path = "./data/geopolitical_intel.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar cache reciente (últimas 2 horas)
            cache_threshold = datetime.now() - timedelta(hours=2)
            cache_threshold_str = cache_threshold.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM ai_detected_conflicts 
                WHERE detected_at > ? AND is_active = 1
            """, (cache_threshold_str,))
            
            recent_count = cursor.fetchone()[0]
            
            if recent_count > 0:
                logger.info(f"✅ Cache disponible: {recent_count} conflictos detectados en las últimas 2 horas")
                
                # Mostrar datos del cache
                cursor.execute("""
                    SELECT location_name, latitude, longitude, intensity, confidence, detected_at
                    FROM ai_detected_conflicts 
                    WHERE detected_at > ? AND is_active = 1
                    ORDER BY confidence DESC, detected_at DESC
                    LIMIT 10
                """, (cache_threshold_str,))
                
                cached_conflicts = cursor.fetchall()
                logger.info("🎯 Conflictos en cache (listos para respuesta instantánea):")
                for conflict in cached_conflicts:
                    logger.info(f"   - {conflict[0]}: ({conflict[1]:.4f}, {conflict[2]:.4f}) - {conflict[3]} (conf: {conflict[4]:.2f}) - {conflict[5]}")
                
                return True
            else:
                logger.warning("⚠️ No hay cache reciente disponible")
                logger.info("💡 El endpoint ejecutará análisis completo de IA")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error verificando cache: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Inicializando sistema de cache de conflictos...")
    
    # Crear tabla
    if create_conflicts_cache_table():
        # Probar disponibilidad del cache
        test_cache_availability()
        logger.info("✅ Sistema de cache inicializado correctamente")
    else:
        logger.error("❌ Error inicializando sistema de cache")
