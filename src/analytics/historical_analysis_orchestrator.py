"""
Historical Analysis Orchestrator
Main orchestration module that integrates historical data collection, predictive modeling,
pattern detection, and visualization for comprehensive geopolitical risk analysis.
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Import our custom modules
from .historical_data_integration import HistoricalDataIntegrator, DataSource
from .predictive_modeling import MultiVariatePredictor
from .pattern_detection import AdvancedPatternDetector
from ..visualization.historical_dashboard import HistoricalDashboard

logger = logging.getLogger(__name__)

class HistoricalAnalysisOrchestrator:
    """
    Main orchestrator for comprehensive historical analysis system
    Coordinates data integration, analysis, prediction, and visualization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.data_integrator = HistoricalDataIntegrator(
            data_dir=self.config.get('data_dir', 'datasets/historical')
        )
        
        self.predictor = MultiVariatePredictor(
            model_dir=self.config.get('model_dir', 'models/predictive')
        )
        
        self.pattern_detector = AdvancedPatternDetector(
            output_dir=self.config.get('output_dir', 'outputs/patterns')
        )
        
        self.dashboard = None
        
        # Analysis state
        self.analysis_state = {
            'data_loaded': False,
            'models_trained': False,
            'patterns_detected': False,
            'dashboard_ready': False,
            'last_update': None
        }
        
        # Results storage
        self.analysis_results = {
            'data_summary': {},
            'prediction_results': {},
            'pattern_results': {},
            'performance_metrics': {},
            'alerts': []
        }
        
        # Execution pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=mp.cpu_count())
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the orchestrator"""
        return {
            'data_dir': 'datasets/historical',
            'model_dir': 'models/predictive',
            'output_dir': 'outputs/patterns',
            'dashboard_port': 8051,
            'update_frequency_hours': 24,
            'parallel_processing': True,
            'cache_results': True,
            'data_sources': [
                DataSource.UCDP_GED.value,
                DataSource.EMDAT.value,
                DataSource.WORLD_BANK.value
            ],
            'prediction_models': ['prophet', 'lstm', 'arima', 'ensemble'],
            'pattern_detection_methods': ['kmeans', 'dbscan', 'isolation_forest'],
            'forecast_horizon_days': 30,
            'confidence_level': 0.8
        }
    
    async def initialize_system(self) -> Dict[str, Any]:
        """
        Initialize the complete historical analysis system
        
        Returns:
            Initialization results and status
        """
        try:
            logger.info("Initializing Historical Analysis System...")
            
            initialization_results = {
                'status': 'success',
                'components_initialized': [],
                'errors': [],
                'start_time': datetime.now().isoformat()
            }
            
            # Initialize database
            try:
                await self.data_integrator.initialize_database()
                initialization_results['components_initialized'].append('database')
                logger.info("Database initialized successfully")
            except Exception as e:
                error_msg = f"Database initialization failed: {e}"
                initialization_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            # Initialize dashboard
            try:
                self.dashboard = HistoricalDashboard(
                    data_source=self.data_integrator,
                    port=self.config['dashboard_port']
                )
                initialization_results['components_initialized'].append('dashboard')
                logger.info("Dashboard initialized successfully")
            except Exception as e:
                error_msg = f"Dashboard initialization failed: {e}"
                initialization_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            # Check data availability
            try:
                data_summary = self.data_integrator.get_data_summary()
                if data_summary:
                    self.analysis_results['data_summary'] = data_summary
                    self.analysis_state['data_loaded'] = True
                    initialization_results['components_initialized'].append('data_check')
                    logger.info("Data availability verified")
            except Exception as e:
                error_msg = f"Data availability check failed: {e}"
                initialization_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            initialization_results['end_time'] = datetime.now().isoformat()
            
            if initialization_results['errors']:
                initialization_results['status'] = 'partial_success'
            
            logger.info(f"System initialization completed with status: {initialization_results['status']}")
            
            return initialization_results
            
        except Exception as e:
            logger.error(f"Critical error during system initialization: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def update_historical_data(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update historical data from all configured sources
        
        Args:
            force_update: Force update even if recent data exists
            
        Returns:
            Update results and statistics
        """
        try:
            logger.info("Starting historical data update...")
            
            update_results = {
                'status': 'success',
                'sources_updated': [],
                'errors': [],
                'statistics': {},
                'start_time': datetime.now().isoformat()
            }
            
            # Check if update is needed
            if not force_update and self.analysis_state.get('last_update'):
                last_update = datetime.fromisoformat(self.analysis_state['last_update'])
                hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
                
                if hours_since_update < self.config['update_frequency_hours']:
                    logger.info(f"Data updated {hours_since_update:.1f} hours ago, skipping update")
                    update_results['status'] = 'skipped'
                    update_results['reason'] = 'Recent update exists'
                    return update_results
            
            # Update from all configured sources
            if self.config['parallel_processing']:
                # Parallel update
                tasks = []
                
                if DataSource.UCDP_GED.value in self.config['data_sources']:
                    tasks.append(self._update_ucdp_data())
                
                if DataSource.EMDAT.value in self.config['data_sources']:
                    tasks.append(self._update_emdat_data())
                
                if DataSource.WORLD_BANK.value in self.config['data_sources']:
                    tasks.append(self._update_world_bank_data())
                
                # Execute all updates concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    source = list(self.config['data_sources'])[i]
                    if isinstance(result, Exception):
                        update_results['errors'].append(f"{source}: {str(result)}")
                    else:
                        update_results['sources_updated'].append(source)
                        update_results['statistics'][source] = result
            else:
                # Sequential update
                for source in self.config['data_sources']:
                    try:
                        if source == DataSource.UCDP_GED.value:
                            result = await self._update_ucdp_data()
                        elif source == DataSource.EMDAT.value:
                            result = await self._update_emdat_data()
                        elif source == DataSource.WORLD_BANK.value:
                            result = await self._update_world_bank_data()
                        else:
                            continue
                        
                        update_results['sources_updated'].append(source)
                        update_results['statistics'][source] = result
                        
                    except Exception as e:
                        error_msg = f"{source}: {str(e)}"
                        update_results['errors'].append(error_msg)
                        logger.error(f"Error updating {source}: {e}")
            
            # Update analysis state
            if update_results['sources_updated']:
                self.analysis_state['data_loaded'] = True
                self.analysis_state['last_update'] = datetime.now().isoformat()
                
                # Refresh data summary
                self.analysis_results['data_summary'] = self.data_integrator.get_data_summary()
            
            update_results['end_time'] = datetime.now().isoformat()
            
            if update_results['errors']:
                update_results['status'] = 'partial_success'
            
            logger.info(f"Data update completed with status: {update_results['status']}")
            
            return update_results
            
        except Exception as e:
            logger.error(f"Critical error during data update: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _update_ucdp_data(self) -> Dict[str, Any]:
        """Update UCDP conflict data"""
        try:
            events = await self.data_integrator.fetch_ucdp_data(start_year=1989)
            if events:
                await self.data_integrator.store_historical_events(events)
            
            return {
                'events_fetched': len(events),
                'source': 'UCDP',
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error updating UCDP data: {e}")
            raise
    
    async def _update_emdat_data(self) -> Dict[str, Any]:
        """Update EM-DAT disaster data"""
        try:
            events = await self.data_integrator.fetch_emdat_data(start_year=1900)
            if events:
                await self.data_integrator.store_historical_events(events)
            
            return {
                'events_fetched': len(events),
                'source': 'EM-DAT',
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error updating EM-DAT data: {e}")
            raise
    
    async def _update_world_bank_data(self) -> Dict[str, Any]:
        """Update World Bank economic indicators"""
        try:
            indicators = await self.data_integrator.fetch_world_bank_indicators(start_year=1960)
            if indicators:
                await self.data_integrator.store_economic_indicators(indicators)
            
            total_indicators = sum(len(country_data) for country_data in indicators.values())
            
            return {
                'indicators_fetched': total_indicators,
                'countries': len(indicators),
                'source': 'World Bank',
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error updating World Bank data: {e}")
            raise
    
    async def run_comprehensive_analysis(self, 
                                       start_date: datetime = None,
                                       end_date: datetime = None,
                                       regions: List[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive historical analysis including prediction and pattern detection
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            regions: List of regions to analyze
            
        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info("Starting comprehensive historical analysis...")
            
            analysis_results = {
                'status': 'success',
                'analysis_id': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'parameters': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'regions': regions
                },
                'results': {},
                'errors': [],
                'start_time': datetime.now().isoformat()
            }
            
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=365 * 5)  # 5 years
            
            # Step 1: Load and prepare data
            logger.info("Loading historical data...")
            historical_data = await self._load_analysis_data(start_date, end_date, regions)
            
            if historical_data.empty:
                raise ValueError("No historical data available for analysis")
            
            analysis_results['results']['data_loaded'] = {
                'records_count': len(historical_data),
                'date_range': {
                    'start': historical_data.index.min().isoformat() if hasattr(historical_data.index, 'min') else str(historical_data.index[0]),
                    'end': historical_data.index.max().isoformat() if hasattr(historical_data.index, 'max') else str(historical_data.index[-1])
                },
                'columns': list(historical_data.columns)
            }
            
            # Step 2: Pattern Detection
            if self.config['parallel_processing']:
                # Run pattern detection and predictive modeling in parallel
                pattern_task = asyncio.create_task(self._run_pattern_detection(historical_data))
                prediction_task = asyncio.create_task(self._run_predictive_modeling(historical_data))
                
                pattern_results, prediction_results = await asyncio.gather(
                    pattern_task, prediction_task, return_exceptions=True
                )
                
                if isinstance(pattern_results, Exception):
                    analysis_results['errors'].append(f"Pattern detection failed: {pattern_results}")
                    pattern_results = {}
                
                if isinstance(prediction_results, Exception):
                    analysis_results['errors'].append(f"Predictive modeling failed: {prediction_results}")
                    prediction_results = {}
            else:
                # Sequential execution
                try:
                    pattern_results = await self._run_pattern_detection(historical_data)
                except Exception as e:
                    analysis_results['errors'].append(f"Pattern detection failed: {e}")
                    pattern_results = {}
                
                try:
                    prediction_results = await self._run_predictive_modeling(historical_data)
                except Exception as e:
                    analysis_results['errors'].append(f"Predictive modeling failed: {e}")
                    prediction_results = {}
            
            # Store results
            analysis_results['results']['pattern_detection'] = pattern_results
            analysis_results['results']['predictive_modeling'] = prediction_results
            
            # Step 3: Generate comprehensive insights
            insights = await self._generate_comprehensive_insights(
                historical_data, pattern_results, prediction_results
            )
            analysis_results['results']['insights'] = insights
            
            # Step 4: Generate alerts
            alerts = await self._generate_analysis_alerts(
                historical_data, pattern_results, prediction_results
            )
            analysis_results['results']['alerts'] = alerts
            
            # Update analysis state
            self.analysis_state['models_trained'] = bool(prediction_results)
            self.analysis_state['patterns_detected'] = bool(pattern_results)
            
            # Store results for dashboard
            self.analysis_results.update(analysis_results['results'])
            
            analysis_results['end_time'] = datetime.now().isoformat()
            analysis_results['duration_seconds'] = (
                datetime.fromisoformat(analysis_results['end_time']) - 
                datetime.fromisoformat(analysis_results['start_time'])
            ).total_seconds()
            
            if analysis_results['errors']:
                analysis_results['status'] = 'partial_success'
            
            logger.info(f"Comprehensive analysis completed with status: {analysis_results['status']}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Critical error during comprehensive analysis: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _load_analysis_data(self, start_date: datetime, end_date: datetime, 
                                regions: List[str] = None) -> pd.DataFrame:
        """Load and prepare data for analysis"""
        try:
            # Load historical events
            events_df = await self.data_integrator.get_historical_events(
                start_date=start_date,
                end_date=end_date
            )
            
            if events_df.empty:
                logger.warning("No historical events found for the specified period")
                return pd.DataFrame()
            
            # Load economic indicators
            indicators_df = await self.data_integrator.get_economic_indicators(
                start_year=start_date.year,
                end_year=end_date.year
            )
            
            # Prepare combined dataset
            prepared_data = self._prepare_analysis_dataset(events_df, indicators_df, regions)
            
            return prepared_data
            
        except Exception as e:
            logger.error(f"Error loading analysis data: {e}")
            return pd.DataFrame()
    
    def _prepare_analysis_dataset(self, events_df: pd.DataFrame, 
                                indicators_df: pd.DataFrame,
                                regions: List[str] = None) -> pd.DataFrame:
        """Prepare combined dataset for analysis"""
        try:
            # Convert events to time series
            if not events_df.empty:
                events_df['date'] = pd.to_datetime(events_df['date'])
                
                # Filter by regions if specified
                if regions:
                    events_df = events_df[events_df['region'].isin(regions)]
                
                # Aggregate events by date
                daily_events = events_df.groupby('date').agg({
                    'severity_score': ['mean', 'max', 'count'],
                    'casualties': 'sum',
                    'event_type': lambda x: x.mode().iloc[0] if not x.empty else 'unknown'
                }).reset_index()
                
                # Flatten column names
                daily_events.columns = ['date', 'avg_severity', 'max_severity', 'event_count', 
                                      'total_casualties', 'dominant_event_type']
                
                daily_events = daily_events.set_index('date')
            else:
                daily_events = pd.DataFrame()
            
            # Process economic indicators
            if not indicators_df.empty:
                # Pivot indicators to have one row per country-year
                indicators_pivot = indicators_df.pivot_table(
                    index=['country', 'year'],
                    columns='indicator_code',
                    values='value',
                    aggfunc='mean'
                ).reset_index()
                
                # Convert to daily frequency (approximate)
                indicators_daily = []
                for _, row in indicators_pivot.iterrows():
                    year_start = pd.Timestamp(f"{row['year']}-01-01")
                    year_end = pd.Timestamp(f"{row['year']}-12-31")
                    dates = pd.date_range(start=year_start, end=year_end, freq='D')
                    
                    for date in dates:
                        daily_row = {'date': date, 'country': row['country']}
                        for col in indicators_pivot.columns:
                            if col not in ['country', 'year']:
                                daily_row[f'econ_{col}'] = row[col]
                        indicators_daily.append(daily_row)
                
                if indicators_daily:
                    indicators_df_daily = pd.DataFrame(indicators_daily)
                    indicators_df_daily = indicators_df_daily.set_index('date')
                    
                    # Aggregate by date (average across countries)
                    economic_features = indicators_df_daily.select_dtypes(include=[np.number]).groupby('date').mean()
                else:
                    economic_features = pd.DataFrame()
            else:
                economic_features = pd.DataFrame()
            
            # Combine datasets
            if not daily_events.empty and not economic_features.empty:
                combined_data = daily_events.join(economic_features, how='outer')
            elif not daily_events.empty:
                combined_data = daily_events
            elif not economic_features.empty:
                combined_data = economic_features
            else:
                combined_data = pd.DataFrame()
            
            # Fill missing values and resample
            if not combined_data.empty:
                combined_data = combined_data.resample('D').mean()
                combined_data = combined_data.fillna(method='forward').fillna(method='backward')
                combined_data = combined_data.fillna(0)
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error preparing analysis dataset: {e}")
            return pd.DataFrame()
    
    async def _run_pattern_detection(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run pattern detection analysis"""
        try:
            logger.info("Running pattern detection analysis...")
            
            # Preprocess data
            processed_data = self.pattern_detector.preprocess_data(
                data, 
                scaling_method='standard',
                handle_missing='fill'
            )
            
            if processed_data.empty:
                return {'error': 'No data available for pattern detection'}
            
            results = {}
            
            # Dimensionality reduction
            reduced_data = self.pattern_detector.apply_dimensionality_reduction(
                processed_data, 
                methods=['pca', 'tsne'],
                n_components=2
            )
            results['dimensionality_reduction'] = {
                'methods_applied': list(reduced_data.keys()),
                'original_dimensions': processed_data.shape[1],
                'reduced_dimensions': 2
            }
            
            # Clustering
            clustering_results = self.pattern_detector.detect_clusters(
                processed_data,
                methods=self.config['pattern_detection_methods'],
                n_clusters_range=(2, 8)
            )
            results['clustering'] = clustering_results
            
            # Anomaly detection
            anomaly_results = self.pattern_detector.detect_anomalies(
                processed_data,
                methods=['isolation_forest', 'one_class_svm'],
                contamination=0.1
            )
            results['anomaly_detection'] = anomaly_results
            
            # Temporal patterns (if timestamp data available)
            if hasattr(data.index, 'to_pydatetime'):
                temporal_patterns = self.pattern_detector.identify_temporal_patterns(
                    data.reset_index(),
                    timestamp_column='date' if 'date' in data.reset_index().columns else data.index.name
                )
                results['temporal_patterns'] = temporal_patterns
            
            # Generate pattern report
            pattern_report = self.pattern_detector.generate_pattern_report(
                clustering_results, anomaly_results, results.get('temporal_patterns')
            )
            results['pattern_report'] = pattern_report
            
            return results
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            raise
    
    async def _run_predictive_modeling(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run predictive modeling analysis"""
        try:
            logger.info("Running predictive modeling analysis...")
            
            if data.empty:
                return {'error': 'No data available for predictive modeling'}
            
            # Prepare multivariate data
            target_column = 'avg_severity' if 'avg_severity' in data.columns else data.columns[0]
            feature_columns = [col for col in data.columns if col != target_column]
            
            prepared_data = self.predictor.prepare_multivariate_data(
                data,
                target_column=target_column,
                feature_columns=feature_columns,
                lag_features=7,
                rolling_windows=[7, 14, 30]
            )
            
            if prepared_data.empty:
                return {'error': 'Data preparation failed for predictive modeling'}
            
            results = {}
            
            # Train models based on configuration
            for model_type in self.config['prediction_models']:
                try:
                    if model_type == 'prophet':
                        model_result = self.predictor.train_prophet_model(
                            prepared_data,
                            target_column=target_column,
                            external_regressors=feature_columns[:5]  # Limit regressors
                        )
                    elif model_type == 'lstm':
                        model_result = self.predictor.train_lstm_model(
                            prepared_data,
                            target_column=target_column,
                            feature_columns=feature_columns,
                            epochs=50
                        )
                    elif model_type == 'arima':
                        model_result = self.predictor.train_arima_model(
                            prepared_data,
                            target_column=target_column
                        )
                    elif model_type == 'ensemble':
                        model_result = self.predictor.train_ensemble_model(
                            prepared_data,
                            target_column=target_column,
                            feature_columns=feature_columns
                        )
                    else:
                        continue
                    
                    results[model_type] = model_result
                    
                except Exception as e:
                    logger.error(f"Error training {model_type} model: {e}")
                    results[model_type] = {'error': str(e)}
            
            # Generate predictions
            if any('error' not in result for result in results.values()):
                predictions = self.predictor.predict_future_risks(
                    periods=self.config['forecast_horizon_days'],
                    confidence_interval=self.config['confidence_level']
                )
                results['predictions'] = predictions
            
            # Model performance summary
            performance_summary = self.predictor.get_model_performance_summary()
            results['performance_summary'] = performance_summary
            
            return results
            
        except Exception as e:
            logger.error(f"Error in predictive modeling: {e}")
            raise
    
    async def _generate_comprehensive_insights(self, data: pd.DataFrame,
                                             pattern_results: Dict[str, Any],
                                             prediction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights from all analyses"""
        try:
            insights = {
                'data_insights': [],
                'pattern_insights': [],
                'prediction_insights': [],
                'cross_analysis_insights': [],
                'recommendations': []
            }
            
            # Data insights
            if not data.empty:
                insights['data_insights'].extend([
                    f"Analysis covers {len(data)} data points spanning {(data.index.max() - data.index.min()).days} days",
                    f"Average risk level: {data.select_dtypes(include=[np.number]).mean().mean():.2f}",
                    f"Data completeness: {(1 - data.isnull().sum().sum() / (data.shape[0] * data.shape[1])) * 100:.1f}%"
                ])
            
            # Pattern insights
            if pattern_results and 'pattern_report' in pattern_results:
                report = pattern_results['pattern_report']
                if 'insights' in report:
                    insights['pattern_insights'] = [insight['insight'] for insight in report['insights']]
            
            # Prediction insights
            if prediction_results and 'predictions' in prediction_results:
                pred = prediction_results['predictions']
                if 'ensemble_prediction' in pred and pred['ensemble_prediction']:
                    ensemble = pred['ensemble_prediction']
                    avg_future_risk = np.mean(ensemble['values'])
                    insights['prediction_insights'].append(
                        f"Predicted average risk for next {len(ensemble['values'])} days: {avg_future_risk:.2f}"
                    )
            
            # Cross-analysis insights
            if pattern_results and prediction_results:
                insights['cross_analysis_insights'].append(
                    "Pattern detection and predictive modeling completed successfully"
                )
            
            # Recommendations
            if pattern_results and 'pattern_report' in pattern_results:
                report = pattern_results['pattern_report']
                if 'recommendations' in report:
                    insights['recommendations'].extend(report['recommendations'])
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {}
    
    async def _generate_analysis_alerts(self, data: pd.DataFrame,
                                      pattern_results: Dict[str, Any],
                                      prediction_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on analysis results"""
        try:
            alerts = []
            
            # Data quality alerts
            if not data.empty:
                missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
                if missing_ratio > 0.2:
                    alerts.append({
                        'type': 'data_quality',
                        'severity': 'medium',
                        'message': f'High missing data ratio: {missing_ratio:.1%}',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Pattern alerts
            if pattern_results and 'pattern_report' in pattern_results:
                report = pattern_results['pattern_report']
                if 'alerts' in report:
                    alerts.extend(report['alerts'])
            
            # Prediction alerts
            if prediction_results and 'predictions' in prediction_results:
                pred = prediction_results['predictions']
                if 'alerts' in pred:
                    alerts.extend(pred['alerts'])
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return []
    
    async def start_dashboard(self, debug: bool = False) -> Dict[str, Any]:
        """
        Start the interactive dashboard
        
        Args:
            debug: Whether to run in debug mode
            
        Returns:
            Dashboard startup results
        """
        try:
            if not self.dashboard:
                self.dashboard = HistoricalDashboard(
                    data_source=self.data_integrator,
                    port=self.config['dashboard_port']
                )
            
            logger.info(f"Starting dashboard on port {self.config['dashboard_port']}")
            
            # Run dashboard in a separate thread to avoid blocking
            dashboard_task = asyncio.create_task(
                asyncio.to_thread(self.dashboard.run_dashboard, debug)
            )
            
            self.analysis_state['dashboard_ready'] = True
            
            return {
                'status': 'started',
                'port': self.config['dashboard_port'],
                'url': f"http://localhost:{self.config['dashboard_port']}",
                'debug_mode': debug,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            return {
                'system_status': 'operational',
                'analysis_state': self.analysis_state,
                'data_summary': self.analysis_results.get('data_summary', {}),
                'last_analysis': self.analysis_results.get('insights', {}),
                'active_alerts': self.analysis_results.get('alerts', []),
                'configuration': self.config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'system_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_automated_analysis_cycle(self):
        """Run automated analysis cycle"""
        try:
            logger.info("Starting automated analysis cycle...")
            
            # Update data
            update_result = await self.update_historical_data()
            
            # Run analysis if data was updated
            if update_result['status'] in ['success', 'partial_success']:
                analysis_result = await self.run_comprehensive_analysis()
                
                return {
                    'cycle_status': 'completed',
                    'update_result': update_result,
                    'analysis_result': analysis_result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'cycle_status': 'skipped',
                    'reason': 'No data updates needed',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in automated analysis cycle: {e}")
            return {
                'cycle_status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)