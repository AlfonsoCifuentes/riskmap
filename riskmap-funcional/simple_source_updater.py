#!/usr/bin/env python3
"""
Script simple para actualizar las fuentes de artículos RSS usando detección de patrones
"""

import sqlite3
import re
from urllib.parse import urlparse
from pathlib import Path

class SimpleSourceDetector:
    def __init__(self):
        """Inicializar el detector simple de fuentes"""
        
        # Mapeo de dominios a fuentes
        self.domain_sources = {
            # Fuentes internacionales principales
            'reuters.com': 'Reuters',
            'bbc.com': 'BBC News',
            'bbc.co.uk': 'BBC News',
            'cnn.com': 'CNN',
            'nytimes.com': 'The New York Times',
            'washingtonpost.com': 'The Washington Post',
            'theguardian.com': 'The Guardian',
            'ft.com': 'Financial Times',
            'wsj.com': 'Wall Street Journal',
            'bloomberg.com': 'Bloomberg',
            'ap.org': 'Associated Press',
            'apnews.com': 'Associated Press',
            'aljazeera.com': 'Al Jazeera',
            'aljazeera.net': 'Al Jazeera',
            
            # Fuentes españolas
            'elpais.com': 'El País',
            'elmundo.es': 'El Mundo',
            'abc.es': 'ABC',
            'lavanguardia.com': 'La Vanguardia',
            'elconfidencial.com': 'El Confidencial',
            'publico.es': 'Público',
            'rtve.es': 'RTVE',
            
            # Fuentes francesas
            'lemonde.fr': 'Le Monde',
            'lefigaro.fr': 'Le Figaro',
            'liberation.fr': 'Libération',
            
            # Fuentes alemanas
            'spiegel.de': 'Der Spiegel',
            'zeit.de': 'Die Zeit',
            'faz.net': 'Frankfurter Allgemeine',
            
            # Fuentes italianas
            'corriere.it': 'Corriere della Sera',
            'repubblica.it': 'La Repubblica',
            
            # Fuentes rusas
            'rt.com': 'RT News',
            'sputniknews.com': 'Sputnik News',
            'tass.com': 'TASS',
            'tass.ru': 'TASS',
            
            # Fuentes asiáticas
            'xinhuanet.com': 'Xinhua News',
            'scmp.com': 'South China Morning Post',
            'japantimes.co.jp': 'The Japan Times',
            'straitstimes.com': 'The Straits Times',
            
            # Fuentes latinoamericanas
            'clarin.com': 'Clarín',
            'lanacion.com.ar': 'La Nación',
            'folha.uol.com.br': 'Folha de S.Paulo',
            'globo.com': 'O Globo',
            'milenio.com': 'Milenio',
            
            # Agencias de noticias
            'efe.com': 'Agencia EFE',
            'afp.com': 'AFP',
            'dpa.com': 'DPA',
            'ansa.it': 'ANSA'
        }
        
        # Patrones de texto para detectar fuentes
        self.text_patterns = {
            'Reuters': [
                r'\breuters\b',
                r'\bthomson reuters\b',
                r'\(reuters\)',
                r'reuters\.com'
            ],
            'BBC News': [
                r'\bbbc\b',
                r'\bbbc news\b',
                r'\bbritish broadcasting\b',
                r'bbc\.com',
                r'bbc\.co\.uk'
            ],
            'CNN': [
                r'\bcnn\b',
                r'\bcable news network\b',
                r'cnn\.com'
            ],
            'Associated Press': [
                r'\bassociated press\b',
                r'\bap news\b',
                r'\b\(ap\)\b',
                r'apnews\.com'
            ],
            'Al Jazeera': [
                r'\bal jazeera\b',
                r'\baljazeera\b',
                r'aljazeera\.com',
                r'aljazeera\.net'
            ],
            'Financial Times': [
                r'\bfinancial times\b',
                r'\bft\.com\b',
                r'\b\(ft\)\b'
            ],
            'The Guardian': [
                r'\bguardian\b',
                r'\bthe guardian\b',
                r'theguardian\.com'
            ],
            'Bloomberg': [
                r'\bbloomberg\b',
                r'bloomberg\.com'
            ],
            'The New York Times': [
                r'\bnew york times\b',
                r'\bnytimes\b',
                r'nytimes\.com'
            ],
            'The Washington Post': [
                r'\bwashington post\b',
                r'\bwashingtonpost\b',
                r'washingtonpost\.com'
            ],
            'Wall Street Journal': [
                r'\bwall street journal\b',
                r'\bwsj\b',
                r'wsj\.com'
            ],
            'El País': [
                r'\bel país\b',
                r'\belpais\b',
                r'elpais\.com'
            ],
            'Le Monde': [
                r'\ble monde\b',
                r'lemonde\.fr'
            ],
            'Der Spiegel': [
                r'\bder spiegel\b',
                r'\bspiegel\b',
                r'spiegel\.de'
            ],
            'RT News': [
                r'\brt news\b',
                r'\brussia today\b',
                r'\brt\.com\b'
            ],
            'TASS': [
                r'\btass\b',
                r'tass\.com',
                r'tass\.ru'
            ],
            'Xinhua News': [
                r'\bxinhua\b',
                r'xinhuanet\.com'
            ],
            'Agencia EFE': [
                r'\bagencia efe\b',
                r'\befe\b',
                r'efe\.com'
            ]
        }
    
    def extract_domain_from_url(self, url):
        """Extraer dominio de URL"""
        try:
            if not url:
                return None
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remover prefijo www.
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def detect_source_from_url(self, url):
        """Detectar fuente desde URL"""
        domain = self.extract_domain_from_url(url)
        if domain and domain in self.domain_sources:
            return self.domain_sources[domain]
        return None
    
    def detect_source_from_text(self, text):
        """Detectar fuente desde texto usando patrones"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Buscar patrones de texto
        for source, patterns in self.text_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return source
        
        return None
    
    def analyze_article(self, title, content, url):
        """Analizar artículo completo para detectar fuente"""
        
        # Primero intentar con URL
        if url:
            source = self.detect_source_from_url(url)
            if source:
                return source
        
        # Luego intentar con texto
        full_text = f"{title or ''} {content or ''}"
        source = self.detect_source_from_text(full_text)
        if source:
            return source
        
        return None

def update_rss_sources(limit=None, dry_run=False):
    """Actualizar fuentes RSS con detección simple"""
    
    # Conectar a la base de datos
    db_path = Path(__file__).parent / 'data' / 'geopolitical_intel.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    detector = SimpleSourceDetector()
    
    try:
        # Obtener artículos con fuente "RSS Feed"
        query = """
            SELECT id, title, content, url, source 
            FROM articles 
            WHERE source = 'RSS Feed' OR source = 'RSS' OR source = 'Feed'
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        articles = cursor.fetchall()
        
        if not articles:
            print("✅ No se encontraron artículos con fuente 'RSS Feed' para procesar")
            return
        
        print(f"🔍 Encontrados {len(articles)} artículos con fuente RSS para procesar")
        
        updated_count = 0
        failed_count = 0
        
        for i, (article_id, title, content, url, current_source) in enumerate(articles, 1):
            try:
                print(f"\n📰 Procesando artículo {i}/{len(articles)}: {(title or '')[:60]}...")
                
                # Detectar la fuente real
                detected_source = detector.analyze_article(title, content, url)
                
                # Solo actualizar si se detectó una fuente válida
                if detected_source and detected_source != current_source:
                    print(f"   🎯 Fuente detectada: {detected_source}")
                    
                    if not dry_run:
                        # Actualizar en la base de datos
                        cursor.execute(
                            "UPDATE articles SET source = ? WHERE id = ?",
                            (detected_source, article_id)
                        )
                        updated_count += 1
                        print(f"   ✅ Actualizado: {current_source} → {detected_source}")
                    else:
                        print(f"   🔄 [DRY RUN] Cambiaría: {current_source} → {detected_source}")
                        updated_count += 1
                else:
                    print(f"   ⚠️  No se pudo detectar fuente específica")
                    failed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error procesando artículo {article_id}: {e}")
                failed_count += 1
                continue
        
        if not dry_run:
            # Confirmar cambios
            conn.commit()
            print(f"\n✅ Proceso completado:")
            print(f"   📊 Artículos actualizados: {updated_count}")
            print(f"   ❌ Artículos fallidos: {failed_count}")
        else:
            print(f"\n🔄 [DRY RUN] Resumen:")
            print(f"   📊 Artículos que se actualizarían: {updated_count}")
            print(f"   ❌ Artículos que fallarían: {failed_count}")
        
        # Mostrar estadísticas de fuentes después del procesamiento
        print(f"\n📈 Estadísticas de fuentes actualizadas:")
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM articles 
            WHERE source IS NOT NULL 
            GROUP BY source 
            ORDER BY count DESC 
            LIMIT 15
        """)
        
        for source, count in cursor.fetchall():
            print(f"   {source}: {count} artículos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def show_rss_stats():
    """Mostrar estadísticas de artículos RSS"""
    db_path = Path(__file__).parent / 'data' / 'geopolitical_intel.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Contar artículos con RSS Feed
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE source IN ('RSS Feed', 'RSS', 'Feed')
        """)
        rss_count = cursor.fetchone()[0]
        
        # Contar total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_count = cursor.fetchone()[0]
        
        print(f"📊 Estadísticas de fuentes RSS:")
        print(f"   📰 Total de artículos: {total_count}")
        print(f"   📡 Artículos con 'RSS Feed': {rss_count}")
        if total_count > 0:
            print(f"   📈 Porcentaje RSS: {(rss_count/total_count*100):.1f}%")
        
        # Mostrar ejemplos de artículos RSS
        cursor.execute("""
            SELECT id, title, url, created_at 
            FROM articles 
            WHERE source IN ('RSS Feed', 'RSS', 'Feed')
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        print(f"\n🔍 Ejemplos de artículos con fuente RSS:")
        for article_id, title, url, created_at in cursor.fetchall():
            print(f"   {article_id}: {(title or 'Sin título')[:50]}...")
            if url:
                print(f"      URL: {url}")
            print(f"      Fecha: {created_at}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Actualizar fuentes RSS con detección de patrones")
    parser.add_argument("--limit", type=int, help="Número máximo de artículos a procesar")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cambios sin aplicarlos")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas de fuentes RSS")
    
    args = parser.parse_args()
    
    if args.stats:
        show_rss_stats()
    else:
        print("🚀 Iniciando actualización de fuentes RSS con detección de patrones...")
        update_rss_sources(limit=args.limit, dry_run=args.dry_run)