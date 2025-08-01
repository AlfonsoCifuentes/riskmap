#!/usr/bin/env python3
"""
Script de entrenamiento para el modelo xView2 de evaluación de daños
Entrena el modelo usando datos satelitales existentes y datos xView2 si están disponibles
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from vision_analysis.xview2_trainer import XView2DamageClassifier

def setup_logging(log_level=logging.INFO):
    """Configura el logging"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'xview2_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Train xView2 Damage Assessment Model')
    parser.add_argument('--data-dir', 
                       default='models/xView2_baseline-master/data',
                       help='Directory containing xView2 data')
    parser.add_argument('--satellite-dir', 
                       default='data/satellite_images',
                       help='Directory containing satellite images')
    parser.add_argument('--model-dir', 
                       default='models/xview2_damage',
                       help='Directory to save trained model')
    parser.add_argument('--epochs', 
                       type=int, 
                       default=50,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', 
                       type=int, 
                       default=32,
                       help='Batch size for training')
    parser.add_argument('--use-xview2', 
                       action='store_true',
                       help='Use xView2 dataset if available')
    parser.add_argument('--use-satellite', 
                       action='store_true', 
                       default=True,
                       help='Use existing satellite images')
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    # Configuration
    config = {
        'model_dir': args.model_dir,
        'data_dir': args.data_dir,
        'cache_dir': args.satellite_dir,
        'use_gpu': True,
        'random_seed': 42
    }
    
    logger.info("🛰️ Starting xView2 Damage Assessment Training")
    logger.info(f"Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Use xView2 data: {args.use_xview2}")
    logger.info(f"Use satellite data: {args.use_satellite}")
    
    try:
        # Initialize trainer
        trainer = XView2DamageClassifier(config)
        trainer.epochs = args.epochs
        trainer.batch_size = args.batch_size
        
        # Check data availability
        satellite_images = list(Path(args.satellite_dir).glob('*.png'))
        satellite_images.extend(list(Path(args.satellite_dir).glob('*.jpg')))
        
        logger.info(f"Found {len(satellite_images)} satellite images")
        
        xview2_data_available = Path(args.data_dir).exists()
        logger.info(f"xView2 data available: {xview2_data_available}")
        
        if not satellite_images and not (args.use_xview2 and xview2_data_available):
            logger.error("No training data available!")
            logger.error("Please ensure you have either:")
            logger.error("1. Satellite images in the satellite directory, or")
            logger.error("2. xView2 dataset and --use-xview2 flag")
            return 1
        
        # Train model
        logger.info("Starting training...")
        history = trainer.train_model(
            use_satellite_data=args.use_satellite,
            use_xview2_data=args.use_xview2 and xview2_data_available
        )
        
        if history:
            logger.info("✅ Training completed successfully!")
            
            # Get model info
            model_info = trainer.get_model_info()
            
            if 'evaluation_results' in model_info:
                eval_results = model_info['evaluation_results']
                logger.info(f"📊 Final Results:")
                logger.info(f"   Validation Accuracy: {eval_results['validation_accuracy']:.4f}")
                logger.info(f"   Validation Loss: {eval_results['validation_loss']:.4f}")
                
                # Print class-wise results
                if 'classification_report' in eval_results:
                    report = eval_results['classification_report']
                    logger.info("   Class-wise Performance:")
                    for class_name, metrics in report.items():
                        if isinstance(metrics, dict) and 'f1-score' in metrics:
                            logger.info(f"     {class_name}: F1={metrics['f1-score']:.3f}, "
                                      f"Precision={metrics['precision']:.3f}, "
                                      f"Recall={metrics['recall']:.3f}")
            
            # Test prediction on sample image
            if satellite_images:
                logger.info("🧪 Testing prediction on sample image...")
                sample_img = satellite_images[0]
                result = trainer.predict_damage(str(sample_img))
                
                logger.info(f"Sample prediction for {sample_img.name}:")
                logger.info(f"   Damage class: {result.get('damage_class', 'unknown')}")
                logger.info(f"   Confidence: {result.get('confidence', 0):.2%}")
                logger.info(f"   Risk level: {result.get('risk_level', 'unknown')}")
                
                # Show all probabilities
                if 'all_probabilities' in result:
                    logger.info("   All class probabilities:")
                    for class_name, prob in result['all_probabilities'].items():
                        logger.info(f"     {class_name}: {prob:.3f}")
            
            # Save summary
            summary_path = Path(args.model_dir) / 'training_summary.txt'
            with open(summary_path, 'w') as f:
                f.write(f"xView2 Damage Assessment Training Summary\n")
                f.write(f"=========================================\n\n")
                f.write(f"Training Date: {datetime.now().isoformat()}\n")
                f.write(f"Epochs: {args.epochs}\n")
                f.write(f"Batch Size: {args.batch_size}\n")
                f.write(f"Satellite Images Used: {len(satellite_images)}\n")
                f.write(f"xView2 Data Used: {args.use_xview2 and xview2_data_available}\n\n")
                
                if 'evaluation_results' in model_info:
                    eval_results = model_info['evaluation_results']
                    f.write(f"Final Validation Accuracy: {eval_results['validation_accuracy']:.4f}\n")
                    f.write(f"Final Validation Loss: {eval_results['validation_loss']:.4f}\n")
            
            logger.info(f"📝 Training summary saved to: {summary_path}")
            
        else:
            logger.error("❌ Training failed!")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Error during training: {e}", exc_info=True)
        return 1
    
    logger.info("🎉 Training process completed!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
