"""
Controlador Flask para el ETL de Conflictos Geopolíticos
Integra el sistema ETL con la aplicación web Flask
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import jsonify, request
from functools import wraps
import threading
import time

# Añadir el directorio src al path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from etl.conflict_data_etl import ConflictDataETL, ETLConfig, create_etl_instance
    from etl.config import get_etl_config, get_api_credentials, validate_configuration, DEFAULT_DB_PATH
except ImportError as e:
    print(f"Error importando módulos ETL: {e}")
    # Fallback para desarrollo
    ConflictDataETL = None
    ETLConfig = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLController:
    """
    Controlador principal para el sistema ETL de conflictos geopolíticos
    Maneja la ejecución, monitoreo y configuración del pipeline ETL
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.config = get_etl_config()
        self.credentials = get_api_credentials()
        self.current_etl_instance = None  # Tipo dinámico
        self.running_jobs = {}  # Tracking de jobs ETL en ejecución
        self.job_counter = 0
        
        # Validar configuración al inicializar
        self.config_warnings = validate_configuration()
        if self.config_warnings:
            logger.warning(f"Advertencias de configuración: {self.config_warnings}")
    
    def _create_etl_instance(self, custom_config: Dict = None):
        """Crear instancia ETL con configuración personalizada"""
        try:
            if not ConflictDataETL:
                raise ImportError("Módulo ETL no disponible")
            
            # Configuración por defecto
            default_config = self.config['defaults'].copy()
            
            # Aplicar configuración personalizada
            if custom_config:
                default_config.update(custom_config)
            
            # Crear instancia
            etl_config = ETLConfig(
                sources=default_config.get('sources', ['acled', 'gdelt']),
                date_range={
                    'start': (datetime.now() - timedelta(days=default_config.get('date_range_days', 7))).strftime('%Y-%m-%d'),
                    'end': datetime.now().strftime('%Y-%m-%d')
                },
                regions=default_config.get('regions', []),
                conflict_types=default_config.get('conflict_types', []),
                enable_alerts=default_config.get('enable_alerts', True),
                alert_threshold=default_config.get('alert_threshold', 50),
                batch_size=default_config.get('batch_size', 100),
                max_retries=default_config.get('max_retries', 3)
            )
            
            return ConflictDataETL(db_path=self.db_path, config=etl_config)
            
        except Exception as e:
            logger.error(f"Error creando instancia ETL: {e}")
            raise
    
    def get_datasets_catalog(self) -> Dict[str, Any]:
        """Obtener catálogo completo de datasets disponibles"""
        try:
            # Datasets del sistema ETL
            etl_instance = self._create_etl_instance()
            etl_datasets = etl_instance.get_datasets_catalog()
            
            # Datasets específicos de la configuración
            specific_datasets = self.config.get('datasets', {})
            
            # Información de fuentes configuradas
            sources_info = self.config.get('sources', {})
            
            return {
                'etl_datasets': etl_datasets,
                'specific_conflicts': specific_datasets,
                'sources_configuration': sources_info,
                'regions': self.config.get('regions', {}),
                'conflict_types': self.config.get('conflict_types', {}),
                'last_updated': datetime.now().isoformat(),
                'credentials_status': {
                    'acled_configured': bool(self.credentials.get('acled_api_key')),
                    'planet_configured': bool(self.credentials.get('planet_api_key')),
                    'gdelt_available': True  # GDELT no requiere API key
                },
                'configuration_warnings': self.config_warnings
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo catálogo de datasets: {e}")
            return {
                'error': str(e),
                'etl_datasets': {},
                'specific_conflicts': {},
                'sources_configuration': {},
                'last_updated': datetime.now().isoformat()
            }
    
    def execute_etl_pipeline(self, config: Dict = None, background: bool = True) -> Dict[str, Any]:
        """
        Ejecutar pipeline ETL completo
        
        Args:
            config: Configuración personalizada para el ETL
            background: Si True, ejecuta en background y retorna job_id
        """
        try:
            self.job_counter += 1
            job_id = f"etl_job_{self.job_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🚀 Iniciando job ETL: {job_id}")
            
            if background:
                # Ejecutar en background
                self.running_jobs[job_id] = {
                    'status': 'running',
                    'started_at': datetime.now().isoformat(),
                    'config': config or {},
                    'progress': 0,
                    'current_phase': 'initializing'
                }
                
                # Lanzar thread para ejecución
                thread = threading.Thread(
                    target=self._run_etl_background,
                    args=(job_id, config),
                    daemon=True
                )
                thread.start()
                
                return {
                    'job_id': job_id,
                    'status': 'started',
                    'background': True,
                    'message': 'Pipeline ETL iniciado en background'
                }
            else:
                # Ejecutar sincrónicamente
                return self._run_etl_sync(config)
                
        except Exception as e:
            logger.error(f"Error ejecutando pipeline ETL: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _run_etl_background(self, job_id: str, config: Dict = None):
        """Ejecutar ETL en background con tracking de progreso"""
        try:
            logger.info(f"⚙️ Ejecutando ETL en background: {job_id}")
            
            # Actualizar estado
            self.running_jobs[job_id].update({
                'status': 'running',
                'current_phase': 'creating_instance',
                'progress': 10
            })
            
            # Crear instancia ETL
            etl_instance = self._create_etl_instance(config)
            
            self.running_jobs[job_id].update({
                'current_phase': 'executing_pipeline',
                'progress': 20
            })
            
            # Ejecutar pipeline
            results = etl_instance.run_full_pipeline(run_id=job_id)
            
            # Actualizar resultado final
            self.running_jobs[job_id].update({
                'status': results.get('status', 'completed'),
                'completed_at': datetime.now().isoformat(),
                'progress': 100,
                'current_phase': 'completed',
                'results': results
            })
            
            logger.info(f"✅ ETL background completado: {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Error en ETL background {job_id}: {e}")
            self.running_jobs[job_id].update({
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now().isoformat(),
                'progress': 0,
                'current_phase': 'failed'
            })
    
    def _run_etl_sync(self, config: Dict = None) -> Dict[str, Any]:
        """Ejecutar ETL sincrónicamente"""
        try:
            etl_instance = self._create_etl_instance(config)
            results = etl_instance.run_full_pipeline()
            return results
            
        except Exception as e:
            logger.error(f"Error en ETL síncrono: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_etl_status(self, job_id: str = None) -> Dict[str, Any]:
        """
        Obtener estado del ETL
        
        Args:
            job_id: ID específico del job, si no se proporciona retorna estado general
        """
        try:
            if job_id:
                # Estado de job específico
                if job_id in self.running_jobs:
                    return self.running_jobs[job_id]
                else:
                    return {
                        'error': f'Job {job_id} no encontrado',
                        'available_jobs': list(self.running_jobs.keys())
                    }
            else:
                # Estado general del sistema
                etl_instance = self._create_etl_instance()
                stats = etl_instance.get_etl_statistics()
                
                return {
                    'system_status': 'operational' if not self.config_warnings else 'warning',
                    'running_jobs': len([j for j in self.running_jobs.values() if j['status'] == 'running']),
                    'completed_jobs': len([j for j in self.running_jobs.values() if j['status'] == 'completed']),
                    'failed_jobs': len([j for j in self.running_jobs.values() if j['status'] == 'failed']),
                    'etl_statistics': stats,
                    'configuration_warnings': self.config_warnings,
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estado ETL: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_critical_events(self, limit: int = 20, severity: str = None) -> List[Dict]:
        """Obtener eventos críticos recientes"""
        try:
            etl_instance = self._create_etl_instance()
            events = etl_instance.get_recent_critical_events(limit=limit)
            
            # Filtrar por severidad si se especifica
            if severity:
                events = [e for e in events if e.get('severity') == severity]
            
            return events
            
        except Exception as e:
            logger.error(f"Error obteniendo eventos críticos: {e}")
            return []
    
    def get_analytics_data(self, **kwargs) -> Dict[str, Any]:
        """Obtener datos de analytics para el dashboard"""
        days_back = kwargs.get('days_back', 30)
        try:
            etl_instance = self._create_etl_instance()
            
            # Obtener estadísticas generales
            stats = etl_instance.get_etl_statistics()
            
            # Obtener eventos críticos para métricas
            critical_events = etl_instance.get_recent_critical_events(limit=100)
            
            # Procesar datos para analytics
            analytics = {
                'summary': stats,
                'critical_events_summary': {
                    'total': len(critical_events),
                    'by_severity': {},
                    'by_country': {},
                    'recent_trend': []
                },
                'data_sources_health': {
                    'acled': {'status': 'active' if self.credentials.get('acled_api_key') else 'disabled'},
                    'gdelt': {'status': 'active'},
                    'ucdp': {'status': 'available'}
                },
                'generated_at': datetime.now().isoformat()
            }
            
            # Análisis de eventos críticos por severidad
            for event in critical_events:
                severity = event.get('severity', 'unknown')
                analytics['critical_events_summary']['by_severity'][severity] = (
                    analytics['critical_events_summary']['by_severity'].get(severity, 0) + 1
                )
            
            # Análisis por país
            for event in critical_events:
                country = event.get('country', 'unknown')
                analytics['critical_events_summary']['by_country'][country] = (
                    analytics['critical_events_summary']['by_country'].get(country, 0) + 1
                )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics: {e}")
            return {
                'error': str(e),
                'summary': {},
                'generated_at': datetime.now().isoformat()
            }
    
    def update_configuration(self, new_config: Dict) -> Dict[str, Any]:
        """Actualizar configuración del ETL"""
        try:
            # Validar nueva configuración
            valid_keys = ['sources', 'date_range_days', 'alert_threshold', 'regions', 'enable_alerts']
            
            updated_config = {}
            for key, value in new_config.items():
                if key in valid_keys:
                    updated_config[key] = value
                else:
                    logger.warning(f"Clave de configuración ignorada: {key}")
            
            # Aquí podrías guardar la configuración en un archivo o base de datos
            # Por ahora, solo actualizamos la configuración en memoria
            self.config['defaults'].update(updated_config)
            
            logger.info(f"Configuración actualizada: {updated_config}")
            
            return {
                'status': 'success',
                'updated_config': updated_config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error actualizando configuración: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Limpiar jobs antiguos del tracking"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            jobs_to_remove = []
            for job_id, job_info in self.running_jobs.items():
                started_at = datetime.fromisoformat(job_info['started_at'])
                if started_at < cutoff_time and job_info['status'] in ['completed', 'failed']:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.running_jobs[job_id]
            
            logger.info(f"🧹 Limpieza de jobs: {len(jobs_to_remove)} jobs eliminados")
            
        except Exception as e:
            logger.error(f"Error limpiando jobs: {e}")

# Función para crear rutas Flask
def create_etl_routes(app, etl_controller: ETLController = None):
    """
    Crear rutas Flask para el sistema ETL
    
    Args:
        app: Instancia de la aplicación Flask
        etl_controller: Instancia del controlador ETL
    """
    
    if not etl_controller:
        etl_controller = ETLController()
    
    def require_etl(f):
        """Decorador para verificar que el ETL esté disponible"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not ConflictDataETL:
                return jsonify({
                    'error': 'Sistema ETL no disponible',
                    'message': 'El módulo ETL no está instalado o configurado correctamente'
                }), 503
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/api/etl/conflicts/datasets', methods=['GET'])
    @require_etl
    def get_datasets():
        """Obtener catálogo de datasets disponibles"""
        try:
            catalog = etl_controller.get_datasets_catalog()
            return jsonify(catalog)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/etl/conflicts/execute', methods=['POST'])
    @require_etl
    def execute_etl():
        """Ejecutar pipeline ETL"""
        try:
            config = request.get_json() if request.is_json else {}
            background = config.pop('background', True)
            
            result = etl_controller.execute_etl_pipeline(config=config, background=background)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/etl/conflicts/status', methods=['GET'])
    @app.route('/api/etl/conflicts/status/<job_id>', methods=['GET'])
    @require_etl
    def get_etl_status(job_id=None):
        """Obtener estado del ETL"""
        try:
            status = etl_controller.get_etl_status(job_id=job_id)
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/etl/conflicts/critical-events', methods=['GET'])
    @require_etl
    def get_critical_events():
        """Obtener eventos críticos"""
        try:
            limit = request.args.get('limit', 20, type=int)
            severity = request.args.get('severity')
            
            events = etl_controller.get_critical_events(limit=limit, severity=severity)
            return jsonify(events)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/etl/conflicts/analytics', methods=['GET'])
    @require_etl
    def get_analytics():
        """Obtener datos de analytics"""
        try:
            days_back = request.args.get('days', 30, type=int)
            analytics = etl_controller.get_analytics_data(days_back=days_back)
            return jsonify(analytics)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/etl/conflicts/config', methods=['GET'])
    def get_config():
        """Obtener configuración actual"""
        try:
            config = etl_controller.config
            return jsonify({
                'current_config': config['defaults'],
                'available_sources': list(config['sources'].keys()),
                'regions': config['regions'],
                'conflict_types': config['conflict_types'],
                'credentials_status': {
                    'acled_configured': bool(etl_controller.credentials.get('acled_api_key')),
                    'planet_configured': bool(etl_controller.credentials.get('planet_api_key'))
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/etl/conflicts/config', methods=['POST'])
    @require_etl
    def update_config():
        """Actualizar configuración"""
        try:
            new_config = request.get_json()
            if not new_config:
                return jsonify({'error': 'No se proporcionó configuración'}), 400
            
            result = etl_controller.update_configuration(new_config)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Cleanup job periódico - usar threading en lugar de before_first_request
    def setup_cleanup():
        """Configurar limpieza periódica de jobs"""
        def cleanup_job():
            while True:
                time.sleep(3600)  # Cada hora
                etl_controller.cleanup_old_jobs()
        
        cleanup_thread = threading.Thread(target=cleanup_job, daemon=True)
        cleanup_thread.start()
    
    # Iniciar cleanup en un thread separado
    setup_cleanup()
    
    logger.info("✅ Rutas ETL configuradas correctamente")

# Instancia global del controlador ETL (singleton)
_etl_controller = None

def get_etl_controller() -> ETLController:
    """Obtener instancia singleton del controlador ETL"""
    global _etl_controller
    if _etl_controller is None:
        _etl_controller = ETLController()
    return _etl_controller

if __name__ == "__main__":
    # Test del controlador
    controller = ETLController()
    
    print("🧪 Testing ETL Controller...")
    
    # Test catálogo de datasets
    catalog = controller.get_datasets_catalog()
    print(f"📊 Datasets disponibles: {len(catalog.get('etl_datasets', {}))}")
    
    # Test estado del sistema
    status = controller.get_etl_status()
    print(f"⚡ Estado del sistema: {status.get('system_status', 'unknown')}")
    
    print("✅ ETL Controller funcionando correctamente")
