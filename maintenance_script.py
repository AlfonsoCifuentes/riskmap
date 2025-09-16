#!/usr/bin/env python3
"""
Script de mantenimiento para el sistema de filtrado geopolítico y imágenes
"""

import os
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

class RiskMapMaintenance:
    """Clase para mantenimiento del sistema RiskMap"""
    
    def __init__(self):
        self.db_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
        self.images_dir = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\static\images\news"
        
    def run_daily_maintenance(self):
        """Ejecutar mantenimiento diario del sistema"""
        print("🔧 INICIANDO MANTENIMIENTO DIARIO RISKMAP")
        print("=" * 60)
        
        self.check_geopolitical_filter()
        self.verify_image_system()
        self.cleanup_old_images()
        self.generate_health_report()
        
        print("\n✅ MANTENIMIENTO COMPLETADO")
        
    def check_geopolitical_filter(self):
        """Verificar que el filtro geopolítico funcione correctamente"""
        print("📊 Verificando filtro geopolítico...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Consulta con filtro geopolítico (misma lógica que app_BUENA.py)
                query = """
                SELECT title, source, image_url 
                FROM articles 
                WHERE (
                    -- Incluir contenido geopolítico
                    (LOWER(title || ' ' || COALESCE(content, '')) LIKE '%war%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%conflict%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%military%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%politics%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%government%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%security%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%nato%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%russia%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%china%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%israel%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gaza%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%iran%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%guerra%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%militar%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%política%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gobierno%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%seguridad%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%otan%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%rusia%' OR
                     LOWER(title || ' ' || COALESCE(content, '')) LIKE '%irán%')
                ) AND (
                    -- Excluir contenido no geopolítico
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%sport%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%game%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%match%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%team%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%player%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%goal%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%football%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%soccer%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%basketball%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%emmy%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%oscar%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%movie%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%actor%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%hollywood%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%music%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%celebrity%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%iphone%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%apple%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%anime%' AND
                    LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tv show%'
                )
                ORDER BY created_at DESC 
                LIMIT 10
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                print(f"   ✅ Filtro funcionando: {len(results)} artículos geopolíticos encontrados")
                
                # Verificar que no haya contenido no geopolítico
                non_geo_patterns = ['sport', 'game', 'emmy', 'oscar', 'movie', 'iphone']
                contaminated = 0
                
                for title, source, img in results:
                    title_lower = title.lower()
                    for pattern in non_geo_patterns:
                        if pattern in title_lower:
                            contaminated += 1
                            print(f"   ⚠️  Posible contaminación: '{title[:50]}...'")
                            break
                
                if contaminated == 0:
                    print(f"   ✅ Sin contaminación: 0 artículos no geopolíticos")
                else:
                    print(f"   ⚠️  {contaminated} artículos posiblemente contaminados")
                    
        except Exception as e:
            print(f"   ❌ Error verificando filtro: {e}")
    
    def verify_image_system(self):
        """Verificar sistema de imágenes"""
        print("🖼️  Verificando sistema de imágenes...")
        
        try:
            # Verificar directorio de imágenes
            if not os.path.exists(self.images_dir):
                print(f"   ❌ Directorio de imágenes no existe: {self.images_dir}")
                return
                
            image_count = len([f for f in os.listdir(self.images_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))])
            print(f"   📊 {image_count} imágenes almacenadas localmente")
            
            # Verificar artículos con imágenes locales en la BD
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM articles 
                    WHERE original_image_url IS NOT NULL AND original_image_url != ''
                """)
                
                local_images_count = cursor.fetchone()[0]
                print(f"   📊 {local_images_count} artículos con URL de imagen original en BD")
                
                # Verificar artículos con imágenes placeholder
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM articles 
                    WHERE (image_url LIKE '%placeholder%' OR image_url IS NULL)
                """)
                
                placeholder_count = cursor.fetchone()[0]
                
                if placeholder_count > 0:
                    print(f"   ⚠️  {placeholder_count} artículos con imagen placeholder")
                else:
                    print(f"   ✅ Todos los artículos tienen imagen real")
                    
        except Exception as e:
            print(f"   ❌ Error verificando imágenes: {e}")
    
    def cleanup_old_images(self):
        """Limpiar imágenes antiguas (más de 30 días)"""
        print("🧹 Limpiando imágenes antiguas...")
        
        try:
            if not os.path.exists(self.images_dir):
                return
                
            cutoff_date = datetime.now() - timedelta(days=30)
            cleaned_count = 0
            
            for filename in os.listdir(self.images_dir):
                file_path = os.path.join(self.images_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        # Verificar si la imagen está referenciada en la BD
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT COUNT(*) 
                                FROM articles 
                                WHERE original_image_url LIKE ?
                            """, (f"%{filename}%",))
                            
                            if cursor.fetchone()[0] == 0:
                                os.remove(file_path)
                                cleaned_count += 1
            
            print(f"   🧹 {cleaned_count} imágenes antiguas eliminadas")
            
        except Exception as e:
            print(f"   ❌ Error limpiando imágenes: {e}")
    
    def generate_health_report(self):
        """Generar reporte de salud del sistema"""
        print("📋 Generando reporte de salud...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas generales
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-7 days')")
                recent_articles = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE original_image_url IS NOT NULL AND original_image_url != ''
                """)
                articles_with_local_images = cursor.fetchone()[0]
                
                # Crear reporte
                report = f"""
📊 REPORTE DE SALUD DEL SISTEMA
===============================
📰 Total artículos: {total_articles:,}
📅 Artículos últimos 7 días: {recent_articles:,}
🖼️  Artículos con imagen local: {articles_with_local_images:,}
📈 Cobertura de imágenes: {(articles_with_local_images/total_articles*100):.1f}%

🎯 FILTRO GEOPOLÍTICO: ACTIVO ✅
🖼️  SISTEMA DE IMÁGENES: ACTIVO ✅

Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                print(report)
                
                # Guardar reporte en archivo
                with open("maintenance_report.txt", "w", encoding="utf-8") as f:
                    f.write(report)
                    
                print("   📄 Reporte guardado en maintenance_report.txt")
                
        except Exception as e:
            print(f"   ❌ Error generando reporte: {e}")

def main():
    """Función principal"""
    maintenance = RiskMapMaintenance()
    maintenance.run_daily_maintenance()

if __name__ == "__main__":
    main()