#!/usr/bin/env python3
"""
Script para limpiar artículos deportivos existentes de la base de datos
"""

import sqlite3
import re
import json
import logging
from pathlib import Path
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportsArticleCleaner:
    """Limpia artículos deportivos de la base de datos."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Patrones para identificar contenido deportivo
        self.sports_patterns = [
            # Sports - English
            r'\bsports?\b', r'\bfootball\b', r'\bbasketball\b', r'\bsoccer\b',
            r'\bbaseball\b', r'\btennis\b', r'\bgolf\b', r'\bhockey\b',
            r'\bvolleyball\b', r'\bswimming\b', r'\bathletics\b', r'\bgymnastics\b',
            r'\boxing\b', r'\bwrestling\b', r'\bmma\b', r'\bufc\b',
            r'\bolympics?\b', r'\bworld cup\b', r'\bchampionship\b(?!.*political)',
            r'\bteam\b.*\b(wins?|lost?|defeats?|victory|champion)\b',
            r'\bplayer\b', r'\bcoach\b', r'\bstadium\b', r'\bmatch\b(?!.*diplomatic)',
            r'\btournament\b', r'\bleague\b', r'\bseason\b(?!.*political)',
            
            # Sports - Spanish
            r'\bdeporte\b', r'\bfútbol\b', r'\bbaloncesto\b', r'\btenis\b',
            r'\bgolf\b', r'\bjockey\b', r'\bvoleibol\b', r'\bnatación\b',
            r'\batletismo\b', r'\bgimnasia\b', r'\bbox\b', r'\blucha\b',
            r'\bolímpicos?\b', r'\bmundial\b(?!.*político)', r'\bcampeonato\b(?!.*político)',
            r'\bequipo\b.*\b(gana|ganó|pierde|perdió|derrota|victoria|campeón)\b',
            r'\bjugador\b', r'\bentrenador\b', r'\bestadio\b', r'\bpartido\b(?!.*político)',
            r'\btorneo\b', r'\bliga\b', r'\btemporada\b(?!.*política)',
            
            # Sports - French
            r'\bsport\b', r'\bfootball\b', r'\bbasket\b', r'\btennis\b',
            r'\bgolf\b', r'\bhockey\b', r'\bvolley\b', r'\bnatation\b',
            r'\bathlétisme\b', r'\bgymnastique\b', r'\bbox\b', r'\blutte\b',
            r'\bolympiques?\b', r'\bmondial\b(?!.*politique)', r'\bchampionnat\b(?!.*politique)',
            r'\béquipe\b.*\b(gagne|gagné|perd|perdu|défaite|victoire|champion)\b',
            r'\bjoueur\b', r'\bentraîneur\b', r'\bstade\b', r'\bmatch\b(?!.*diplomatique)',
            r'\btournoi\b', r'\bligue\b', r'\bsaison\b(?!.*politique)',
            
            # Sports - German
            r'\bsport\b', r'\bfußball\b', r'\bbasketball\b', r'\btennis\b',
            r'\bgolf\b', r'\bhockey\b', r'\bvolleyball\b', r'\bschwimmen\b',
            r'\bleichtathletik\b', r'\bturnen\b', r'\bbox\b', r'\bringen\b',
            r'\bolympische?\b', r'\bweltmeisterschaft\b(?!.*politisch)',
            r'\bmannschaft\b.*\b(gewinnt|gewonnen|verliert|verloren|niederlage|sieg|meister)\b',
            r'\bspieler\b', r'\btrainer\b', r'\bstadion\b', r'\bspiel\b(?!.*diplomatisch)',
            r'\bturnier\b', r'\bliga\b', r'\bsaison\b(?!.*politisch)',
        ]
        
        # Palabras clave específicas de deportes que son muy indicativas
        self.strong_sports_keywords = [
            'fifa', 'uefa', 'nba', 'nfl', 'mlb', 'nhl', 'premier league',
            'champions league', 'la liga', 'bundesliga', 'serie a',
            'real madrid', 'barcelona', 'manchester', 'liverpool',
            'bayern munich', 'juventus', 'psg', 'chelsea',
            'arsenal', 'tottenham', 'atletico', 'valencia',
            'sevilla', 'villarreal', 'athletic bilbao',
            'messi', 'ronaldo', 'neymar', 'mbappe', 'haaland',
            'benzema', 'lewandowski', 'salah', 'kane', 'de bruyne'
        ]
    
    def get_db_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def is_sports_article(self, title: str, content: str) -> bool:
        """Determina si un artículo es sobre deportes."""
        text = f"{title} {content}".lower()
        
        # Verificar palabras clave fuertes de deportes
        for keyword in self.strong_sports_keywords:
            if keyword.lower() in text:
                return True
        
        # Contar coincidencias de patrones deportivos
        matches = 0
        for pattern in self.sports_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        # Si hay 2 o más coincidencias, es probable que sea deportes
        return matches >= 2
    
    def find_sports_articles(self) -> List[Dict]:
        """Encuentra artículos deportivos en la base de datos."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los artículos
        cursor.execute('''
            SELECT id, title, content, url, source, created_at
            FROM articles
            ORDER BY created_at DESC
        ''')
        
        articles = cursor.fetchall()
        sports_articles = []
        
        logger.info(f"Analizando {len(articles)} artículos...")
        
        for article in articles:
            title = article['title'] or ''
            content = article['content'] or ''
            
            if self.is_sports_article(title, content):
                sports_articles.append({
                    'id': article['id'],
                    'title': title,
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'url': article['url'],
                    'source': article['source'],
                    'created_at': article['created_at']
                })
        
        conn.close()
        return sports_articles
    
    def delete_sports_articles(self, article_ids: List[int]) -> int:
        """Elimina artículos deportivos de la base de datos."""
        if not article_ids:
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Eliminar datos procesados relacionados
            placeholders = ','.join(['?' for _ in article_ids])
            cursor.execute(f'''
                DELETE FROM processed_data 
                WHERE article_id IN ({placeholders})
            ''', article_ids)
            
            processed_deleted = cursor.rowcount
            logger.info(f"Eliminados {processed_deleted} registros de processed_data")
            
            # Eliminar artículos
            cursor.execute(f'''
                DELETE FROM articles 
                WHERE id IN ({placeholders})
            ''', article_ids)
            
            articles_deleted = cursor.rowcount
            logger.info(f"Eliminados {articles_deleted} artículos")
            
            conn.commit()
            return articles_deleted
            
        except Exception as e:
            logger.error(f"Error eliminando artículos: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def clean_sports_articles(self, dry_run: bool = True) -> Dict:
        """Limpia artículos deportivos de la base de datos."""
        logger.info("Iniciando limpieza de artículos deportivos...")
        
        # Encontrar artículos deportivos
        sports_articles = self.find_sports_articles()
        
        logger.info(f"Encontrados {len(sports_articles)} artículos deportivos")
        
        if not sports_articles:
            return {'found': 0, 'deleted': 0, 'dry_run': dry_run}
        
        # Mostrar algunos ejemplos
        logger.info("Ejemplos de artículos deportivos encontrados:")
        for i, article in enumerate(sports_articles[:5]):
            logger.info(f"  {i+1}. [{article['source']}] {article['title']}")
        
        if len(sports_articles) > 5:
            logger.info(f"  ... y {len(sports_articles) - 5} más")
        
        deleted_count = 0
        if not dry_run:
            # Eliminar artículos deportivos
            article_ids = [article['id'] for article in sports_articles]
            deleted_count = self.delete_sports_articles(article_ids)
            logger.info(f"Eliminados {deleted_count} artículos deportivos")
        else:
            logger.info("Modo dry_run: no se eliminaron artículos")
        
        return {
            'found': len(sports_articles),
            'deleted': deleted_count,
            'dry_run': dry_run,
            'articles': sports_articles[:10]  # Primeros 10 para revisión
        }
    
    def update_category_for_sports(self) -> int:
        """Actualiza la categoría de artículos deportivos existentes."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Obtener artículos sin categoría o con categoría general
        cursor.execute('''
            SELECT a.id, a.title, a.content, pd.id as pd_id
            FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE pd.category IS NULL OR pd.category = 'general_news'
            ORDER BY a.created_at DESC
        ''')
        
        articles = cursor.fetchall()
        updated_count = 0
        
        logger.info(f"Revisando {len(articles)} artículos para actualizar categorías...")
        
        for article in articles:
            title = article['title'] or ''
            content = article['content'] or ''
            
            if self.is_sports_article(title, content):
                if article['pd_id']:
                    # Actualizar categoría existente
                    cursor.execute('''
                        UPDATE processed_data 
                        SET category = 'sports_entertainment'
                        WHERE id = ?
                    ''', (article['pd_id'],))
                else:
                    # Crear registro de processed_data
                    cursor.execute('''
                        INSERT INTO processed_data (
                            article_id, summary, category, keywords, sentiment, entities
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        article['id'],
                        content[:300] + '...' if len(content) > 300 else content,
                        'sports_entertainment',
                        json.dumps(['sports', 'entertainment']),
                        0.0,
                        json.dumps(['sports_organization'])
                    ))
                
                updated_count += 1
                logger.info(f"Actualizado artículo deportivo: {title[:50]}...")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Actualizadas {updated_count} categorías de artículos deportivos")
        return updated_count

def main():
    """Función principal."""
    # Ruta de la base de datos
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
    
    # Verificar que existe la base de datos
    if not Path(DB_PATH).exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return
    
    # Crear limpiador
    cleaner = SportsArticleCleaner(DB_PATH)
    
    # Opción 1: Solo identificar artículos deportivos (dry run)
    logger.info("=== MODO DRY RUN: Identificando artículos deportivos ===")
    result = cleaner.clean_sports_articles(dry_run=True)
    
    print(f"\nResultados del análisis:")
    print(f"- Artículos deportivos encontrados: {result['found']}")
    print(f"- Modo dry run: {result['dry_run']}")
    
    if result['found'] > 0:
        print(f"\nEjemplos de artículos deportivos:")
        for i, article in enumerate(result['articles']):
            print(f"  {i+1}. [{article['source']}] {article['title']}")
        
        # Preguntar si eliminar
        response = input(f"\n¿Desea eliminar los {result['found']} artículos deportivos? (s/N): ")
        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            logger.info("=== ELIMINANDO ARTÍCULOS DEPORTIVOS ===")
            delete_result = cleaner.clean_sports_articles(dry_run=False)
            print(f"Eliminados {delete_result['deleted']} artículos deportivos")
        else:
            print("No se eliminaron artículos")
    
    # Opción 2: Actualizar categorías de artículos deportivos existentes
    response = input("\n¿Desea actualizar las categorías de artículos deportivos existentes? (s/N): ")
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        logger.info("=== ACTUALIZANDO CATEGORÍAS ===")
        updated = cleaner.update_category_for_sports()
        print(f"Actualizadas {updated} categorías de artículos deportivos")

if __name__ == "__main__":
    main()