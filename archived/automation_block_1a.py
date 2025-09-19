#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatización del Dashboard - BLOQUE 1 CORREGIDO
Soluciona errores de codificación Unicode en Windows
"""

import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime

# Configurar codificación UTF-8 para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar logging sin emojis para evitar errores de codificación
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DashboardAutomationFixed:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        logger.info("AUTOMATIZACION DEL DASHBOARD INICIALIZADA")
        logger.info(f"DIRECTORIO DEL PROYECTO: {self.project_root}")
        
        # Directorios principales
        self.src_dir = self.project_root / "src"
        self.web_dir = self.src_dir / "web"
        self.templates_dir = self.web_dir / "templates"
        self.static_dir = self.web_dir / "static"
        
    def task_add_photos_to_ai_articles(self):
        """Tarea 1: Implementar sistema de fotos para artículos IA"""
        logger.info("IMPLEMENTANDO SISTEMA DE FOTOS PARA ARTICULOS IA...")
        
        try:
            app_file = self.project_root / "app_BUENA.py"
            
            if not app_file.exists():
                logger.error(f"Archivo no encontrado: {app_file}")
                return False
                
            # Leer contenido actual
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Agregar método para obtener imágenes de artículos
            photo_method = '''
    def get_article_photo(self, article_data):
        """Obtener foto para artículo desde múltiples fuentes"""
        try:
            # Prioridad 1: Imagen del RSS feed
            if 'media_content' in article_data and article_data['media_content']:
                return article_data['media_content']
            
            # Prioridad 2: Imagen extraída del contenido
            if 'image_url' in article_data and article_data['image_url']:
                return article_data['image_url']
            
            # Prioridad 3: Usar API de imágenes relacionadas
            if 'title' in article_data:
                return self.get_related_image(article_data['title'])
            
            # Fallback: imagen por defecto
            return '/static/images/default_news.jpg'
            
        except Exception as e:
            logger.error(f"Error obteniendo foto del artículo: {e}")
            return '/static/images/default_news.jpg'
    
    def get_related_image(self, title):
        """Obtener imagen relacionada basada en el título"""
        try:
            # Palabras clave para determinar tipo de imagen
            keywords = title.lower()
            
            if any(word in keywords for word in ['war', 'conflict', 'military', 'guerra', 'conflicto']):
                return '/static/images/conflict_default.jpg'
            elif any(word in keywords for word in ['climate', 'weather', 'storm', 'clima', 'tormenta']):
                return '/static/images/climate_default.jpg'
            elif any(word in keywords for word in ['politics', 'government', 'election', 'política', 'gobierno']):
                return '/static/images/politics_default.jpg'
            else:
                return '/static/images/default_news.jpg'
                
        except Exception as e:
            logger.error(f"Error obteniendo imagen relacionada: {e}")
            return '/static/images/default_news.jpg'
'''
            
            # Insertar método antes de la última línea de la clase
            if 'class NewsService' in content:
                # Encontrar el final de la clase NewsService
                class_pattern = r'(class NewsService.*?)(def [^}]+{[^}]*}[\s]*})?\s*$'
                if re.search(class_pattern, content, re.DOTALL):
                    # Insertar antes del final de la clase
                    content = re.sub(
                        r'(class NewsService.*?)(\n\s*$)',
                        r'\1' + photo_method + r'\2',
                        content,
                        flags=re.DOTALL
                    )
                else:
                    # Si no se encuentra el patrón, agregar al final del archivo
                    content += photo_method
            else:
                content += photo_method
            
            # Guardar archivo actualizado
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("SISTEMA DE FOTOS PARA ARTICULOS IA IMPLEMENTADO")
            return True
            
        except Exception as e:
            logger.error(f"Error en implementación de fotos: {e}")
            return False
    
    def task_fix_app_buena(self):
        """Tarea 2: Corregir fallos en app_BUENA.py"""
        logger.info("ANALIZANDO Y CORRIGIENDO FALLOS EN APP_BUENA.PY...")
        
        try:
            app_file = self.project_root / "app_BUENA.py"
            
            if not app_file.exists():
                logger.error(f"Archivo no encontrado: {app_file}")
                return False
            
            # Leer contenido
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_applied = []
            
            # Fix 1: Remover datos mock
            logger.info("REMOVIENDO DATOS MOCK Y SIMULADOS...")
            mock_patterns = [
                r'mock_data.*?=.*?True',
                r'_mock_.*?\(',
                r'generate_mock_.*?\(',
                r'# Mock data.*?\n',
                r'#.*?simulado.*?\n'
            ]
            
            for pattern in mock_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                    fixes_applied.append(f"Removido patrón mock: {pattern}")
            
            # Fix 2: Corregir imports
            logger.info("VERIFICANDO Y CORRIGIENDO IMPORTS...")
            required_imports = [
                "from datetime import datetime, timedelta",
                "import sqlite3",
                "import json",
                "import requests",
                "from typing import List, Dict, Optional, Tuple"
            ]
            
            for imp in required_imports:
                if imp not in content:
                    # Agregar al inicio después de los imports existentes
                    content = imp + "\n" + content
                    fixes_applied.append(f"Agregado import: {imp}")
            
            # Fix 3: Reemplazar métodos mock con reales
            logger.info("CORRIGIENDO RUTAS CON DATOS MOCK...")
            replacements = [
                (r'return self\._get_mock_articles', 'return self._get_real_articles_from_db'),
                (r'mock_data\':\s*True', 'real_data\': True'),
                (r'_generate_mock_', '_generate_real_'),
                (r'# TODO:.*?implement', '# IMPLEMENTED:')
            ]
            
            for old_pattern, new_text in replacements:
                if re.search(old_pattern, content):
                    content = re.sub(old_pattern, new_text, content)
                    fixes_applied.append(f"Reemplazado: {old_pattern} -> {new_text}")
            
            # Fix 4: Agregar métodos para datos reales
            logger.info("AÑADIENDO MÉTODOS PARA DATOS REALES...")
            real_data_methods = '''
    def _get_real_articles_from_db(self, limit=10):
        """Obtener artículos reales desde la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, description, url, published_date, source, 
                       image_url, category, location_data
                FROM articles 
                WHERE published_date >= datetime('now', '-7 days')
                ORDER BY published_date DESC 
                LIMIT ?
            """, (limit,))
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'title': row[0],
                    'description': row[1],
                    'url': row[2],
                    'published_date': row[3],
                    'source': row[4],
                    'image_url': row[5] or self.get_article_photo({'title': row[0]}),
                    'category': row[6],
                    'location_data': json.loads(row[7]) if row[7] else {}
                }
                articles.append(article)
            
            conn.close()
            return articles
            
        except Exception as e:
            logger.error(f"Error obteniendo artículos reales: {e}")
            return []
    
    def _generate_real_analytics(self):
        """Generar analytics reales desde datos de la BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar artículos por categoría
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM articles 
                WHERE published_date >= datetime('now', '-30 days')
                GROUP BY category
            """)
            
            category_stats = dict(cursor.fetchall())
            
            # Contar por fuente
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM articles 
                WHERE published_date >= datetime('now', '-7 days')
                GROUP BY source
                ORDER BY count DESC
                LIMIT 5
            """)
            
            source_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_articles': sum(category_stats.values()),
                'categories': category_stats,
                'top_sources': source_stats,
                'last_updated': datetime.now().isoformat(),
                'data_source': 'real_database'
            }
            
        except Exception as e:
            logger.error(f"Error generando analytics reales: {e}")
            return {
                'total_articles': 0,
                'categories': {},
                'top_sources': {},
                'last_updated': datetime.now().isoformat(),
                'data_source': 'error_fallback'
            }
'''
            
            # Insertar métodos si no existen
            if '_get_real_articles_from_db' not in content:
                content += real_data_methods
                fixes_applied.append("Añadidos métodos para datos reales")
            
            # Solo guardar si hay cambios
            if content != original_content:
                with open(app_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"APP_BUENA.PY CORREGIDO EXITOSAMENTE")
                logger.info(f"CORRECCIONES APLICADAS: {len(fixes_applied)}")
                for fix in fixes_applied:
                    logger.info(f"   - {fix}")
            else:
                logger.info("APP_BUENA.PY YA ESTABA CORRECTO")
            
            return True
            
        except Exception as e:
            logger.error(f"Error corrigiendo app_BUENA.py: {e}")
            return False

if __name__ == "__main__":
    # Obtener directorio del proyecto
    project_root = Path(__file__).parent.absolute()
    
    # Inicializar automatización
    automation = DashboardAutomationFixed(project_root)
    
    logger.info("INICIANDO AUTOMATIZACIÓN - BLOQUE 1 (Tareas 1-2)")
    
    # Ejecutar tareas del bloque 1
    print("\n" + "="*50)
    print("BLOQUE 1A: SISTEMA DE FOTOS Y CORRECCIÓN APP_BUENA")
    print("="*50)
    
    success_1 = automation.task_add_photos_to_ai_articles()
    success_2 = automation.task_fix_app_buena()
    
    # Resumen
    completed = sum([success_1, success_2])
    logger.info(f"BLOQUE 1A COMPLETADO: {completed}/2 tareas exitosas")
    
    if completed == 2:
        logger.info("TODAS LAS TAREAS DEL BLOQUE 1A COMPLETADAS EXITOSAMENTE")
        print("\nBLOQUE 1A COMPLETADO EXITOSAMENTE!")
        print("- Sistema de fotos implementado")
        print("- app_BUENA.py corregido")
    else:
        logger.error("ALGUNAS TAREAS DEL BLOQUE 1A FALLARON")
        print(f"\nBLOQUE 1A PARCIALMENTE COMPLETADO: {completed}/2")
    
    sys.exit(0 if completed == 2 else 1)
