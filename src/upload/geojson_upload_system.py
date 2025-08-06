
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil
import logging

class GeoJSONUploadSystem:
    """Sistema de subida automática de GeoJSON"""
    
    def __init__(self):
        self.geojson_dir = Path('src/satellite/geojson')
        self.upload_dir = Path('src/web/static/geojson')
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = 'geopolitical_intelligence.db'
    
    def scan_and_upload_geojson(self):
        """Escanear y subir archivos GeoJSON automáticamente"""
        try:
            uploaded_files = []
            
            # Buscar archivos GeoJSON
            geojson_files = list(self.geojson_dir.glob('*.geojson'))
            
            for geojson_file in geojson_files:
                # Leer contenido
                with open(geojson_file, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # Copiar a directorio web
                web_filename = f"auto_{geojson_file.name}"
                web_path = self.upload_dir / web_filename
                
                shutil.copy2(geojson_file, web_path)
                
                # Registrar en BD
                self.register_geojson_in_database(geojson_data, str(web_path))
                
                uploaded_files.append({
                    'original': str(geojson_file),
                    'web_path': str(web_path),
                    'location': geojson_data['properties'].get('location', 'Unknown')
                })
            
            print(f"Subidos automáticamente {len(uploaded_files)} archivos GeoJSON")
            return uploaded_files
            
        except Exception as e:
            print(f"Error en subida automática: {e}")
            return []
    
    def register_geojson_in_database(self, geojson_data, web_path):
        """Registrar GeoJSON en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            properties = geojson_data['properties']
            
            cursor = conn.execute("""
                INSERT OR REPLACE INTO geojson_files
                (filename, location, upload_date, properties, geometry, web_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                Path(web_path).name,
                properties.get('location', 'Unknown'),
                datetime.now().isoformat(),
                json.dumps(properties),
                json.dumps(geojson_data['geometry']),
                web_path
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error registrando GeoJSON en BD: {e}")
    
    def create_geojson_api_endpoint(self):
        """Crear endpoint API para GeoJSON"""
        endpoint_code = """
# Endpoints API para GeoJSON
@app.route('/api/geojson/list')
def api_geojson_list():
    """Listar todos los archivos GeoJSON disponibles"""
    try:
        conn = sqlite3.connect('geopolitical_intelligence.db')
        
        cursor = conn.execute("""
            SELECT filename, location, upload_date, web_path, properties
            FROM geojson_files
            ORDER BY upload_date DESC
        """)
        
        geojson_files = []
        for row in cursor.fetchall():
            geojson_files.append({
                'filename': row[0],
                'location': row[1], 
                'upload_date': row[2],
                'web_path': row[3],
                'properties': json.loads(row[4]) if row[4] else {}
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(geojson_files),
            'files': geojson_files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geojson/auto-upload')
def api_geojson_auto_upload():
    """Ejecutar subida automática de GeoJSON"""
    try:
        upload_system = GeoJSONUploadSystem()
        uploaded_files = upload_system.scan_and_upload_geojson()
        
        return jsonify({
            'success': True,
            'uploaded_count': len(uploaded_files),
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
"""
        return endpoint_code
            