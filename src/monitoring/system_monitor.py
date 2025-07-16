"""
Sistema de Monitoreo Avanzado para Plataforma OSINT.
======================================================
Monitoreo integral de rendimiento, APIs, base de datos y recursos del sistema.
Diseñado para análisis geopolítico en tiempo real con datos 100% reales.
"""

import psutil
import sqlite3
import requests
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import socket

from utils.config import config, logger


class AdvancedSystemMonitor:
    """Monitor integral de sistema con alertas inteligentes."""
    
    def __init__(self):
        self.db_path = config.get('database', {}).get('path', 'data/riskmap.db')
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Métricas históricas (últimas 100 mediciones)
        self.cpu_history = deque(maxlen=100)
        self.memory_history = deque(maxlen=100)
        self.disk_history = deque(maxlen=100)
        
        # Umbrales de alerta
        self.thresholds = {
            'cpu_critical': 90.0,
            'cpu_warning': 75.0,
            'memory_critical': 90.0,
            'memory_warning': 80.0,
            'disk_critical': 95.0,
            'disk_warning': 85.0,
            'response_time_warning': 5.0,
            'response_time_critical': 10.0
        }
        
        # Estado del sistema
        self._monitoring_active = False
        self._monitor_thread = None
        
    def start_continuous_monitoring(self, interval: int = 30) -> None:
        """Inicia monitoreo continuo del sistema."""
        if self._monitoring_active:
            logger.warning("Monitoreo ya está activo")
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._continuous_monitor,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Monitoreo continuo iniciado (intervalo: {interval}s)")
    
    def stop_continuous_monitoring(self) -> None:
        """Detiene el monitoreo continuo."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Monitoreo continuo detenido")
    
    def _continuous_monitor(self, interval: int) -> None:
        """Bucle de monitoreo continuo."""
        while self._monitoring_active:
            try:
                health_status = self.check_system_health()
                self._process_alerts(health_status)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error en monitoreo continuo: {e}")
                time.sleep(interval)
    
    def check_system_health(self) -> Dict[str, Any]:
        """Verificación integral de salud del sistema."""
        start_time = time.time()
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'score': 100,
            'checks': {},
            'metrics': {},
            'alerts': []
        }
        
        try:
            # Verificaciones principales
            checks = [
                ('system_resources', self._check_system_resources),
                ('database', self._check_database_health),
                ('apis', self._check_api_status),
                ('storage', self._check_storage),
                ('logs', self._check_log_health),
                ('network', self._check_network_connectivity),
                ('processes', self._check_processes)
            ]
            
            total_score = 0
            critical_issues = 0
            warnings = 0
            
            for check_name, check_func in checks:
                try:
                    result = check_func()
                    health_status['checks'][check_name] = result
                    
                    # Calcular puntuación
                    if result['status'] == 'critical':
                        critical_issues += 1
                        total_score += 0
                    elif result['status'] == 'warning':
                        warnings += 1
                        total_score += 50
                    else:
                        total_score += 100
                        
                except Exception as e:
                    logger.error(f"Error en verificación {check_name}: {e}")
                    health_status['checks'][check_name] = {
                        'status': 'critical',
                        'message': f'Error de verificación: {str(e)}'
                    }
                    critical_issues += 1
            
            # Calcular estado general
            if critical_issues > 0:
                health_status['overall_status'] = 'critical'
            elif warnings > 0:
                health_status['overall_status'] = 'warning'
            
            # Puntuación final
            health_status['score'] = total_score // len(checks) if checks else 0
            
            # Métricas de rendimiento
            health_status['metrics'] = {
                'check_duration': round(time.time() - start_time, 3),
                'critical_issues': critical_issues,
                'warnings': warnings,
                'uptime': self._get_system_uptime()
            }
            
        except Exception as e:
            logger.error(f"Error crítico en verificación de salud: {e}")
            health_status.update({
                'overall_status': 'critical',
                'score': 0,
                'error': str(e)
            })
        
        return health_status
    
    def _process_alerts(self, health_status: Dict[str, Any]) -> None:
        """Procesa y registra alertas basadas en el estado del sistema."""
        if health_status['overall_status'] == 'critical':
            logger.critical(f"ALERTA CRÍTICA: Sistema en estado crítico (Score: {health_status['score']})")
        elif health_status['overall_status'] == 'warning':
            logger.warning(f"ALERTA: Sistema con advertencias (Score: {health_status['score']})")
        
        # Alertas específicas
        for check_name, check_result in health_status['checks'].items():
            if check_result.get('status') == 'critical':
                logger.critical(f"CRÍTICO - {check_name}: {check_result.get('message', 'Sin detalles')}")
            elif check_result.get('status') == 'warning':
                logger.warning(f"ADVERTENCIA - {check_name}: {check_result.get('message', 'Sin detalles')}")
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Verificación avanzada de recursos del sistema."""
        try:
            # Obtener métricas
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Agregar a historial
            self.cpu_history.append(cpu_percent)
            self.memory_history.append(memory.percent)
            
            # Determinar estado
            status = 'healthy'
            messages = []
            metrics = {
                'cpu_percent': cpu_percent,
                'cpu_avg_5min': sum(list(self.cpu_history)[-10:]) / min(10, len(self.cpu_history)),
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2)
            }
            
            # Verificar umbrales
            if cpu_percent > self.thresholds['cpu_critical']:
                status = 'critical'
                messages.append(f"CPU crítico: {cpu_percent}%")
            elif cpu_percent > self.thresholds['cpu_warning']:
                status = 'warning'
                messages.append(f"CPU alto: {cpu_percent}%")
            
            if memory.percent > self.thresholds['memory_critical']:
                status = 'critical'
                messages.append(f"Memoria crítica: {memory.percent}%")
            elif memory.percent > self.thresholds['memory_warning']:
                status = 'warning'
                messages.append(f"Memoria alta: {memory.percent}%")
            
            return {
                'status': status,
                'message': '; '.join(messages) if messages else 'Recursos del sistema normales',
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error verificando recursos del sistema: {e}")
            return {
                'status': 'critical',
                'message': f'Error obteniendo métricas: {str(e)}'
            }
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'warnings': warnings,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and integrity."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if main tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('articles', 'analysis_results');
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Count records
            article_count = 0
            analysis_count = 0
            
            if 'articles' in tables:
                cursor.execute("SELECT COUNT(*) FROM articles")
                article_count = cursor.fetchone()[0]
                
            if 'analysis_results' in tables:
                cursor.execute("SELECT COUNT(*) FROM analysis_results")
                analysis_count = cursor.fetchone()[0]
            
            # Check for recent activity
            recent_articles = 0
            if 'articles' in tables:
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE created_at > datetime('now', '-24 hours')
                """)
                recent_articles = cursor.fetchone()[0]
            
            conn.close()
            
            status = 'healthy'
            if len(tables) < 2:
                status = 'warning'
            elif recent_articles == 0:
                status = 'warning'
                
            return {
                'status': status,
                'tables_found': tables,
                'article_count': article_count,
                'analysis_count': analysis_count,
                'recent_articles_24h': recent_articles,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_api_status(self) -> Dict[str, Any]:
        """Check external API endpoints status."""
        apis_to_check = [
            {
                'name': 'NewsAPI',
                'url': 'https://newsapi.org/v2/top-headlines?country=us&apiKey=' + 
                       config.get('newsapi', {}).get('api_key', 'test'),
                'timeout': 10
            },
            {
                'name': 'OpenAI',
                'url': 'https://api.openai.com/v1/models',
                'headers': {'Authorization': f"Bearer {config.get('openai', {}).get('api_key', 'test')}"},
                'timeout': 10
            }
        ]
        
        api_status = {}
        overall_status = 'healthy'
        
        for api in apis_to_check:
            try:
                start_time = time.time()
                response = requests.get(
                    api['url'], 
                    headers=api.get('headers', {}),
                    timeout=api['timeout']
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    status = 'healthy'
                elif response.status_code == 401:
                    status = 'auth_error'
                    overall_status = 'degraded'
                else:
                    status = 'error'
                    overall_status = 'degraded'
                    
                api_status[api['name']] = {
                    'status': status,
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time, 2),
                    'timestamp': datetime.now().isoformat()
                }
                
            except requests.exceptions.Timeout:
                api_status[api['name']] = {
                    'status': 'timeout',
                    'error': 'Request timeout',
                    'timestamp': datetime.now().isoformat()
                }
                overall_status = 'degraded'
                
            except Exception as e:
                api_status[api['name']] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'apis': api_status,
            'timestamp': datetime.now().isoformat()
        }
    
    def _check_storage(self) -> Dict[str, Any]:
        """Check storage usage and availability."""
        try:
            # Check main directories
            dirs_to_check = ['data', 'logs', 'reports', 'models']
            storage_info = {}
            
            for dir_name in dirs_to_check:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    file_count = len(list(dir_path.rglob('*')))
                    storage_info[dir_name] = {
                        'size_mb': round(size / (1024 * 1024), 2),
                        'file_count': file_count
                    }
                else:
                    storage_info[dir_name] = {'status': 'missing'}
            
            # Check total disk usage
            disk_usage = psutil.disk_usage('.')
            free_space_gb = disk_usage.free / (1024**3)
            
            status = 'healthy'
            if free_space_gb < 1:  # Less than 1GB free
                status = 'critical'
            elif free_space_gb < 5:  # Less than 5GB free
                status = 'warning'
            
            return {
                'status': status,
                'directories': storage_info,
                'free_space_gb': round(free_space_gb, 2),
                'total_space_gb': round(disk_usage.total / (1024**3), 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_log_health(self) -> Dict[str, Any]:
        """Check log files for errors and warnings."""
        try:
            log_files = list(self.log_dir.glob('*.log'))
            log_analysis = {}
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    error_count = sum(1 for line in lines if 'ERROR' in line.upper())
                    warning_count = sum(1 for line in lines if 'WARNING' in line.upper())
                    
                    # Check for recent errors (last 24 hours)
                    recent_errors = 0
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    for line in lines:
                        if today in line and 'ERROR' in line.upper():
                            recent_errors += 1
                    
                    log_analysis[log_file.name] = {
                        'total_lines': len(lines),
                        'error_count': error_count,
                        'warning_count': warning_count,
                        'recent_errors_24h': recent_errors,
                        'file_size_mb': round(log_file.stat().st_size / (1024 * 1024), 2)
                    }
                    
                except Exception as e:
                    log_analysis[log_file.name] = {'error': str(e)}
            
            total_recent_errors = sum(
                info.get('recent_errors_24h', 0) 
                for info in log_analysis.values() 
                if isinstance(info, dict) and 'recent_errors_24h' in info
            )
            
            status = 'healthy'
            if total_recent_errors > 10:
                status = 'warning'
            elif total_recent_errors > 50:
                status = 'critical'
            
            return {
                'status': status,
                'log_files': log_analysis,
                'total_recent_errors': total_recent_errors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance metrics for the specified time period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get processing statistics
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN processed = 1 THEN 1 END) as processed_articles,
                    AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time END) as avg_processing_time
                FROM articles 
                WHERE created_at > datetime('now', '-{hours} hours')
            """)
            
            stats = cursor.fetchone()
            conn.close()
            
            # Calculate processing efficiency
            total_articles = stats[0] if stats[0] else 0
            processed_articles = stats[1] if stats[1] else 0
            avg_processing_time = stats[2] if stats[2] else 0
            
            processing_rate = (processed_articles / total_articles * 100) if total_articles > 0 else 0
            
            return {
                'period_hours': hours,
                'total_articles': total_articles,
                'processed_articles': processed_articles,
                'processing_rate_percent': round(processing_rate, 2),
                'avg_processing_time_seconds': round(avg_processing_time, 2),
                'articles_per_hour': round(total_articles / hours, 2) if hours > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def save_health_report(self, health_status: Dict[str, Any]) -> str:
        """Save health check report to file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.log_dir / f"health_check_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(health_status, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Health report saved to: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Error saving health report: {e}")
            return ""
    
    def cleanup_old_reports(self, days: int = 7):
        """Clean up old health reports and logs."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_files = 0
            
            # Clean health reports
            for report_file in self.log_dir.glob("health_check_*.json"):
                if datetime.fromtimestamp(report_file.stat().st_mtime) < cutoff_date:
                    report_file.unlink()
                    cleaned_files += 1
            
            # Clean old log files
            for log_file in self.log_dir.glob("*.log"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    log_file.unlink()
                    cleaned_files += 1
            
            logger.info(f"Cleaned up {cleaned_files} old files")
            return cleaned_files
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0


# Instancia singleton del monitor
system_monitor = AdvancedSystemMonitor()

# Funciones de utilidad para compatibilidad
def get_system_status() -> Dict[str, Any]:
    """Obtiene el estado actual del sistema."""
    return system_monitor.check_system_health()

def start_monitoring(interval: int = 30) -> None:
    """Inicia el monitoreo continuo."""
    system_monitor.start_continuous_monitoring(interval)

def stop_monitoring() -> None:
    """Detiene el monitoreo continuo."""
    system_monitor.stop_continuous_monitoring()
