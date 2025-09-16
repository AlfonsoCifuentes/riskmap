"""
Sistema Completo de Análisis Geopolítico
========================================
Orchestador principal que ejecuta todo el pipeline de manera automatizada.
"""

import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geopolitical_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeopoliticalSystemOrchestrator:
    """Orchestador principal del sistema de análisis geopolítico"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.models_dir = self.project_root / "models" / "trained"
        
        # Rutas de bases de datos
        self.original_db = self.data_dir / "geopolitical_intel.db"
        self.trained_db = self.data_dir / "trained_analysis.db"
        
        # Verificar estructura de directorios
        self.setup_directories()
        
    def setup_directories(self):
        """Crear estructura de directorios necesaria"""
        dirs_to_create = [
            self.data_dir,
            self.data_dir / "image_cache",
            self.models_dir,
            self.project_root / "logs",
            self.project_root / "output"
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        logger.info("✅ Estructura de directorios verificada")
    
    def check_dependencies(self):
        """Verificar que todas las dependencias estén instaladas"""
        logger.info("🔍 Verificando dependencias...")
        
        required_packages = [
            'torch', 'transformers', 'peft', 'datasets',
            'pandas', 'numpy', 'scikit-learn',
            'requests', 'beautifulsoup4', 'selenium',
            'feedparser', 'opencv-python', 'Pillow'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"  ❌ {package} no encontrado")
        
        if missing_packages:
            logger.error(f"❌ Faltan dependencias: {missing_packages}")
            logger.info("💡 Ejecuta: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("✅ Todas las dependencias están instaladas")
        return True
    
    def run_data_ingestion(self, max_articles=100):
        """Ejecutar ingesta de datos"""
        logger.info("📡 Iniciando ingesta de datos...")
        
        try:
            from data_ingestion import GeopoliticalDataIngestion
            
            ingestion_system = GeopoliticalDataIngestion(
                db_path=str(self.original_db),
                trained_db_path=str(self.trained_db)
            )
            
            # Ejecutar ingesta
            ingestion_system.run_ingestion(max_articles_per_source=max_articles)
            
            # Crear dataset de entrenamiento
            training_df = ingestion_system.create_training_dataset(sample_size=1000)
            
            logger.info(f"✅ Ingesta completada: {len(training_df)} artículos para entrenamiento")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en ingesta de datos: {e}")
            return False
    
    def run_auto_labeling(self, max_articles=1500):
        """Ejecutar etiquetado automático"""
        logger.info("🏷️ Iniciando etiquetado automático...")
        
        try:
            from auto_labeler import GeopoliticalAutoLabeler
            
            auto_labeler = GeopoliticalAutoLabeler(str(self.trained_db))
            
            # Etiquetar artículos
            labeled_count = auto_labeler.auto_label_articles(limit=max_articles)
            
            # Crear splits de entrenamiento
            splits_info = auto_labeler.create_training_splits()
            
            # Exportar datos
            _, _ = auto_labeler.export_training_data()
            
            logger.info(f"✅ Etiquetado completado: {labeled_count} artículos")
            logger.info(f"📊 Splits: {splits_info}")
            
            return True, splits_info
            
        except Exception as e:
            logger.error(f"❌ Error en etiquetado automático: {e}")
            return False, {}
    
    def run_model_training(self):
        """Ejecutar entrenamiento del modelo usando el notebook"""
        logger.info("🤖 Iniciando entrenamiento del modelo...")
        
        notebook_path = self.models_dir / "ai_training_bert_lora_geopolitical_intelligence.ipynb"
        
        if not notebook_path.exists():
            logger.error(f"❌ Notebook no encontrado: {notebook_path}")
            return False
        
        try:
            # Ejecutar notebook con nbconvert
            cmd = [
                "jupyter", "nbconvert", 
                "--to", "notebook",
                "--execute",
                "--inplace",
                str(notebook_path)
            ]
            
            logger.info("🚀 Ejecutando notebook de entrenamiento...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hora timeout
            
            if result.returncode == 0:
                logger.info("✅ Entrenamiento completado exitosamente")
                
                # Verificar que se creó el modelo
                model_path = self.models_dir / "best_model.pt"
                if model_path.exists():
                    logger.info(f"✅ Modelo guardado en: {model_path}")
                    return True
                else:
                    logger.warning("⚠️ Entrenamiento completado pero modelo no encontrado")
                    return False
            else:
                logger.error(f"❌ Error en entrenamiento: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout en entrenamiento (>1 hora)")
            return False
        except Exception as e:
            logger.error(f"❌ Error ejecutando entrenamiento: {e}")
            return False
    
    def run_inference_analysis(self, max_articles=50):
        """Ejecutar análisis de inferencia"""
        logger.info("🔮 Iniciando análisis de inferencia...")
        
        model_path = self.models_dir / "best_model.pt"
        if not model_path.exists():
            logger.error(f"❌ Modelo no encontrado: {model_path}")
            logger.info("💡 Ejecuta primero el entrenamiento del modelo")
            return False
        
        try:
            from inference_engine import GeopoliticalInferenceEngine
            
            # Crear motor de inferencia
            engine = GeopoliticalInferenceEngine(
                model_path=str(model_path),
                db_path=str(self.trained_db)
            )
            
            # Ejecutar análisis en lote
            results = engine.batch_analyze(limit=max_articles)
            
            # Obtener datos de dashboard
            dashboard_data = engine.get_dashboard_data()
            
            logger.info(f"✅ Análisis completado: {len(results)} artículos")
            logger.info(f"🚨 Alertas activas: {len(dashboard_data['active_alerts'])}")
            
            # Guardar resumen del análisis
            summary = {
                'timestamp': datetime.now().isoformat(),
                'articles_analyzed': len(results),
                'active_alerts': len(dashboard_data['active_alerts']),
                'dashboard_data': dashboard_data
            }
            
            summary_path = self.project_root / "output" / f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"📊 Resumen guardado en: {summary_path}")
            
            return True, dashboard_data
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de inferencia: {e}")
            return False, {}
    
    def run_full_pipeline(self, skip_training=False):
        """Ejecutar pipeline completo"""
        logger.info("🚀 Iniciando pipeline completo de análisis geopolítico")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. Verificar dependencias
        if not self.check_dependencies():
            return False
        
        # 2. Ingesta de datos
        logger.info("\n📡 FASE 1: Ingesta de Datos")
        if not self.run_data_ingestion(max_articles=30):
            logger.error("❌ Fallo en ingesta de datos")
            return False
        
        # 3. Etiquetado automático
        logger.info("\n🏷️ FASE 2: Etiquetado Automático")
        success, splits_info = self.run_auto_labeling(max_articles=1000)
        if not success:
            logger.error("❌ Fallo en etiquetado automático")
            return False
        
        # 4. Entrenamiento del modelo (opcional)
        if not skip_training:
            logger.info("\n🤖 FASE 3: Entrenamiento del Modelo")
            if not self.run_model_training():
                logger.error("❌ Fallo en entrenamiento del modelo")
                return False
        else:
            logger.info("\n⏭️ FASE 3: Entrenamiento omitido")
        
        # 5. Análisis de inferencia
        logger.info("\n🔮 FASE 4: Análisis de Inferencia")
        success, dashboard_data = self.run_inference_analysis(max_articles=100)
        if not success:
            logger.error("❌ Fallo en análisis de inferencia")
            return False
        
        # Resumen final
        total_time = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 PIPELINE COMPLETADO EXITOSAMENTE")
        logger.info("=" * 60)
        logger.info(f"⏱️ Tiempo total: {total_time/60:.1f} minutos")
        logger.info(f"📊 Datos de entrenamiento: {splits_info}")
        logger.info(f"🚨 Alertas generadas: {len(dashboard_data.get('active_alerts', []))}")
        logger.info(f"📁 Resultados en: {self.project_root}/output/")
        
        return True
    
    def run_monitoring_mode(self, interval_hours=6):
        """Ejecutar en modo monitoreo continuo"""
        logger.info(f"👁️ Iniciando modo monitoreo (cada {interval_hours} horas)")
        
        while True:
            try:
                logger.info(f"\n🔄 Ciclo de monitoreo - {datetime.now()}")
                
                # Solo ingesta, etiquetado e inferencia (no re-entrenar)
                self.run_data_ingestion(max_articles=20)
                self.run_auto_labeling(max_articles=500)
                self.run_inference_analysis(max_articles=100)
                
                logger.info(f"✅ Ciclo completado. Siguiente en {interval_hours} horas.")
                time.sleep(interval_hours * 3600)  # Convertir a segundos
                
            except KeyboardInterrupt:
                logger.info("⏹️ Monitoreo detenido por el usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")
                logger.info(f"⏰ Reintentando en {interval_hours} horas...")
                time.sleep(interval_hours * 3600)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Sistema de Análisis Geopolítico")
    parser.add_argument("--mode", choices=['full', 'ingestion', 'labeling', 'training', 'inference', 'monitor'], 
                       default='full', help="Modo de ejecución")
    parser.add_argument("--skip-training", action='store_true', help="Omitir entrenamiento en modo full")
    parser.add_argument("--monitor-interval", type=int, default=6, help="Intervalo de monitoreo en horas")
    
    args = parser.parse_args()
    
    # Crear orchestador
    orchestrator = GeopoliticalSystemOrchestrator()
    
    if args.mode == 'full':
        success = orchestrator.run_full_pipeline(skip_training=args.skip_training)
        sys.exit(0 if success else 1)
    
    elif args.mode == 'ingestion':
        success = orchestrator.run_data_ingestion()
        sys.exit(0 if success else 1)
    
    elif args.mode == 'labeling':
        success, _ = orchestrator.run_auto_labeling()
        sys.exit(0 if success else 1)
    
    elif args.mode == 'training':
        success = orchestrator.run_model_training()
        sys.exit(0 if success else 1)
    
    elif args.mode == 'inference':
        success, _ = orchestrator.run_inference_analysis()
        sys.exit(0 if success else 1)
    
    elif args.mode == 'monitor':
        orchestrator.run_monitoring_mode(interval_hours=args.monitor_interval)

if __name__ == "__main__":
    main()
