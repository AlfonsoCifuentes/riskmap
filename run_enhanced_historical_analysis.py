"""
Enhanced Historical Analysis System Runner
Main script for the comprehensive multivariate relational analysis system that integrates
energy, climate, political, health, and resource variables for geopolitical risk assessment.
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

from src.analytics.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_historical_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_enhanced_config(args) -> dict:
    """Create enhanced configuration based on command line arguments"""
    config = {
        # Base configuration
        'data_dir': args.data_dir,
        'model_dir': args.model_dir,
        'output_dir': args.output_dir,
        'dashboard_port': args.port,
        'update_frequency_hours': args.update_frequency,
        'parallel_processing': not args.no_parallel,
        'cache_results': not args.no_cache,
        
        # Enhanced multivariate configuration
        'multivariate_data_dir': args.multivariate_data_dir,
        'relationships_output_dir': args.relationships_output_dir,
        'multivariate_dashboard_port': args.multivariate_port,
        
        # Data sources configuration
        'energy_data_sources': args.energy_sources,
        'climate_data_sources': args.climate_sources,
        'political_data_sources': args.political_sources,
        'health_data_sources': args.health_sources,
        'resource_data_sources': args.resource_sources,
        
        # Analysis configuration
        'correlation_methods': args.correlation_methods,
        'causality_max_lags': args.max_lags,
        'significance_level': args.significance_level,
        'min_correlation_threshold': args.min_correlation,
        'network_edge_threshold': args.network_threshold,
        
        # Real-time analysis
        'enable_real_time_analysis': not args.no_real_time,
        'batch_processing_interval_hours': args.batch_interval,
        
        # Prediction models
        'prediction_models': args.models,
        'pattern_detection_methods': args.pattern_methods,
        'forecast_horizon_days': args.forecast_days,
        'confidence_level': args.confidence
    }
    
    return config

async def run_enhanced_initialization(orchestrator: EnhancedHistoricalOrchestrator):
    """Initialize the enhanced historical analysis system"""
    print("\n" + "="*70)
    print("INITIALIZING ENHANCED HISTORICAL ANALYSIS SYSTEM")
    print("="*70)
    
    init_result = await orchestrator.initialize_enhanced_system()
    
    print(f"Initialization Status: {init_result['status']}")
    
    # Base system initialization
    base_init = init_result.get('base_initialization', {})
    if base_init:
        print(f"Base Components: {', '.join(base_init.get('components_initialized', []))}")
    
    # Enhanced components
    enhanced_components = init_result.get('enhanced_components', [])
    if enhanced_components:
        print(f"Enhanced Components: {', '.join(enhanced_components)}")
    
    if init_result.get('errors'):
        print("Initialization Errors:")
        for error in init_result['errors']:
            print(f"  - {error}")
    
    return init_result['status'] in ['success', 'partial_success']

async def run_multivariate_data_update(orchestrator: EnhancedHistoricalOrchestrator, force: bool = False):
    """Update multivariate data from all sources"""
    print("\n" + "="*70)
    print("UPDATING MULTIVARIATE DATA")
    print("="*70)
    
    update_result = await orchestrator.update_multivariate_data(force_update=force)
    
    print(f"Update Status: {update_result['status']}")
    
    categories_updated = update_result.get('data_categories_updated', [])
    if categories_updated:
        print(f"Data Categories Updated: {', '.join(categories_updated)}")
    
    integration_summary = update_result.get('integration_summary', {})
    if integration_summary:
        metadata = integration_summary.get('metadata', {})
        if metadata:
            print(f"Variables Integrated: {metadata.get('variables', {}).get('total_count', 0)}")
            print(f"Data Completeness: {metadata.get('data_quality', {}).get('completeness', 0):.1%}")
    
    if update_result.get('errors'):
        print("Update Errors:")
        for error in update_result['errors']:
            print(f"  - {error}")
    
    return update_result['status'] in ['success', 'partial_success']

async def run_comprehensive_multivariate_analysis(orchestrator: EnhancedHistoricalOrchestrator,
                                                 start_date: datetime = None,
                                                 end_date: datetime = None,
                                                 target_variable: str = 'conflict_risk'):
    """Run comprehensive multivariate analysis"""
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE MULTIVARIATE ANALYSIS")
    print("="*70)
    
    if not start_date:
        start_date = datetime.now() - timedelta(days=365 * 3)  # 3 years
    if not end_date:
        end_date = datetime.now()
    
    print(f"Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Target Variable: {target_variable}")
    
    analysis_result = await orchestrator.run_comprehensive_multivariate_analysis(
        start_date=start_date,
        end_date=end_date,
        target_variable=target_variable
    )
    
    print(f"Analysis Status: {analysis_result['status']}")
    print(f"Analysis ID: {analysis_result['analysis_id']}")
    print(f"Duration: {analysis_result.get('duration_seconds', 0):.1f} seconds")
    
    # Display results summary
    results = analysis_result.get('results', {})
    
    # Data summary
    if 'data_summary' in results:
        data_info = results['data_summary']
        print(f"\nData Summary:")
        print(f"  Records: {data_info['records_count']}")
        print(f"  Variables: {data_info['variables_count']}")
        print(f"  Completeness: {data_info['completeness']:.1%}")
    
    # Correlation analysis
    if 'correlation' in results:
        corr_info = results['correlation']
        if 'correlations' in corr_info and 'pearson' in corr_info['correlations']:
            pearson_corrs = corr_info['correlations']['pearson']
            strong_corrs = {k: v for k, v in pearson_corrs.items() if abs(v) > 0.5}
            print(f"\nCorrelation Analysis:")
            print(f"  Variables Analyzed: {len(pearson_corrs)}")
            print(f"  Strong Correlations: {len(strong_corrs)}")
            
            if strong_corrs:
                strongest = max(strong_corrs.items(), key=lambda x: abs(x[1]))
                print(f"  Strongest Correlation: {strongest[0]} (r={strongest[1]:.3f})")
    
    # Causality analysis
    if 'causality' in results:
        causality_info = results['causality']
        significant_relationships = causality_info.get('significant_relationships', {})
        print(f"\nCausality Analysis:")
        print(f"  Variables Tested: {len(causality_info.get('causality_tests', {}))}")
        print(f"  Significant Causal Relationships: {len(significant_relationships)}")
        
        if significant_relationships:
            strongest_causal = min(significant_relationships.items(), 
                                 key=lambda x: x[1]['min_pvalue'])
            print(f"  Strongest Causal Relationship: {strongest_causal[0]} (p={strongest_causal[1]['min_pvalue']:.4f})")
    
    # Feature importance
    if 'feature_importance' in results:
        importance_info = results['feature_importance']
        if 'top_features' in importance_info and 'aggregated' in importance_info['top_features']:
            top_features = importance_info['top_features']['aggregated'][:5]
            print(f"\nFeature Importance:")
            print(f"  Features Analyzed: {importance_info.get('n_features', 0)}")
            print(f"  Top 5 Features:")
            for i, (feature, importance) in enumerate(top_features, 1):
                print(f"    {i}. {feature}: {importance:.3f}")
    
    # Threshold effects
    if 'threshold_effects' in results:
        threshold_info = results['threshold_effects']
        significant_thresholds = threshold_info.get('significant_thresholds', {})
        print(f"\nThreshold Effects:")
        print(f"  Variables Tested: {len(threshold_info.get('threshold_effects', {}))}")
        print(f"  Significant Thresholds: {len(significant_thresholds)}")
    
    # Network analysis
    if 'relationship_network' in results:
        network_info = results['relationship_network']
        network_stats = network_info.get('network_stats', {})
        print(f"\nRelationship Network:")
        print(f"  Nodes: {network_stats.get('nodes', 0)}")
        print(f"  Edges: {network_stats.get('edges', 0)}")
        print(f"  Density: {network_stats.get('density', 0):.3f}")
    
    # Key insights
    if 'insights' in results:
        insights = results['insights']
        print(f"\nKey Insights:")
        
        # Show insights from each category
        for category, insight_list in insights.items():
            if insight_list and isinstance(insight_list, list):
                print(f"  {category.replace('_', ' ').title()}:")
                for insight in insight_list[:2]:  # Show first 2 insights
                    print(f"    - {insight}")
    
    # Executive report
    if 'executive_report' in results:
        exec_report = results['executive_report']
        print(f"\nExecutive Summary:")
        exec_summary = exec_report.get('executive_summary', {})
        key_findings = exec_summary.get('key_findings', [])
        for i, finding in enumerate(key_findings[:3], 1):
            print(f"  {i}. {finding}")
    
    if analysis_result.get('errors'):
        print("\nAnalysis Errors:")
        for error in analysis_result['errors']:
            print(f"  - {error}")
    
    return analysis_result['status'] in ['success', 'partial_success']

async def start_multivariate_dashboard(orchestrator: EnhancedHistoricalOrchestrator, debug: bool = False):
    """Start the multivariate dashboard"""
    print("\n" + "="*70)
    print("STARTING MULTIVARIATE RELATIONSHIP DASHBOARD")
    print("="*70)
    
    dashboard_result = await orchestrator.start_multivariate_dashboard(debug=debug)
    
    print(f"Dashboard Status: {dashboard_result['status']}")
    
    if dashboard_result['status'] == 'started':
        print(f"Dashboard URL: {dashboard_result['url']}")
        print(f"Debug Mode: {dashboard_result['debug_mode']}")
        print("\nMultivariate dashboard is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the dashboard running
            while True:
                await asyncio.sleep(60)  # Check every minute
                status = await orchestrator.get_enhanced_system_status()
                if status['system_status'] != 'operational':
                    print(f"System status changed to: {status['system_status']}")
                    break
        except KeyboardInterrupt:
            print("\nMultivariate dashboard stopped by user.")
    else:
        print(f"Dashboard failed to start: {dashboard_result.get('error', 'Unknown error')}")

async def run_real_time_analysis(orchestrator: EnhancedHistoricalOrchestrator):
    """Run real-time multivariate analysis"""
    print("\n" + "="*70)
    print("RUNNING REAL-TIME MULTIVARIATE ANALYSIS")
    print("="*70)
    
    real_time_result = await orchestrator.run_real_time_analysis()
    
    print(f"Real-time Analysis Status: {real_time_result['status']}")
    
    if real_time_result['status'] == 'completed':
        print(f"Analysis Timestamp: {real_time_result['analysis_timestamp']}")
        
        data_period = real_time_result.get('data_period', {})
        print(f"Data Period: {data_period.get('start')} to {data_period.get('end')}")
        
        data_quality = real_time_result.get('data_quality', {})
        print(f"Data Quality: {data_quality.get('completeness', 0):.1%} complete, {data_quality.get('records_count', 0)} records")
        
        alerts = real_time_result.get('real_time_alerts', [])
        if alerts:
            print(f"\nReal-time Alerts ({len(alerts)}):")
            for alert in alerts[:5]:  # Show first 5 alerts
                print(f"  - {alert['type']}: {alert['message']}")
        else:
            print("\nNo real-time alerts generated")
    
    elif real_time_result['status'] == 'no_data':
        print(f"Message: {real_time_result['message']}")
    
    else:
        print(f"Error: {real_time_result.get('error', 'Unknown error')}")

async def run_enhanced_automated_cycle(orchestrator: EnhancedHistoricalOrchestrator, 
                                     interval_hours: int = 6):
    """Run enhanced automated analysis cycle"""
    print("\n" + "="*70)
    print("STARTING ENHANCED AUTOMATED ANALYSIS CYCLE")
    print("="*70)
    print(f"Cycle Interval: {interval_hours} hours")
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running enhanced automated cycle...")
            
            cycle_result = await orchestrator.run_enhanced_automated_cycle()
            
            print(f"Cycle Status: {cycle_result['cycle_status']}")
            
            if cycle_result['cycle_status'] == 'completed':
                print("Enhanced analysis cycle completed successfully")
                
                # Show brief summary of each analysis
                base_analysis = cycle_result.get('base_analysis', {})
                if base_analysis:
                    print(f"  Base Analysis: {base_analysis.get('cycle_status', 'unknown')}")
                
                multivariate_analysis = cycle_result.get('multivariate_analysis', {})
                if multivariate_analysis:
                    print(f"  Multivariate Analysis: {multivariate_analysis.get('status', 'unknown')}")
                
                real_time_analysis = cycle_result.get('real_time_analysis', {})
                if real_time_analysis:
                    print(f"  Real-time Analysis: {real_time_analysis.get('status', 'unknown')}")
            
            elif cycle_result['cycle_status'] == 'skipped':
                print(f"Cycle skipped: {cycle_result.get('reason', 'Unknown reason')}")
            else:
                print(f"Cycle failed: {cycle_result.get('error', 'Unknown error')}")
            
            # Wait for next cycle
            print(f"Next cycle in {interval_hours} hours...")
            await asyncio.sleep(interval_hours * 3600)
            
    except KeyboardInterrupt:
        print("\nEnhanced automated cycle stopped by user.")

async def display_enhanced_system_status(orchestrator: EnhancedHistoricalOrchestrator):
    """Display enhanced system status"""
    print("\n" + "="*70)
    print("ENHANCED SYSTEM STATUS")
    print("="*70)
    
    status = await orchestrator.get_enhanced_system_status()
    
    print(f"System Status: {status['system_status']}")
    print(f"Timestamp: {status['timestamp']}")
    
    # Base analysis state
    analysis_state = status.get('analysis_state', {})
    print(f"\nBase Analysis State:")
    print(f"  Data Loaded: {analysis_state.get('data_loaded', False)}")
    print(f"  Models Trained: {analysis_state.get('models_trained', False)}")
    print(f"  Patterns Detected: {analysis_state.get('patterns_detected', False)}")
    print(f"  Dashboard Ready: {analysis_state.get('dashboard_ready', False)}")
    
    # Multivariate analysis state
    multivariate_state = status.get('multivariate_analysis_state', {})
    print(f"\nMultivariate Analysis State:")
    print(f"  Data Integrated: {multivariate_state.get('data_integrated', False)}")
    print(f"  Relationships Analyzed: {multivariate_state.get('relationships_analyzed', False)}")
    print(f"  Dashboard Ready: {multivariate_state.get('dashboard_ready', False)}")
    
    # Results summary
    multivariate_results = status.get('multivariate_results_summary', {})
    print(f"\nMultivariate Results Available:")
    for analysis_type, available in multivariate_results.items():
        print(f"  {analysis_type.replace('_', ' ').title()}: {available}")
    
    # Data integration summary
    integration_summary = status.get('data_integration_summary', {})
    if integration_summary:
        metadata = integration_summary.get('metadata', {})
        if metadata:
            print(f"\nData Integration Summary:")
            print(f"  Variables: {metadata.get('variables', {}).get('total_count', 0)}")
            print(f"  Completeness: {metadata.get('data_quality', {}).get('completeness', 0):.1%}")
            
            by_category = metadata.get('variables', {}).get('by_category', {})
            if by_category:
                print(f"  Variables by Category:")
                for category, count in by_category.items():
                    print(f"    {category.title()}: {count}")
    
    # Enhanced capabilities
    capabilities = status.get('enhanced_capabilities', [])
    if capabilities:
        print(f"\nEnhanced Capabilities:")
        for capability in capabilities:
            print(f"  - {capability}")
    
    # Active alerts
    alerts = status.get('active_alerts', [])
    if alerts:
        print(f"\nActive Alerts: {len(alerts)}")
        for alert in alerts[:3]:  # Show first 3 alerts
            print(f"  - {alert.get('type', 'unknown')}: {alert.get('message', 'No message')}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced Historical Analysis System with Multivariate Relationships')
    
    # Base configuration arguments
    parser.add_argument('--data-dir', default='datasets/historical', 
                       help='Directory for historical data storage')
    parser.add_argument('--model-dir', default='models/predictive',
                       help='Directory for predictive models')
    parser.add_argument('--output-dir', default='outputs/patterns',
                       help='Directory for analysis outputs')
    parser.add_argument('--port', type=int, default=8051,
                       help='Base dashboard port')
    
    # Enhanced configuration arguments
    parser.add_argument('--multivariate-data-dir', default='datasets/multivariate',
                       help='Directory for multivariate data storage')
    parser.add_argument('--relationships-output-dir', default='outputs/relationships',
                       help='Directory for relationship analysis outputs')
    parser.add_argument('--multivariate-port', type=int, default=8052,
                       help='Multivariate dashboard port')
    
    # Data sources configuration
    parser.add_argument('--energy-sources', nargs='+', 
                       default=['eia_oil', 'eia_production', 'world_bank_energy'],
                       help='Energy data sources')
    parser.add_argument('--climate-sources', nargs='+',
                       default=['noaa_climate', 'nasa_earthdata'],
                       help='Climate data sources')
    parser.add_argument('--political-sources', nargs='+',
                       default=['vdem', 'freedom_house', 'world_bank_governance'],
                       help='Political data sources')
    parser.add_argument('--health-sources', nargs='+',
                       default=['who_health', 'fao_food'],
                       help='Health data sources')
    parser.add_argument('--resource-sources', nargs='+',
                       default=['world_bank_resources', 'global_forest_watch'],
                       help='Resource data sources')
    
    # Analysis configuration
    parser.add_argument('--correlation-methods', nargs='+',
                       default=['pearson', 'spearman', 'kendall'],
                       help='Correlation methods to use')
    parser.add_argument('--max-lags', type=int, default=12,
                       help='Maximum lags for causality testing')
    parser.add_argument('--significance-level', type=float, default=0.05,
                       help='Statistical significance level')
    parser.add_argument('--min-correlation', type=float, default=0.1,
                       help='Minimum correlation threshold')
    parser.add_argument('--network-threshold', type=float, default=0.3,
                       help='Network edge threshold')
    
    # Processing configuration
    parser.add_argument('--update-frequency', type=int, default=24,
                       help='Data update frequency in hours')
    parser.add_argument('--batch-interval', type=int, default=6,
                       help='Batch processing interval in hours')
    parser.add_argument('--forecast-days', type=int, default=30,
                       help='Forecast horizon in days')
    parser.add_argument('--confidence', type=float, default=0.8,
                       help='Confidence level for predictions')
    
    # Feature flags
    parser.add_argument('--no-parallel', action='store_true',
                       help='Disable parallel processing')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable result caching')
    parser.add_argument('--no-real-time', action='store_true',
                       help='Disable real-time analysis')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--force-update', action='store_true',
                       help='Force data update')
    
    # Models and methods
    parser.add_argument('--models', nargs='+',
                       default=['prophet', 'lstm', 'arima', 'ensemble'],
                       help='Prediction models to train')
    parser.add_argument('--pattern-methods', nargs='+',
                       default=['kmeans', 'dbscan', 'isolation_forest'],
                       help='Pattern detection methods')
    
    # Operation mode
    parser.add_argument('--mode', choices=[
        'full', 'init', 'update', 'analyze', 'multivariate', 'dashboard', 
        'multivariate-dashboard', 'real-time', 'status', 'auto'
    ], default='full', help='Operation mode')
    
    # Analysis parameters
    parser.add_argument('--start-date', type=str,
                       help='Analysis start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='Analysis end date (YYYY-MM-DD)')
    parser.add_argument('--target-variable', default='conflict_risk',
                       help='Target variable for analysis')
    parser.add_argument('--auto-interval', type=int, default=6,
                       help='Automated cycle interval in hours')
    
    args = parser.parse_args()
    
    # Create directories
    Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path(args.multivariate_data_dir).mkdir(parents=True, exist_ok=True)
    Path(args.relationships_output_dir).mkdir(parents=True, exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    async def run_enhanced_system():
        """Run the enhanced system based on mode"""
        # Create enhanced configuration
        config = create_enhanced_config(args)
        
        # Initialize enhanced orchestrator
        orchestrator = EnhancedHistoricalOrchestrator(config)
        
        try:
            if args.mode in ['full', 'init']:
                success = await run_enhanced_initialization(orchestrator)
                if not success and args.mode == 'init':
                    return
            
            if args.mode in ['full', 'update']:
                success = await run_multivariate_data_update(orchestrator, force=args.force_update)
                if not success and args.mode == 'update':
                    return
            
            if args.mode in ['full', 'analyze', 'multivariate']:
                success = await run_comprehensive_multivariate_analysis(
                    orchestrator, start_date, end_date, args.target_variable
                )
                if not success and args.mode in ['analyze', 'multivariate']:
                    return
            
            if args.mode == 'dashboard':
                # Start base dashboard
                await orchestrator.start_dashboard(debug=args.debug)
            
            elif args.mode == 'multivariate-dashboard':
                await start_multivariate_dashboard(orchestrator, debug=args.debug)
            
            elif args.mode == 'real-time':
                await run_real_time_analysis(orchestrator)
            
            elif args.mode == 'status':
                await display_enhanced_system_status(orchestrator)
            
            elif args.mode == 'auto':
                await run_enhanced_automated_cycle(orchestrator, args.auto_interval)
            
            elif args.mode == 'full':
                # Show final status
                await display_enhanced_system_status(orchestrator)
                
                # Provide next steps
                print(f"\nEnhanced system ready! You can now:")
                print(f"  - View base dashboard: python {__file__} --mode dashboard")
                print(f"  - View multivariate dashboard: python {__file__} --mode multivariate-dashboard")
                print(f"  - Run real-time analysis: python {__file__} --mode real-time")
                print(f"  - Check status: python {__file__} --mode status")
                print(f"  - Run auto cycle: python {__file__} --mode auto")
        
        except Exception as e:
            logger.error(f"Critical error in enhanced system execution: {e}")
            raise
    
    # Run the enhanced system
    try:
        asyncio.run(run_enhanced_system())
    except KeyboardInterrupt:
        print("\nEnhanced system stopped by user.")
    except Exception as e:
        print(f"Enhanced system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()