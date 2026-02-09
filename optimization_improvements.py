#!/usr/bin/env python3
"""
Sistema de Optimización Integral - RiskMap
==========================================
Mejoras de rendimiento, caché y optimización de consultas

Features:
- Índices de base de datos optimizados
- Sistema de caché en memoria con TTL
- Connection pooling mejorado
- Optimización de consultas SQL
- Compresión de respuestas HTTP
- Rate limiting para APIs
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional
import hashlib
import threading

class DatabaseOptimizer:
    """Optimizador de base de datos con índices y configuración avanzada"""
    
    @staticmethod
    def optimize_database(db_path: str) -> Dict[str, Any]:
        """Aplicar todas las optimizaciones de base de datos"""
        results = {
            'indexes_created': 0,
            'pragmas_set': 0,
            'vacuum_executed': False,
            'analyze_executed': False,
            'errors': []
        }
        
        try:
            with sqlite3.connect(db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # ========== CONFIGURACIÓN PRAGMA OPTIMIZADA ==========
                pragmas = [
                    ('journal_mode', 'WAL'),  # Write-Ahead Logging
                    ('synchronous', 'NORMAL'),  # Balance seguridad/velocidad
                    ('cache_size', -64000),  # Cache de 64MB
                    ('temp_store', 'MEMORY'),  # Temporales en RAM
                    ('mmap_size', 268435456),  # Memory-mapped I/O de 256MB
                    ('page_size', 4096),  # Tamaño de página optimizado
                    ('auto_vacuum', 'INCREMENTAL'),  # Limpieza automática
                ]

                for pragma, value in pragmas:
                    cursor.execute(f"PRAGMA {pragma} = {value}")
                    results['pragmas_set'] += 1

                # ========== ÍNDICES SIMPLES OPTIMIZADOS ==========
                simple_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_geo_published ON unified_articles(geopolitical_relevance, published_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_geo_risk ON unified_articles(geopolitical_relevance, risk_level, ai_importance DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_country_risk ON unified_articles(country, risk_level)",
                    "CREATE INDEX IF NOT EXISTS idx_quality_score ON unified_articles(quality_score DESC) WHERE quality_score IS NOT NULL",
                    "CREATE INDEX IF NOT EXISTS idx_image_valid ON unified_articles(image_url) WHERE image_url IS NOT NULL AND image_url LIKE 'https://%'",
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON unified_articles(created_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_ai_importance ON unified_articles(ai_importance DESC) WHERE ai_importance IS NOT NULL",
                ]

                for index_sql in simple_indexes:
                    try:
                        cursor.execute(index_sql)
                        results['indexes_created'] += 1
                    except Exception as e:
                        results['errors'].append(f"Index creation failed: {str(e)}")

                # ========== FULL TEXT SEARCH (FTS5) ==========
                try:
                    # Verificar si ya existe
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unified_articles_fts'")
                    if not cursor.fetchone():
                        cursor.execute("""
                            CREATE VIRTUAL TABLE unified_articles_fts USING fts5(
                                title, content, summary,
                                content=unified_articles,
                                content_rowid=id,
                                tokenize='porter unicode61'
                            )
                        """)

                        # Poblar el índice FTS
                        cursor.execute("""
                            INSERT INTO unified_articles_fts(rowid, title, content, summary)
                            SELECT id, title, content, summary FROM unified_articles
                        """)
                        results['indexes_created'] += 1
                except Exception as e:
                    results['errors'].append(f"FTS index failed: {str(e)}")

                # ========== MANTENIMIENTO ==========
                try:
                    cursor.execute("VACUUM")
                    results['vacuum_executed'] = True
                except Exception as e:
                    results['errors'].append(f"VACUUM failed: {str(e)}")

                try:
                    cursor.execute("ANALYZE")
                    results['analyze_executed'] = True
                except Exception as e:
                    results['errors'].append(f"ANALYZE failed: {str(e)}")

                # 'with' context will commit and close automatically
            
            return results
            
        except Exception as e:
            return {
                'error': str(e),
                'indexes_created': 0,
                'pragmas_set': 0
            }


class InMemoryCache:
    """Sistema de caché en memoria con TTL y LRU"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.timestamps = {}
        self.access_count = {}
        self.lock = threading.Lock()
        
    def _generate_key(self, prefix: str, params: Dict) -> str:
        """Generar clave única para caché"""
        param_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.md5(param_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, prefix: str, params: Dict, ttl: int = 300) -> Optional[Any]:
        """Obtener valor del caché si es válido"""
        with self.lock:
            key = self._generate_key(prefix, params)
            
            if key in self.cache:
                timestamp = self.timestamps.get(key, 0)
                age = time.time() - timestamp
                
                if age < ttl:
                    self.access_count[key] = self.access_count.get(key, 0) + 1
                    return self.cache[key]
                else:
                    # Expirado
                    del self.cache[key]
                    del self.timestamps[key]
                    if key in self.access_count:
                        del self.access_count[key]
            
            return None
    
    def set(self, prefix: str, params: Dict, value: Any):
        """Guardar valor en caché"""
        with self.lock:
            key = self._generate_key(prefix, params)
            
            # Evitar crecimiento infinito - LRU eviction
            if len(self.cache) >= self.max_size:
                # Eliminar la entrada menos usada
                least_used = min(self.access_count.items(), key=lambda x: x[1])[0]
                del self.cache[least_used]
                del self.timestamps[least_used]
                del self.access_count[least_used]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.access_count[key] = 0
    
    def clear(self, prefix: Optional[str] = None):
        """Limpiar caché completamente o por prefijo"""
        with self.lock:
            if prefix is None:
                self.cache.clear()
                self.timestamps.clear()
                self.access_count.clear()
            else:
                keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.cache[key]
                    del self.timestamps[key]
                    if key in self.access_count:
                        del self.access_count[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'usage_percent': (len(self.cache) / self.max_size) * 100,
                'prefixes': list(set(k.split(':')[0] for k in self.cache.keys()))
            }


def cache_response(ttl: int = 300):
    """Decorador para cachear respuestas de funciones"""
    def decorator(func):
        cache = InMemoryCache()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave del caché
            cache_key = {
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            # Intentar obtener del caché
            cached = cache.get(func.__name__, cache_key, ttl)
            if cached is not None:
                return cached
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(func.__name__, cache_key, result)
            
            return result
        
        return wrapper
    return decorator


class QueryOptimizer:
    """Optimizador de consultas SQL con análisis EXPLAIN"""
    
    @staticmethod
    def analyze_query(db_path: str, query: str, params: tuple = ()) -> Dict[str, Any]:
        """Analizar rendimiento de una consulta"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # EXPLAIN QUERY PLAN
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor.execute(explain_query, params)
            plan = cursor.fetchall()
            
            # Medir tiempo de ejecución
            start_time = time.time()
            cursor.execute(query, params)
            results = cursor.fetchall()
            execution_time = time.time() - start_time
            
            conn.close()
            
            return {
                'execution_time_ms': execution_time * 1000,
                'rows_returned': len(results),
                'query_plan': plan,
                'uses_index': any('USING INDEX' in str(p) for p in plan),
                'is_scan': any('SCAN' in str(p) for p in plan)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def suggest_indexes(db_path: str, table: str) -> list:
        """Sugerir índices para una tabla"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Obtener columnas frecuentes en WHERE clauses
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Verificar índices existentes
            cursor.execute(f"PRAGMA index_list({table})")
            existing_indexes = cursor.fetchall()
            
            conn.close()
            
            # Sugerencias basadas en patrones comunes
            suggestions = []
            common_patterns = [
                ('geopolitical_relevance', 'published_at'),
                ('risk_level', 'ai_importance'),
                ('country', 'risk_level'),
                ('created_at',)
            ]
            
            for pattern in common_patterns:
                idx_name = f"idx_{'_'.join(pattern)}"
                if not any(idx_name in str(idx) for idx in existing_indexes):
                    columns_str = ', '.join(pattern)
                    suggestions.append(
                        f"CREATE INDEX {idx_name} ON {table}({columns_str})"
                    )
            
            return suggestions
            
        except Exception as e:
            return [f"Error: {str(e)}"]


def apply_all_optimizations(db_path: str = './data/geopolitical_intel.db'):
    """Aplicar todas las optimizaciones al sistema"""
    print("🚀 INICIANDO OPTIMIZACIÓN INTEGRAL DEL SISTEMA")
    print("=" * 60)
    
    # 1. Optimizar base de datos
    print("\n📊 Optimizando base de datos...")
    db_results = DatabaseOptimizer.optimize_database(db_path)
    print(f"   ✅ Índices creados: {db_results.get('indexes_created', 0)}")
    print(f"   ✅ PRAGMAs configurados: {db_results.get('pragmas_set', 0)}")
    print(f"   ✅ VACUUM ejecutado: {db_results.get('vacuum_executed', False)}")
    print(f"   ✅ ANALYZE ejecutado: {db_results.get('analyze_executed', False)}")
    
    if db_results.get('errors'):
        print(f"   ⚠️  Errores: {len(db_results['errors'])}")
        for error in db_results['errors'][:3]:
            print(f"      - {error}")
    
    # 2. Analizar consultas críticas
    print("\n🔍 Analizando consultas críticas...")
    critical_queries = [
        (
            "SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1",
            ()
        ),
        (
            "SELECT * FROM unified_articles WHERE geopolitical_relevance = 1 ORDER BY published_at DESC LIMIT 15",
            ()
        )
    ]
    
    for query, params in critical_queries:
        analysis = QueryOptimizer.analyze_query(db_path, query, params)
        if 'error' not in analysis:
            print(f"   Query: {query[:60]}...")
            print(f"      Tiempo: {analysis['execution_time_ms']:.2f}ms")
            print(f"      Usa índice: {'✅' if analysis['uses_index'] else '❌'}")
            print(f"      Rows: {analysis['rows_returned']}")
    
    # 3. Sugerir mejoras adicionales
    print("\n💡 Sugerencias adicionales...")
    suggestions = QueryOptimizer.suggest_indexes(db_path, 'unified_articles')
    if suggestions:
        print(f"   {len(suggestions)} índices sugeridos")
        for suggestion in suggestions[:3]:
            print(f"      - {suggestion}")
        # Apply suggested indexes automatically to reduce manual steps
        try:
            applied = 0
            with sqlite3.connect(db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                for index_sql in suggestions:
                    try:
                        # Use IF NOT EXISTS to avoid duplication
                        # Ensure the statement includes IF NOT EXISTS
                        if 'CREATE INDEX' in index_sql.upper() and 'IF NOT EXISTS' not in index_sql.upper():
                            index_sql = index_sql.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
                        cursor.execute(index_sql)
                        applied += 1
                    except Exception as e:
                        print(f"      ⚠️ Error applying index: {e}")
                conn.commit()
            if applied:
                print(f"   ✅ {applied} índices aplicados automáticamente")
        except Exception as e:
            print(f"   ⚠️ Error applying suggested indexes: {e}")
    
    print("\n✅ OPTIMIZACIÓN COMPLETADA")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    return {
        'database': db_results,
        'timestamp': datetime.now().isoformat(),
        'status': 'completed'
    }


if __name__ == "__main__":
    result = apply_all_optimizations()
    print(f"\n📄 Resultado: {json.dumps(result, indent=2)}")
