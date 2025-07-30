"""
Historical Analysis System Runner
Main script to initialize, configure, and run the comprehensive historical analysis system
for geopolitical risk assessment and prediction.
"""

import asyncio
import logging
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.analytics.historical_analysis_orchestrator import HistoricalAnalysisOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_config(args) -> dict:
    """Create configuration based on command line arguments"""
    config = {
        'data_dir': args.data_dir,
        'model_dir': args.model_dir,
        'output_dir': args.output_dir,
        'dashboard_port': args.port,
        'update_frequency_hours': args.update_frequency,
        'parallel_processing': not args.no_parallel,
        'cache_results': not args.no_cache,
        'data_sources': args.data_sources,
        'prediction_models': args.models,
        'pattern_detection_methods': args.pattern_methods,
        'forecast_horizon_days': args.forecast_days,
        'confidence_level': args.confidence
    }
    
    return config

async def run_initialization(orchestrator: HistoricalAnalysisOrchestrator):
    """Initialize the historical analysis system"""
    print("\n" + "="*60)
    print("INITIALIZING HISTORICAL ANALYSIS SYSTEM")
    print("="*60)
    
    init_result = await orchestrator.initialize_system()
    
    print(f"Initialization Status: {init_result['status']}")
    print(f"Components Initialized: {', '.join(init_result['components_initialized'])}")
    
    if init_result['errors']:
        print("Initialization Errors:")
        for error in init_result['errors']:
            print(f"  - {error}")
    
    return init_result['status'] in ['success', 'partial_success']

async def run_data_update(orchestrator: HistoricalAnalysisOrchestrator, force: bool = False):
    """Update historical data from all sources"""
    print("\n" + "="*60)
    print("UPDATING HISTORICAL DATA")
    print("="*60)
    
    update_result = await orchestrator.update_historical_data(force_update=force)
    
    print(f"Update Status: {update_result['status']}")
    
    if update_result['sources_updated']:
        print(f"Sources Updated: {', '.join(update_result['sources_updated'])}")
        
        for source, stats in update_result.get('statistics', {}).items():
            print(f"  {source}: {stats}")
    
    if update_result['errors']:
        print("Update Errors:")
        for error in update_result['errors']:
            print(f"  - {error}")
    
    return update_result['status'] in ['success', 'partial_success']

async def run_comprehensive_analysis(orchestrator: HistoricalAnalysisOrchestrator, 
                                   start_date: datetime = None,
                                   end_date: datetime = None,
                                   regions: list = None):
    """Run comprehensive historical analysis"""
    print("\n" + "="*60)
    print("RUNNING COMPREHENSIVE ANALYSIS")
    print("="*60)
    
    if not start_date:
        start_date = datetime.now() - timedelta(days=365 * 2)  # 2 years
    if not end_date:
        end_date = datetime.now()
    
    print(f"Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    if regions:
        print(f"Regions: {', '.join(regions)}")
    
    analysis_result = await orchestrator.run_comprehensive_analysis(
        start_date=start_date,
        end_date=end_date,
        regions=regions
    )
    
    print(f"Analysis Status: {analysis_result['status']}")
    print(f"Analysis ID: {analysis_result['analysis_id']}")
    print(f"Duration: {analysis_result.get('duration_seconds', 0):.1f} seconds")
    
    # Display results summary
    results = analysis_result.get('results', {})
    
    if 'data_loaded' in results:
        data_info = results['data_loaded']
        print(f"\nData Loaded: {data_info['records_count']} records")
        print(f"Date Range: {data_info['date_range']['start']} to {data_info['date_range']['end']}")
    
    if 'pattern_detection' in results:
        pattern_info = results['pattern_detection']
        if 'clustering' in pattern_info:
            clustering = pattern_info['clustering']
            print(f"\nPattern Detection:")
            print(f"  Methods Used: {', '.join(clustering.get('methods_used', []))}")
            for method, k in clustering.get('optimal_clusters', {}).items():
                print(f"  {method}: {k} clusters detected")
    
    if 'predictive_modeling' in results:
        pred_info = results['predictive_modeling']
        print(f"\nPredictive Modeling:")
        successful_models = [model for model, result in pred_info.items() 
                           if isinstance(result, dict) and 'error' not in result]
        print(f"  Successful Models: {', '.join(successful_models)}")
        
        if 'predictions' in pred_info:
            predictions = pred_info['predictions']
            print(f"  Forecast Horizon: {predictions.get('forecast_horizon', 0)} days")
            print(f"  Models Used: {', '.join(predictions.get('models_used', []))}")
    
    if 'insights' in results:
        insights = results['insights']
        print(f"\nKey Insights:")
        for category, insight_list in insights.items():
            if insight_list:
                print(f"  {category.replace('_', ' ').title()}:")
                for insight in insight_list[:3]:  # Show first 3 insights
                    print(f"    - {insight}")
    
    if 'alerts' in results:
        alerts = results['alerts']
        if alerts:
            print(f"\nAlerts Generated: {len(alerts)}")
            for alert in alerts[:5]:  # Show first 5 alerts
                print(f"  - {alert.get('type', 'unknown')}: {alert.get('message', 'No message')}")
    
    if analysis_result['errors']:
        print("\nAnalysis Errors:")
        for error in analysis_result['errors']:
            print(f"  - {error}")
    
    return analysis_result['status'] in ['success', 'partial_success']

async def start_dashboard(orchestrator: HistoricalAnalysisOrchestrator, debug: bool = False):
    """Start the interactive dashboard"""
    print("\n" + "="*60)
    print("STARTING INTERACTIVE DASHBOARD")
    print("="*60)
    
    dashboard_result = await orchestrator.start_dashboard(debug=debug)
    
    print(f"Dashboard Status: {dashboard_result['status']}")
    
    if dashboard_result['status'] == 'started':
        print(f"Dashboard URL: {dashboard_result['url']}")
        print(f"Debug Mode: {dashboard_result['debug_mode']}")
        print("\nDashboard is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the dashboard running
            while True:
                await asyncio.sleep(60)  # Check every minute
                status = await orchestrator.get_system_status()
                if status['system_status'] != 'operational':
                    print(f"System status changed to: {status['system_status']}")
                    break
        except KeyboardInterrupt:
            print("\nDashboard stopped by user.")
    else:
        print(f"Dashboard failed to start: {dashboard_result.get('error', 'Unknown error')}")

async def run_automated_cycle(orchestrator: HistoricalAnalysisOrchestrator, 
                            interval_hours: int = 24):
    """Run automated analysis cycle"""
    print("\n" + "="*60)
    print("STARTING AUTOMATED ANALYSIS CYCLE")
    print("="*60)
    print(f"Cycle Interval: {interval_hours} hours")
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running automated cycle...")
            
            cycle_result = await orchestrator.run_automated_analysis_cycle()
            
            print(f"Cycle Status: {cycle_result['cycle_status']}")
            
            if cycle_result['cycle_status'] == 'completed':
                print("Analysis cycle completed successfully")
            elif cycle_result['cycle_status'] == 'skipped':
                print(f"Cycle skipped: {cycle_result['reason']}")
            else:
                print(f"Cycle failed: {cycle_result.get('error', 'Unknown error')}")
            
            # Wait for next cycle
            print(f"Next cycle in {interval_hours} hours...")
            await asyncio.sleep(interval_hours * 3600)
            
    except KeyboardInterrupt:
        print("\nAutomated cycle stopped by user.")

async def display_system_status(orchestrator: HistoricalAnalysisOrchestrator):
    """Display current system status"""
    print("\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)
    
    status = await orchestrator.get_system_status()
    
    print(f"System Status: {status['system_status']}")
    print(f"Timestamp: {status['timestamp']}")
    
    analysis_state = status.get('analysis_state', {})
    print(f"\nAnalysis State:")
    print(f"  Data Loaded: {analysis_state.get('data_loaded', False)}")
    print(f"  Models Trained: {analysis_state.get('models_trained', False)}")
    print(f"  Patterns Detected: {analysis_state.get('patterns_detected', False)}")
    print(f"  Dashboard Ready: {analysis_state.get('dashboard_ready', False)}")
    
    if analysis_state.get('last_update'):
        print(f"  Last Update: {analysis_state['last_update']}")
    
    data_summary = status.get('data_summary', {})
    if data_summary:
        print(f"\nData Summary:")
        overall = data_summary.get('overall', {})
        print(f"  Total Events: {overall.get('total_events', 0)}")
        print(f"  Economic Indicators: {overall.get('total_economic_indicators', 0)}")
        print(f"  Data Sources: {overall.get('data_sources', 0)}")
    
    alerts = status.get('active_alerts', [])
    if alerts:
        print(f"\nActive Alerts: {len(alerts)}")
        for alert in alerts[:3]:  # Show first 3 alerts
            print(f"  - {alert.get('type', 'unknown')}: {alert.get('message', 'No message')}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Historical Analysis System')
    
    # Configuration arguments
    parser.add_argument('--data-dir', default='datasets/historical', 
                       help='Directory for historical data storage')
    parser.add_argument('--model-dir', default='models/predictive',
                       help='Directory for predictive models')
    parser.add_argument('--output-dir', default='outputs/patterns',
                       help='Directory for analysis outputs')
    parser.add_argument('--port', type=int, default=8051,
                       help='Dashboard port')
    parser.add_argument('--update-frequency', type=int, default=24,
                       help='Data update frequency in hours')
    parser.add_argument('--forecast-days', type=int, default=30,
                       help='Forecast horizon in days')
    parser.add_argument('--confidence', type=float, default=0.8,
                       help='Confidence level for predictions')
    
    # Feature flags
    parser.add_argument('--no-parallel', action='store_true',
                       help='Disable parallel processing')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable result caching')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--force-update', action='store_true',
                       help='Force data update')
    
    # Data sources
    parser.add_argument('--data-sources', nargs='+', 
                       default=['ucdp_ged', 'emdat', 'world_bank'],
                       help='Data sources to use')
    
    # Models
    parser.add_argument('--models', nargs='+',
                       default=['prophet', 'lstm', 'arima', 'ensemble'],
                       help='Prediction models to train')
    
    # Pattern detection methods
    parser.add_argument('--pattern-methods', nargs='+',
                       default=['kmeans', 'dbscan', 'isolation_forest'],
                       help='Pattern detection methods')
    
    # Operation mode
    parser.add_argument('--mode', choices=['full', 'init', 'update', 'analyze', 'dashboard', 'status', 'auto'],
                       default='full', help='Operation mode')
    
    # Analysis parameters
    parser.add_argument('--start-date', type=str,
                       help='Analysis start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='Analysis end date (YYYY-MM-DD)')
    parser.add_argument('--regions', nargs='+',
                       help='Regions to analyze')
    parser.add_argument('--auto-interval', type=int, default=24,
                       help='Automated cycle interval in hours')
    
    args = parser.parse_args()
    
    # Create directories
    Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    async def run_system():
        """Run the system based on mode"""
        # Create configuration
        config = create_config(args)
        
        # Initialize orchestrator
        orchestrator = HistoricalAnalysisOrchestrator(config)
        
        try:
            if args.mode in ['full', 'init']:
                success = await run_initialization(orchestrator)
                if not success and args.mode == 'init':
                    return
            
            if args.mode in ['full', 'update']:
                success = await run_data_update(orchestrator, force=args.force_update)
                if not success and args.mode == 'update':
                    return
            
            if args.mode in ['full', 'analyze']:
                success = await run_comprehensive_analysis(
                    orchestrator, start_date, end_date, args.regions
                )
                if not success and args.mode == 'analyze':
                    return
            
            if args.mode == 'dashboard':
                await start_dashboard(orchestrator, debug=args.debug)
            
            elif args.mode == 'status':
                await display_system_status(orchestrator)
            
            elif args.mode == 'auto':
                await run_automated_cycle(orchestrator, args.auto_interval)
            
            elif args.mode == 'full':
                # Show final status
                await display_system_status(orchestrator)
                
                # Optionally start dashboard
                print(f"\nSystem ready! You can now:")
                print(f"  - View dashboard: python {__file__} --mode dashboard")
                print(f"  - Check status: python {__file__} --mode status")
                print(f"  - Run auto cycle: python {__file__} --mode auto")
        
        except Exception as e:
            logger.error(f"Critical error in system execution: {e}")
            raise
    
    # Run the system
    try:
        asyncio.run(run_system())
    except KeyboardInterrupt:
        print("\nSystem stopped by user.")
    except Exception as e:
        print(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()