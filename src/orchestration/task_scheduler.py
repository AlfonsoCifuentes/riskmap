"""
Módulo para la programación y ejecución de tareas programadas.
"""

import schedule
import time
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Gestiona y ejecuta tareas programadas para el sistema de inteligencia."""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.is_running = False

    def setup_schedules(self):
        """Configura las tareas programadas."""
        logger.info("Configurando tareas programadas...")

        # Tareas de recolección
        schedule.every(
            config.get(
                'schedules.collection.global_hours',
                4)).hours.do(
            self.orchestrator.run_global_collection)
        schedule.every().day.at(
            config.get(
                'schedules.collection.intelligence_time',
                "03:00")).do(
            self.orchestrator.run_intelligence_only_collection)

        # Tarea de procesamiento
        schedule.every(
            config.get(
                'schedules.processing.minutes',
                60)).minutes.do(
            self.orchestrator.process_data_only)

        # Tareas de generación de informes
        schedule.every().day.at(
            config.get(
                'schedules.reporting.daily_time',
                "06:00")).do(
            self.orchestrator.generate_reports_only,
            report_type='daily')
        schedule.every().monday.at(
            config.get(
                'schedules.reporting.weekly_time',
                "07:00")).do(
            self.orchestrator.generate_reports_only,
            report_type='weekly')

        # Tareas de mantenimiento
        schedule.every().sunday.at(
            config.get(
                'schedules.maintenance.time',
                "04:00")).do(
            self.orchestrator.system_maintenance)

        logger.info("Tareas programadas configuradas:")
        for job in schedule.get_jobs():
            logger.info(f"- {job}")

    def run(self):
        """Inicia el bucle del planificador."""
        self.is_running = True
        logger.info("Iniciando planificador de tareas...")

        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Planificador detenido por el usuario.")
        except Exception as e:
            logger.error(f"Error en el planificador: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("El planificador ha finalizado.")

    def stop(self):
        """Detiene el bucle del planificador."""
        logger.info("Deteniendo el planificador...")
        self.is_running = False


# Es necesario importar 'config' para que esté disponible en este módulo
try:
    from src.utils.config import config
except ImportError:
    # Manejo de error si el módulo no se encuentra (ej. ejecución directa)
    print("Advertencia: No se pudo importar 'config'. Las configuraciones de schedule pueden fallar.")
    config = {'get': lambda key, default=None: default}
