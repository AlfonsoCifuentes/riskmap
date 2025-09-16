#!/usr/bin/env python3
"""Script para adaptar el esquema de las tablas satelitales existentes."""

import sqlite3
from datetime import datetime

def adapt_satellite_schema():
    """Adaptar el esquema de las tablas satelitales existentes."""
    try:
        db_path = "./data/geopolitical_intel.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🔧 ADAPTANDO ESQUEMA DE TABLAS SATELITALES")
            print("=" * 60)
            
            # Verificar esquema actual de satellite_images
            cursor.execute("PRAGMA table_info(satellite_images)")
            columns = cursor.fetchall()
            print("📋 Esquema actual de satellite_images:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
            
            # Crear tabla satellite_analysis_new (con esquema correcto)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_analysis_new (
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
            print("✅ Tabla satellite_analysis_new creada")
            
            # Crear tabla satellite_detections_new
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_detections_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id INTEGER,
                    detection_type TEXT,
                    confidence REAL,
                    latitude REAL,
                    longitude REAL,
                    bounding_box TEXT,
                    detection_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT
                )
            """)
            print("✅ Tabla satellite_detections_new creada")
            
            # Crear tabla computer_vision_results_new
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS computer_vision_results_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id INTEGER,
                    detection_type TEXT,
                    confidence REAL,
                    description TEXT,
                    coordinates TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Tabla computer_vision_results_new creada")
            
            # Insertar datos de prueba usando esquema existente
            print("\n📊 INSERTANDO DATOS DE PRUEBA COMPATIBLES...")
            
            # Para satellite_analysis_new
            cursor.execute("""
                INSERT OR REPLACE INTO satellite_analysis_new 
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
            
            # Para satellite_detections_new
            test_detections = [
                (1, 'vehicle', 0.85, 40.7589, -73.9851, '{"x": 100, "y": 150, "width": 50, "height": 25}', 'yolo_v8'),
                (2, 'building', 0.92, 40.7590, -73.9850, '{"x": 200, "y": 200, "width": 100, "height": 80}', 'yolo_v8'),
                (3, 'military_vehicle', 0.78, 34.0522, -118.2437, '{"x": 300, "y": 100, "width": 60, "height": 30}', 'yolo_v8'),
            ]
            
            for det_data in test_detections:
                cursor.execute("""
                    INSERT INTO satellite_detections_new 
                    (image_id, detection_type, confidence, latitude, longitude, bounding_box, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, det_data)
            
            # Para computer_vision_results_new
            test_cv_results = [
                (1, 'conflict_indicators', 0.73, 'Multiple vehicles detected in formation', '40.7589,-73.9851'),
                (2, 'military_presence', 0.82, 'Military vehicles identified', '34.0522,-118.2437'),
                (3, 'infrastructure_damage', 0.67, 'Potential structural damage visible', '51.5074,-0.1278')
            ]
            
            for cv_data in test_cv_results:
                cursor.execute("""
                    INSERT INTO computer_vision_results_new 
                    (image_id, detection_type, confidence, description, coordinates)
                    VALUES (?, ?, ?, ?, ?)
                """, cv_data)
            
            # Agregar algunos registros a la tabla satellite_images existente
            existing_images = [
                (101, 'sentinel-2', datetime.now().strftime('%Y-%m-%d'), 10, -74.0, 40.7, -73.9, 40.8, 
                 'https://example.com/nyc_preview.jpg', 'https://example.com/nyc_full.jpg', None, 
                 '{"resolution": "10m", "bands": ["B02", "B03", "B04"]}', 1),
                (102, 'landsat-8', datetime.now().strftime('%Y-%m-%d'), 5, -118.3, 34.0, -118.2, 34.1,
                 'https://example.com/la_preview.jpg', 'https://example.com/la_full.jpg', None,
                 '{"resolution": "30m", "bands": ["B2", "B3", "B4"]}', 2),
            ]
            
            for img_data in existing_images:
                cursor.execute("""
                    INSERT OR IGNORE INTO satellite_images 
                    (image_id, collection, date, cloud_cover, bbox_min_lon, bbox_min_lat, 
                     bbox_max_lon, bbox_max_lat, preview_url, download_url, local_path, metadata, zone_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, img_data)
            
            conn.commit()
            print("✅ Datos de prueba insertados")
            
            # Verificar datos
            cursor.execute("SELECT COUNT(*) FROM satellite_analysis_new")
            analysis_count = cursor.fetchone()[0]
            print(f"   📊 Análisis: {analysis_count}")
            
            cursor.execute("SELECT COUNT(*) FROM satellite_images")
            images_count = cursor.fetchone()[0]
            print(f"   🖼️ Imágenes: {images_count}")
            
            cursor.execute("SELECT COUNT(*) FROM satellite_detections_new")
            detections_count = cursor.fetchone()[0]
            print(f"   🎯 Detecciones: {detections_count}")
            
            cursor.execute("SELECT COUNT(*) FROM computer_vision_results_new")
            cv_count = cursor.fetchone()[0]
            print(f"   🤖 Resultados CV: {cv_count}")
            
            print("\n✅ ESQUEMA ADAPTADO CORRECTAMENTE")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    adapt_satellite_schema()
