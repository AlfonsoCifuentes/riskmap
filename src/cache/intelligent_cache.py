
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import pickle

class IntelligentCacheSystem:
    """Sistema de cache inteligente para optimizar rendimiento"""
    
    def __init__(self):
        self.cache_dir = Path('src/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de cache
        self.cache_config = {
            'maps': {'ttl': 3600, 'max_size': 100},  # 1 hora
            'satellite': {'ttl': 7200, 'max_size': 50},  # 2 horas
            'geojson': {'ttl': 1800, 'max_size': 200},  # 30 minutos
            'analysis': {'ttl': 86400, 'max_size': 1000}  # 24 horas
        }
    
    def generate_cache_key(self, data_type, params):
        """Generar clave única para cache"""
        key_string = f"{data_type}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_file_path(self, cache_key):
        """Obtener ruta del archivo cache"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def is_cache_valid(self, cache_file, ttl):
        """Verificar si cache es válido"""
        if not cache_file.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(seconds=ttl)
        
        return file_time > expiry_time
    
    def get_from_cache(self, data_type, params):
        """Obtener datos del cache"""
        try:
            cache_key = self.generate_cache_key(data_type, params)
            cache_file = self.get_cache_file_path(cache_key)
            
            config = self.cache_config.get(data_type, {'ttl': 3600})
            
            if self.is_cache_valid(cache_file, config['ttl']):
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                print(f"Cache HIT para {data_type}: {cache_key[:8]}...")
                return cached_data
            else:
                print(f"Cache MISS para {data_type}: {cache_key[:8]}...")
                return None
                
        except Exception as e:
            print(f"Error obteniendo del cache: {e}")
            return None
    
    def save_to_cache(self, data_type, params, data):
        """Guardar datos en cache"""
        try:
            cache_key = self.generate_cache_key(data_type, params)
            cache_file = self.get_cache_file_path(cache_key)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"Guardado en cache {data_type}: {cache_key[:8]}...")
            
            # Limpiar cache si es necesario
            self.cleanup_cache(data_type)
            
        except Exception as e:
            print(f"Error guardando en cache: {e}")
    
    def cleanup_cache(self, data_type):
        """Limpiar cache antiguo"""
        try:
            config = self.cache_config.get(data_type, {'max_size': 100})
            max_size = config['max_size']
            
            # Obtener archivos cache ordenados por fecha
            cache_files = list(self.cache_dir.glob('*.cache'))
            cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Eliminar archivos excedentes
            if len(cache_files) > max_size:
                for old_file in cache_files[max_size:]:
                    old_file.unlink()
                    print(f"Cache limpiado: {old_file.name}")
                    
        except Exception as e:
            print(f"Error limpiando cache: {e}")
    
    def clear_all_cache(self):
        """Limpiar todo el cache"""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            for cache_file in cache_files:
                cache_file.unlink()
            
            print(f"Cache completamente limpiado: {len(cache_files)} archivos eliminados")
            
        except Exception as e:
            print(f"Error limpiando cache completo: {e}")
    
    def get_cache_stats(self):
        """Obtener estadísticas del cache"""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_files': len(cache_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_file': min((f.stat().st_mtime for f in cache_files), default=0),
                'newest_file': max((f.stat().st_mtime for f in cache_files), default=0)
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas cache: {e}")
            return {}
            