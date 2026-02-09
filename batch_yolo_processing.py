#!/usr/bin/env python3
"""
Procesamiento por Lotes YOLO - RiskMap

Script para procesar todas las imágenes satelitales existentes con YOLO
y generar detecciones automáticas de objetos militares y conflictos.

Uso:
    python batch_yolo_processing.py

Características:
✅ Procesamiento automático de todas las imágenes satelitales
✅ Detección de objetos militares, conflictos y desastres
✅ Generación de overlays con bounding boxes
✅ Almacenamiento en base de datos
✅ Reportes de progreso y estadísticas
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import sqlite3

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/batch_yolo_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchYOLOProcessor:
    """Procesador por lotes para análisis YOLO de imágenes satelitales."""

    def __init__(self):
        self.db_path = "satellite_analysis.db"
        self.images_base_dir = Path("static/images/satellite")
        self.processed_count = 0
        self.errors_count = 0
        self.total_detections = 0

        # Importar el sistema ultra HD
        try:
            from ultra_hd_satellite_system import ultra_hd_system
            self.yolo_system = ultra_hd_system
            logger.info("✅ Sistema YOLO Ultra HD cargado")
        except ImportError as e:
            logger.error(f"❌ Error importando sistema YOLO: {e}")
            sys.exit(1)

    def get_all_satellite_images(self) -> list:
        """
        Obtiene todas las imágenes satelitales disponibles para procesar.

        Returns:
            Lista de rutas de imágenes
        """
        image_paths = []

        # Buscar en el directorio de imágenes satelitales
        if self.images_base_dir.exists():
            for file_path in self.images_base_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    image_paths.append(str(file_path))
                    logger.info(f"📁 Encontrada imagen: {file_path}")

        # También buscar imágenes en el directorio de Google Maps cache
        google_maps_dir = Path("static/google_maps_cache")
        if google_maps_dir.exists():
            for file_path in google_maps_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    image_paths.append(str(file_path))
                    logger.info(f"📁 Encontrada imagen Google Maps: {file_path}")

        logger.info(f"📊 Total de imágenes encontradas: {len(image_paths)}")
        return image_paths

    def get_already_processed_images(self) -> set:
        """
        Obtiene las imágenes que ya han sido procesadas.

        Returns:
            Set de rutas de imágenes ya procesadas
        """
        processed_images = set()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT image_path FROM ultra_hd_analysis")
            rows = cursor.fetchall()

            for row in rows:
                processed_images.add(row[0])

            conn.close()

        except Exception as e:
            logger.warning(f"Error obteniendo imágenes procesadas: {e}")

        logger.info(f"📊 Imágenes ya procesadas: {len(processed_images)}")
        return processed_images

    def process_batch(self, force_reprocess: bool = False):
        """
        Procesa todas las imágenes satelitales con YOLO.

        Args:
            force_reprocess: Si True, reprocesa todas las imágenes
        """
        logger.info("🚀 Iniciando procesamiento por lotes YOLO")
        logger.info(f"⏰ Timestamp: {datetime.now().isoformat()}")

        # Obtener todas las imágenes disponibles
        all_images = self.get_all_satellite_images()

        if not all_images:
            logger.warning("⚠️ No se encontraron imágenes para procesar")
            return

        # Obtener imágenes ya procesadas (si no es reproceso forzado)
        processed_images = set()
        if not force_reprocess:
            processed_images = self.get_already_processed_images()

        # Filtrar imágenes no procesadas
        images_to_process = []
        for image_path in all_images:
            if force_reprocess or image_path not in processed_images:
                images_to_process.append(image_path)
            else:
                logger.info(f"⏭️ Saltando imagen ya procesada: {os.path.basename(image_path)}")

        if not images_to_process:
            logger.info("✅ Todas las imágenes ya están procesadas")
            return

        logger.info(f"🎯 Imágenes a procesar: {len(images_to_process)}")

        # Procesar en lotes
        batch_size = 5  # Procesar de 5 en 5 para no sobrecargar
        total_batches = (len(images_to_process) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(images_to_process))
            batch_images = images_to_process[start_idx:end_idx]

            logger.info(f"🔄 Procesando lote {batch_num + 1}/{total_batches} ({len(batch_images)} imágenes)")

            try:
                # Procesar el lote
                results = self.yolo_system.process_satellite_image_batch(batch_images)

                # Actualizar estadísticas
                for result in results:
                    if result.get('detections'):
                        self.processed_count += 1
                        self.total_detections += len(result['detections'])
                    else:
                        self.errors_count += 1

                logger.info(f"✅ Lote {batch_num + 1} completado: {len(results)} procesadas")

            except Exception as e:
                logger.error(f"❌ Error procesando lote {batch_num + 1}: {e}")
                self.errors_count += len(batch_images)

            # Pequeña pausa entre lotes
            if batch_num < total_batches - 1:
                import time
                time.sleep(2)

        # Generar reporte final
        self.generate_final_report()

    def generate_final_report(self):
        """Genera un reporte final del procesamiento por lotes."""
        logger.info("📊 Generando reporte final...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_images_processed': self.processed_count,
            'total_errors': self.errors_count,
            'total_detections': self.total_detections,
            'success_rate': (self.processed_count / max(self.processed_count + self.errors_count, 1)) * 100,
            'avg_detections_per_image': self.total_detections / max(self.processed_count, 1)
        }

        # Guardar reporte en archivo
        report_path = f"reports/yolo_batch_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            os.makedirs("reports", exist_ok=True)

            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Reporte guardado: {report_path}")

        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")

        # Mostrar resumen en consola
        print("\n" + "="*60)
        print("📊 REPORTE DE PROCESAMIENTO YOLO POR LOTES")
        print("="*60)
        print(f"🖼️  Imágenes procesadas: {report['total_images_processed']}")
        print(f"❌ Errores: {report['total_errors']}")
        print(f"🎯 Detecciones totales: {report['total_detections']}")
        print(f"📊 Tasa de éxito: {report['success_rate']:.1f}%")
        print(f"🎯 Promedio detecciones/imagen: {report['avg_detections_per_image']:.1f}")
        print(f"📁 Reporte completo: {report_path}")
        print("="*60)

def main():
    """Función principal."""
    print("🛰️ RiskMap - Procesamiento por Lotes YOLO")
    print("="*50)

    # Parsear argumentos
    import argparse
    parser = argparse.ArgumentParser(description='Procesamiento por lotes YOLO para imágenes satelitales')
    parser.add_argument('--force', action='store_true', help='Forzar reprocesamiento de todas las imágenes')
    parser.add_argument('--batch-size', type=int, default=5, help='Tamaño del lote de procesamiento')

    args = parser.parse_args()

    try:
        # Inicializar procesador
        processor = BatchYOLOProcessor()

        # Ejecutar procesamiento
        processor.process_batch(force_reprocess=args.force)

        print("\n✅ Procesamiento completado exitosamente")

    except KeyboardInterrupt:
        print("\n⚠️ Procesamiento interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()