"""
Advanced Pattern Detection and Clustering Module
Implements unsupervised learning techniques including K-means, DBSCAN, deep neural networks
for feature extraction, and dimensionality reduction to identify complex patterns, anomalies,
and emerging trends in geopolitical and disaster data.
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

# Clustering algorithms
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, SpectralClustering
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA, FastICA, TruncatedSVD
from sklearn.manifold import TSNE
from umap import UMAP
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

# Anomaly detection
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope

# Deep learning for feature extraction
import tensorflow as tf
from keras.models import Model, Sequential
from keras.layers import Dense, Input, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras import regularizers

# Statistical analysis
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.signal import find_peaks, savgol_filter
import networkx as nx

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import ListedColormap

logger = logging.getLogger(__name__)

class AdvancedPatternDetector:
    """
    Comprehensive pattern detection system using multiple unsupervised learning techniques
    to identify complex patterns, anomalies, and emerging trends in geopolitical data
    """
    
    def __init__(self, output_dir: str = "outputs/patterns"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Scalers for different preprocessing approaches
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler()
        }
        
        # Dimensionality reduction models
        self.dim_reduction_models = {
            'pca': None,
            'ica': None,
            'tsne': None,
            'umap': None
        }
        
        # Clustering models
        self.clustering_models = {
            'kmeans': None,
            'dbscan': None,
            'gaussian_mixture': None,
            'spectral': None,
            'hierarchical': None
        }
        
        # Anomaly detection models
        self.anomaly_models = {
            'isolation_forest': None,
            'one_class_svm': None,
            'local_outlier_factor': None,
            'elliptic_envelope': None
        }
        
        # Deep learning autoencoder for feature extraction
        self.autoencoder = None
        self.encoder = None
        
        # Pattern library
        self.detected_patterns = {}
        self.pattern_metadata = {}
        
        # Performance metrics
        self.clustering_metrics = {}
        self.anomaly_scores = {}
    
    def preprocess_data(self, data: pd.DataFrame, 
                       scaling_method: str = 'standard',
                       handle_missing: str = 'drop',
                       feature_selection: bool = True) -> pd.DataFrame:
        """
        Comprehensive data preprocessing for pattern detection
        
        Args:
            data: Input DataFrame
            scaling_method: Scaling method ('standard', 'minmax', 'robust')
            handle_missing: How to handle missing values ('drop', 'fill', 'interpolate')
            feature_selection: Whether to perform feature selection
            
        Returns:
            Preprocessed DataFrame
        """
        try:
            logger.info("Preprocessing data for pattern detection")
            
            # Create a copy
            processed_data = data.copy()
            
            # Handle missing values
            if handle_missing == 'drop':
                processed_data = processed_data.dropna()
            elif handle_missing == 'fill':
                # Fill numeric columns with median, categorical with mode
                for col in processed_data.columns:
                    if processed_data[col].dtype in ['int64', 'float64']:
                        processed_data[col].fillna(processed_data[col].median(), inplace=True)
                    else:
                        processed_data[col].fillna(processed_data[col].mode().iloc[0] if not processed_data[col].mode().empty else 'unknown', inplace=True)
            elif handle_missing == 'interpolate':
                processed_data = processed_data.interpolate(method='linear')
                processed_data = processed_data.fillna(method='bfill').fillna(method='ffill')
            
            # Select only numeric columns for clustering
            numeric_columns = processed_data.select_dtypes(include=[np.number]).columns
            processed_data = processed_data[numeric_columns]
            
            # Remove constant columns
            constant_columns = processed_data.columns[processed_data.nunique() <= 1]
            if len(constant_columns) > 0:
                processed_data = processed_data.drop(columns=constant_columns)
                logger.info(f"Removed {len(constant_columns)} constant columns")
            
            # Feature selection based on variance
            if feature_selection and len(processed_data.columns) > 10:
                from sklearn.feature_selection import VarianceThreshold
                
                # Remove low variance features
                variance_selector = VarianceThreshold(threshold=0.01)
                selected_features = variance_selector.fit_transform(processed_data)
                selected_columns = processed_data.columns[variance_selector.get_support()]
                processed_data = pd.DataFrame(selected_features, columns=selected_columns, index=processed_data.index)
                
                logger.info(f"Selected {len(selected_columns)} features after variance filtering")
            
            # Scale the data
            if scaling_method in self.scalers:
                scaled_data = self.scalers[scaling_method].fit_transform(processed_data)
                processed_data = pd.DataFrame(scaled_data, columns=processed_data.columns, index=processed_data.index)
            
            logger.info(f"Preprocessed data shape: {processed_data.shape}")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return pd.DataFrame()
    
    def apply_dimensionality_reduction(self, data: pd.DataFrame, 
                                     methods: List[str] = ['pca', 'tsne'],
                                     n_components: int = 2) -> Dict[str, np.ndarray]:
        """
        Apply multiple dimensionality reduction techniques
        
        Args:
            data: Input data
            methods: List of methods to apply
            n_components: Number of components to reduce to
            
        Returns:
            Dictionary of reduced data for each method
        """
        try:
            logger.info(f"Applying dimensionality reduction with methods: {methods}")
            
            reduced_data = {}
            
            for method in methods:
                if method == 'pca':
                    self.dim_reduction_models['pca'] = PCA(n_components=n_components, random_state=42)
                    reduced_data['pca'] = self.dim_reduction_models['pca'].fit_transform(data)
                    
                    # Store explained variance ratio
                    explained_variance = self.dim_reduction_models['pca'].explained_variance_ratio_
                    logger.info(f"PCA explained variance ratio: {explained_variance}")
                
                elif method == 'ica':
                    self.dim_reduction_models['ica'] = FastICA(n_components=n_components, random_state=42)
                    reduced_data['ica'] = self.dim_reduction_models['ica'].fit_transform(data)
                
                elif method == 'tsne':
                    # t-SNE is computationally expensive, limit data size
                    sample_size = min(5000, len(data))
                    if len(data) > sample_size:
                        sample_indices = np.random.choice(len(data), sample_size, replace=False)
                        sample_data = data.iloc[sample_indices]
                    else:
                        sample_data = data
                        sample_indices = np.arange(len(data))
                    
                    self.dim_reduction_models['tsne'] = TSNE(
                        n_components=n_components, 
                        random_state=42, 
                        perplexity=min(30, len(sample_data) - 1)
                    )
                    tsne_result = self.dim_reduction_models['tsne'].fit_transform(sample_data)
                    
                    # Create full array with NaN for non-sampled points
                    full_tsne = np.full((len(data), n_components), np.nan)
                    full_tsne[sample_indices] = tsne_result
                    reduced_data['tsne'] = full_tsne
                
                elif method == 'umap':
                    try:
                        import umap
                        self.dim_reduction_models['umap'] = umap.UMAP(
                            n_components=n_components, 
                            random_state=42
                        )
                        reduced_data['umap'] = self.dim_reduction_models['umap'].fit_transform(data)
                    except ImportError:
                        logger.warning("UMAP not available, skipping")
                        continue
            
            return reduced_data
            
        except Exception as e:
            logger.error(f"Error applying dimensionality reduction: {e}")
            return {}
    
    def detect_clusters(self, data: pd.DataFrame, 
                       methods: List[str] = ['kmeans', 'dbscan', 'gaussian_mixture'],
                       n_clusters_range: Tuple[int, int] = (2, 10)) -> Dict[str, Any]:
        """
        Apply multiple clustering algorithms to detect patterns
        
        Args:
            data: Input data
            methods: List of clustering methods to apply
            n_clusters_range: Range of cluster numbers to try
            
        Returns:
            Dictionary containing clustering results and metrics
        """
        try:
            logger.info(f"Detecting clusters using methods: {methods}")
            
            clustering_results = {
                'methods_used': methods,
                'cluster_labels': {},
                'cluster_centers': {},
                'metrics': {},
                'optimal_clusters': {}
            }
            
            for method in methods:
                if method == 'kmeans':
                    results = self._apply_kmeans_clustering(data, n_clusters_range)
                    clustering_results['cluster_labels']['kmeans'] = results['labels']
                    clustering_results['cluster_centers']['kmeans'] = results['centers']
                    clustering_results['metrics']['kmeans'] = results['metrics']
                    clustering_results['optimal_clusters']['kmeans'] = results['optimal_k']
                
                elif method == 'dbscan':
                    results = self._apply_dbscan_clustering(data)
                    clustering_results['cluster_labels']['dbscan'] = results['labels']
                    clustering_results['metrics']['dbscan'] = results['metrics']
                
                elif method == 'gaussian_mixture':
                    results = self._apply_gaussian_mixture_clustering(data, n_clusters_range)
                    clustering_results['cluster_labels']['gaussian_mixture'] = results['labels']
                    clustering_results['cluster_centers']['gaussian_mixture'] = results['centers']
                    clustering_results['metrics']['gaussian_mixture'] = results['metrics']
                    clustering_results['optimal_clusters']['gaussian_mixture'] = results['optimal_k']
                
                elif method == 'spectral':
                    results = self._apply_spectral_clustering(data, n_clusters_range)
                    clustering_results['cluster_labels']['spectral'] = results['labels']
                    clustering_results['metrics']['spectral'] = results['metrics']
                    clustering_results['optimal_clusters']['spectral'] = results['optimal_k']
                
                elif method == 'hierarchical':
                    results = self._apply_hierarchical_clustering(data, n_clusters_range)
                    clustering_results['cluster_labels']['hierarchical'] = results['labels']
                    clustering_results['metrics']['hierarchical'] = results['metrics']
                    clustering_results['optimal_clusters']['hierarchical'] = results['optimal_k']
            
            # Store clustering metrics
            self.clustering_metrics = clustering_results['metrics']
            
            return clustering_results
            
        except Exception as e:
            logger.error(f"Error detecting clusters: {e}")
            return {}
    
    def _apply_kmeans_clustering(self, data: pd.DataFrame, n_clusters_range: Tuple[int, int]) -> Dict[str, Any]:
        """Apply K-means clustering with optimal cluster selection"""
        try:
            min_k, max_k = n_clusters_range
            max_k = min(max_k, len(data) - 1)
            
            silhouette_scores = []
            inertias = []
            calinski_scores = []
            
            best_score = -1
            best_k = min_k
            best_labels = None
            best_centers = None
            
            for k in range(min_k, max_k + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(data)
                
                # Calculate metrics
                silhouette_avg = silhouette_score(data, labels)
                calinski_avg = calinski_harabasz_score(data, labels)
                
                silhouette_scores.append(silhouette_avg)
                inertias.append(kmeans.inertia_)
                calinski_scores.append(calinski_avg)
                
                # Select best based on silhouette score
                if silhouette_avg > best_score:
                    best_score = silhouette_avg
                    best_k = k
                    best_labels = labels
                    best_centers = kmeans.cluster_centers_
            
            # Store the best model
            self.clustering_models['kmeans'] = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            self.clustering_models['kmeans'].fit(data)
            
            return {
                'labels': best_labels,
                'centers': best_centers,
                'optimal_k': best_k,
                'metrics': {
                    'silhouette_scores': silhouette_scores,
                    'inertias': inertias,
                    'calinski_scores': calinski_scores,
                    'best_silhouette': best_score,
                    'davies_bouldin': davies_bouldin_score(data, best_labels)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in K-means clustering: {e}")
            return {}
    
    def _apply_dbscan_clustering(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Apply DBSCAN clustering with parameter optimization"""
        try:
            from sklearn.neighbors import NearestNeighbors
            
            # Estimate optimal eps using k-distance graph
            k = min(4, len(data) - 1)
            neighbors = NearestNeighbors(n_neighbors=k)
            neighbors_fit = neighbors.fit(data)
            distances, indices = neighbors_fit.kneighbors(data)
            
            # Sort distances and find the elbow
            distances = np.sort(distances[:, k-1], axis=0)
            
            # Use gradient to find elbow point
            gradients = np.gradient(distances)
            elbow_index = np.argmax(gradients)
            optimal_eps = distances[elbow_index]
            
            # Apply DBSCAN with optimal parameters
            dbscan = DBSCAN(eps=optimal_eps, min_samples=k)
            labels = dbscan.fit_predict(data)
            
            # Calculate metrics
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)
            
            metrics = {
                'n_clusters': n_clusters,
                'n_noise_points': n_noise,
                'noise_ratio': n_noise / len(labels),
                'optimal_eps': optimal_eps,
                'min_samples': k
            }
            
            # Calculate silhouette score if we have clusters
            if n_clusters > 1:
                # Exclude noise points for silhouette calculation
                non_noise_mask = labels != -1
                if np.sum(non_noise_mask) > 1:
                    silhouette_avg = silhouette_score(data[non_noise_mask], labels[non_noise_mask])
                    metrics['silhouette_score'] = silhouette_avg
            
            self.clustering_models['dbscan'] = dbscan
            
            return {
                'labels': labels,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error in DBSCAN clustering: {e}")
            return {}
    
    def _apply_gaussian_mixture_clustering(self, data: pd.DataFrame, n_clusters_range: Tuple[int, int]) -> Dict[str, Any]:
        """Apply Gaussian Mixture Model clustering"""
        try:
            min_k, max_k = n_clusters_range
            max_k = min(max_k, len(data) - 1)
            
            bic_scores = []
            aic_scores = []
            best_bic = np.inf
            best_k = min_k
            best_labels = None
            best_centers = None
            
            for k in range(min_k, max_k + 1):
                gmm = GaussianMixture(n_components=k, random_state=42)
                gmm.fit(data)
                labels = gmm.predict(data)
                
                bic = gmm.bic(data)
                aic = gmm.aic(data)
                
                bic_scores.append(bic)
                aic_scores.append(aic)
                
                # Select best based on BIC (lower is better)
                if bic < best_bic:
                    best_bic = bic
                    best_k = k
                    best_labels = labels
                    best_centers = gmm.means_
            
            # Store the best model
            self.clustering_models['gaussian_mixture'] = GaussianMixture(n_components=best_k, random_state=42)
            self.clustering_models['gaussian_mixture'].fit(data)
            
            # Calculate additional metrics
            silhouette_avg = silhouette_score(data, best_labels)
            
            return {
                'labels': best_labels,
                'centers': best_centers,
                'optimal_k': best_k,
                'metrics': {
                    'bic_scores': bic_scores,
                    'aic_scores': aic_scores,
                    'best_bic': best_bic,
                    'silhouette_score': silhouette_avg
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Gaussian Mixture clustering: {e}")
            return {}
    
    def _apply_spectral_clustering(self, data: pd.DataFrame, n_clusters_range: Tuple[int, int]) -> Dict[str, Any]:
        """Apply Spectral clustering"""
        try:
            min_k, max_k = n_clusters_range
            max_k = min(max_k, len(data) - 1)
            
            silhouette_scores = []
            best_score = -1
            best_k = min_k
            best_labels = None
            
            for k in range(min_k, max_k + 1):
                spectral = SpectralClustering(n_clusters=k, random_state=42, affinity='rbf')
                labels = spectral.fit_predict(data)
                
                silhouette_avg = silhouette_score(data, labels)
                silhouette_scores.append(silhouette_avg)
                
                if silhouette_avg > best_score:
                    best_score = silhouette_avg
                    best_k = k
                    best_labels = labels
            
            self.clustering_models['spectral'] = SpectralClustering(n_clusters=best_k, random_state=42, affinity='rbf')
            
            return {
                'labels': best_labels,
                'optimal_k': best_k,
                'metrics': {
                    'silhouette_scores': silhouette_scores,
                    'best_silhouette': best_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Spectral clustering: {e}")
            return {}
    
    def _apply_hierarchical_clustering(self, data: pd.DataFrame, n_clusters_range: Tuple[int, int]) -> Dict[str, Any]:
        """Apply Hierarchical clustering"""
        try:
            min_k, max_k = n_clusters_range
            max_k = min(max_k, len(data) - 1)
            
            # Compute linkage matrix
            linkage_matrix = linkage(data, method='ward')
            
            silhouette_scores = []
            best_score = -1
            best_k = min_k
            best_labels = None
            
            for k in range(min_k, max_k + 1):
                labels = fcluster(linkage_matrix, k, criterion='maxclust') - 1  # Convert to 0-based
                
                silhouette_avg = silhouette_score(data, labels)
                silhouette_scores.append(silhouette_avg)
                
                if silhouette_avg > best_score:
                    best_score = silhouette_avg
                    best_k = k
                    best_labels = labels
            
            self.clustering_models['hierarchical'] = AgglomerativeClustering(n_clusters=best_k)
            
            return {
                'labels': best_labels,
                'optimal_k': best_k,
                'linkage_matrix': linkage_matrix,
                'metrics': {
                    'silhouette_scores': silhouette_scores,
                    'best_silhouette': best_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Hierarchical clustering: {e}")
            return {}
    
    def detect_anomalies(self, data: pd.DataFrame, 
                        methods: List[str] = ['isolation_forest', 'one_class_svm'],
                        contamination: float = 0.1) -> Dict[str, Any]:
        """
        Detect anomalies using multiple algorithms
        
        Args:
            data: Input data
            methods: List of anomaly detection methods
            contamination: Expected proportion of anomalies
            
        Returns:
            Dictionary containing anomaly detection results
        """
        try:
            logger.info(f"Detecting anomalies using methods: {methods}")
            
            anomaly_results = {
                'methods_used': methods,
                'anomaly_labels': {},
                'anomaly_scores': {},
                'consensus_anomalies': [],
                'summary': {}
            }
            
            all_anomaly_labels = []
            
            for method in methods:
                if method == 'isolation_forest':
                    results = self._apply_isolation_forest(data, contamination)
                    anomaly_results['anomaly_labels']['isolation_forest'] = results['labels']
                    anomaly_results['anomaly_scores']['isolation_forest'] = results['scores']
                    all_anomaly_labels.append(results['labels'])
                
                elif method == 'one_class_svm':
                    results = self._apply_one_class_svm(data, contamination)
                    anomaly_results['anomaly_labels']['one_class_svm'] = results['labels']
                    anomaly_results['anomaly_scores']['one_class_svm'] = results['scores']
                    all_anomaly_labels.append(results['labels'])
                
                elif method == 'local_outlier_factor':
                    results = self._apply_local_outlier_factor(data, contamination)
                    anomaly_results['anomaly_labels']['local_outlier_factor'] = results['labels']
                    anomaly_results['anomaly_scores']['local_outlier_factor'] = results['scores']
                    all_anomaly_labels.append(results['labels'])
                
                elif method == 'elliptic_envelope':
                    results = self._apply_elliptic_envelope(data, contamination)
                    anomaly_results['anomaly_labels']['elliptic_envelope'] = results['labels']
                    anomaly_results['anomaly_scores']['elliptic_envelope'] = results['scores']
                    all_anomaly_labels.append(results['labels'])
            
            # Find consensus anomalies (detected by multiple methods)
            if len(all_anomaly_labels) > 1:
                anomaly_matrix = np.array(all_anomaly_labels).T
                consensus_count = np.sum(anomaly_matrix == -1, axis=1)
                
                # Points detected as anomalies by at least half of the methods
                threshold = len(methods) // 2 + 1
                consensus_anomalies = np.where(consensus_count >= threshold)[0].tolist()
                anomaly_results['consensus_anomalies'] = consensus_anomalies
            
            # Generate summary
            anomaly_results['summary'] = self._generate_anomaly_summary(anomaly_results, data)
            
            # Store anomaly scores
            self.anomaly_scores = anomaly_results['anomaly_scores']
            
            return anomaly_results
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {}
    
    def _apply_isolation_forest(self, data: pd.DataFrame, contamination: float) -> Dict[str, Any]:
        """Apply Isolation Forest anomaly detection"""
        try:
            isolation_forest = IsolationForest(contamination=contamination, random_state=42)
            labels = isolation_forest.fit_predict(data)
            scores = isolation_forest.score_samples(data)
            
            self.anomaly_models['isolation_forest'] = isolation_forest
            
            return {
                'labels': labels,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"Error in Isolation Forest: {e}")
            return {}
    
    def _apply_one_class_svm(self, data: pd.DataFrame, contamination: float) -> Dict[str, Any]:
        """Apply One-Class SVM anomaly detection"""
        try:
            nu = min(contamination, 0.5)  # nu parameter should be <= 0.5
            one_class_svm = OneClassSVM(nu=nu, kernel='rbf', gamma='scale')
            labels = one_class_svm.fit_predict(data)
            scores = one_class_svm.score_samples(data)
            
            self.anomaly_models['one_class_svm'] = one_class_svm
            
            return {
                'labels': labels,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"Error in One-Class SVM: {e}")
            return {}
    
    def _apply_local_outlier_factor(self, data: pd.DataFrame, contamination: float) -> Dict[str, Any]:
        """Apply Local Outlier Factor anomaly detection"""
        try:
            lof = LocalOutlierFactor(contamination=contamination, novelty=False)
            labels = lof.fit_predict(data)
            scores = lof.negative_outlier_factor_
            
            self.anomaly_models['local_outlier_factor'] = lof
            
            return {
                'labels': labels,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"Error in Local Outlier Factor: {e}")
            return {}
    
    def _apply_elliptic_envelope(self, data: pd.DataFrame, contamination: float) -> Dict[str, Any]:
        """Apply Elliptic Envelope anomaly detection"""
        try:
            elliptic_envelope = EllipticEnvelope(contamination=contamination, random_state=42)
            labels = elliptic_envelope.fit_predict(data)
            scores = elliptic_envelope.score_samples(data)
            
            self.anomaly_models['elliptic_envelope'] = elliptic_envelope
            
            return {
                'labels': labels,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"Error in Elliptic Envelope: {e}")
            return {}
    
    def _generate_anomaly_summary(self, anomaly_results: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary of anomaly detection results"""
        try:
            summary = {
                'total_samples': len(data),
                'methods_comparison': {},
                'consensus_analysis': {},
                'top_anomalies': []
            }
            
            # Compare methods
            for method, labels in anomaly_results['anomaly_labels'].items():
                n_anomalies = np.sum(labels == -1)
                anomaly_rate = n_anomalies / len(labels)
                
                summary['methods_comparison'][method] = {
                    'anomalies_detected': int(n_anomalies),
                    'anomaly_rate': float(anomaly_rate)
                }
            
            # Consensus analysis
            if anomaly_results['consensus_anomalies']:
                consensus_count = len(anomaly_results['consensus_anomalies'])
                summary['consensus_analysis'] = {
                    'consensus_anomalies': consensus_count,
                    'consensus_rate': consensus_count / len(data),
                    'agreement_threshold': 'majority'
                }
            
            # Identify top anomalies based on scores
            if anomaly_results['anomaly_scores']:
                # Combine scores from all methods
                combined_scores = []
                for method, scores in anomaly_results['anomaly_scores'].items():
                    # Normalize scores to [0, 1] range
                    normalized_scores = (scores - scores.min()) / (scores.max() - scores.min())
                    combined_scores.append(normalized_scores)
                
                if combined_scores:
                    avg_scores = np.mean(combined_scores, axis=0)
                    top_anomaly_indices = np.argsort(avg_scores)[:10]  # Top 10 anomalies
                    
                    summary['top_anomalies'] = [
                        {
                            'index': int(idx),
                            'anomaly_score': float(avg_scores[idx]),
                            'data_point': data.iloc[idx].to_dict()
                        }
                        for idx in top_anomaly_indices
                    ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating anomaly summary: {e}")
            return {}
    
    def train_autoencoder(self, data: pd.DataFrame, 
                         encoding_dim: int = 10,
                         epochs: int = 100,
                         batch_size: int = 32) -> Dict[str, Any]:
        """
        Train deep autoencoder for feature extraction and anomaly detection
        
        Args:
            data: Input data
            encoding_dim: Dimension of encoded representation
            epochs: Training epochs
            batch_size: Batch size
            
        Returns:
            Training results
        """
        try:
            logger.info("Training autoencoder for feature extraction")
            
            input_dim = data.shape[1]
            
            # Build autoencoder architecture
            input_layer = Input(shape=(input_dim,))
            
            # Encoder
            encoded = Dense(64, activation='relu', activity_regularizer=regularizers.l1(10e-5))(input_layer)
            encoded = BatchNormalization()(encoded)
            encoded = Dropout(0.2)(encoded)
            
            encoded = Dense(32, activation='relu')(encoded)
            encoded = BatchNormalization()(encoded)
            encoded = Dropout(0.2)(encoded)
            
            encoded = Dense(encoding_dim, activation='relu')(encoded)
            
            # Decoder
            decoded = Dense(32, activation='relu')(encoded)
            decoded = BatchNormalization()(decoded)
            decoded = Dropout(0.2)(decoded)
            
            decoded = Dense(64, activation='relu')(decoded)
            decoded = BatchNormalization()(decoded)
            decoded = Dropout(0.2)(decoded)
            
            decoded = Dense(input_dim, activation='linear')(decoded)
            
            # Create models
            self.autoencoder = Model(input_layer, decoded)
            self.encoder = Model(input_layer, encoded)
            
            # Compile autoencoder
            self.autoencoder.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            
            # Train autoencoder
            history = self.autoencoder.fit(
                data, data,
                epochs=epochs,
                batch_size=batch_size,
                shuffle=True,
                validation_split=0.2,
                verbose=0
            )
            
            # Generate encoded features
            encoded_features = self.encoder.predict(data)
            
            # Calculate reconstruction error for anomaly detection
            reconstructed = self.autoencoder.predict(data)
            reconstruction_error = np.mean(np.square(data - reconstructed), axis=1)
            
            # Identify anomalies based on reconstruction error
            threshold = np.percentile(reconstruction_error, 95)  # Top 5% as anomalies
            autoencoder_anomalies = reconstruction_error > threshold
            
            # Save models
            autoencoder_path = self.output_dir / 'autoencoder.h5'
            encoder_path = self.output_dir / 'encoder.h5'
            
            self.autoencoder.save(autoencoder_path)
            self.encoder.save(encoder_path)
            
            return {
                'model_type': 'Autoencoder',
                'input_dim': input_dim,
                'encoding_dim': encoding_dim,
                'training_epochs': len(history.history['loss']),
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'encoded_features_shape': encoded_features.shape,
                'anomaly_threshold': float(threshold),
                'anomalies_detected': int(np.sum(autoencoder_anomalies)),
                'model_paths': {
                    'autoencoder': str(autoencoder_path),
                    'encoder': str(encoder_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Error training autoencoder: {e}")
            return {}
    
    def identify_temporal_patterns(self, data: pd.DataFrame, 
                                 timestamp_column: str = 'timestamp',
                                 value_columns: List[str] = None) -> Dict[str, Any]:
        """
        Identify temporal patterns including cycles, trends, and seasonality
        
        Args:
            data: Time series data
            timestamp_column: Name of timestamp column
            value_columns: List of value columns to analyze
            
        Returns:
            Temporal pattern analysis results
        """
        try:
            logger.info("Identifying temporal patterns")
            
            if timestamp_column not in data.columns:
                return {'error': 'Timestamp column not found'}
            
            # Ensure timestamp is datetime
            data[timestamp_column] = pd.to_datetime(data[timestamp_column])
            data = data.sort_values(timestamp_column)
            
            if value_columns is None:
                value_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            
            temporal_patterns = {
                'analysis_period': {
                    'start': data[timestamp_column].min().isoformat(),
                    'end': data[timestamp_column].max().isoformat(),
                    'duration_days': (data[timestamp_column].max() - data[timestamp_column].min()).days
                },
                'patterns_by_column': {},
                'cross_correlation': {},
                'seasonal_decomposition': {}
            }
            
            for column in value_columns:
                if column == timestamp_column:
                    continue
                
                series = data.set_index(timestamp_column)[column].dropna()
                
                if len(series) < 10:  # Need minimum data points
                    continue
                
                column_patterns = self._analyze_temporal_series(series)
                temporal_patterns['patterns_by_column'][column] = column_patterns
            
            # Cross-correlation analysis
            if len(value_columns) > 1:
                temporal_patterns['cross_correlation'] = self._analyze_cross_correlation(data, value_columns, timestamp_column)
            
            return temporal_patterns
            
        except Exception as e:
            logger.error(f"Error identifying temporal patterns: {e}")
            return {}
    
    def _analyze_temporal_series(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze individual time series for patterns"""
        try:
            patterns = {
                'trend_analysis': {},
                'seasonality': {},
                'cycles': {},
                'anomalies': {},
                'statistics': {}
            }
            
            # Basic statistics
            patterns['statistics'] = {
                'mean': float(series.mean()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'skewness': float(stats.skew(series)),
                'kurtosis': float(stats.kurtosis(series))
            }
            
            # Trend analysis
            x = np.arange(len(series))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, series.values)
            
            patterns['trend_analysis'] = {
                'slope': float(slope),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                'trend_strength': 'strong' if abs(r_value) > 0.7 else 'moderate' if abs(r_value) > 0.3 else 'weak'
            }
            
            # Detect cycles using autocorrelation
            if len(series) > 50:
                autocorr = [series.autocorr(lag=i) for i in range(1, min(50, len(series)//2))]
                peaks, _ = find_peaks(autocorr, height=0.3, distance=5)
                
                if len(peaks) > 0:
                    dominant_cycle = peaks[np.argmax([autocorr[p] for p in peaks])] + 1
                    patterns['cycles'] = {
                        'dominant_cycle_length': int(dominant_cycle),
                        'cycle_strength': float(autocorr[dominant_cycle - 1]),
                        'all_cycles': [int(p + 1) for p in peaks]
                    }
            
            # Seasonality detection (if enough data)
            if len(series) > 100:
                try:
                    # Resample to daily frequency if needed
                    if series.index.freq is None:
                        series_daily = series.resample('D').mean().fillna(method='forward')
                    else:
                        series_daily = series
                    
                    if len(series_daily) > 100:
                        decomposition = seasonal_decompose(series_daily, model='additive', period=30)
                        
                        patterns['seasonality'] = {
                            'seasonal_strength': float(np.std(decomposition.seasonal) / np.std(series_daily)),
                            'trend_strength': float(np.std(decomposition.trend.dropna()) / np.std(series_daily)),
                            'residual_strength': float(np.std(decomposition.resid.dropna()) / np.std(series_daily))
                        }
                except Exception:
                    # Seasonality analysis failed
                    pass
            
            # Anomaly detection using statistical methods
            z_scores = np.abs(stats.zscore(series))
            anomaly_threshold = 3
            anomalies = np.where(z_scores > anomaly_threshold)[0]
            
            patterns['anomalies'] = {
                'count': len(anomalies),
                'indices': anomalies.tolist(),
                'threshold': anomaly_threshold,
                'anomaly_rate': len(anomalies) / len(series)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing temporal series: {e}")
            return {}
    
    def _analyze_cross_correlation(self, data: pd.DataFrame, value_columns: List[str], timestamp_column: str) -> Dict[str, Any]:
        """Analyze cross-correlation between different time series"""
        try:
            cross_corr = {}
            
            # Set timestamp as index
            data_indexed = data.set_index(timestamp_column)
            
            for i, col1 in enumerate(value_columns):
                for col2 in value_columns[i+1:]:
                    if col1 in data_indexed.columns and col2 in data_indexed.columns:
                        series1 = data_indexed[col1].dropna()
                        series2 = data_indexed[col2].dropna()
                        
                        # Find common index
                        common_index = series1.index.intersection(series2.index)
                        if len(common_index) > 10:
                            s1_common = series1.loc[common_index]
                            s2_common = series2.loc[common_index]
                            
                            # Calculate correlation
                            correlation = s1_common.corr(s2_common)
                            
                            # Calculate lagged correlations
                            max_lag = min(30, len(common_index) // 4)
                            lagged_corrs = []
                            
                            for lag in range(-max_lag, max_lag + 1):
                                if lag == 0:
                                    lagged_corr = correlation
                                elif lag > 0:
                                    lagged_corr = s1_common.corr(s2_common.shift(lag))
                                else:
                                    lagged_corr = s1_common.shift(-lag).corr(s2_common)
                                
                                if not np.isnan(lagged_corr):
                                    lagged_corrs.append({'lag': lag, 'correlation': float(lagged_corr)})
                            
                            # Find best lag
                            if lagged_corrs:
                                best_lag_info = max(lagged_corrs, key=lambda x: abs(x['correlation']))
                                
                                cross_corr[f"{col1}_vs_{col2}"] = {
                                    'correlation': float(correlation),
                                    'best_lag': best_lag_info['lag'],
                                    'best_lag_correlation': best_lag_info['correlation'],
                                    'lagged_correlations': lagged_corrs,
                                    'relationship_strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak'
                                }
            
            return cross_corr
            
        except Exception as e:
            logger.error(f"Error analyzing cross-correlation: {e}")
            return {}
    
    def generate_pattern_report(self, clustering_results: Dict[str, Any] = None,
                              anomaly_results: Dict[str, Any] = None,
                              temporal_patterns: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive pattern analysis report
        
        Args:
            clustering_results: Results from cluster analysis
            anomaly_results: Results from anomaly detection
            temporal_patterns: Results from temporal pattern analysis
            
        Returns:
            Comprehensive pattern report
        """
        try:
            logger.info("Generating comprehensive pattern report")
            
            report = {
                'analysis_timestamp': datetime.now().isoformat(),
                'executive_summary': {},
                'clustering_analysis': clustering_results or {},
                'anomaly_analysis': anomaly_results or {},
                'temporal_analysis': temporal_patterns or {},
                'insights': [],
                'recommendations': [],
                'alerts': []
            }
            
            # Generate executive summary
            summary = {
                'total_patterns_detected': 0,
                'anomalies_detected': 0,
                'temporal_patterns_found': 0,
                'data_quality_score': 0.0
            }
            
            # Count patterns from clustering
            if clustering_results and 'cluster_labels' in clustering_results:
                for method, labels in clustering_results['cluster_labels'].items():
                    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    summary['total_patterns_detected'] += n_clusters
            
            # Count anomalies
            if anomaly_results and 'anomaly_labels' in anomaly_results:
                for method, labels in anomaly_results['anomaly_labels'].items():
                    n_anomalies = np.sum(np.array(labels) == -1)
                    summary['anomalies_detected'] += n_anomalies
                
                # Average across methods
                summary['anomalies_detected'] = summary['anomalies_detected'] // len(anomaly_results['anomaly_labels'])
            
            # Count temporal patterns
            if temporal_patterns and 'patterns_by_column' in temporal_patterns:
                summary['temporal_patterns_found'] = len(temporal_patterns['patterns_by_column'])
            
            # Calculate data quality score
            quality_factors = []
            
            if clustering_results and 'metrics' in clustering_results:
                # Use average silhouette score as quality indicator
                silhouette_scores = []
                for method_metrics in clustering_results['metrics'].values():
                    if 'best_silhouette' in method_metrics:
                        silhouette_scores.append(method_metrics['best_silhouette'])
                    elif 'silhouette_score' in method_metrics:
                        silhouette_scores.append(method_metrics['silhouette_score'])
                
                if silhouette_scores:
                    quality_factors.append(np.mean(silhouette_scores))
            
            if quality_factors:
                summary['data_quality_score'] = float(np.mean(quality_factors))
            
            report['executive_summary'] = summary
            
            # Generate insights
            insights = self._generate_insights(clustering_results, anomaly_results, temporal_patterns)
            report['insights'] = insights
            
            # Generate recommendations
            recommendations = self._generate_recommendations(clustering_results, anomaly_results, temporal_patterns)
            report['recommendations'] = recommendations
            
            # Generate alerts
            alerts = self._generate_pattern_alerts(clustering_results, anomaly_results, temporal_patterns)
            report['alerts'] = alerts
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating pattern report: {e}")
            return {}
    
    def _generate_insights(self, clustering_results, anomaly_results, temporal_patterns) -> List[Dict[str, Any]]:
        """Generate insights from pattern analysis"""
        insights = []
        
        try:
            # Clustering insights
            if clustering_results and 'optimal_clusters' in clustering_results:
                for method, n_clusters in clustering_results['optimal_clusters'].items():
                    insights.append({
                        'type': 'clustering',
                        'method': method,
                        'insight': f'{method} identified {n_clusters} distinct patterns in the data',
                        'confidence': 'high' if n_clusters > 1 else 'medium'
                    })
            
            # Anomaly insights
            if anomaly_results and 'consensus_anomalies' in anomaly_results:
                n_consensus = len(anomaly_results['consensus_anomalies'])
                if n_consensus > 0:
                    insights.append({
                        'type': 'anomaly',
                        'insight': f'{n_consensus} data points were consistently identified as anomalies across multiple detection methods',
                        'confidence': 'high'
                    })
            
            # Temporal insights
            if temporal_patterns and 'patterns_by_column' in temporal_patterns:
                for column, patterns in temporal_patterns['patterns_by_column'].items():
                    if 'trend_analysis' in patterns:
                        trend = patterns['trend_analysis']
                        if trend.get('trend_strength') == 'strong':
                            insights.append({
                                'type': 'temporal',
                                'column': column,
                                'insight': f'{column} shows a strong {trend.get("trend_direction")} trend (R² = {trend.get("r_squared", 0):.3f})',
                                'confidence': 'high'
                            })
                    
                    if 'cycles' in patterns and patterns['cycles']:
                        cycle_length = patterns['cycles'].get('dominant_cycle_length')
                        if cycle_length:
                            insights.append({
                                'type': 'temporal',
                                'column': column,
                                'insight': f'{column} exhibits cyclical behavior with a dominant cycle of {cycle_length} periods',
                                'confidence': 'medium'
                            })
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    def _generate_recommendations(self, clustering_results, anomaly_results, temporal_patterns) -> List[str]:
        """Generate recommendations based on pattern analysis"""
        recommendations = []
        
        try:
            # Clustering recommendations
            if clustering_results and 'metrics' in clustering_results:
                best_method = None
                best_score = -1
                
                for method, metrics in clustering_results['metrics'].items():
                    score = metrics.get('best_silhouette', metrics.get('silhouette_score', 0))
                    if score > best_score:
                        best_score = score
                        best_method = method
                
                if best_method and best_score > 0.5:
                    recommendations.append(f"Use {best_method} clustering for pattern segmentation (silhouette score: {best_score:.3f})")
            
            # Anomaly recommendations
            if anomaly_results and 'summary' in anomaly_results:
                consensus_rate = anomaly_results['summary'].get('consensus_analysis', {}).get('consensus_rate', 0)
                if consensus_rate > 0.05:  # More than 5% anomalies
                    recommendations.append("High anomaly rate detected - investigate data quality and potential outliers")
                elif consensus_rate > 0:
                    recommendations.append("Monitor consensus anomalies for potential emerging patterns or data quality issues")
            
            # Temporal recommendations
            if temporal_patterns and 'patterns_by_column' in temporal_patterns:
                for column, patterns in temporal_patterns['patterns_by_column'].items():
                    if 'cycles' in patterns and patterns['cycles']:
                        cycle_length = patterns['cycles'].get('dominant_cycle_length')
                        recommendations.append(f"Consider {cycle_length}-period forecasting models for {column}")
                    
                    if 'trend_analysis' in patterns:
                        trend = patterns['trend_analysis']
                        if trend.get('trend_strength') == 'strong':
                            recommendations.append(f"Incorporate trend component in predictive models for {column}")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _generate_pattern_alerts(self, clustering_results, anomaly_results, temporal_patterns) -> List[Dict[str, Any]]:
        """Generate alerts based on pattern analysis"""
        alerts = []
        
        try:
            # High anomaly rate alert
            if anomaly_results and 'summary' in anomaly_results:
                for method, comparison in anomaly_results['summary'].get('methods_comparison', {}).items():
                    anomaly_rate = comparison.get('anomaly_rate', 0)
                    if anomaly_rate > 0.1:  # More than 10% anomalies
                        alerts.append({
                            'type': 'high_anomaly_rate',
                            'method': method,
                            'severity': 'high',
                            'rate': anomaly_rate,
                            'message': f'{method} detected {anomaly_rate:.1%} anomalies - investigate data quality'
                        })
            
            # Poor clustering quality alert
            if clustering_results and 'metrics' in clustering_results:
                for method, metrics in clustering_results['metrics'].items():
                    silhouette = metrics.get('best_silhouette', metrics.get('silhouette_score', 0))
                    if silhouette < 0.2:  # Poor clustering quality
                        alerts.append({
                            'type': 'poor_clustering_quality',
                            'method': method,
                            'severity': 'medium',
                            'score': silhouette,
                            'message': f'{method} clustering shows poor separation (silhouette: {silhouette:.3f})'
                        })
            
            # Temporal anomaly alerts
            if temporal_patterns and 'patterns_by_column' in temporal_patterns:
                for column, patterns in temporal_patterns['patterns_by_column'].items():
                    if 'anomalies' in patterns:
                        anomaly_rate = patterns['anomalies'].get('anomaly_rate', 0)
                        if anomaly_rate > 0.05:  # More than 5% temporal anomalies
                            alerts.append({
                                'type': 'temporal_anomalies',
                                'column': column,
                                'severity': 'medium',
                                'rate': anomaly_rate,
                                'message': f'{column} shows {anomaly_rate:.1%} temporal anomalies'
                            })
            
        except Exception as e:
            logger.error(f"Error generating pattern alerts: {e}")
        
        return alerts