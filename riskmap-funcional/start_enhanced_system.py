"""
Enhanced Geopolitical Intelligence System Startup Script
Launches the complete AI-powered conflict monitoring system with all capabilities.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/enhanced_system.log')
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'torch', 'transformers', 'ultralytics', 'opencv-python',
        'scikit-learn', 'pandas', 'numpy', 'fastapi', 'uvicorn',
        'prophet', 'plotly', 'jinja2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Please install missing packages using:")
        logger.info(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'reports',
        'templates',
        'src/data',
        'models/huggingface'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def download_models():
    """Download required AI models"""
    try:
        logger.info("Downloading required AI models...")
        
        # Download YOLOv8 model
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        logger.info("YOLOv8 model downloaded")
        
        # Download transformer models (they will be cached automatically)
        from transformers import AutoTokenizer, AutoModelForTokenClassification
        
        models_to_download = [
            "xlm-roberta-large-finetuned-conll03-english",
            "cardiffnlp/twitter-xlm-roberta-base-sentiment",
            "facebook/bart-large-cnn"
        ]
        
        for model_name in models_to_download:
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                logger.info(f"Downloaded tokenizer for {model_name}")
            except Exception as e:
                logger.warning(f"Could not download {model_name}: {e}")
        
        logger.info("Model download completed")
        
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        return False
    
    return True

def run_system_tests():
    """Run basic system tests"""
    try:
        logger.info("Running system tests...")
        
        # Test orchestrator initialization
        from src.orchestration.enhanced_orchestrator import EnhancedGeopoliticalOrchestrator
        orchestrator = EnhancedGeopoliticalOrchestrator()
        
        # Test basic functionality
        status = orchestrator.get_system_status()
        if status.get('components', {}).get('ner_processor'):
            logger.info("✓ NER processor initialized")
        
        if status.get('components', {}).get('conflict_classifier'):
            logger.info("✓ Conflict classifier initialized")
        
        if status.get('components', {}).get('vision_analyzer'):
            logger.info("✓ Vision analyzer initialized")
        
        logger.info("System tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"System tests failed: {e}")
        return False

def start_api_server(host="0.0.0.0", port=8000, reload=False):
    """Start the enhanced API server"""
    try:
        logger.info(f"Starting Enhanced Geopolitical Intelligence API on {host}:{port}")
        
        from src.api.enhanced_api import run_api
        run_api(host=host, port=port, reload=reload)
        
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        return False

def start_monitoring():
    """Start real-time monitoring"""
    try:
        logger.info("Starting real-time conflict monitoring...")
        
        from src.orchestration.enhanced_orchestrator import EnhancedGeopoliticalOrchestrator
        orchestrator = EnhancedGeopoliticalOrchestrator()
        
        # Start monitoring
        result = orchestrator.start_real_time_monitoring()
        
        if result.get('status') == 'monitoring_started':
            logger.info("✓ Real-time monitoring started successfully")
            return True
        else:
            logger.error("Failed to start monitoring")
            return False
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return False

def run_comprehensive_analysis():
    """Run a comprehensive analysis"""
    try:
        logger.info("Running comprehensive geopolitical analysis...")
        
        from src.orchestration.enhanced_orchestrator import EnhancedGeopoliticalOrchestrator
        orchestrator = EnhancedGeopoliticalOrchestrator()
        
        # Run analysis
        results = orchestrator.run_comprehensive_analysis(
            include_data_collection=True,
            include_vision_analysis=False,  # Disable for initial run
            generate_reports=True
        )
        
        if 'error' not in results:
            logger.info("✓ Comprehensive analysis completed successfully")
            
            # Print summary
            summary = results.get('summary', {})
            logger.info(f"Analysis Summary:")
            logger.info(f"  - Articles analyzed: {summary.get('data_processed', {}).get('articles_analyzed', 0)}")
            logger.info(f"  - Threat level: {summary.get('threat_level', 'unknown')}")
            logger.info(f"  - Alerts generated: {summary.get('alerts_generated', 0)}")
            logger.info(f"  - Reports generated: {summary.get('reports_generated', 0)}")
            
            return True
        else:
            logger.error(f"Analysis failed: {results.get('error')}")
            return False
        
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        return False

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Enhanced Geopolitical Intelligence System",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'test', 'api', 'monitor', 'analyze', 'full'],
        help="""Command to execute:
  setup    - Setup system (check deps, create dirs, download models)
  test     - Run system tests
  api      - Start API server
  monitor  - Start real-time monitoring
  analyze  - Run comprehensive analysis
  full     - Complete setup and start all services"""
    )
    
    parser.add_argument('--host', default='0.0.0.0', help='API host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--skip-models', action='store_true', help='Skip model download')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'setup':
            logger.info("Setting up Enhanced Geopolitical Intelligence System...")
            
            # Check dependencies
            if not check_dependencies():
                sys.exit(1)
            
            # Setup directories
            setup_directories()
            
            # Download models
            if not args.skip_models:
                if not download_models():
                    logger.warning("Model download failed, but continuing...")
            
            logger.info("✓ System setup completed successfully")
        
        elif args.command == 'test':
            logger.info("Running system tests...")
            
            if not check_dependencies():
                sys.exit(1)
            
            if run_system_tests():
                logger.info("✓ All tests passed")
            else:
                logger.error("✗ Tests failed")
                sys.exit(1)
        
        elif args.command == 'api':
            logger.info("Starting API server...")
            
            if not check_dependencies():
                sys.exit(1)
            
            start_api_server(host=args.host, port=args.port, reload=args.reload)
        
        elif args.command == 'monitor':
            logger.info("Starting real-time monitoring...")
            
            if not check_dependencies():
                sys.exit(1)
            
            if start_monitoring():
                logger.info("Monitoring started. Press Ctrl+C to stop.")
                try:
                    import time
                    while True:
                        time.sleep(60)
                        logger.info("Monitoring active...")
                except KeyboardInterrupt:
                    logger.info("Monitoring stopped by user")
            else:
                sys.exit(1)
        
        elif args.command == 'analyze':
            logger.info("Running comprehensive analysis...")
            
            if not check_dependencies():
                sys.exit(1)
            
            if run_comprehensive_analysis():
                logger.info("✓ Analysis completed successfully")
            else:
                logger.error("✗ Analysis failed")
                sys.exit(1)
        
        elif args.command == 'full':
            logger.info("Starting complete Enhanced Geopolitical Intelligence System...")
            
            # Setup
            if not check_dependencies():
                sys.exit(1)
            
            setup_directories()
            
            if not args.skip_models:
                download_models()
            
            # Test
            if not run_system_tests():
                logger.error("System tests failed")
                sys.exit(1)
            
            # Run initial analysis
            logger.info("Running initial analysis...")
            run_comprehensive_analysis()
            
            # Start monitoring
            logger.info("Starting monitoring...")
            start_monitoring()
            
            # Start API server
            logger.info("Starting API server...")
            start_api_server(host=args.host, port=args.port, reload=args.reload)
    
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()