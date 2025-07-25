"""
Sistema de Inteligencia Geopolítica - Punto de Entrada Principal
Interfaz de línea de comandos (CLI) para interactuar con el sistema.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for consistent module resolution
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.config import logger
    from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
    from src.orchestration.task_scheduler import TaskScheduler
except ImportError as e:
    print(f"[ERROR] Error importando módulos: {e}")
    print(f"[INFO] Python Path: {sys.path}")
    print("[WARN] Asegúrese de que el entorno virtual esté activado y las dependencias instaladas.")
    sys.exit(1)


def main():
    """Función principal con interfaz de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Sistema de Inteligencia Geopolítica - Análisis OSINT Automatizado",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ejecutar el pipeline completo una vez
  python main.py full-pipeline

  # Iniciar el modo de planificación continua
  python main.py schedule

  # Recolectar datos de fuentes globales
  python main.py collect --source global

  # Recolectar datos de una región específica
  python main.py collect --source regional --region americas

  # Procesar artículos pendientes
  python main.py process

  # Generar informes diarios
  python main.py report --type daily

  # Ver el estado del sistema
  python main.py status

  # Realizar una comprobación de salud
  python main.py health-check
""")

    subparsers = parser.add_subparsers(
        dest='command',
        required=True,
        help='Comando a ejecutar')

    # Comando: full-pipeline
    parser_pipeline = subparsers.add_parser(
        'full-pipeline',
        help='Ejecutar el pipeline completo una vez (recolectar, procesar, informar)')
    parser_pipeline.add_argument(
        '--no-validate',
        action='store_true',
        help='Omitir el paso de validación de datos')
    parser_pipeline.add_argument(
        '--mode',
        choices=[
            'global',
            'legacy'],
        default='global',
        help='Modo de recolección a usar')

    # Comando: schedule
    subparsers.add_parser(
        'schedule',
        help='Iniciar el planificador de tareas para ejecución continua')

    # Comando: collect
    parser_collect = subparsers.add_parser(
        'collect', help='Ejecutar solo el paso de recolección de datos')
    parser_collect.add_argument(
        '--source',
        choices=[
            'global',
            'regional',
            'intelligence',
            'legacy'],
        required=True,
        help='Tipo de fuente a recolectar')
    parser_collect.add_argument(
        '--region',
        choices=[
            'americas',
            'europe',
            'asia_pacific',
            'middle_east',
            'africa'],
        help='Región específica para recolección regional')
    parser_collect.add_argument(
        '--languages',
        nargs='+',
        help='Especificar idiomas para la recolección')

    # Comando: process
    subparsers.add_parser(
        'process',
        help='Ejecutar solo el procesamiento NLP de artículos pendientes')

    # Comando: report
    parser_report = subparsers.add_parser('report', help='Generar informes')
    parser_report.add_argument(
        '--type',
        choices=[
            'daily',
            'weekly',
            'trend'],
        default='daily',
        help='Tipo de informe a generar')

    # Comando: status
    subparsers.add_parser(
        'status',
        help='Mostrar el estado actual del sistema')

    # Comando: health-check
    subparsers.add_parser(
        'health-check',
        help='Realizar una comprobación completa de la salud del sistema')

    # Comando: maintenance
    subparsers.add_parser(
        'maintenance',
        help='Ejecutar tareas de mantenimiento del sistema')

    # Comando: validate-data
    parser_validate = subparsers.add_parser(
        'validate-data', help='Validar la calidad de los datos')
    parser_validate.add_argument(
        '--days',
        type=int,
        default=7,
        help='Número de días a validar')

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Habilitar registro detallado')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Registro detallado habilitado")

    try:
        orchestrator = GeopoliticalIntelligenceOrchestrator()

        if args.command == 'full-pipeline':
            success = orchestrator.run_full_pipeline(
                validate_data=not args.no_validate,
                use_global_collection=(args.mode == 'global')
            )
            sys.exit(0 if success else 1)

        elif args.command == 'schedule':
            scheduler = TaskScheduler(orchestrator)
            scheduler.setup_schedules()
            scheduler.run()

        elif args.command == 'collect':
            if args.source == 'global':
                count = orchestrator.run_global_collection(
                    languages=args.languages)
            elif args.source == 'regional':
                if not args.region:
                    parser.error(
                        "--region es requerido para la recolección regional")
                count = orchestrator.run_regional_collection(args.region)
            elif args.source == 'intelligence':
                count = orchestrator.run_intelligence_only_collection()
            elif args.source == 'legacy':
                count = orchestrator.collect_data_only()
            print(f"Se recolectaron {count} artículos.")

        elif args.command == 'process':
            count = orchestrator.process_data_only()
            print(f"Se procesaron {count} artículos.")

        elif args.command == 'report':
            reports = orchestrator.generate_reports_only(report_type=args.type)
            if reports:
                print(f"Informes de tipo '{args.type}' generados:")
                for format_type, file_path in reports.items():
                    print(f"  - {format_type.upper()}: {file_path}")
            else:
                print("No se generaron informes.")

        elif args.command == 'status':
            orchestrator.show_status()

        elif args.command == 'health-check':
            health_status = orchestrator.health_check()
            sys.exit(
                0 if health_status.get('overall_status') in [
                    'healthy', 'degraded'] else 1)

        elif args.command == 'maintenance':
            orchestrator.system_maintenance()

        elif args.command == 'validate-data':
            orchestrator.validate_data_quality(days=args.days)

    except KeyboardInterrupt:
        logger.info("Operación interrumpida por el usuario.")
        sys.exit(0)
    except Exception as e:
        logger.critical(
            f"Error no controlado en la ejecución principal: {e}",
            exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
