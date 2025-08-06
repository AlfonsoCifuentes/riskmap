#!/usr/bin/env python3
"""
Script para reparar y actualizar la tabla de cache de conflictos
"""

import sqlite3
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_conflicts_table():
    """Reparar la tabla ai_detected_conflicts"""
    
    db_path = "./data/geopolitical_intel.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar estructura actual
            cursor.execute("PRAGMA table_info(ai_detected_conflicts);")
            existing_columns = [col[1] for col in cursor.fetchall()]
            logger.info(f"📊 Columnas existentes: {existing_columns}")
            
            # Lista de columnas necesarias
            required_columns = {
                'is_active': 'BOOLEAN DEFAULT 1',
                'area_km': 'REAL DEFAULT 1.0',
                'precision_level': 'TEXT DEFAULT "city"',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            # Agregar columnas faltantes
            for col_name, col_def in required_columns.items():
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE ai_detected_conflicts ADD COLUMN {col_name} {col_def};")
                        logger.info(f"✅ Columna '{col_name}' agregada")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo agregar columna '{col_name}': {e}")
            
            # Crear índices
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_conflicts_detected_at ON ai_detected_conflicts(detected_at);",
                "CREATE INDEX IF NOT EXISTS idx_conflicts_active ON ai_detected_conflicts(is_active);", 
                "CREATE INDEX IF NOT EXISTS idx_conflicts_intensity ON ai_detected_conflicts(intensity);",
                "CREATE INDEX IF NOT EXISTS idx_conflicts_location ON ai_detected_conflicts(location_name);"
            ]
            
            for index_sql in indices:
                try:
                    cursor.execute(index_sql)
                    logger.info("✅ Índice creado")
                except Exception as e:
                    logger.warning(f"⚠️ Error creando índice: {e}")
            
            # Actualizar registros existentes para que tengan is_active = 1
            cursor.execute("UPDATE ai_detected_conflicts SET is_active = 1 WHERE is_active IS NULL;")
            updated = cursor.rowcount
            logger.info(f"✅ {updated} registros actualizados con is_active = 1")
            
            conn.commit()
            
            # Verificar estructura final
            cursor.execute("PRAGMA table_info(ai_detected_conflicts);")
            final_columns = cursor.fetchall()
            logger.info("📊 Estructura final de la tabla:")
            for col in final_columns:
                logger.info(f"   - {col[1]} ({col[2]})")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM ai_detected_conflicts;")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_detected_conflicts WHERE is_active = 1;")
            active_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Total de conflictos: {total_count}")
            logger.info(f"📊 Conflictos activos: {active_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error reparando tabla: {e}")
        return False

def test_cache_query():
    """Probar consulta de cache como lo hace el endpoint"""
    
    db_path = "./data/geopolitical_intel.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Misma consulta que usa el endpoint
            cache_threshold = datetime.now() - timedelta(hours=2)
            cache_threshold_str = cache_threshold.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT location_name, latitude, longitude, intensity, confidence, detected_at
                FROM ai_detected_conflicts 
                WHERE detected_at > ? AND is_active = 1
                ORDER BY confidence DESC, detected_at DESC
                LIMIT 20
            """, (cache_threshold_str,))
            
            cached_conflicts = cursor.fetchall()
            
            if cached_conflicts:
                logger.info(f"✅ Cache funciona: {len(cached_conflicts)} conflictos disponibles")
                logger.info("🎯 Conflictos en cache:")
                for conflict in cached_conflicts[:5]:  # Solo mostrar primeros 5
                    logger.info(f"   - {conflict[0]}: ({conflict[1]:.4f}, {conflict[2]:.4f}) - {conflict[3]} (conf: {conflict[4]:.2f})")
                
                if len(cached_conflicts) > 5:
                    logger.info(f"   ... y {len(cached_conflicts) - 5} más")
                
                return True
            else:
                logger.warning("⚠️ No hay conflictos en cache reciente")
                
                # Mostrar los más recientes sin filtro de tiempo
                cursor.execute("""
                    SELECT location_name, latitude, longitude, intensity, confidence, detected_at
                    FROM ai_detected_conflicts 
                    WHERE is_active = 1
                    ORDER BY detected_at DESC
                    LIMIT 5
                """)
                
                all_conflicts = cursor.fetchall()
                if all_conflicts:
                    logger.info("📊 Conflictos más recientes (sin filtro de tiempo):")
                    for conflict in all_conflicts:
                        logger.info(f"   - {conflict[0]}: {conflict[3]} (conf: {conflict[4]:.2f}) - {conflict[5]}")
                
                return False
                
    except Exception as e:
        logger.error(f"❌ Error probando cache: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Reparando tabla de cache de conflictos...")
    
    if fix_conflicts_table():
        logger.info("✅ Tabla reparada correctamente")
        
        logger.info("🧪 Probando funcionalidad de cache...")
        if test_cache_query():
            logger.info("✅ Cache está listo para uso instantáneo")
        else:
            logger.warning("⚠️ Cache vacío - endpoint ejecutará análisis completo")
    else:
        logger.error("❌ Error reparando tabla")
