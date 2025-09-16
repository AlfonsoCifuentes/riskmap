"""
Enhanced Historical Analysis Orchestrator
Extended orchestrator that integrates multivariate relational analysis with energy, climate,
political, health, and resource variables for comprehensive geopolitical risk assessment.
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

# Import base orchestrator
from .historical_analysis_orchestrator import HistoricalAnalysisOrchestrator

# Import new multivariate components
from .multivariate_relational_analysis import MultivariateDataIntegrator, DataCategory
from .correlation_relationship_analyzer import CorrelationRelationshipAnalyzer
from ..visualization.multivariate_dashboard import MultivariateRelationshipDashboard

logger = logging.getLogger(__name__)

class EnhancedHistoricalOrchestrator(HistoricalAnalysisOrchestrator):
    """
    Enhanced orchestrator that adds multivariate relational analysis capabilities
    to the base historical analysis system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # Initialize base orchestrator
        super().__init__(config)
        
        # Initialize multivariate components
        self.multivariate_integrator = MultivariateDataIntegrator(
            data_dir=self.config.get('multivariate_data_dir', 'datasets/multivariate')
        )
        
        self.relationship_analyzer = CorrelationRelationshipAnalyzer(
            output_dir=self.config.get('relationships_output_dir', 'outputs/relationships')
        )
        
        self.multivariate_dashboard = None
        
        # Enhanced analysis state
        self.analysis_state.update({
            'multivariate_data_integrated': False,
            'relationships_analyzed': False,
            'multivariate_dashboard_ready': False
        })
        
        # Enhanced results storage
        self.analysis_results.update({
            'multivariate_integration': {},
            'correlation_analysis': {},
            'causality_analysis': {},
            'feature_importance': {},
            'threshold_effects': {},
            'relationship_network': {},
            'multivariate_insights': {}
        })
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get enhanced default configuration"""
        base_config = super()._get_default_config()
        
        # Add multivariate-specific configuration
        enhanced_config = {
            **base_config,
            'multivariate_data_dir': 'datasets/multivariate',
            'relationships_output_dir': 'outputs/relationships',
            'multivariate_dashboard_port': 8052,
            'energy_data_sources': [
                'eia_oil', 'eia_production', 'world_bank_energy'
            ],
            'climate_data_sources': [
                'noaa_climate', 'nasa_earthdata'
            ],
            'political_data_sources': [
                'vdem', 'freedom_house', 'world_bank_governance'
            ],
            'health_data_sources': [
                'who_health', 'fao_food'
            ],
            'resource_data_sources': [
                'world_bank_resources', 'global_forest_watch'
            ],
            'correlation_methods': ['pearson', 'spearman', 'kendall'],
            'causality_max_lags': 12,
            'significance_level': 0.05,
            'min_correlation_threshold': 0.1,
            'network_edge_threshold': 0.3,
            'enable_real_time_analysis': True,
            'batch_processing_interval_hours': 6
        }
        
        return enhanced_config
    
    async def initialize_enhanced_system(self) -> Dict[str, Any]:
        """
        Initialize the enhanced multivariate analysis system
        
        Returns:
            Enhanced initialization results
        """
        try:
            logger.info("Initializing Enhanced Historical Analysis System...")
            
            # Initialize base system first
            base_results = await super().initialize_system()
            
            initialization_results = {
                'status': 'success',
                'base_initialization': base_results,
                'enhanced_components': [],
                'errors': [],
                'start_time': datetime.now().isoformat()
            }
            
            # Initialize multivariate data integrator
            try:
                # Test data integration capabilities
                test_integration = await self.multivariate_integrator.integrate_all_data(
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now()
                )
                
                if not test_integration.empty:
                    initialization_results['enhanced_components'].append('multivariate_integrator')
                    logger.info("Multivariate data integrator initialized successfully")
                else:
                    initialization_results['errors'].append("Multivariate data integration test failed")
                    
            except Exception as e:
                error_msg = f"Multivariate integrator initialization failed: {e}"
                initialization_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            # Initialize relationship analyzer
            try:
                # Test analyzer with sample data
                sample_data = pd.DataFrame({
                    'conflict_risk': np.random.uniform(3, 8, 100),
                    'oil_price': np.random.uniform(60, 90, 100),
                    'temperature': np.random.normal(0, 1, 100)
                })
                
                test_correlations = self.relationship_analyzer.compute_comprehensive_correlations(
                    sample_data, 'conflict_risk'
                )
                
                if test_correlations:
                    initialization_results['enhanced_components'].append('relationship_analyzer')
                    logger.info("Relationship analyzer initialized successfully")
                else:
                    initialization_results['errors'].append("Relationship analyzer test failed")
                    
            except Exception as e:
                error_msg = f"Relationship analyzer initialization failed: {e}"
                initialization_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            # Initialize multivariate dashboard
            try:
                self.multivariate_dashboard = MultivariateRelationshipDashboard(
                    data_integrator=self.multivariate_integrator,
                    relationship_analyzer=self.relationship_analyzer,
                    port=self.config['multivariate_dashboard_port']
                )
                initialization_results['enhanced_components'].append('multivariate_dashboard')
                logger.info("Multivariate dashboard initialized successfully")
                
            except Exception as e:
                error_msg = f"Multivariate dashboard initialization failed: {e}"
                initialization_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            initialization_results['end_time'] = datetime.now().isoformat()
            
            if initialization_results['errors']:
                initialization_results['status'] = 'partial_success'
            
            logger.info(f"Enhanced system initialization completed with status: {initialization_results['status']}")
            
            return initialization_results
            
        except Exception as e:
            logger.error(f"Critical error during enhanced system initialization: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def update_multivariate_data(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update multivariate data from all configured sources
        
        Args:
            force_update: Force update even if recent data exists
            
        Returns:
            Multivariate data update results
        """
        try:
            logger.info("Starting multivariate data update...")
            
            update_results = {
                'status': 'success',
                'data_categories_updated': [],
                'integration_summary': {},
                'errors': [],
                'start_time': datetime.now().isoformat()
            }
            
            # Define update period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 3)  # 3 years of data
            
            # Integrate data from all sources
            try:
                integrated_data = await self.multivariate_integrator.integrate_all_data(
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not integrated_data.empty:
                    # Get integration summary
                    integration_summary = self.multivariate_integrator.get_integration_summary()
                    update_results['integration_summary'] = integration_summary
                    
                    # Determine which categories were updated
                    for category in DataCategory:
                        category_vars = [
                            var for var, metadata in self.multivariate_integrator.variable_registry.items()
                            if metadata.category == category and var in integrated_data.columns
                        ]
                        if category_vars:
                            update_results['data_categories_updated'].append(category.value)
                    
                    # Update analysis state
                    self.analysis_state['multivariate_data_integrated'] = True
                    self.analysis_results['multivariate_integration'] = integration_summary
                    
                    logger.info(f"Multivariate data integration completed. Shape: {integrated_data.shape}")
                    
                else:
                    update_results['errors'].append("No data was integrated")
                    
            except Exception as e:
                error_msg = f"Data integration failed: {e}"
                update_results['errors'].append(error_msg)
                logger.error(error_msg)
            
            update_results['end_time'] = datetime.now().isoformat()
            
            if update_results['errors']:
                update_results['status'] = 'partial_success'
            
            return update_results
            
        except Exception as e:
            logger.error(f"Critical error during multivariate data update: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_comprehensive_multivariate_analysis(self, 
                                                    start_date: datetime = None,
                                                    end_date: datetime = None,
                                                    target_variable: str = 'conflict_risk') -> Dict[str, Any]:
        """
        Run comprehensive multivariate relational analysis
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            target_variable: Target variable for analysis
            
        Returns:
            Comprehensive multivariate analysis results
        """
        try:
            logger.info("Starting comprehensive multivariate analysis...")
            
            analysis_results = {
                'status': 'success',
                'analysis_id': f"multivariate_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'target_variable': target_variable,
                'parameters': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                },
                'results': {},
                'errors': [],
                'start_time': datetime.now().isoformat()
            }
            
            # Set default date range
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=365 * 3)  # 3 years
            
            # Step 1: Ensure multivariate data is available
            if not self.analysis_state.get('multivariate_data_integrated', False):
                logger.info("Updating multivariate data...")
                update_result = await self.update_multivariate_data()
                analysis_results['results']['data_update'] = update_result
            
            # Step 2: Get integrated data
            integrated_data = await self.multivariate_integrator.integrate_all_data(
                start_date=start_date,
                end_date=end_date
            )
            
            if integrated_data.empty:
                raise ValueError("No integrated data available for analysis")
            
            analysis_results['results']['data_summary'] = {
                'records_count': len(integrated_data),
                'variables_count': len(integrated_data.columns),
                'date_range': {
                    'start': integrated_data.index.min().isoformat(),
                    'end': integrated_data.index.max().isoformat()
                },
                'completeness': float(1 - integrated_data.isnull().sum().sum() / (integrated_data.shape[0] * integrated_data.shape[1]))
            }
            
            # Step 3: Run relationship analyses in parallel
            if self.config['parallel_processing']:
                analysis_tasks = [
                    self._run_correlation_analysis(integrated_data, target_variable),
                    self._run_causality_analysis(integrated_data, target_variable),
                    self._run_feature_importance_analysis(integrated_data, target_variable),
                    self._run_threshold_effects_analysis(integrated_data, target_variable)
                ]
                
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                
                # Process results
                analysis_names = ['correlation', 'causality', 'feature_importance', 'threshold_effects']
                for i, result in enumerate(results):
                    analysis_name = analysis_names[i]
                    if isinstance(result, Exception):
                        analysis_results['errors'].append(f"{analysis_name} analysis failed: {result}")
                    else:
                        analysis_results['results'][analysis_name] = result
                        self.analysis_results[f'{analysis_name}_analysis'] = result
            else:
                # Sequential execution
                try:
                    correlation_results = await self._run_correlation_analysis(integrated_data, target_variable)
                    analysis_results['results']['correlation'] = correlation_results
                    self.analysis_results['correlation_analysis'] = correlation_results
                except Exception as e:
                    analysis_results['errors'].append(f"Correlation analysis failed: {e}")
                
                try:
                    causality_results = await self._run_causality_analysis(integrated_data, target_variable)
                    analysis_results['results']['causality'] = causality_results
                    self.analysis_results['causality_analysis'] = causality_results
                except Exception as e:
                    analysis_results['errors'].append(f"Causality analysis failed: {e}")
                
                try:
                    importance_results = await self._run_feature_importance_analysis(integrated_data, target_variable)
                    analysis_results['results']['feature_importance'] = importance_results
                    self.analysis_results['feature_importance'] = importance_results
                except Exception as e:
                    analysis_results['errors'].append(f"Feature importance analysis failed: {e}")
                
                try:
                    threshold_results = await self._run_threshold_effects_analysis(integrated_data, target_variable)
                    analysis_results['results']['threshold_effects'] = threshold_results
                    self.analysis_results['threshold_effects'] = threshold_results
                except Exception as e:
                    analysis_results['errors'].append(f"Threshold effects analysis failed: {e}")
            
            # Step 4: Build relationship network
            try:
                network_results = await self._build_relationship_network()
                analysis_results['results']['relationship_network'] = network_results
                self.analysis_results['relationship_network'] = network_results
            except Exception as e:
                analysis_results['errors'].append(f"Network analysis failed: {e}")
            
            # Step 5: Generate comprehensive insights
            try:
                insights = await self._generate_multivariate_insights(
                    integrated_data, analysis_results['results']
                )
                analysis_results['results']['insights'] = insights
                self.analysis_results['multivariate_insights'] = insights
            except Exception as e:
                analysis_results['errors'].append(f"Insights generation failed: {e}")
            
            # Step 6: Generate executive report
            try:
                executive_report = await self._generate_executive_report(analysis_results['results'])
                analysis_results['results']['executive_report'] = executive_report
            except Exception as e:
                analysis_results['errors'].append(f"Executive report generation failed: {e}")
            
            # Update analysis state
            self.analysis_state['relationships_analyzed'] = True
            
            analysis_results['end_time'] = datetime.now().isoformat()
            analysis_results['duration_seconds'] = (
                datetime.fromisoformat(analysis_results['end_time']) - 
                datetime.fromisoformat(analysis_results['start_time'])
            ).total_seconds()
            
            if analysis_results['errors']:
                analysis_results['status'] = 'partial_success'
            
            logger.info(f"Comprehensive multivariate analysis completed with status: {analysis_results['status']}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Critical error during multivariate analysis: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _run_correlation_analysis(self, data: pd.DataFrame, target_variable: str) -> Dict[str, Any]:
        """Run comprehensive correlation analysis"""
        try:
            logger.info("Running correlation analysis...")
            
            # Comprehensive correlations
            correlation_results = self.relationship_analyzer.compute_comprehensive_correlations(
                data, target_variable
            )
            
            return correlation_results
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            raise
    
    async def _run_causality_analysis(self, data: pd.DataFrame, target_variable: str) -> Dict[str, Any]:
        """Run Granger causality analysis"""
        try:
            logger.info("Running causality analysis...")
            
            causality_results = self.relationship_analyzer.analyze_granger_causality(
                data, target_variable, max_lags=self.config['causality_max_lags']
            )
            
            return causality_results
            
        except Exception as e:
            logger.error(f"Error in causality analysis: {e}")
            raise
    
    async def _run_feature_importance_analysis(self, data: pd.DataFrame, target_variable: str) -> Dict[str, Any]:
        """Run feature importance analysis"""
        try:
            logger.info("Running feature importance analysis...")
            
            importance_results = self.relationship_analyzer.analyze_feature_importance(
                data, target_variable
            )
            
            return importance_results
            
        except Exception as e:
            logger.error(f"Error in feature importance analysis: {e}")
            raise
    
    async def _run_threshold_effects_analysis(self, data: pd.DataFrame, target_variable: str) -> Dict[str, Any]:
        """Run threshold effects analysis"""
        try:
            logger.info("Running threshold effects analysis...")
            
            threshold_results = self.relationship_analyzer.detect_threshold_effects(
                data, target_variable
            )
            
            return threshold_results
            
        except Exception as e:
            logger.error(f"Error in threshold effects analysis: {e}")
            raise
    
    async def _build_relationship_network(self) -> Dict[str, Any]:
        """Build relationship network from analysis results"""
        try:
            logger.info("Building relationship network...")
            
            network_results = self.relationship_analyzer.build_relationship_network(
                correlation_threshold=self.config['network_edge_threshold'],
                significance_threshold=self.config['significance_level']
            )
            
            return network_results
            
        except Exception as e:
            logger.error(f"Error building relationship network: {e}")
            raise
    
    async def _generate_multivariate_insights(self, data: pd.DataFrame, 
                                            analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive multivariate insights"""
        try:
            logger.info("Generating multivariate insights...")
            
            insights = {
                'data_insights': [],
                'correlation_insights': [],
                'causality_insights': [],
                'importance_insights': [],
                'threshold_insights': [],
                'network_insights': [],
                'cross_domain_insights': [],
                'policy_implications': [],
                'monitoring_recommendations': []
            }
            
            # Data insights
            if not data.empty:
                insights['data_insights'].extend([
                    f"Integrated {len(data.columns)} variables across {len(set(self.multivariate_integrator.variable_registry[var].category.value for var in data.columns if var in self.multivariate_integrator.variable_registry))} domains",
                    f"Analysis covers {len(data)} time points spanning {(data.index.max() - data.index.min()).days} days",
                    f"Data completeness: {(1 - data.isnull().sum().sum() / (data.shape[0] * data.shape[1])) * 100:.1f}%"
                ])
            
            # Correlation insights
            if 'correlation' in analysis_results:
                corr_results = analysis_results['correlation']
                if 'correlations' in corr_results and 'pearson' in corr_results['correlations']:
                    pearson_corrs = corr_results['correlations']['pearson']
                    strong_corrs = {k: v for k, v in pearson_corrs.items() if abs(v) > 0.5}
                    
                    if strong_corrs:
                        strongest_var, strongest_corr = max(strong_corrs.items(), key=lambda x: abs(x[1]))
                        direction = "positively" if strongest_corr > 0 else "negatively"
                        insights['correlation_insights'].append(
                            f"{strongest_var} shows the strongest correlation with conflict risk "
                            f"({direction} correlated, r={strongest_corr:.3f})"
                        )
                        
                        # Domain-specific insights
                        energy_corrs = {k: v for k, v in strong_corrs.items() if 'oil' in k or 'energy' in k}
                        climate_corrs = {k: v for k, v in strong_corrs.items() if 'temperature' in k or 'climate' in k or 'drought' in k}
                        
                        if energy_corrs:
                            insights['cross_domain_insights'].append(
                                f"Energy variables show significant correlation with conflict risk: {list(energy_corrs.keys())}"
                            )
                        
                        if climate_corrs:
                            insights['cross_domain_insights'].append(
                                f"Climate variables demonstrate strong relationship with conflict risk: {list(climate_corrs.keys())}"
                            )
            
            # Causality insights
            if 'causality' in analysis_results:
                causality_results = analysis_results['causality']
                if 'significant_relationships' in causality_results:
                    causal_vars = list(causality_results['significant_relationships'].keys())
                    if causal_vars:
                        insights['causality_insights'].append(
                            f"Granger causality analysis identified {len(causal_vars)} variables that "
                            f"significantly predict future conflict risk: {', '.join(causal_vars[:3])}"
                        )
                        
                        # Lag insights
                        optimal_lags = causality_results.get('optimal_lags', {})
                        if optimal_lags:
                            avg_lag = np.mean(list(optimal_lags.values()))
                            insights['causality_insights'].append(
                                f"Average optimal prediction lag is {avg_lag:.1f} periods, "
                                f"suggesting early warning capabilities"
                            )
            
            # Feature importance insights
            if 'feature_importance' in analysis_results:
                importance_results = analysis_results['feature_importance']
                if 'top_features' in importance_results and 'aggregated' in importance_results['top_features']:
                    top_features = importance_results['top_features']['aggregated'][:5]
                    feature_names = [f[0] for f in top_features]
                    insights['importance_insights'].append(
                        f"Most predictive variables for conflict risk: {', '.join(feature_names)}"
                    )
                    
                    # Category analysis
                    category_importance = {}
                    for feature_name, importance in top_features:
                        if feature_name in self.multivariate_integrator.variable_registry:
                            category = self.multivariate_integrator.variable_registry[feature_name].category.value
                            if category not in category_importance:
                                category_importance[category] = 0
                            category_importance[category] += importance
                    
                    if category_importance:
                        top_category = max(category_importance.items(), key=lambda x: x[1])
                        insights['importance_insights'].append(
                            f"{top_category[0].title()} variables show highest overall predictive importance"
                        )
            
            # Threshold insights
            if 'threshold_effects' in analysis_results:
                threshold_results = analysis_results['threshold_effects']
                if 'significant_thresholds' in threshold_results:
                    threshold_vars = list(threshold_results['significant_thresholds'].keys())
                    if threshold_vars:
                        insights['threshold_insights'].append(
                            f"Non-linear threshold effects detected for {len(threshold_vars)} variables: {', '.join(threshold_vars[:3])}"
                        )
                        
                        # Policy implications
                        for var in threshold_vars[:3]:
                            threshold_info = threshold_results['significant_thresholds'][var]
                            threshold_value = threshold_info['threshold_value']
                            insights['policy_implications'].append(
                                f"Monitor {var} closely when approaching threshold of {threshold_value:.2f}"
                            )
            
            # Network insights
            if 'relationship_network' in analysis_results:
                network_results = analysis_results['relationship_network']
                if 'network_stats' in network_results:
                    stats = network_results['network_stats']
                    insights['network_insights'].append(
                        f"Relationship network contains {stats['nodes']} variables with {stats['edges']} significant connections"
                    )
                    
                    if 'centrality_measures' in network_results:
                        centrality = network_results['centrality_measures']
                        if 'degree_centrality' in centrality:
                            most_central = max(centrality['degree_centrality'].items(), key=lambda x: x[1])
                            insights['network_insights'].append(
                                f"{most_central[0]} is the most central variable in the relationship network"
                            )
            
            # Monitoring recommendations
            insights['monitoring_recommendations'].extend([
                "Implement real-time monitoring for variables with strong causal relationships",
                "Establish threshold-based alert systems for variables showing regime-switching behavior",
                "Focus data collection efforts on high-importance variables identified in the analysis",
                "Develop early warning indicators based on optimal lag relationships"
            ])
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating multivariate insights: {e}")
            return {}
    
    async def _generate_executive_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary report"""
        try:
            logger.info("Generating executive report...")
            
            # Generate comprehensive relationship report
            relationship_report = self.relationship_analyzer.generate_relationship_report()
            
            executive_report = {
                'report_timestamp': datetime.now().isoformat(),
                'executive_summary': {
                    'analysis_scope': 'Comprehensive multivariate relationship analysis',
                    'variables_analyzed': analysis_results.get('data_summary', {}).get('variables_count', 0),
                    'time_period': analysis_results.get('data_summary', {}).get('date_range', {}),
                    'key_findings': []
                },
                'relationship_analysis': relationship_report,
                'risk_assessment': {},
                'recommendations': {
                    'immediate_actions': [],
                    'medium_term_strategies': [],
                    'long_term_initiatives': []
                },
                'monitoring_framework': {
                    'priority_variables': [],
                    'alert_thresholds': {},
                    'update_frequency': {}
                }
            }
            
            # Extract key findings
            if 'insights' in analysis_results:
                insights = analysis_results['insights']
                
                # Combine insights from different categories
                all_insights = []
                for category, insight_list in insights.items():
                    if isinstance(insight_list, list):
                        all_insights.extend(insight_list[:2])  # Top 2 from each category
                
                executive_report['executive_summary']['key_findings'] = all_insights[:10]
            
            # Risk assessment
            if 'correlation' in analysis_results:
                corr_results = analysis_results['correlation']
                if 'correlations' in corr_results and 'pearson' in corr_results['correlations']:
                    strong_negative_corrs = {
                        k: v for k, v in corr_results['correlations']['pearson'].items() 
                        if v < -0.5
                    }
                    strong_positive_corrs = {
                        k: v for k, v in corr_results['correlations']['pearson'].items() 
                        if v > 0.5
                    }
                    
                    executive_report['risk_assessment'] = {
                        'risk_amplifying_factors': len(strong_positive_corrs),
                        'risk_mitigating_factors': len(strong_negative_corrs),
                        'overall_risk_level': 'high' if len(strong_positive_corrs) > len(strong_negative_corrs) else 'moderate'
                    }
            
            # Recommendations
            if 'causality' in analysis_results and analysis_results['causality'].get('significant_relationships'):
                executive_report['recommendations']['immediate_actions'].append(
                    "Implement predictive monitoring for variables with established causal relationships"
                )
            
            if 'threshold_effects' in analysis_results and analysis_results['threshold_effects'].get('significant_thresholds'):
                executive_report['recommendations']['medium_term_strategies'].append(
                    "Develop threshold-based early warning systems for non-linear risk factors"
                )
            
            executive_report['recommendations']['long_term_initiatives'].extend([
                "Expand data collection to improve relationship detection accuracy",
                "Develop automated analysis pipelines for continuous monitoring",
                "Integrate findings into strategic planning and policy development"
            ])
            
            return executive_report
            
        except Exception as e:
            logger.error(f"Error generating executive report: {e}")
            return {}
    
    async def start_multivariate_dashboard(self, debug: bool = False) -> Dict[str, Any]:
        """
        Start the multivariate relationship dashboard
        
        Args:
            debug: Whether to run in debug mode
            
        Returns:
            Dashboard startup results
        """
        try:
            if not self.multivariate_dashboard:
                self.multivariate_dashboard = MultivariateRelationshipDashboard(
                    data_integrator=self.multivariate_integrator,
                    relationship_analyzer=self.relationship_analyzer,
                    port=self.config['multivariate_dashboard_port']
                )
            
            logger.info(f"Starting multivariate dashboard on port {self.config['multivariate_dashboard_port']}")
            
            # Run dashboard in a separate thread
            dashboard_task = asyncio.create_task(
                asyncio.to_thread(self.multivariate_dashboard.run_dashboard, debug)
            )
            
            self.analysis_state['multivariate_dashboard_ready'] = True
            
            return {
                'status': 'started',
                'port': self.config['multivariate_dashboard_port'],
                'url': f"http://localhost:{self.config['multivariate_dashboard_port']}",
                'debug_mode': debug,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting multivariate dashboard: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_real_time_analysis(self) -> Dict[str, Any]:
        """
        Run real-time multivariate analysis on current data
        
        Returns:
            Real-time analysis results
        """
        try:
            logger.info("Running real-time multivariate analysis...")
            
            # Get current data (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Integrate current data
            current_data = await self.multivariate_integrator.integrate_all_data(
                start_date=start_date,
                end_date=end_date
            )
            
            if current_data.empty:
                return {
                    'status': 'no_data',
                    'message': 'No current data available for real-time analysis',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Run quick correlation analysis
            current_correlations = self.relationship_analyzer.compute_comprehensive_correlations(
                current_data, 'conflict_risk'
            )
            
            # Compare with historical patterns
            comparison_results = await self._compare_with_historical_patterns(current_correlations)
            
            # Generate real-time alerts
            alerts = await self._generate_real_time_alerts(current_data, current_correlations)
            
            return {
                'status': 'completed',
                'analysis_timestamp': datetime.now().isoformat(),
                'data_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'current_correlations': current_correlations,
                'historical_comparison': comparison_results,
                'real_time_alerts': alerts,
                'data_quality': {
                    'completeness': float(1 - current_data.isnull().sum().sum() / (current_data.shape[0] * current_data.shape[1])),
                    'records_count': len(current_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in real-time analysis: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _compare_with_historical_patterns(self, current_correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current correlations with historical patterns"""
        try:
            # This would compare with stored historical correlation patterns
            # For now, return a placeholder structure
            
            return {
                'comparison_available': False,
                'message': 'Historical pattern comparison requires baseline data',
                'recommendations': [
                    'Establish baseline patterns through extended historical analysis',
                    'Implement automated pattern comparison system'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error comparing with historical patterns: {e}")
            return {}
    
    async def _generate_real_time_alerts(self, current_data: pd.DataFrame, 
                                       correlations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate real-time alerts based on current analysis"""
        try:
            alerts = []
            
            # Check for strong correlations
            if 'correlations' in correlations and 'pearson' in correlations['correlations']:
                strong_corrs = {
                    k: v for k, v in correlations['correlations']['pearson'].items() 
                    if abs(v) > 0.7
                }
                
                if strong_corrs:
                    alerts.append({
                        'type': 'strong_correlation_detected',
                        'severity': 'high',
                        'message': f'Strong correlations detected: {list(strong_corrs.keys())}',
                        'variables': list(strong_corrs.keys()),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check for data quality issues
            missing_ratio = current_data.isnull().sum().sum() / (current_data.shape[0] * current_data.shape[1])
            if missing_ratio > 0.3:
                alerts.append({
                    'type': 'data_quality_issue',
                    'severity': 'medium',
                    'message': f'High missing data ratio: {missing_ratio:.1%}',
                    'missing_ratio': missing_ratio,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for extreme values
            for col in current_data.select_dtypes(include=[np.number]).columns:
                z_scores = np.abs(stats.zscore(current_data[col].dropna()))
                extreme_count = np.sum(z_scores > 3)
                
                if extreme_count > 0:
                    alerts.append({
                        'type': 'extreme_values_detected',
                        'severity': 'medium',
                        'message': f'Extreme values detected in {col}: {extreme_count} observations',
                        'variable': col,
                        'extreme_count': int(extreme_count),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating real-time alerts: {e}")
            return []
    
    async def get_enhanced_system_status(self) -> Dict[str, Any]:
        """Get comprehensive enhanced system status"""
        try:
            base_status = await super().get_system_status()
            
            enhanced_status = {
                **base_status,
                'multivariate_analysis_state': {
                    'data_integrated': self.analysis_state.get('multivariate_data_integrated', False),
                    'relationships_analyzed': self.analysis_state.get('relationships_analyzed', False),
                    'dashboard_ready': self.analysis_state.get('multivariate_dashboard_ready', False)
                },
                'multivariate_results_summary': {
                    'correlation_analysis': bool(self.analysis_results.get('correlation_analysis')),
                    'causality_analysis': bool(self.analysis_results.get('causality_analysis')),
                    'feature_importance': bool(self.analysis_results.get('feature_importance')),
                    'threshold_effects': bool(self.analysis_results.get('threshold_effects')),
                    'relationship_network': bool(self.analysis_results.get('relationship_network'))
                },
                'data_integration_summary': self.analysis_results.get('multivariate_integration', {}),
                'enhanced_capabilities': [
                    'Multivariate relationship analysis',
                    'Cross-domain correlation detection',
                    'Granger causality testing',
                    'Threshold effects analysis',
                    'Interactive relationship visualization',
                    'Real-time pattern monitoring'
                ]
            }
            
            return enhanced_status
            
        except Exception as e:
            logger.error(f"Error getting enhanced system status: {e}")
            return await super().get_system_status()
    
    async def run_enhanced_automated_cycle(self):
        """Run enhanced automated analysis cycle with multivariate analysis"""
        try:
            logger.info("Starting enhanced automated analysis cycle...")
            
            # Run base automated cycle
            base_result = await super().run_automated_analysis_cycle()
            
            # Run multivariate analysis
            multivariate_result = await self.run_comprehensive_multivariate_analysis()
            
            # Run real-time analysis if enabled
            real_time_result = None
            if self.config.get('enable_real_time_analysis', True):
                real_time_result = await self.run_real_time_analysis()
            
            return {
                'cycle_status': 'completed',
                'base_analysis': base_result,
                'multivariate_analysis': multivariate_result,
                'real_time_analysis': real_time_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced automated cycle: {e}")
            return {
                'cycle_status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }