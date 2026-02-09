#!/usr/bin/env python3
"""
Sistema de Mantenimiento Automatizado - RiskMap
================================================
Ejecuta tareas de mantenimiento programadas automáticamente

Features:
- Limpieza automática de datos antiguos
- Optimización de base de datos programada
- Monitoreo continuo de recursos
- Alertas de problemas de rendimiento
- Reportes automáticos de mantenimiento
"""

import schedule
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Importar módulos de mantenimiento
try:
    from data_cleaner import DataCleaner
except ImportError:
    print("⚠️  data_cleaner.py no encontrado")
    DataCleaner = None

try:
    from performance_monitor import PerformanceMonitor, AutoOptimizer
except ImportError:
    print("⚠️  performance_monitor.py no encontrado")
    PerformanceMonitor = None
    AutoOptimizer = None

try:
    from optimization_improvements import DatabaseOptimizer
except ImportError:
    print("⚠️  optimization_improvements.py no encontrado")
    DatabaseOptimizer = None


class AutomatedMaintenanceScheduler:
    """Programador de tareas de mantenimiento automático"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db'):
        self.db_path = db_path
        self.maintenance_log = './logs/maintenance_log.json'
        self.last_cleanup = None
        self.last_optimization = None
        self.last_health_check = None
        
        # Crear directorio de logs si no existe
        Path('./logs').mkdir(parents=True, exist_ok=True)
        
        # Cargar historial
        self.load_history()
    
    def load_history(self):
        """Cargar historial de mantenimiento"""
        if os.path.exists(self.maintenance_log):
            try:
                with open(self.maintenance_log, 'r') as f:
                    history = json.load(f)
                    self.last_cleanup = history.get('last_cleanup')
                    self.last_optimization = history.get('last_optimization')
                    self.last_health_check = history.get('last_health_check')
            except Exception as e:
                print(f"⚠️  Error cargando historial: {e}")
    
    def save_history(self):
        """Guardar historial de mantenimiento"""
        history = {
            'last_cleanup': self.last_cleanup,
            'last_optimization': self.last_optimization,
            'last_health_check': self.last_health_check,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            with open(self.maintenance_log, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error guardando historial: {e}")
    
    def daily_cleanup(self):
        """Limpieza diaria de archivos temporales"""
        print("\n🧹 LIMPIEZA DIARIA PROGRAMADA")
        print("=" * 60)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if DataCleaner is None:
            print("❌ DataCleaner no disponible")
            return
        
        try:
            cleaner = DataCleaner(self.db_path)
            
            # Solo limpiar temporales y logs recientes
            cleaner.clean_temp_files()
            cleaner.clean_old_logs(days_old=7)  # Logs > 1 semana
            
            self.last_cleanup = datetime.now().isoformat()
            self.save_history()
            
            print(f"✅ Limpieza diaria completada")
            print(f"   💾 Espacio liberado: {cleaner.stats['space_freed_mb']:.2f} MB")
            
        except Exception as e:
            print(f"❌ Error en limpieza diaria: {e}")
    
    def weekly_deep_cleanup(self):
        """Limpieza profunda semanal"""
        print("\n🧹 LIMPIEZA PROFUNDA SEMANAL")
        print("=" * 60)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if DataCleaner is None:
            print("❌ DataCleaner no disponible")
            return
        
        try:
            cleaner = DataCleaner(self.db_path)
            
            # Limpieza completa
            result = cleaner.run_full_cleanup(
                archive_days=180,  # Archivar > 6 meses
                log_days=30        # Logs > 1 mes
            )
            
            self.last_cleanup = datetime.now().isoformat()
            self.save_history()
            
            # Guardar reporte
            report_file = f"weekly_cleanup_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"✅ Limpieza profunda completada")
            print(f"   💾 Espacio total liberado: {result['total_saved_mb']:.2f} MB")
            print(f"   📄 Reporte: {report_file}")
            
        except Exception as e:
            print(f"❌ Error en limpieza profunda: {e}")
    
    def daily_optimization(self):
        """Optimización diaria de base de datos"""
        print("\n⚙️ OPTIMIZACIÓN DIARIA")
        print("=" * 60)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if DatabaseOptimizer is None:
            print("❌ DatabaseOptimizer no disponible")
            return
        
        try:
            optimizer = DatabaseOptimizer(self.db_path)
            
            # Ejecutar ANALYZE para actualizar estadísticas
            optimizer.conn.execute("ANALYZE")
            optimizer.conn.commit()
            
            self.last_optimization = datetime.now().isoformat()
            self.save_history()
            
            print("✅ Optimización diaria completada")
            
        except Exception as e:
            print(f"❌ Error en optimización: {e}")
    
    def hourly_health_check(self):
        """Chequeo de salud cada hora"""
        print("\n🏥 CHEQUEO DE SALUD PROGRAMADO")
        print("=" * 60)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if PerformanceMonitor is None or AutoOptimizer is None:
            print("❌ PerformanceMonitor no disponible")
            return
        
        try:
            monitor = PerformanceMonitor(self.db_path)
            auto_opt = AutoOptimizer(self.db_path)
            
            # Recopilar métricas
            metrics = monitor.collect_metrics()
            
            # Detectar problemas críticos
            bottlenecks = monitor.detect_bottlenecks(metrics)
            
            if bottlenecks:
                print("\n⚠️  PROBLEMAS DETECTADOS:")
                for issue, recommendation in bottlenecks:
                    print(f"   • {issue}")
                    print(f"     → {recommendation}")
                
                # Aplicar optimización automática
                print("\n🔧 Aplicando optimizaciones automáticas...")
                auto_opt.auto_optimize(metrics)
            else:
                print("✅ Sistema saludable - sin problemas detectados")
            
            # Mostrar métricas clave
            print(f"\n📊 Métricas del Sistema:")
            print(f"   CPU: {metrics.cpu_percent:.1f}%")
            print(f"   RAM: {metrics.memory_percent:.1f}%")
            print(f"   Disco: {metrics.disk_percent:.1f}%")
            print(f"   DB: {metrics.db_size_mb:.2f} MB")
            print(f"   Artículos: {metrics.total_articles}")
            
            self.last_health_check = datetime.now().isoformat()
            self.save_history()
            
        except Exception as e:
            print(f"❌ Error en chequeo de salud: {e}")
    
    def setup_schedule(self):
        """Configurar programa de tareas automáticas"""
        print("\n📅 CONFIGURANDO PROGRAMA DE MANTENIMIENTO")
        print("=" * 60)
        
        # Limpieza diaria a las 3:00 AM
        schedule.every().day.at("03:00").do(self.daily_cleanup)
        print("✅ Limpieza diaria programada: 3:00 AM")
        
        # Limpieza profunda semanal los domingos a las 4:00 AM
        schedule.every().sunday.at("04:00").do(self.weekly_deep_cleanup)
        print("✅ Limpieza profunda semanal: Domingos 4:00 AM")
        
        # Optimización diaria a las 2:00 AM
        schedule.every().day.at("02:00").do(self.daily_optimization)
        print("✅ Optimización diaria: 2:00 AM")
        
        # Chequeo de salud cada hora
        schedule.every().hour.do(self.hourly_health_check)
        print("✅ Chequeo de salud: Cada hora")
        
        print("\n🚀 Sistema de mantenimiento automático iniciado")
        print("   Presiona Ctrl+C para detener")
    
    def run_forever(self):
        """Ejecutar programa continuamente"""
        self.setup_schedule()
        
        # Ejecutar chequeo inicial
        print("\n🔍 Ejecutando chequeo inicial...")
        self.hourly_health_check()
        
        # Loop principal
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            print("\n\n👋 Sistema de mantenimiento detenido")
            self.save_history()


class MaintenanceReporter:
    """Generador de reportes de mantenimiento"""
    
    def __init__(self):
        self.reports_dir = './logs/maintenance_reports'
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_weekly_report(self):
        """Generar reporte semanal de mantenimiento"""
        print("\n📊 GENERANDO REPORTE SEMANAL")
        print("=" * 60)
        
        report = {
            'period': 'weekly',
            'start_date': (datetime.now() - timedelta(days=7)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'generated_at': datetime.now().isoformat()
        }
        
        # Recopilar reportes de limpieza de la semana
        cleanup_files = list(Path('.').glob('cleanup_report_*.json'))
        cleanup_files += list(Path('.').glob('weekly_cleanup_*.json'))
        
        total_space_freed = 0
        cleanup_count = 0
        
        for file in cleanup_files:
            try:
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                if mod_time > datetime.now() - timedelta(days=7):
                    with open(file, 'r') as f:
                        data = json.load(f)
                        total_space_freed += data.get('total_saved_mb', 0)
                        cleanup_count += 1
            except Exception:
                pass
        
        report['cleanup_operations'] = cleanup_count
        report['total_space_freed_mb'] = round(total_space_freed, 2)
        
        # Recopilar reportes de rendimiento
        perf_files = list(Path('.').glob('performance_report_*.json'))
        
        avg_cpu = 0
        avg_memory = 0
        perf_count = 0
        
        for file in perf_files:
            try:
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                if mod_time > datetime.now() - timedelta(days=7):
                    with open(file, 'r') as f:
                        data = json.load(f)
                        metrics = data.get('system_metrics', {})
                        avg_cpu += metrics.get('cpu_percent', 0)
                        avg_memory += metrics.get('memory_percent', 0)
                        perf_count += 1
            except Exception:
                pass
        
        if perf_count > 0:
            report['average_cpu_percent'] = round(avg_cpu / perf_count, 2)
            report['average_memory_percent'] = round(avg_memory / perf_count, 2)
        
        # Guardar reporte
        report_file = f"{self.reports_dir}/weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Reporte semanal generado")
        print(f"   📄 {report_file}")
        print(f"   🧹 Operaciones de limpieza: {cleanup_count}")
        print(f"   💾 Espacio liberado: {total_space_freed:.2f} MB")
        
        return report


def main():
    """Ejecutar sistema de mantenimiento automático"""
    print("\n🤖 SISTEMA DE MANTENIMIENTO AUTOMATIZADO - RISKMAP")
    print("=" * 60)
    
    # Opciones de ejecución
    print("\nOpciones:")
    print("1. Ejecutar mantenimiento continuo (recomendado)")
    print("2. Ejecutar todas las tareas ahora")
    print("3. Generar reporte semanal")
    print("4. Solo chequeo de salud")
    
    try:
        choice = input("\nSelecciona una opción (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada")
        return
    
    scheduler = AutomatedMaintenanceScheduler()
    
    if choice == '1':
        # Mantenimiento continuo
        scheduler.run_forever()
    
    elif choice == '2':
        # Ejecutar todas las tareas ahora
        print("\n🚀 Ejecutando todas las tareas de mantenimiento...")
        scheduler.daily_cleanup()
        scheduler.daily_optimization()
        scheduler.hourly_health_check()
        print("\n✅ Todas las tareas completadas")
    
    elif choice == '3':
        # Generar reporte
        reporter = MaintenanceReporter()
        reporter.generate_weekly_report()
    
    elif choice == '4':
        # Solo health check
        scheduler.hourly_health_check()
    
    else:
        print("❌ Opción inválida")


if __name__ == "__main__":
    main()
