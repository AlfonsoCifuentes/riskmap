#!/usr/bin/env python3
"""
Sistema de Monitoreo de Rendimiento - RiskMap
==============================================
Monitorea y optimiza el rendimiento del sistema en tiempo real

Features:
- Métricas de rendimiento en tiempo real
- Detección de cuellos de botella
- Alertas de rendimiento
- Recomendaciones automáticas
- Logs de performance
"""

import sqlite3
import json
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
# dataclass import
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class PerformanceMetric:
    """Métrica de rendimiento"""
    timestamp: str
    metric_name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    is_critical: bool = False

class PerformanceMonitor:
    """Monitor de rendimiento del sistema"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db'):
        self.db_path = db_path
        self.metrics_history = deque(maxlen=1000)
        self.alerts = []
        
    def collect_system_metrics(self) -> Dict[str, PerformanceMetric]:
        """Recolectar métricas del sistema"""
        metrics = {}
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics['cpu'] = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_name='cpu_usage',
            value=cpu_percent,
            unit='percent',
            threshold=80.0,
            is_critical=cpu_percent > 80
        )
        
        # Memoria
        memory = psutil.virtual_memory()
        metrics['memory'] = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_name='memory_usage',
            value=memory.percent,
            unit='percent',
            threshold=85.0,
            is_critical=memory.percent > 85
        )
        
        # Disco
        disk = psutil.disk_usage('/')
        metrics['disk'] = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_name='disk_usage',
            value=disk.percent,
            unit='percent',
            threshold=90.0,
            is_critical=disk.percent > 90
        )
        
        return metrics
    
    def collect_database_metrics(self) -> Dict[str, PerformanceMetric]:
        """Recolectar métricas de la base de datos"""
        metrics = {}
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
            
            # Tamaño de la base de datos
            db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            metrics['db_size'] = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name='database_size',
                value=db_size_mb,
                unit='MB',
                threshold=1000.0,
                is_critical=db_size_mb > 1000
            )
            
            # Conteo de artículos
            cursor.execute("SELECT COUNT(*) FROM unified_articles")
            article_count = cursor.fetchone()[0]
            metrics['article_count'] = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name='total_articles',
                value=article_count,
                unit='articles'
            )
            
            # Artículos geopolíticos
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1")
            geo_count = cursor.fetchone()[0]
            metrics['geo_articles'] = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name='geopolitical_articles',
                value=geo_count,
                unit='articles'
            )
            
            # Análisis de fragmentación
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA freelist_count")
            freelist = cursor.fetchone()[0]
            
            fragmentation = (freelist / page_count * 100) if page_count > 0 else 0
            metrics['fragmentation'] = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name='database_fragmentation',
                value=fragmentation,
                unit='percent',
                threshold=20.0,
                is_critical=fragmentation > 20
            )
            
            # Índices existentes
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            index_count = cursor.fetchone()[0]
            metrics['indexes'] = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name='index_count',
                value=index_count,
                unit='indexes'
            )
            
            # with-context auto closes
            
        except Exception as e:
            print(f"❌ Error recolectando métricas de BD: {e}")
        
        return metrics
    
    def benchmark_query(self, query: str, params: tuple = (), iterations: int = 10) -> Dict[str, Any]:
        """Hacer benchmark de una consulta"""
        times = []
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                for _ in range(iterations):
                    start = time.time()
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    cursor.fetchall()
                    end = time.time()
                    times.append((end - start) * 1000)  # ms
            
            # with-context auto closes
            
            return {
                'query': query[:100],
                'iterations': iterations,
                'min_ms': min(times),
                'max_ms': max(times),
                'avg_ms': sum(times) / len(times),
                'total_ms': sum(times)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def detect_bottlenecks(self) -> List[Dict[str, Any]]:
        """Detectar cuellos de botella"""
        bottlenecks = []
        
        # Recolectar todas las métricas
        system_metrics = self.collect_system_metrics()
        db_metrics = self.collect_database_metrics()
        
        all_metrics = {**system_metrics, **db_metrics}
        
        # Analizar métricas críticas
        for key, metric in all_metrics.items():
            if metric.is_critical:
                bottlenecks.append({
                    'type': 'critical_metric',
                    'metric': metric.metric_name,
                    'value': metric.value,
                    'threshold': metric.threshold,
                    'severity': 'high',
                    'recommendation': self._get_recommendation(metric)
                })
        
        # Benchmarks de consultas críticas
        critical_queries = [
            ("SELECT * FROM unified_articles WHERE geopolitical_relevance = 1 ORDER BY published_at DESC LIMIT 15", ()),
            ("SELECT COUNT(*) FROM unified_articles", ())
        ]
        
        for query, params in critical_queries:
            benchmark = self.benchmark_query(query, params, iterations=5)
            if 'error' not in benchmark and benchmark['avg_ms'] > 100:
                bottlenecks.append({
                    'type': 'slow_query',
                    'query': benchmark['query'],
                    'avg_time_ms': benchmark['avg_ms'],
                    'severity': 'medium' if benchmark['avg_ms'] < 500 else 'high',
                    'recommendation': 'Considere agregar índices o reescribir la consulta'
                })
        
        return bottlenecks
    
    def _get_recommendation(self, metric: PerformanceMetric) -> str:
        """Obtener recomendación basada en métrica"""
        recommendations = {
            'cpu_usage': 'Reducir procesos en segundo plano o aumentar capacidad de CPU',
            'memory_usage': 'Liberar memoria o aumentar RAM disponible',
            'disk_usage': 'Limpiar archivos temporales o aumentar espacio en disco',
            'database_fragmentation': 'Ejecutar VACUUM para desfragmentar la base de datos',
            'database_size': 'Considerar archivado de datos antiguos'
        }
        return recommendations.get(metric.metric_name, 'Monitorear de cerca esta métrica')
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generar reporte completo de rendimiento"""
        print("\n📊 REPORTE DE RENDIMIENTO DEL SISTEMA")
        print("=" * 60)
        
        # Métricas del sistema
        print("\n🖥️  MÉTRICAS DEL SISTEMA:")
        system_metrics = self.collect_system_metrics()
        for key, metric in system_metrics.items():
            status = "🔴" if metric.is_critical else "🟢"
            print(f"   {status} {metric.metric_name}: {metric.value:.2f} {metric.unit}")
            if metric.threshold:
                print(f"      Umbral: {metric.threshold} {metric.unit}")
        
        # Métricas de la base de datos
        print("\n💾 MÉTRICAS DE BASE DE DATOS:")
        db_metrics = self.collect_database_metrics()
        for key, metric in db_metrics.items():
            status = "🔴" if metric.is_critical else "🟢"
            print(f"   {status} {metric.metric_name}: {metric.value:.2f} {metric.unit}")
            if metric.threshold:
                print(f"      Umbral: {metric.threshold} {metric.unit}")
        
        # Cuellos de botella
        print("\n⚠️  CUELLOS DE BOTELLA DETECTADOS:")
        bottlenecks = self.detect_bottlenecks()
        if bottlenecks:
            for i, bottleneck in enumerate(bottlenecks, 1):
                severity_icon = "🔴" if bottleneck['severity'] == 'high' else "🟡"
                print(f"   {severity_icon} {i}. {bottleneck['type'].replace('_', ' ').title()}")
                if 'metric' in bottleneck:
                    print(f"      Métrica: {bottleneck['metric']}")
                    print(f"      Valor: {bottleneck['value']:.2f} (Umbral: {bottleneck['threshold']})")
                if 'query' in bottleneck:
                    print(f"      Query: {bottleneck['query']}")
                    print(f"      Tiempo promedio: {bottleneck['avg_time_ms']:.2f}ms")
                print(f"      Recomendación: {bottleneck['recommendation']}")
        else:
            print("   ✅ No se detectaron cuellos de botella")
        
        # Benchmarks
        print("\n⚡ BENCHMARKS DE CONSULTAS:")
        benchmarks = []
        test_queries = [
            ("SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1", ()),
            ("SELECT * FROM unified_articles ORDER BY created_at DESC LIMIT 10", ()),
            ("SELECT COUNT(*) FROM unified_articles WHERE image_url IS NOT NULL", ())
        ]
        
        for query, params in test_queries:
            result = self.benchmark_query(query, params, iterations=5)
            if 'error' not in result:
                benchmarks.append(result)
                status = "🟢" if result['avg_ms'] < 50 else "🟡" if result['avg_ms'] < 100 else "🔴"
                print(f"   {status} {result['query']}")
                print(f"      Promedio: {result['avg_ms']:.2f}ms | Min: {result['min_ms']:.2f}ms | Max: {result['max_ms']:.2f}ms")
        
        print(f"\n✅ Reporte generado: {datetime.now().isoformat()}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {k: asdict(v) for k, v in system_metrics.items()},
            'database_metrics': {k: asdict(v) for k, v in db_metrics.items()},
            'bottlenecks': bottlenecks,
            'benchmarks': benchmarks
        }


class AutoOptimizer:
    """Optimizador automático que aplica mejoras basadas en métricas"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db'):
        self.db_path = db_path
        self.monitor = PerformanceMonitor(db_path)
    
    def auto_optimize(self) -> Dict[str, Any]:
        """Ejecutar optimización automática basada en métricas"""
        print("\n🤖 OPTIMIZACIÓN AUTOMÁTICA")
        print("=" * 60)
        
        actions_taken = []
        
        # 1. Detectar problemas
        bottlenecks = self.monitor.detect_bottlenecks()
        
        # 2. Aplicar soluciones
        if bottlenecks:
            for bottleneck in bottlenecks:
                if bottleneck['type'] == 'critical_metric':
                    if bottleneck['metric'] == 'database_fragmentation':
                        try:
                            print("   🔧 Desfragmentando base de datos...")
                            conn = sqlite3.connect(self.db_path)
                            conn.execute("VACUUM")
                            conn.close()
                            actions_taken.append('vacuum_executed')
                            print("   ✅ VACUUM completado")
                        except Exception as e:
                            print(f"   ❌ Error: {e}")
                
                elif bottleneck['type'] == 'slow_query':
                    print(f"   ℹ️  Consulta lenta detectada: {bottleneck['query'][:50]}...")
                    print(f"      Considere optimizar índices")
                    actions_taken.append('slow_query_detected')
        
        # 3. Actualizar estadísticas
        try:
            print("   📊 Actualizando estadísticas de la BD...")
            conn = sqlite3.connect(self.db_path)
            conn.execute("ANALYZE")
            conn.close()
            actions_taken.append('analyze_executed')
            print("   ✅ ANALYZE completado")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print(f"\n✅ Optimización automática completada")
        print(f"   Acciones tomadas: {len(actions_taken)}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': actions_taken,
            'bottlenecks_found': len(bottlenecks)
        }


def main():
    """Ejecutar monitoreo y optimización"""
    monitor = PerformanceMonitor()
    
    # Generar reporte
    report = monitor.generate_performance_report()
    
    # Optimización automática si hay problemas
    if report['bottlenecks']:
        print("\n" + "=" * 60)
        optimizer = AutoOptimizer()
        optimizer.auto_optimize()
    
    # Guardar reporte
    report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte guardado en: {report_file}")


if __name__ == "__main__":
    main()
