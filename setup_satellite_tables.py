#!/usr/bin/env python3
"""Script para verificar y crear las tablas de análisis satelital."""

import sqlite3
from datetime import datetime

def check_and_create_satellite_tables():
    """Verificar y crear tablas de análisis satelital si no existen."""
    try:
        db_path = "./data/geopolitical_intel.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🛰️ VERIFICANDO TABLAS DE ANÁLISIS SATELITAL")
            print("=" * 60)
            
            # Verificar tablas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tablas existentes: {len(existing_tables)}")
            
            satellite_tables = [
                'satellite_analysis',
                'satellite_images', 
                'satellite_detections',
                'computer_vision_results'
            ]
            
            for table in satellite_tables:
                if table in existing_tables:
                    print(f"✅ Tabla {table} existe")
                    # Verificar columnas
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    print(f"   Columnas: {', '.join(columns)}")
                else:
                    print(f"❌ Tabla {table} no existe")
            
            print("\n🔧 CREANDO TABLAS FALTANTES...")
            
            # Crear tabla satellite_analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_analysis (
                    id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    total_zones INTEGER DEFAULT 0,
                    processed_zones INTEGER DEFAULT 0,
                    results TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Tabla satellite_analysis creada/verificada")
            
            # Crear tabla satellite_images
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT,
                    latitude REAL,
                    longitude REAL,
                    image_url TEXT,
                    image_path TEXT,
                    satellite_provider TEXT,
                    acquisition_date TEXT,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES satellite_analysis(id)
                )
            """)
            print("✅ Tabla satellite_images creada/verificada")
            
            # Crear tabla satellite_detections
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id INTEGER,
                    detection_type TEXT,
                    confidence REAL,
                    latitude REAL,
                    longitude REAL,
                    bounding_box TEXT,
                    detection_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    FOREIGN KEY (image_id) REFERENCES satellite_images(id)
                )
            """)
            print("✅ Tabla satellite_detections creada/verificada")
            
            # Crear tabla computer_vision_results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS computer_vision_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id INTEGER,
                    detection_type TEXT,
                    confidence REAL,
                    description TEXT,
                    coordinates TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (image_id) REFERENCES satellite_images(id)
                )
            """)
            print("✅ Tabla computer_vision_results creada/verificada")
            
            # Insertar datos de prueba
            print("\n📊 INSERTANDO DATOS DE PRUEBA...")
            
            # Datos de prueba para satellite_analysis
            cursor.execute("""
                INSERT OR REPLACE INTO satellite_analysis 
                (id, status, total_zones, processed_zones, results, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'test_analysis_001',
                'completed',
                3,
                3,
                '{"zones_analyzed": 3, "detections": 5}',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Datos de prueba para satellite_images
            test_images = [
                ('test_analysis_001', 40.7589, -73.9851, 'https://example.com/nyc.jpg', '/images/nyc_satellite.jpg', 'Sentinel-2'),
                ('test_analysis_001', 34.0522, -118.2437, 'https://example.com/la.jpg', '/images/la_satellite.jpg', 'Landsat-8'),
                ('test_analysis_001', 51.5074, -0.1278, 'https://example.com/london.jpg', '/images/london_satellite.jpg', 'Sentinel-2')
            ]
            
            for img_data in test_images:
                cursor.execute("""
                    INSERT OR REPLACE INTO satellite_images 
                    (analysis_id, latitude, longitude, image_url, image_path, satellite_provider)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, img_data)
            
            # Datos de prueba para satellite_detections
            test_detections = [
                (1, 'vehicle', 0.85, 40.7589, -73.9851, '{"x": 100, "y": 150, "width": 50, "height": 25}', 'yolo_v8'),
                (1, 'building', 0.92, 40.7590, -73.9850, '{"x": 200, "y": 200, "width": 100, "height": 80}', 'yolo_v8'),
                (2, 'military_vehicle', 0.78, 34.0522, -118.2437, '{"x": 300, "y": 100, "width": 60, "height": 30}', 'yolo_v8'),
                (3, 'infrastructure', 0.95, 51.5074, -0.1278, '{"x": 150, "y": 250, "width": 120, "height": 90}', 'yolo_v8')
            ]
            
            for det_data in test_detections:
                cursor.execute("""
                    INSERT OR REPLACE INTO satellite_detections 
                    (image_id, detection_type, confidence, latitude, longitude, bounding_box, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, det_data)
            
            # Datos de prueba para computer_vision_results
            test_cv_results = [
                (1, 'conflict_indicators', 0.73, 'Multiple vehicles detected in formation', '40.7589,-73.9851'),
                (2, 'military_presence', 0.82, 'Military vehicles identified', '34.0522,-118.2437'),
                (3, 'infrastructure_damage', 0.67, 'Potential structural damage visible', '51.5074,-0.1278')
            ]
            
            for cv_data in test_cv_results:
                cursor.execute("""
                    INSERT OR REPLACE INTO computer_vision_results 
                    (image_id, detection_type, confidence, description, coordinates)
                    VALUES (?, ?, ?, ?, ?)
                """, cv_data)
            
            conn.commit()
            print("✅ Datos de prueba insertados")
            
            # Verificar datos insertados
            print("\n📈 VERIFICACIÓN DE DATOS:")
            
            cursor.execute("SELECT COUNT(*) FROM satellite_analysis")
            analysis_count = cursor.fetchone()[0]
            print(f"   📊 Análisis satelitales: {analysis_count}")
            
            cursor.execute("SELECT COUNT(*) FROM satellite_images")
            images_count = cursor.fetchone()[0]
            print(f"   🖼️ Imágenes satelitales: {images_count}")
            
            cursor.execute("SELECT COUNT(*) FROM satellite_detections")
            detections_count = cursor.fetchone()[0]
            print(f"   🎯 Detecciones: {detections_count}")
            
            cursor.execute("SELECT COUNT(*) FROM computer_vision_results")
            cv_count = cursor.fetchone()[0]
            print(f"   🤖 Resultados CV: {cv_count}")
            
            print("\n✅ TODAS LAS TABLAS DE ANÁLISIS SATELITAL PREPARADAS")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_and_create_satellite_tables()
