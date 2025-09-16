#!/usr/bin/env python3
"""
Script para migrar y reparar la tabla GDELT
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_gdelt_table():
    """Migrar tabla GDELT existente a nueva estructura"""
    try:
        with sqlite3.connect('./data/geopolitical_intel.db') as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='gdelt_events'
            """)
            
            exists = cursor.fetchone()
            
            if exists:
                print("📋 Tabla gdelt_events existe, verificando estructura...")
                
                # Obtener columnas actuales
                cursor.execute("PRAGMA table_info(gdelt_events)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                print(f"🔍 Columnas actuales: {len(column_names)}")
                
                # Verificar si necesitamos migrar
                required_columns = ['is_conflict', 'conflict_type', 'severity_score']
                missing_columns = [col for col in required_columns if col not in column_names]
                
                if missing_columns:
                    print(f"⚠️ Faltan columnas: {missing_columns}")
                    
                    # Backup de datos existentes si los hay
                    cursor.execute("SELECT COUNT(*) FROM gdelt_events")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        print(f"💾 Haciendo backup de {count} registros existentes...")
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS gdelt_events_backup AS 
                            SELECT * FROM gdelt_events
                        """)
                    
                    # Recrear tabla con nueva estructura
                    print("🔧 Recreando tabla con nueva estructura...")
                    cursor.execute("DROP TABLE gdelt_events")
                    
                    # Crear nueva tabla
                    cursor.execute("""
                        CREATE TABLE gdelt_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            global_event_id TEXT UNIQUE,
                            event_date TEXT,
                            event_type TEXT,
                            event_code TEXT,
                            actor1_name TEXT,
                            actor1_country TEXT,
                            actor2_name TEXT,
                            actor2_country TEXT,
                            action_location TEXT,
                            action_country TEXT,
                            action_latitude REAL,
                            action_longitude REAL,
                            quad_class INTEGER,
                            goldstein_scale REAL,
                            num_mentions INTEGER,
                            avg_tone REAL,
                            source_url TEXT,
                            article_title TEXT,
                            article_content TEXT,
                            article_date TEXT,
                            article_source TEXT,
                            conflict_type TEXT,
                            severity_score REAL,
                            imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            is_conflict INTEGER DEFAULT 0,
                            UNIQUE(global_event_id, event_date)
                        )
                    """)
                    
                    # Crear índices
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_gdelt_conflict 
                        ON gdelt_events(is_conflict, event_date)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_gdelt_location 
                        ON gdelt_events(action_latitude, action_longitude)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_gdelt_date 
                        ON gdelt_events(event_date)
                    """)
                    
                    print("✅ Tabla gdelt_events migrada exitosamente")
                    
                else:
                    print("✅ Tabla gdelt_events ya tiene la estructura correcta")
            
            else:
                print("📋 Tabla gdelt_events no existe, será creada por el ingestor")
            
            conn.commit()
            return True
            
    except Exception as e:
        print(f"❌ Error migrando tabla GDELT: {e}")
        return False

def verify_gdelt_structure():
    """Verificar estructura final de la tabla GDELT"""
    try:
        with sqlite3.connect('./data/geopolitical_intel.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(gdelt_events)")
            columns = cursor.fetchall()
            
            print("\n📋 ESTRUCTURA FINAL DE gdelt_events:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
            
            cursor.execute("SELECT COUNT(*) FROM gdelt_events")
            count = cursor.fetchone()[0]
            print(f"\n📊 Registros en gdelt_events: {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

if __name__ == "__main__":
    print("🔧 MIGRANDO TABLA GDELT...")
    
    if migrate_gdelt_table():
        verify_gdelt_structure()
        print("\n✅ Migración completada. Ahora puede ejecutar el ingestor GDELT.")
    else:
        print("\n❌ Error en migración")
