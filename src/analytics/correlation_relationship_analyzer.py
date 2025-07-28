"""
Correlation and Relationship Analyzer
Advanced module for detecting, quantifying, and analyzing relationships between
multivariate factors and their impact on geopolitical conflict risk.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Statistical analysis
from scipy import stats
from scipy.stats import pearsonr, spearmanr, kendalltau, chi2_contingency
from scipy.stats import mutual_info_regression, f_oneway
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests, coint, adfuller
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import het_breuschpagan, het_white

# Machine learning
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.feature_selection import RFE, SelectFromModel
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import LassoCV, RidgeCV, ElasticNetCV
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score, TimeSeriesSplit

# Network analysis
import networkx as nx
from networkx.algorithms import community

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class RelationshipType:
    """Types of relationships that can be detected"""
    LINEAR = "linear"
    NONLINEAR = "nonlinear"
    CAUSAL = "causal"
    LAGGED = "lagged"
    THRESHOLD = "threshold"
    INTERACTION = "interaction"

class CorrelationRelationshipAnalyzer:
    """
    Advanced analyzer for detecting and quantifying relationships between variables
    """
    
    def __init__(self, output_dir: str = "outputs/relationships"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis results storage
        self.correlation_results = {}
        self.causality_results = {}
        self.feature_importance = {}
        self.relationship_network = None
        self.threshold_effects = {}
        
        # Configuration
        self.significance_level = 0.05
        self.max_lags = 12  # Maximum lags for causality testing
        self.min_correlation = 0.1  # Minimum correlation to consider
        
    def compute_comprehensive_correlations(self, data: pd.DataFrame, 
                                         target_variable: str = 'conflict_risk') -> Dict[str, Any]:
        """
        Compute comprehensive correlation analysis including multiple correlation types
        
        Args:
            data: Input DataFrame with all variables
            target_variable: Target variable for analysis
            
        Returns:
            Dictionary with correlation results
        """
        try:
            logger.info("Computing comprehensive correlations...")
            
            # Ensure target variable exists
            if target_variable not in data.columns:
                raise ValueError(f"Target variable '{target_variable}' not found in data")
            
            # Select numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            
            results = {
                'target_variable': target_variable,
                'analysis_timestamp': datetime.now().isoformat(),
                'correlations': {},
                'significance_tests': {},
                'correlation_matrix': {},
                'partial_correlations': {},
                'nonlinear_associations': {}
            }
            
            # 1. Pearson correlations
            pearson_corrs = {}
            pearson_pvals = {}
            
            for col in numeric_data.columns:
                if col != target_variable:
                    corr, pval = pearsonr(numeric_data[col].dropna(), 
                                        numeric_data[target_variable].dropna())
                    pearson_corrs[col] = corr
                    pearson_pvals[col] = pval
            
            results['correlations']['pearson'] = pearson_corrs
            results['significance_tests']['pearson_pvals'] = pearson_pvals
            
            # 2. Spearman correlations (rank-based, captures monotonic relationships)
            spearman_corrs = {}
            spearman_pvals = {}
            
            for col in numeric_data.columns:
                if col != target_variable:
                    corr, pval = spearmanr(numeric_data[col].dropna(), 
                                         numeric_data[target_variable].dropna())
                    spearman_corrs[col] = corr
                    spearman_pvals[col] = pval
            
            results['correlations']['spearman'] = spearman_corrs
            results['significance_tests']['spearman_pvals'] = spearman_pvals
            
            # 3. Kendall's tau (robust to outliers)
            kendall_corrs = {}
            kendall_pvals = {}
            
            for col in numeric_data.columns:
                if col != target_variable:
                    corr, pval = kendalltau(numeric_data[col].dropna(), 
                                          numeric_data[target_variable].dropna())
                    kendall_corrs[col] = corr
                    kendall_pvals[col] = pval
            
            results['correlations']['kendall'] = kendall_corrs
            results['significance_tests']['kendall_pvals'] = kendall_pvals
            
            # 4. Full correlation matrix
            correlation_matrix = numeric_data.corr(method='pearson')
            results['correlation_matrix']['pearson'] = correlation_matrix.to_dict()
            
            spearman_matrix = numeric_data.corr(method='spearman')
            results['correlation_matrix']['spearman'] = spearman_matrix.to_dict()
            
            # 5. Partial correlations (controlling for other variables)
            partial_corrs = self._compute_partial_correlations(numeric_data, target_variable)
            results['partial_correlations'] = partial_corrs
            
            # 6. Mutual information (captures nonlinear relationships)
            mi_scores = {}
            for col in numeric_data.columns:
                if col != target_variable:
                    # Handle missing values
                    mask = ~(numeric_data[col].isna() | numeric_data[target_variable].isna())
                    if mask.sum() > 10:  # Need minimum samples
                        mi_score = mutual_info_regression(
                            numeric_data[col][mask].values.reshape(-1, 1),
                            numeric_data[target_variable][mask].values,
                            random_state=42
                        )[0]
                        mi_scores[col] = mi_score
            
            results['nonlinear_associations']['mutual_information'] = mi_scores
            
            # 7. Distance correlation (captures all types of dependence)
            distance_corrs = self._compute_distance_correlations(numeric_data, target_variable)
            results['nonlinear_associations']['distance_correlation'] = distance_corrs
            
            # Store results
            self.correlation_results = results
            
            logger.info("Comprehensive correlation analysis completed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error computing correlations: {e}")
            return {}
    
    def _compute_partial_correlations(self, data: pd.DataFrame, target_variable: str) -> Dict[str, float]:
        """Compute partial correlations controlling for other variables"""
        try:
            partial_corrs = {}
            
            # Get all variables except target
            control_vars = [col for col in data.columns if col != target_variable]
            
            for var in control_vars:
                # Variables to control for (all others except current var and target)
                control_for = [col for col in control_vars if col != var]
                
                if len(control_for) == 0:
                    continue
                
                # Create design matrix
                X_control = data[control_for].dropna()
                y_target = data[target_variable].loc[X_control.index]
                y_var = data[var].loc[X_control.index]
                
                if len(X_control) < 10:  # Need minimum samples
                    continue
                
                try:
                    # Regress target on control variables
                    model_target = sm.OLS(y_target, sm.add_constant(X_control)).fit()
                    residuals_target = model_target.resid
                    
                    # Regress variable on control variables
                    model_var = sm.OLS(y_var, sm.add_constant(X_control)).fit()
                    residuals_var = model_var.resid
                    
                    # Correlation of residuals is partial correlation
                    partial_corr, _ = pearsonr(residuals_var, residuals_target)
                    partial_corrs[var] = partial_corr
                    
                except Exception:
                    continue
            
            return partial_corrs
            
        except Exception as e:
            logger.error(f"Error computing partial correlations: {e}")
            return {}
    
    def _compute_distance_correlations(self, data: pd.DataFrame, target_variable: str) -> Dict[str, float]:
        """Compute distance correlations (captures all types of dependence)"""
        try:
            # Simplified distance correlation implementation
            distance_corrs = {}
            
            target_values = data[target_variable].dropna()
            
            for col in data.columns:
                if col != target_variable:
                    var_values = data[col].dropna()
                    
                    # Find common indices
                    common_idx = target_values.index.intersection(var_values.index)
                    if len(common_idx) < 10:
                        continue
                    
                    x = var_values.loc[common_idx].values
                    y = target_values.loc[common_idx].values
                    
                    # Simplified distance correlation calculation
                    # (In production, use dcor library for exact implementation)
                    n = len(x)
                    
                    # Center the distance matrices
                    a = np.abs(x[:, np.newaxis] - x[np.newaxis, :])
                    b = np.abs(y[:, np.newaxis] - y[np.newaxis, :])
                    
                    # Row and column means
                    a_row_means = np.mean(a, axis=1)
                    a_col_means = np.mean(a, axis=0)
                    a_mean = np.mean(a)
                    
                    b_row_means = np.mean(b, axis=1)
                    b_col_means = np.mean(b, axis=0)
                    b_mean = np.mean(b)
                    
                    # Centered matrices
                    A = a - a_row_means[:, np.newaxis] - a_col_means[np.newaxis, :] + a_mean
                    B = b - b_row_means[:, np.newaxis] - b_col_means[np.newaxis, :] + b_mean
                    
                    # Distance covariance and variances
                    dcov_xy = np.sqrt(np.mean(A * B))
                    dcov_xx = np.sqrt(np.mean(A * A))
                    dcov_yy = np.sqrt(np.mean(B * B))
                    
                    # Distance correlation
                    if dcov_xx > 0 and dcov_yy > 0:
                        dcorr = dcov_xy / np.sqrt(dcov_xx * dcov_yy)
                        distance_corrs[col] = dcorr
            
            return distance_corrs
            
        except Exception as e:
            logger.error(f"Error computing distance correlations: {e}")
            return {}
    
    def analyze_granger_causality(self, data: pd.DataFrame, 
                                target_variable: str = 'conflict_risk',
                                max_lags: int = None) -> Dict[str, Any]:
        """
        Analyze Granger causality relationships
        
        Args:
            data: Time series data
            target_variable: Target variable
            max_lags: Maximum number of lags to test
            
        Returns:
            Granger causality results
        """
        try:
            logger.info("Analyzing Granger causality...")
            
            if max_lags is None:
                max_lags = self.max_lags
            
            # Ensure data is stationary
            stationary_data = self._make_stationary(data)
            
            results = {
                'target_variable': target_variable,
                'max_lags_tested': max_lags,
                'causality_tests': {},
                'significant_relationships': {},
                'optimal_lags': {},
                'stationarity_tests': {}
            }
            
            # Test stationarity for all variables
            for col in stationary_data.select_dtypes(include=[np.number]).columns:
                adf_stat, adf_pval, _, _, _, _ = adfuller(stationary_data[col].dropna())
                results['stationarity_tests'][col] = {
                    'adf_statistic': adf_stat,
                    'p_value': adf_pval,
                    'is_stationary': adf_pval < self.significance_level
                }
            
            # Test Granger causality for each variable
            target_series = stationary_data[target_variable].dropna()
            
            for col in stationary_data.columns:
                if col == target_variable:
                    continue
                
                var_series = stationary_data[col].dropna()
                
                # Find common time period
                common_idx = target_series.index.intersection(var_series.index)
                if len(common_idx) < max_lags * 3:  # Need sufficient data
                    continue
                
                # Prepare data for Granger test
                test_data = pd.DataFrame({
                    'target': target_series.loc[common_idx],
                    'variable': var_series.loc[common_idx]
                }).dropna()
                
                if len(test_data) < max_lags * 3:
                    continue
                
                try:
                    # Test if variable Granger-causes target
                    gc_result = grangercausalitytests(
                        test_data[['target', 'variable']], 
                        maxlag=max_lags, 
                        verbose=False
                    )
                    
                    # Extract results for each lag
                    lag_results = {}
                    min_pval = 1.0
                    optimal_lag = 1
                    
                    for lag in range(1, max_lags + 1):
                        if lag in gc_result:
                            # Get F-test p-value
                            f_test_pval = gc_result[lag][0]['ssr_ftest'][1]
                            lag_results[lag] = {
                                'f_test_pvalue': f_test_pval,
                                'f_statistic': gc_result[lag][0]['ssr_ftest'][0],
                                'is_significant': f_test_pval < self.significance_level
                            }
                            
                            if f_test_pval < min_pval:
                                min_pval = f_test_pval
                                optimal_lag = lag
                    
                    results['causality_tests'][col] = lag_results
                    
                    if min_pval < self.significance_level:
                        results['significant_relationships'][col] = {
                            'min_pvalue': min_pval,
                            'optimal_lag': optimal_lag,
                            'relationship_strength': 'strong' if min_pval < 0.01 else 'moderate'
                        }
                        results['optimal_lags'][col] = optimal_lag
                
                except Exception as e:
                    logger.warning(f"Granger causality test failed for {col}: {e}")
                    continue
            
            # Store results
            self.causality_results = results
            
            logger.info(f"Granger causality analysis completed. Found {len(results['significant_relationships'])} significant relationships")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Granger causality analysis: {e}")
            return {}
    
    def _make_stationary(self, data: pd.DataFrame) -> pd.DataFrame:
        """Make time series stationary using differencing"""
        try:
            stationary_data = data.copy()
            
            for col in data.select_dtypes(include=[np.number]).columns:
                series = data[col].dropna()
                
                if len(series) < 10:
                    continue
                
                # Test for stationarity
                adf_stat, adf_pval, _, _, _, _ = adfuller(series)
                
                # If not stationary, apply first difference
                if adf_pval > self.significance_level:
                    diff_series = series.diff().dropna()
                    
                    # Test again
                    if len(diff_series) > 10:
                        adf_stat_diff, adf_pval_diff, _, _, _, _ = adfuller(diff_series)
                        
                        if adf_pval_diff < adf_pval:  # Improvement
                            stationary_data[col] = data[col].diff()
            
            return stationary_data
            
        except Exception as e:
            logger.error(f"Error making data stationary: {e}")
            return data
    
    def analyze_feature_importance(self, data: pd.DataFrame, 
                                 target_variable: str = 'conflict_risk') -> Dict[str, Any]:
        """
        Analyze feature importance using multiple methods
        
        Args:
            data: Input data
            target_variable: Target variable
            
        Returns:
            Feature importance results
        """
        try:
            logger.info("Analyzing feature importance...")
            
            # Prepare data
            X = data.drop(columns=[target_variable]).select_dtypes(include=[np.number])
            y = data[target_variable]
            
            # Remove rows with missing target
            mask = ~y.isna()
            X = X.loc[mask]
            y = y.loc[mask]
            
            # Handle missing values in features
            X = X.fillna(X.median())
            
            if len(X) < 10:
                raise ValueError("Insufficient data for feature importance analysis")
            
            results = {
                'target_variable': target_variable,
                'n_samples': len(X),
                'n_features': len(X.columns),
                'importance_methods': {},
                'feature_rankings': {},
                'top_features': {}
            }
            
            # 1. Random Forest importance
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(X, y)
            
            rf_importance = dict(zip(X.columns, rf_model.feature_importances_))
            results['importance_methods']['random_forest'] = rf_importance
            
            # 2. Extra Trees importance
            et_model = ExtraTreesRegressor(n_estimators=100, random_state=42)
            et_model.fit(X, y)
            
            et_importance = dict(zip(X.columns, et_model.feature_importances_))
            results['importance_methods']['extra_trees'] = et_importance
            
            # 3. Lasso feature selection
            lasso_model = LassoCV(cv=5, random_state=42)
            lasso_model.fit(X, y)
            
            lasso_importance = dict(zip(X.columns, np.abs(lasso_model.coef_)))
            results['importance_methods']['lasso'] = lasso_importance
            
            # 4. Mutual information
            mi_scores = mutual_info_regression(X, y, random_state=42)
            mi_importance = dict(zip(X.columns, mi_scores))
            results['importance_methods']['mutual_information'] = mi_importance
            
            # 5. F-statistic
            f_scores, f_pvals = f_regression(X, y)
            f_importance = dict(zip(X.columns, f_scores))
            results['importance_methods']['f_statistic'] = f_importance
            
            # 6. Recursive Feature Elimination
            rfe_model = RFE(RandomForestRegressor(n_estimators=50, random_state=42), 
                           n_features_to_select=min(10, len(X.columns)))
            rfe_model.fit(X, y)
            
            rfe_ranking = dict(zip(X.columns, rfe_model.ranking_))
            results['feature_rankings']['rfe'] = rfe_ranking
            
            # Aggregate rankings
            aggregated_importance = self._aggregate_feature_importance(results['importance_methods'])
            results['importance_methods']['aggregated'] = aggregated_importance
            
            # Get top features for each method
            for method, importance_dict in results['importance_methods'].items():
                sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
                results['top_features'][method] = sorted_features[:10]
            
            # Store results
            self.feature_importance = results
            
            logger.info("Feature importance analysis completed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in feature importance analysis: {e}")
            return {}
    
    def _aggregate_feature_importance(self, importance_methods: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Aggregate feature importance across multiple methods"""
        try:
            # Normalize each method's scores to 0-1 range
            normalized_scores = {}
            
            for method, scores in importance_methods.items():
                if not scores:
                    continue
                
                values = np.array(list(scores.values()))
                if values.max() > values.min():
                    normalized = (values - values.min()) / (values.max() - values.min())
                else:
                    normalized = np.ones_like(values)
                
                normalized_scores[method] = dict(zip(scores.keys(), normalized))
            
            # Average across methods
            all_features = set()
            for scores in normalized_scores.values():
                all_features.update(scores.keys())
            
            aggregated = {}
            for feature in all_features:
                scores = [method_scores.get(feature, 0) for method_scores in normalized_scores.values()]
                aggregated[feature] = np.mean(scores)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating feature importance: {e}")
            return {}
    
    def detect_threshold_effects(self, data: pd.DataFrame, 
                                target_variable: str = 'conflict_risk',
                                candidate_variables: List[str] = None) -> Dict[str, Any]:
        """
        Detect threshold effects where relationships change at certain values
        
        Args:
            data: Input data
            target_variable: Target variable
            candidate_variables: Variables to test for threshold effects
            
        Returns:
            Threshold effects results
        """
        try:
            logger.info("Detecting threshold effects...")
            
            if candidate_variables is None:
                candidate_variables = [col for col in data.columns 
                                     if col != target_variable and data[col].dtype in ['int64', 'float64']]
            
            results = {
                'target_variable': target_variable,
                'threshold_effects': {},
                'significant_thresholds': {},
                'regime_statistics': {}
            }
            
            for var in candidate_variables:
                var_data = data[[var, target_variable]].dropna()
                
                if len(var_data) < 50:  # Need sufficient data
                    continue
                
                # Test multiple potential thresholds
                var_values = var_data[var].values
                thresholds = np.percentile(var_values, [10, 25, 50, 75, 90])
                
                threshold_results = {}
                
                for threshold in thresholds:
                    # Split data into regimes
                    low_regime = var_data[var_data[var] <= threshold]
                    high_regime = var_data[var_data[var] > threshold]
                    
                    if len(low_regime) < 10 or len(high_regime) < 10:
                        continue
                    
                    # Test for significant difference in means
                    t_stat, t_pval = stats.ttest_ind(
                        low_regime[target_variable], 
                        high_regime[target_variable]
                    )
                    
                    # Test for significant difference in variances
                    f_stat, f_pval = stats.levene(
                        low_regime[target_variable], 
                        high_regime[target_variable]
                    )
                    
                    # Calculate effect size (Cohen's d)
                    pooled_std = np.sqrt(
                        ((len(low_regime) - 1) * low_regime[target_variable].var() + 
                         (len(high_regime) - 1) * high_regime[target_variable].var()) / 
                        (len(low_regime) + len(high_regime) - 2)
                    )
                    
                    cohens_d = (high_regime[target_variable].mean() - low_regime[target_variable].mean()) / pooled_std
                    
                    threshold_results[threshold] = {
                        'mean_difference_pvalue': t_pval,
                        'variance_difference_pvalue': f_pval,
                        'cohens_d': cohens_d,
                        'low_regime_mean': low_regime[target_variable].mean(),
                        'high_regime_mean': high_regime[target_variable].mean(),
                        'low_regime_size': len(low_regime),
                        'high_regime_size': len(high_regime),
                        'is_significant': t_pval < self.significance_level and abs(cohens_d) > 0.2
                    }
                
                results['threshold_effects'][var] = threshold_results
                
                # Find most significant threshold
                significant_thresholds = {
                    t: res for t, res in threshold_results.items() 
                    if res['is_significant']
                }
                
                if significant_thresholds:
                    best_threshold = min(significant_thresholds.keys(), 
                                       key=lambda t: threshold_results[t]['mean_difference_pvalue'])
                    results['significant_thresholds'][var] = {
                        'threshold_value': best_threshold,
                        'threshold_percentile': stats.percentileofscore(var_values, best_threshold),
                        **threshold_results[best_threshold]
                    }
            
            # Store results
            self.threshold_effects = results
            
            logger.info(f"Threshold effects analysis completed. Found {len(results['significant_thresholds'])} significant thresholds")
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting threshold effects: {e}")
            return {}
    
    def build_relationship_network(self, correlation_threshold: float = 0.3,
                                 significance_threshold: float = 0.05) -> Dict[str, Any]:
        """
        Build network graph of variable relationships
        
        Args:
            correlation_threshold: Minimum correlation to include edge
            significance_threshold: Maximum p-value for significance
            
        Returns:
            Network analysis results
        """
        try:
            logger.info("Building relationship network...")
            
            if not self.correlation_results:
                raise ValueError("No correlation results available. Run correlation analysis first.")
            
            # Create network graph
            G = nx.Graph()
            
            # Add nodes (variables)
            correlations = self.correlation_results['correlations']['pearson']
            p_values = self.correlation_results['significance_tests']['pearson_pvals']
            
            all_variables = set(correlations.keys())
            all_variables.add(self.correlation_results['target_variable'])
            
            for var in all_variables:
                G.add_node(var)
            
            # Add edges (significant correlations)
            target_var = self.correlation_results['target_variable']
            
            # Edges to target variable
            for var, corr in correlations.items():
                pval = p_values.get(var, 1.0)
                if abs(corr) >= correlation_threshold and pval <= significance_threshold:
                    G.add_edge(target_var, var, 
                             weight=abs(corr), 
                             correlation=corr,
                             p_value=pval,
                             relationship_type='direct')
            
            # Edges between variables (from correlation matrix)
            if 'pearson' in self.correlation_results['correlation_matrix']:
                corr_matrix = pd.DataFrame(self.correlation_results['correlation_matrix']['pearson'])
                
                for i, var1 in enumerate(corr_matrix.columns):
                    for j, var2 in enumerate(corr_matrix.columns):
                        if i < j:  # Avoid duplicates
                            corr = corr_matrix.loc[var1, var2]
                            if abs(corr) >= correlation_threshold:
                                G.add_edge(var1, var2,
                                         weight=abs(corr),
                                         correlation=corr,
                                         relationship_type='indirect')
            
            # Network analysis
            results = {
                'network_stats': {
                    'nodes': G.number_of_nodes(),
                    'edges': G.number_of_edges(),
                    'density': nx.density(G),
                    'average_clustering': nx.average_clustering(G),
                    'is_connected': nx.is_connected(G)
                },
                'centrality_measures': {},
                'communities': {},
                'key_relationships': {}
            }
            
            if G.number_of_nodes() > 0:
                # Centrality measures
                results['centrality_measures'] = {
                    'degree_centrality': nx.degree_centrality(G),
                    'betweenness_centrality': nx.betweenness_centrality(G),
                    'closeness_centrality': nx.closeness_centrality(G),
                    'eigenvector_centrality': nx.eigenvector_centrality(G, max_iter=1000)
                }
                
                # Community detection
                if G.number_of_edges() > 0:
                    communities = community.greedy_modularity_communities(G)
                    results['communities'] = {
                        'num_communities': len(communities),
                        'modularity': community.modularity(G, communities),
                        'community_assignments': {
                            node: i for i, comm in enumerate(communities) for node in comm
                        }
                    }
                
                # Key relationships (strongest connections)
                edge_weights = [(u, v, d['weight']) for u, v, d in G.edges(data=True)]
                edge_weights.sort(key=lambda x: x[2], reverse=True)
                
                results['key_relationships'] = {
                    'strongest_connections': edge_weights[:10],
                    'target_connections': [
                        (u, v, d) for u, v, d in G.edges(data=True) 
                        if target_var in (u, v)
                    ]
                }
            
            # Store network
            self.relationship_network = G
            
            logger.info(f"Relationship network built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            
            return results
            
        except Exception as e:
            logger.error(f"Error building relationship network: {e}")
            return {}
    
    def generate_relationship_report(self) -> Dict[str, Any]:
        """Generate comprehensive relationship analysis report"""
        try:
            logger.info("Generating relationship analysis report...")
            
            report = {
                'analysis_timestamp': datetime.now().isoformat(),
                'executive_summary': {},
                'correlation_summary': {},
                'causality_summary': {},
                'feature_importance_summary': {},
                'threshold_effects_summary': {},
                'network_summary': {},
                'key_insights': [],
                'recommendations': []
            }
            
            # Executive summary
            if self.correlation_results:
                pearson_corrs = self.correlation_results['correlations']['pearson']
                strong_corrs = {k: v for k, v in pearson_corrs.items() if abs(v) > 0.5}
                
                report['executive_summary'] = {
                    'total_variables_analyzed': len(pearson_corrs),
                    'strong_correlations_found': len(strong_corrs),
                    'target_variable': self.correlation_results['target_variable']
                }
            
            # Correlation summary
            if self.correlation_results:
                report['correlation_summary'] = {
                    'strongest_positive_correlation': max(
                        self.correlation_results['correlations']['pearson'].items(),
                        key=lambda x: x[1] if x[1] > 0 else -float('inf')
                    ),
                    'strongest_negative_correlation': min(
                        self.correlation_results['correlations']['pearson'].items(),
                        key=lambda x: x[1] if x[1] < 0 else float('inf')
                    ),
                    'nonlinear_relationships': len(
                        self.correlation_results['nonlinear_associations']['mutual_information']
                    )
                }
            
            # Causality summary
            if self.causality_results:
                report['causality_summary'] = {
                    'significant_causal_relationships': len(
                        self.causality_results['significant_relationships']
                    ),
                    'variables_tested': len(self.causality_results['causality_tests']),
                    'strongest_causal_relationship': max(
                        self.causality_results['significant_relationships'].items(),
                        key=lambda x: 1 - x[1]['min_pvalue']
                    ) if self.causality_results['significant_relationships'] else None
                }
            
            # Feature importance summary
            if self.feature_importance:
                aggregated_importance = self.feature_importance['importance_methods']['aggregated']
                top_feature = max(aggregated_importance.items(), key=lambda x: x[1])
                
                report['feature_importance_summary'] = {
                    'most_important_feature': top_feature,
                    'features_analyzed': len(aggregated_importance),
                    'methods_used': len(self.feature_importance['importance_methods']) - 1  # Exclude aggregated
                }
            
            # Threshold effects summary
            if self.threshold_effects:
                report['threshold_effects_summary'] = {
                    'variables_with_thresholds': len(self.threshold_effects['significant_thresholds']),
                    'variables_tested': len(self.threshold_effects['threshold_effects'])
                }
            
            # Generate insights
            insights = self._generate_insights()
            report['key_insights'] = insights
            
            # Generate recommendations
            recommendations = self._generate_recommendations()
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating relationship report: {e}")
            return {}
    
    def _generate_insights(self) -> List[str]:
        """Generate key insights from analysis results"""
        insights = []
        
        try:
            # Correlation insights
            if self.correlation_results:
                pearson_corrs = self.correlation_results['correlations']['pearson']
                strong_corrs = {k: v for k, v in pearson_corrs.items() if abs(v) > 0.5}
                
                if strong_corrs:
                    strongest_var, strongest_corr = max(strong_corrs.items(), key=lambda x: abs(x[1]))
                    direction = "positively" if strongest_corr > 0 else "negatively"
                    insights.append(
                        f"{strongest_var} shows the strongest correlation with conflict risk "
                        f"({direction} correlated, r={strongest_corr:.3f})"
                    )
            
            # Causality insights
            if self.causality_results and self.causality_results['significant_relationships']:
                causal_vars = list(self.causality_results['significant_relationships'].keys())
                insights.append(
                    f"Granger causality analysis identified {len(causal_vars)} variables that "
                    f"significantly predict future conflict risk: {', '.join(causal_vars[:3])}"
                )
            
            # Feature importance insights
            if self.feature_importance:
                top_features = self.feature_importance['top_features']['aggregated'][:3]
                feature_names = [f[0] for f in top_features]
                insights.append(
                    f"Most important predictive features: {', '.join(feature_names)}"
                )
            
            # Threshold insights
            if self.threshold_effects and self.threshold_effects['significant_thresholds']:
                threshold_vars = list(self.threshold_effects['significant_thresholds'].keys())
                insights.append(
                    f"Threshold effects detected for {len(threshold_vars)} variables, "
                    f"indicating non-linear relationships with conflict risk"
                )
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        try:
            # Monitoring recommendations
            if self.correlation_results:
                strong_corrs = {
                    k: v for k, v in self.correlation_results['correlations']['pearson'].items() 
                    if abs(v) > 0.5
                }
                if strong_corrs:
                    recommendations.append(
                        f"Prioritize monitoring of {len(strong_corrs)} strongly correlated variables "
                        f"for early warning indicators"
                    )
            
            # Causal variable recommendations
            if self.causality_results and self.causality_results['significant_relationships']:
                recommendations.append(
                    "Focus predictive models on variables with established causal relationships "
                    "for improved forecasting accuracy"
                )
            
            # Threshold monitoring
            if self.threshold_effects and self.threshold_effects['significant_thresholds']:
                recommendations.append(
                    "Implement threshold-based alert systems for variables showing regime-switching behavior"
                )
            
            # Data collection recommendations
            recommendations.append(
                "Continue expanding historical data collection to improve relationship detection "
                "and model accuracy"
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations