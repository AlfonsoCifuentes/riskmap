#!/usr/bin/env python3
"""
Sistema de Limpieza y Optimización de Datos - RiskMap
======================================================
Limpia datos antiguos, comprime archivos y optimiza almacenamiento

Features:
- Archivado de artículos antiguos
- Limpieza de logs viejos
- Compresión de datos históricos
- Gestión de archivos temporales
- Reportes de espacio liberado
"""

import sqlite3
import json
import os
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

class DataCleaner:
    """Limpiador de datos y optimizador de almacenamiento"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db'):
        self.db_path = db_path
        self.archived_path = './data/archived'
        self.logs_path = './logs'
        self.temp_path = './temp'
        self.stats = {
            'articles_archived': 0,
            'logs_removed': 0,
            'temp_files_removed': 0,
            'space_freed_mb': 0.0
        }
    
    def archive_old_articles(self, days_old: int = 180) -> int:
        """Archivar artículos antiguos a archivo separado"""
        print(f"\n📦 Archivando artículos más antiguos de {days_old} días...")
        
        try:
            # Crear directorio de archivo si no existe
            Path(self.archived_path).mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Fecha límite
                cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

                # Obtener artículos antiguos
                cursor.execute("""
                SELECT * FROM unified_articles 
                WHERE created_at < ? 
                AND geopolitical_relevance = 0
                ORDER BY created_at ASC
            """, (cutoff_date,))
            
            old_articles = cursor.fetchall()
            
            if old_articles:
                # Guardar en archivo JSON comprimido
                archive_file = f"{self.archived_path}/articles_archive_{datetime.now().strftime('%Y%m%d')}.json.gz"
                
                # Obtener nombres de columnas
                cursor.execute("PRAGMA table_info(unified_articles)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Convertir a diccionarios
                articles_data = []
                for row in old_articles:
                    article = dict(zip(columns, row))
                    articles_data.append(article)
                
                # Comprimir y guardar
                with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                    json.dump(articles_data, f, indent=2, ensure_ascii=False)
                
                # Eliminar artículos archivados de la BD principal
                cursor.execute("""
                    DELETE FROM unified_articles 
                    WHERE created_at < ? 
                    AND geopolitical_relevance = 0
                """, (cutoff_date,))
                
                conn.commit()
                self.stats['articles_archived'] = len(old_articles)
                
                archive_size = os.path.getsize(archive_file) / (1024 * 1024)
                print(f"   ✅ {len(old_articles)} artículos archivados")
                print(f"   📁 Archivo: {archive_file}")
                print(f"   💾 Tamaño: {archive_size:.2f} MB")
            else:
                print(f"   ℹ️  No hay artículos para archivar")
            
            # with-context will close connection automatically
            return len(old_articles)
            
        except Exception as e:
            print(f"   ❌ Error archivando artículos: {e}")
            return 0
    
    def clean_old_logs(self, days_old: int = 30) -> int:
        """Limpiar logs antiguos"""
        print(f"\n🧹 Limpiando logs más antiguos de {days_old} días...")
        
        removed_count = 0
        space_freed = 0
        
        try:
            if not os.path.exists(self.logs_path):
                print("   ℹ️  Directorio de logs no existe")
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for filename in os.listdir(self.logs_path):
                file_path = os.path.join(self.logs_path, filename)
                
                if os.path.isfile(file_path):
                    # Obtener fecha de modificación
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if mod_time < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        space_freed += file_size
                        print(f"   🗑️  Eliminado: {filename}")
            
            if removed_count > 0:
                self.stats['logs_removed'] = removed_count
                space_mb = space_freed / (1024 * 1024)
                self.stats['space_freed_mb'] += space_mb
                print(f"   ✅ {removed_count} logs eliminados")
                print(f"   💾 Espacio liberado: {space_mb:.2f} MB")
            else:
                print("   ℹ️  No hay logs para eliminar")
            
            return removed_count
            
        except Exception as e:
            print(f"   ❌ Error limpiando logs: {e}")
            return 0
    
    def clean_temp_files(self) -> int:
        """Limpiar archivos temporales"""
        print(f"\n🧹 Limpiando archivos temporales...")
        
        removed_count = 0
        space_freed = 0
        
        try:
            # Limpiar directorio temp
            temp_patterns = [
                './temp',
                './temp_*',
                './__pycache__',
                './src/__pycache__',
                './src/**/__pycache__'
            ]
            
            for pattern in temp_patterns:
                from glob import glob
                for path in glob(pattern, recursive=True):
                    if os.path.isdir(path):
                        try:
                            dir_size = sum(
                                os.path.getsize(os.path.join(dirpath, filename))
                                for dirpath, _, filenames in os.walk(path)
                                for filename in filenames
                            )
                            shutil.rmtree(path)
                            removed_count += 1
                            space_freed += dir_size
                            print(f"   🗑️  Eliminado directorio: {path}")
                        except Exception as e:
                            print(f"   ⚠️  No se pudo eliminar {path}: {e}")
            
            # Limpiar archivos temporales sueltos
            temp_files = [
                'temp_satellite_*.jpg',
                '*.pyc',
                '*.log.tmp',
                '.DS_Store'
            ]
            
            from glob import glob
            for pattern in temp_files:
                for file_path in glob(pattern):
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        space_freed += file_size
                        print(f"   🗑️  Eliminado: {file_path}")
                    except Exception as e:
                        pass
            
            if removed_count > 0:
                self.stats['temp_files_removed'] = removed_count
                space_mb = space_freed / (1024 * 1024)
                self.stats['space_freed_mb'] += space_mb
                print(f"   ✅ {removed_count} archivos/directorios temporales eliminados")
                print(f"   💾 Espacio liberado: {space_mb:.2f} MB")
            else:
                print("   ℹ️  No hay archivos temporales para eliminar")
            
            return removed_count
            
        except Exception as e:
            print(f"   ❌ Error limpiando temporales: {e}")
            return 0
    
    def compress_database(self) -> Dict[str, Any]:
        """Comprimir y optimizar base de datos"""
        print(f"\n🗜️  Comprimiendo y optimizando base de datos...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:

                # Tamaño inicial
                initial_size = os.path.getsize(self.db_path)

                # VACUUM para desfragmentar y comprimir
                print("   🔧 Ejecutando VACUUM...")
                conn.execute("VACUUM")
            
                # ANALYZE para actualizar estadísticas
                print("   📊 Ejecutando ANALYZE...")
                conn.execute("ANALYZE")
            
                # with-context will close connection automatically
            
            # Tamaño final
            final_size = os.path.getsize(self.db_path)
            space_saved = (initial_size - final_size) / (1024 * 1024)
            
            if space_saved > 0:
                self.stats['space_freed_mb'] += space_saved
                print(f"   ✅ Base de datos optimizada")
                print(f"   💾 Espacio liberado: {space_saved:.2f} MB")
            else:
                print(f"   ℹ️  Base de datos ya estaba optimizada")
            
            return {
                'initial_size_mb': initial_size / (1024 * 1024),
                'final_size_mb': final_size / (1024 * 1024),
                'space_saved_mb': space_saved
            }
            
        except Exception as e:
            print(f"   ❌ Error comprimiendo BD: {e}")
            return {'error': str(e)}
    
    def analyze_disk_usage(self) -> Dict[str, Any]:
        """Analizar uso de disco por directorio"""
        print(f"\n📊 ANÁLISIS DE USO DE DISCO")
        print("=" * 60)
        
        directories = {
            'data': './data',
            'logs': './logs',
            'models': './models',
            'datasets': './datasets',
            'outputs': './outputs',
            'src': './src'
        }
        
        usage = {}
        
        for name, path in directories.items():
            if os.path.exists(path):
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(path)
                    for filename in filenames
                )
                size_mb = size / (1024 * 1024)
                usage[name] = size_mb
                print(f"   {name.upper():15} {size_mb:>10.2f} MB")
            else:
                usage[name] = 0
        
        total_mb = sum(usage.values())
        print(f"   {'TOTAL':15} {total_mb:>10.2f} MB")
        
        return usage
    
    def run_full_cleanup(self, 
                        archive_days: int = 180,
                        log_days: int = 30) -> Dict[str, Any]:
        """Ejecutar limpieza completa del sistema"""
        print("\n🧹 LIMPIEZA COMPLETA DEL SISTEMA")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # 1. Analizar uso inicial
        print("\n📊 USO DE DISCO INICIAL:")
        initial_usage = self.analyze_disk_usage()
        
        # 2. Archivar artículos antiguos
        self.archive_old_articles(archive_days)
        
        # 3. Limpiar logs
        self.clean_old_logs(log_days)
        
        # 4. Limpiar temporales
        self.clean_temp_files()
        
        # 5. Comprimir base de datos
        db_stats = self.compress_database()
        
        # 6. Analizar uso final
        print("\n📊 USO DE DISCO FINAL:")
        final_usage = self.analyze_disk_usage()
        
        # Calcular mejora total
        total_initial = sum(initial_usage.values())
        total_final = sum(final_usage.values())
        total_saved = total_initial - total_final
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ LIMPIEZA COMPLETADA")
        print(f"   Duración: {duration:.2f} segundos")
        print(f"   Artículos archivados: {self.stats['articles_archived']}")
        print(f"   Logs eliminados: {self.stats['logs_removed']}")
        print(f"   Archivos temporales: {self.stats['temp_files_removed']}")
        print(f"   💾 Espacio total liberado: {total_saved:.2f} MB")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'statistics': self.stats,
            'initial_usage_mb': initial_usage,
            'final_usage_mb': final_usage,
            'total_saved_mb': total_saved,
            'database_compression': db_stats
        }


def main():
    """Ejecutar limpieza completa"""
    cleaner = DataCleaner()
    
    # Ejecutar limpieza
    result = cleaner.run_full_cleanup(
        archive_days=180,  # Archivar artículos > 6 meses
        log_days=30        # Eliminar logs > 1 mes
    )
    
    # Guardar reporte
    report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte guardado en: {report_file}")


if __name__ == "__main__":
    main()
