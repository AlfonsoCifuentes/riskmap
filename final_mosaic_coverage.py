#!/usr/bin/env python3
"""
Asignador final de imágenes - Garantiza que TODOS los artículos del mosaico tengan imagen
"""

import sqlite3
import json
import requests
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re
import os
from urllib.parse import urlparse, urljoin
import hashlib
from bs4 import BeautifulSoup
import random

# Configurar logging sin emojis para evitar problemas de encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'final_image_assignment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class FinalImageAssigner:
    """Asignador final de imágenes - garantiza 100% de cobertura en mosaico"""
    
    def __init__(self):
        self.db_path = Path('data/geopolitical_intel.db')
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Imágenes de alta calidad categorizadas y validadas
        self.guaranteed_images = {
            'geopolitical': [
                'https://images.unsplash.com/photo-1589578527966-fdac0f44566c?w=1200&h=800&fit=crop&auto=format',  # Mundo
                'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=1200&h=800&fit=crop&auto=format',  # Global
                'https://images.unsplash.com/photo-1569098644584-210bcd375b59?w=1200&h=800&fit=crop&auto=format',  # Internacional
                'https://images.unsplash.com/photo-1568952433726-3896e3881c65?w=1200&h=800&fit=crop&auto=format',  # Diplomacia
                'https://images.unsplash.com/photo-1573164713714-d95e436ab8d6?w=1200&h=800&fit=crop&auto=format',  # Noticias
            ],
            'conflict': [
                'https://images.unsplash.com/photo-1541644387-0fce5b9c8224?w=1200&h=800&fit=crop&auto=format',  # Abstracto tensión
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1200&h=800&fit=crop&auto=format',  # Protestas
                'https://images.unsplash.com/photo-1473177027534-53d906e9abcb?w=1200&h=800&fit=crop&auto=format',  # Crisis
                'https://images.unsplash.com/photo-1562813733-b31f71025d54?w=1200&h=800&fit=crop&auto=format',  # Conflicto
                'https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?w=1200&h=800&fit=crop&auto=format',  # Tensión
            ],
            'politics': [
                'https://images.unsplash.com/photo-1574087449240-b3e4b56eb81c?w=1200&h=800&fit=crop&auto=format',  # Política
                'https://images.unsplash.com/photo-1591789612395-50e7e7e65cb8?w=1200&h=800&fit=crop&auto=format',  # Diplomacia
                'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1200&h=800&fit=crop&auto=format',  # Gobierno
                'https://images.unsplash.com/photo-1586829135343-132950070391?w=1200&h=800&fit=crop&auto=format',  # Instituciones
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1200&h=800&fit=crop&auto=format',  # Poder
            ],
            'economy': [
                'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=1200&h=800&fit=crop&auto=format',  # Economía
                'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=1200&h=800&fit=crop&auto=format',  # Mercados
                'https://images.unsplash.com/photo-1543872084-c7e4c0d6d026?w=1200&h=800&fit=crop&auto=format',  # Comercio
                'https://images.unsplash.com/photo-1580519542036-c47de6196ba5?w=1200&h=800&fit=crop&auto=format',  # Finanzas
                'https://images.unsplash.com/photo-1565843708714-2671dbdae37c?w=1200&h=800&fit=crop&auto=format',  # Trading
            ],
            'technology': [
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=800&fit=crop&auto=format',  # Tech
                'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=800&fit=crop&auto=format',  # Cyber
                'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=1200&h=800&fit=crop&auto=format',  # Digital
                'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=1200&h=800&fit=crop&auto=format',  # Innovación
                'https://images.unsplash.com/photo-1551434678-e076c223a692?w=1200&h=800&fit=crop&auto=format',  # Tech global
            ]
        }
    
    def categorize_article(self, title: str, content: str = "") -> str:
        """Categorizar artículo para asignar imagen apropiada"""
        text = f"{title} {content}".lower()
        
        # Palabras clave por categoría (más extensas)
        categories = {
            'conflict': [
                'war', 'guerra', 'conflict', 'violence', 'attack', 'bomb', 'militar', 'army', 'fight', 'batalla',
                'israel', 'gaza', 'ukraine', 'russia', 'palestin', 'syrian', 'afghanistan', 'iraq', 'iran',
                'sanction', 'crisis', 'tension', 'dispute', 'clash', 'combat', 'weapon', 'missile', 'drone',
                'hostage', 'terrorist', 'rebel', 'insurgent', 'coup', 'invasion', 'occupation'
            ],
            'politics': [
                'president', 'presidente', 'government', 'gobierno', 'politics', 'political', 'politico',
                'election', 'vote', 'congress', 'senate', 'minister', 'trump', 'biden', 'harris', 'putin',
                'diplomatic', 'embassy', 'ambassador', 'treaty', 'negotiation', 'summit', 'policy',
                'administration', 'cabinet', 'parliament', 'legislature', 'senator', 'representative'
            ],
            'economy': [
                'economy', 'economic', 'economia', 'economico', 'trade', 'market', 'tariff', 'inflation',
                'gdp', 'comercio', 'mercado', 'arancel', 'stock', 'financial', 'bank', 'currency',
                'dollar', 'euro', 'yuan', 'price', 'cost', 'budget', 'debt', 'investment', 'business',
                'corporate', 'company', 'revenue', 'profit', 'loss', 'growth', 'recession'
            ],
            'technology': [
                'technology', 'tech', 'cyber', 'digital', 'internet', 'ai', 'artificial', 'computer',
                'tecnologia', 'ciberseguridad', 'data', 'software', 'hardware', 'innovation', 'startup',
                'silicon', 'algorithm', 'blockchain', 'cryptocurrency', 'cloud', 'platform', 'app'
            ]
        }
        
        # Contar matches por categoría
        scores = {}
        for category, keywords in categories.items():
            scores[category] = sum(1 for keyword in keywords if keyword in text)
        
        # Retornar categoría con más matches
        if any(scores.values()):
            best_category = max(scores, key=scores.get)
            # Si es muy bajo el score, usar geopolitical como fallback
            if scores[best_category] < 2:
                return 'geopolitical'
            return best_category
        
        return 'geopolitical'
    
    def download_guaranteed_image(self, image_url: str, article_id: int) -> Optional[str]:
        """Descargar imagen garantizada desde URL confiable"""
        try:
            # Añadir parámetros para garantizar descarga
            if '?' in image_url:
                image_url += '&q=80&fm=jpg'
            else:
                image_url += '?q=80&fm=jpg'
            
            response = requests.get(image_url, headers=self.headers, timeout=30, stream=True)
            if response.status_code == 200:
                # Generar nombre único
                url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
                extension = '.jpg'
                
                filename = f"mosaic_{article_id}_{url_hash}{extension}"
                filepath = self.images_dir / filename
                
                # Descargar imagen
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verificar que se descargó correctamente
                if filepath.exists() and filepath.stat().st_size > 5000:  # Al menos 5KB
                    logger.info(f"Imagen garantizada descargada: {filename}")
                    return str(filepath)
                else:
                    filepath.unlink(missing_ok=True)
                    logger.warning(f"Imagen descargada demasiado pequeña: {filename}")
                    
        except Exception as e:
            logger.warning(f"Error descargando imagen garantizada {image_url}: {e}")
        
        return None
    
    def assign_guaranteed_image(self, article_id: int, title: str, content: str = "") -> Optional[str]:
        """Asignar imagen garantizada según categoría del artículo"""
        category = self.categorize_article(title, content)
        images = self.guaranteed_images.get(category, self.guaranteed_images['geopolitical'])
        
        # Intentar con múltiples imágenes de la categoría hasta conseguir una
        for image_url in images:
            logger.info(f"Intentando imagen garantizada categoria '{category}': {image_url}")
            downloaded_path = self.download_guaranteed_image(image_url, article_id)
            if downloaded_path:
                return downloaded_path
            time.sleep(1)  # Pausa entre intentos
        
        # Si falla la categoría específica, intentar con geopolitical
        if category != 'geopolitical':
            logger.info(f"Fallback a categoria geopolitical para articulo {article_id}")
            for image_url in self.guaranteed_images['geopolitical']:
                downloaded_path = self.download_guaranteed_image(image_url, article_id)
                if downloaded_path:
                    return downloaded_path
                time.sleep(1)
        
        return None
    
    def ensure_complete_mosaic_coverage(self):
        """Garantizar que TODOS los artículos del mosaico tengan imagen"""
        
        if not self.db_path.exists():
            print("ERROR: Base de datos no encontrada")
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        print("ASIGNACION FINAL DE IMAGENES - COBERTURA 100%")
        print("=" * 60)
        
        # Obtener TODOS los artículos de mosaico sin imagen
        cursor.execute('''
            SELECT id, title, url, risk_level, summary
            FROM articles 
            WHERE risk_level IN ('medium', 'high')
            AND (image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%")
            ORDER BY 
                CASE 
                    WHEN risk_level = 'high' THEN 1
                    WHEN risk_level = 'medium' THEN 2
                    ELSE 3
                END,
                created_at DESC
        ''')
        
        articles_without_images = cursor.fetchall()
        total_articles = len(articles_without_images)
        
        print(f"Articulos de mosaico pendientes: {total_articles}")
        
        if total_articles == 0:
            print("PERFECTO: Todos los articulos del mosaico ya tienen imagen!")
            conn.close()
            return
        
        print(f"Asignando imagenes garantizadas a {total_articles} articulos...")
        print("-" * 60)
        
        success_count = 0
        start_time = time.time()
        
        for i, (article_id, title, url, risk_level, summary) in enumerate(articles_without_images, 1):
            print(f"[{i}/{total_articles}] ID {article_id} [{risk_level.upper()}]")
            print(f"Titulo: {title[:60]}...")
            
            # Asignar imagen garantizada
            content = summary or ""
            image_path = self.assign_guaranteed_image(article_id, title, content)
            
            if image_path:
                print("  EXITO: Imagen garantizada asignada")
                
                # Actualizar base de datos
                try:
                    cursor.execute(
                        'UPDATE articles SET image_url = ? WHERE id = ?',
                        (image_path, article_id)
                    )
                    conn.commit()
                    success_count += 1
                    logger.info(f"Imagen garantizada asignada al articulo {article_id}")
                except Exception as e:
                    logger.error(f"Error actualizando BD para articulo {article_id}: {e}")
            else:
                print("  ERROR: No se pudo asignar imagen garantizada")
            
            # Pausa entre asignaciones
            time.sleep(0.5)
            
            # Progreso cada 5 artículos
            if i % 5 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed * 60 if elapsed > 0 else 0
                print(f"Progreso: {i}/{total_articles} ({success_count} exitosos) - {rate:.1f} art/min")
                print()
        
        conn.close()
        
        # Reporte final
        elapsed_total = time.time() - start_time
        success_rate = (success_count / total_articles * 100) if total_articles > 0 else 0
        
        print("=" * 60)
        print("ASIGNACION FINAL COMPLETADA:")
        print(f"  Total procesados: {total_articles}")
        print(f"  Exitosos: {success_count} ({success_rate:.1f}%)")
        print(f"  Tiempo total: {elapsed_total/60:.1f} minutos")
        if total_articles > 0:
            print(f"  Velocidad promedio: {total_articles/(elapsed_total/60):.1f} articulos/minuto")
        print("=" * 60)
        
        return success_count, total_articles

    def verify_final_coverage(self):
        """Verificar cobertura final del mosaico"""
        
        if not self.db_path.exists():
            print("ERROR: Base de datos no encontrada")
            return 0, 0, 0
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        print("VERIFICACION FINAL DE COBERTURA")
        print("=" * 40)
        
        # Los 150 artículos de riesgo medio/alto más recientes (mosaico completo)
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            )
        ''')
        total_mosaic = cursor.fetchone()[0]
        
        # Los que tienen imagen
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            ) WHERE image_url IS NOT NULL AND image_url != "" 
            AND image_url NOT LIKE "%placeholder%" AND image_url NOT LIKE "%picsum%"
        ''')
        with_images = cursor.fetchone()[0]
        
        without_images = total_mosaic - with_images
        coverage = (with_images / total_mosaic * 100) if total_mosaic > 0 else 0
        
        print(f"MOSAICO COMPLETO (150 articulos recientes):")
        print(f"  Total articulos: {total_mosaic}")
        print(f"  Con imagen: {with_images}")
        print(f"  Sin imagen: {without_images}")
        print(f"  Cobertura: {coverage:.1f}%")
        
        if coverage >= 100:
            print("  PERFECTO: Cobertura completa del mosaico!")
        elif coverage >= 95:
            print("  EXCELENTE: Cobertura casi completa")
        elif coverage >= 90:
            print("  MUY BIEN: Muy buena cobertura")
        elif coverage >= 80:
            print("  BIEN: Buena cobertura")
        else:
            print("  ATENCION: Cobertura insuficiente")
        
        # Distribución por categorías de riesgo
        cursor.execute('''
            SELECT 
                risk_level,
                COUNT(*) as total,
                COUNT(CASE WHEN image_url IS NOT NULL AND image_url != "" 
                          AND image_url NOT LIKE "%placeholder%" AND image_url NOT LIKE "%picsum%" 
                          THEN 1 END) as with_image
            FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            )
            GROUP BY risk_level
            ORDER BY 
                CASE 
                    WHEN risk_level = 'high' THEN 1
                    WHEN risk_level = 'medium' THEN 2
                    ELSE 3
                END
        ''')
        
        risk_stats = cursor.fetchall()
        
        print("\nCOBERTURA POR NIVEL DE RIESGO:")
        for risk_level, total, with_image in risk_stats:
            coverage_pct = (with_image / total * 100) if total > 0 else 0
            print(f"  {risk_level.upper()}: {with_image}/{total} ({coverage_pct:.1f}%)")
        
        conn.close()
        
        return coverage, with_images, without_images

def main():
    """Función principal"""
    assigner = FinalImageAssigner()
    
    print("ASIGNADOR FINAL DE IMAGENES - COBERTURA 100% GARANTIZADA")
    print("=" * 70)
    
    # 1. Verificar estado actual
    coverage, with_images, without_images = assigner.verify_final_coverage()
    
    if coverage >= 100:
        print("\nPERFECTO: Todos los articulos del mosaico ya tienen imagen!")
        return
    
    # 2. Confirmar procesamiento
    print(f"\nAsignar imagenes garantizadas a {without_images} articulos restantes? (y/N): ", end="")
    try:
        confirm = input().lower().strip()
        if confirm != 'y':
            print("Procesamiento cancelado")
            return
    except KeyboardInterrupt:
        print("\nProcesamiento cancelado por el usuario")
        return
    
    # 3. Asignar imágenes garantizadas
    success, total = assigner.ensure_complete_mosaic_coverage()
    
    # 4. Verificar resultado final
    print("\nVerificando cobertura final...")
    final_coverage, final_with, final_without = assigner.verify_final_coverage()
    
    print(f"\nRESUMEN COMPLETO:")
    print(f"  Cobertura inicial: {coverage:.1f}%")
    print(f"  Cobertura final: {final_coverage:.1f}%")
    print(f"  Mejora: +{final_coverage - coverage:.1f}%")
    print(f"  Articulos procesados: {total}")
    print(f"  Exitosos: {success}")
    
    if final_coverage >= 100:
        print("  MISION CUMPLIDA: Cobertura 100% del mosaico!")
    else:
        print(f"  Pendientes: {final_without} articulos")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
