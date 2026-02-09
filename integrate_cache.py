#!/usr/bin/env python3
"""
Script de Integración Rápida - Sistema de Caché en RISKMAP
===========================================================
Integra el sistema de caché en los endpoints API de RISKMAP.py

Este script:
1. Lee RISKMAP.py
2. Agrega imports del sistema de caché
3. Integra decoradores @cached en endpoints clave
4. Crea backup antes de modificar
"""

import re
import shutil
from datetime import datetime
from pathlib import Path


class CacheIntegrator:
    """Integrador de sistema de caché en RISKMAP"""
    
    def __init__(self, app_file: str = 'RISKMAP.py'):
        self.app_file = app_file
        self.backup_file = f"{app_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_backup(self):
        """Crear backup del archivo original"""
        print(f"📦 Creando backup: {self.backup_file}")
        shutil.copy(self.app_file, self.backup_file)
        print(f"   ✅ Backup creado exitosamente")
    
    def read_file(self) -> str:
        """Leer contenido del archivo"""
        with open(self.app_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, content: str):
        """Escribir contenido al archivo"""
        with open(self.app_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def add_cache_import(self, content: str) -> str:
        """Agregar import del sistema de caché"""
        print("\n📝 Agregando imports de caché...")
        
        # Buscar la última línea de imports
        import_pattern = r'(^import .*$|^from .* import .*$)'
        imports = list(re.finditer(import_pattern, content, re.MULTILINE))
        
        if not imports:
            print("   ⚠️  No se encontraron imports, agregando al inicio")
            cache_import = """
# Sistema de Caché Integrado
try:
    from optimization_improvements import InMemoryCache
    CACHE_AVAILABLE = True
    # Crear instancia global de caché
    api_cache = InMemoryCache(max_size=200, default_ttl=300)  # 5 minutos TTL
except ImportError:
    print("⚠️  Sistema de caché no disponible")
    CACHE_AVAILABLE = False
    # Mock cache para evitar errores
    class MockCache:
        def cached(self, ttl=300):
            def decorator(func):
                return func
            return decorator
    api_cache = MockCache()

"""
            return cache_import + content
        
        # Insertar después del último import
        last_import = imports[-1]
        insert_pos = last_import.end()
        
        cache_import = """

# Sistema de Caché Integrado
try:
    from optimization_improvements import InMemoryCache
    CACHE_AVAILABLE = True
    # Crear instancia global de caché
    api_cache = InMemoryCache(max_size=200, default_ttl=300)  # 5 minutos TTL
except ImportError:
    print("⚠️  Sistema de caché no disponible")
    CACHE_AVAILABLE = False
    # Mock cache para evitar errores
    class MockCache:
        def cached(self, ttl=300):
            def decorator(func):
                return func
            return decorator
    api_cache = MockCache()
"""
        
        new_content = content[:insert_pos] + cache_import + content[insert_pos:]
        print("   ✅ Imports agregados")
        return new_content
    
    def add_cache_to_endpoints(self, content: str) -> str:
        """Agregar decoradores @cached a endpoints API"""
        print("\n🔧 Agregando decoradores de caché a endpoints...")
        
        # Patrones de endpoints a cachear
        endpoints_to_cache = [
            {
                'name': 'api_articles',
                'pattern': r'(    def api_articles\(self\):)',
                'ttl': 300,  # 5 minutos
                'description': 'Lista de artículos'
            },
            {
                'name': 'api_hero_article',
                'pattern': r'(    def api_hero_article\(self\):)',
                'ttl': 600,  # 10 minutos
                'description': 'Artículo principal'
            },
            {
                'name': 'api_articles_deduplicated',
                'pattern': r'(    def api_articles_deduplicated\(self\):)',
                'ttl': 300,
                'description': 'Artículos sin duplicados'
            },
            {
                'name': 'api_geopolitical_stats',
                'pattern': r'(    def api_geopolitical_stats\(self\):)',
                'ttl': 900,  # 15 minutos
                'description': 'Estadísticas geopolíticas'
            },
            {
                'name': 'api_risk_map_data',
                'pattern': r'(    def api_risk_map_data\(self\):)',
                'ttl': 600,
                'description': 'Datos de mapa de riesgo'
            },
            {
                'name': 'api_conflict_zones',
                'pattern': r'(    def api_conflict_zones\(self\):)',
                'ttl': 1800,  # 30 minutos
                'description': 'Zonas de conflicto'
            },
            {
                'name': 'api_gpr_index',
                'pattern': r'(    def api_gpr_index\(self\):)',
                'ttl': 3600,  # 1 hora
                'description': 'Índice GPR'
            },
            {
                'name': 'api_satellite_alerts',
                'pattern': r'(    def api_satellite_alerts\(self\):)',
                'ttl': 600,
                'description': 'Alertas satelitales'
            }
        ]
        
        modified_count = 0
        
        for endpoint in endpoints_to_cache:
            pattern = endpoint['pattern']
            matches = list(re.finditer(pattern, content))
            
            if matches:
                match = matches[0]
                # Verificar si ya tiene decorador de caché
                before_text = content[max(0, match.start() - 100):match.start()]
                
                if '@api_cache.cached' not in before_text and '@cached' not in before_text:
                    # Agregar decorador antes del método
                    decorator = f"        @api_cache.cached(ttl={endpoint['ttl']})  # Cache: {endpoint['description']}\n"
                    
                    # Buscar el inicio de la línea (respetando indentación)
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    
                    content = content[:line_start] + decorator + content[line_start:]
                    modified_count += 1
                    print(f"   ✅ Caché agregado a: {endpoint['name']} (TTL: {endpoint['ttl']}s)")
                else:
                    print(f"   ℹ️  {endpoint['name']} ya tiene caché")
            else:
                print(f"   ⚠️  Endpoint no encontrado: {endpoint['name']}")
        
        print(f"\n   📊 Total endpoints modificados: {modified_count}")
        return content
    
    def add_cache_stats_endpoint(self, content: str) -> str:
        """Agregar endpoint para estadísticas de caché"""
        print("\n📊 Agregando endpoint de estadísticas de caché...")
        
        # Verificar si ya existe
        if 'api_cache_stats' in content:
            print("   ℹ️  Endpoint de estadísticas ya existe")
            return content
        
        # Buscar dónde agregar (después del último @app.route)
        route_pattern = r'(@app\.route\([^)]+\)[^\n]*\n[^\n]*def [^(]+\([^)]*\):)'
        routes = list(re.finditer(route_pattern, content, re.DOTALL))
        
        if not routes:
            print("   ⚠️  No se encontraron rutas para agregar endpoint")
            return content
        
        # Insertar después de la última ruta
        last_route = routes[-1]
        insert_pos = content.find('\n\n', last_route.end())
        
        if insert_pos == -1:
            insert_pos = last_route.end()
        
        stats_endpoint = """
        @app.route('/api/cache/stats')
        def api_cache_stats(self):
            \"\"\"Estadísticas del sistema de caché\"\"\"
            try:
                if not CACHE_AVAILABLE:
                    return jsonify({
                        'status': 'disabled',
                        'message': 'Sistema de caché no disponible'
                    }), 503
                
                stats = api_cache.get_stats()
                
                return jsonify({
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'cache_stats': {
                        'size': stats['size'],
                        'max_size': stats['max_size'],
                        'hit_rate': f"{stats['hit_rate']:.2%}",
                        'hits': stats['hits'],
                        'misses': stats['misses'],
                        'keys': list(stats['keys'])[:10]  # Primeras 10 keys
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
"""
        
        new_content = content[:insert_pos] + stats_endpoint + content[insert_pos:]
        print("   ✅ Endpoint de estadísticas agregado: /api/cache/stats")
        return new_content
    
    def integrate(self):
        """Ejecutar integración completa"""
        print("\n🚀 INTEGRACIÓN DE SISTEMA DE CACHÉ")
        print("=" * 60)
        
        # 1. Crear backup
        self.create_backup()
        
        # 2. Leer archivo
        print("\n📖 Leyendo RISKMAP.py...")
        content = self.read_file()
        print(f"   ✅ Archivo leído ({len(content)} caracteres)")
        
        # 3. Agregar imports
        content = self.add_cache_import(content)
        
        # 4. Agregar caché a endpoints
        content = self.add_cache_to_endpoints(content)
        
        # 5. Agregar endpoint de estadísticas
        content = self.add_cache_stats_endpoint(content)
        
        # 6. Escribir archivo modificado
        print("\n💾 Guardando cambios...")
        self.write_file(content)
        print(f"   ✅ Archivo actualizado")
        
        print("\n✅ INTEGRACIÓN COMPLETADA")
        print("\nPróximos pasos:")
        print("1. Revisar cambios: git diff RISKMAP.py")
        print("2. Probar endpoints con caché")
        print("3. Verificar estadísticas: http://localhost:5001/api/cache/stats")
        print("4. Si hay problemas, restaurar: mv", self.backup_file, "RISKMAP.py")
        
        return True


def main():
    """Ejecutar integración"""
    integrator = CacheIntegrator()
    
    # Verificar que existe RISKMAP.py
    if not Path('RISKMAP.py').exists():
        print("❌ Error: RISKMAP.py no encontrado")
        print("   Asegúrate de ejecutar este script desde el directorio del proyecto")
        return
    
    # Verificar que existe optimization_improvements.py
    if not Path('optimization_improvements.py').exists():
        print("⚠️  Advertencia: optimization_improvements.py no encontrado")
        print("   El sistema de caché no estará disponible")
        response = input("   ¿Continuar de todas formas? (s/n): ")
        if response.lower() != 's':
            return
    
    print("\n⚠️  IMPORTANTE:")
    print("Este script modificará RISKMAP.py agregando sistema de caché.")
    print("Se creará un backup automáticamente.")
    
    response = input("\n¿Continuar con la integración? (s/n): ")
    
    if response.lower() == 's':
        integrator.integrate()
    else:
        print("\n❌ Integración cancelada")


if __name__ == "__main__":
    main()
