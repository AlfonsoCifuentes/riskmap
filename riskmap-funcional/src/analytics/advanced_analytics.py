"""
Advanced Analytics Module for Conflict Prediction and Trend Analysis
Implements LSTM, Prophet, clustering, and anomaly detection for predicting
conflict evolution and identifying patterns in geopolitical data.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import json

# Time series and forecasting
from prophet import Prophet
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# Deep learning
import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.optimizers import Adam

# Statistical analysis
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class ConflictTrendPredictor:
    """
    Advanced trend prediction using LSTM and Prophet models
    for forecasting conflict evolution and tension levels
    """
    
    def __init__(self):
        self.lstm_model = None
        self.prophet_model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        self.feature_columns = []
        
    def prepare_time_series_data(self, data: pd.DataFrame, target_column: str = 'risk_score') -> pd.DataFrame:
        """
        Prepare time series data for forecasting models
        
        Args:
            data: DataFrame with temporal conflict data
            target_column: Column to predict
            
        Returns:
            Prepared DataFrame for time series analysis
        """
        try:
            # Ensure datetime index
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.set_index('timestamp')
            
            # Resample to daily frequency and fill missing values
            daily_data = data.resample('D').agg({
                target_column: 'mean',
                'conflict_intensity': 'mean',
                'humanitarian_impact': 'mean',
                'actor_count': 'sum',
                'event_count': 'sum'
            }).fillna(method='forward').fillna(0)
            
            # Add temporal features
            daily_data['day_of_week'] = daily_data.index.dayofweek
            daily_data['month'] = daily_data.index.month
            daily_data['quarter'] = daily_data.index.quarter
            
            # Add rolling statistics
            for window in [7, 14, 30]:
                daily_data[f'{target_column}_ma_{window}'] = daily_data[target_column].rolling(window=window).mean()
                daily_data[f'{target_column}_std_{window}'] = daily_data[target_column].rolling(window=window).std()
            
            # Add lag features
            for lag in [1, 3, 7]:
                daily_data[f'{target_column}_lag_{lag}'] = daily_data[target_column].shift(lag)
            
            # Remove rows with NaN values
            daily_data = daily_data.dropna()
            
            self.feature_columns = [col for col in daily_data.columns if col != target_column]
            
            return daily_data
            
        except Exception as e:
            logger.error(f"Error preparing time series data: {e}")
            return pd.DataFrame()
    
    def train_lstm_model(self, data: pd.DataFrame, target_column: str = 'risk_score', 
                        sequence_length: int = 30, epochs: int = 50) -> Dict[str, Any]:
        """
        Train LSTM model for conflict prediction
        
        Args:
            data: Prepared time series data
            target_column: Target variable to predict
            sequence_length: Length of input sequences
            epochs: Training epochs
            
        Returns:
            Training results and model metrics
        """
        try:
            logger.info("Training LSTM model for conflict prediction...")
            
            # Prepare sequences
            X, y = self._create_sequences(data, target_column, sequence_length)
            
            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Scale data
            X_train_scaled = self.scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
            X_test_scaled = self.scaler.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)
            
            # Build LSTM model
            self.lstm_model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(sequence_length, len(self.feature_columns))),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            self.lstm_model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
            
            # Train model
            history = self.lstm_model.fit(
                X_train_scaled, y_train,
                batch_size=32,
                epochs=epochs,
                validation_data=(X_test_scaled, y_test),
                verbose=0
            )
            
            # Evaluate model
            train_loss = self.lstm_model.evaluate(X_train_scaled, y_train, verbose=0)
            test_loss = self.lstm_model.evaluate(X_test_scaled, y_test, verbose=0)
            
            # Make predictions for evaluation
            y_pred = self.lstm_model.predict(X_test_scaled)
            
            # Calculate metrics
            mse = np.mean((y_test - y_pred.flatten()) ** 2)
            mae = np.mean(np.abs(y_test - y_pred.flatten()))
            rmse = np.sqrt(mse)
            
            self.is_trained = True
            
            return {
                'model_type': 'LSTM',
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'train_loss': train_loss[0],
                'test_loss': test_loss[0],
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'training_history': {
                    'loss': history.history['loss'],
                    'val_loss': history.history['val_loss']
                }
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return {}
    
    def train_prophet_model(self, data: pd.DataFrame, target_column: str = 'risk_score') -> Dict[str, Any]:
        """
        Train Prophet model for conflict forecasting
        
        Args:
            data: Time series data
            target_column: Target variable
            
        Returns:
            Training results
        """
        try:
            logger.info("Training Prophet model for conflict forecasting...")
            
            # Prepare data for Prophet
            prophet_data = data.reset_index()[['timestamp', target_column]].rename(
                columns={'timestamp': 'ds', target_column: 'y'}
            )
            
            # Initialize and train Prophet model
            self.prophet_model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            
            self.prophet_model.fit(prophet_data)
            
            # Cross-validation
            from prophet.diagnostics import cross_validation, performance_metrics
            
            df_cv = cross_validation(self.prophet_model, initial='30 days', period='7 days', horizon='14 days')
            df_p = performance_metrics(df_cv)
            
            return {
                'model_type': 'Prophet',
                'training_samples': len(prophet_data),
                'cross_validation_metrics': {
                    'mse': float(df_p['mse'].mean()),
                    'rmse': float(df_p['rmse'].mean()),
                    'mae': float(df_p['mae'].mean()),
                    'mape': float(df_p['mape'].mean())
                }
            }
            
        except Exception as e:
            logger.error(f"Error training Prophet model: {e}")
            return {}
    
    def predict_future_trends(self, periods: int = 30, confidence_interval: float = 0.8) -> Dict[str, Any]:
        """
        Predict future conflict trends using trained models
        
        Args:
            periods: Number of days to predict
            confidence_interval: Confidence level for predictions
            
        Returns:
            Future predictions with confidence intervals
        """
        try:
            if not self.is_trained or self.prophet_model is None:
                return {'error': 'Models not trained'}
            
            predictions = {
                'forecast_period': periods,
                'confidence_interval': confidence_interval,
                'predictions': {}
            }
            
            # Prophet predictions
            future = self.prophet_model.make_future_dataframe(periods=periods)
            prophet_forecast = self.prophet_model.predict(future)
            
            # Extract future predictions
            future_predictions = prophet_forecast.tail(periods)
            
            predictions['predictions']['prophet'] = {
                'dates': future_predictions['ds'].dt.strftime('%Y-%m-%d').tolist(),
                'values': future_predictions['yhat'].tolist(),
                'lower_bound': future_predictions['yhat_lower'].tolist(),
                'upper_bound': future_predictions['yhat_upper'].tolist(),
                'trend': future_predictions['trend'].tolist()
            }
            
            # Analyze trend direction
            trend_slope = np.polyfit(range(len(future_predictions)), future_predictions['yhat'], 1)[0]
            
            if trend_slope > 0.1:
                trend_direction = 'escalating'
            elif trend_slope < -0.1:
                trend_direction = 'de-escalating'
            else:
                trend_direction = 'stable'
            
            predictions['trend_analysis'] = {
                'direction': trend_direction,
                'slope': float(trend_slope),
                'confidence': 'high' if abs(trend_slope) > 0.2 else 'medium'
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting future trends: {e}")
            return {}
    
    def _create_sequences(self, data: pd.DataFrame, target_column: str, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        features = data[self.feature_columns].values
        target = data[target_column].values
        
        X, y = [], []
        for i in range(sequence_length, len(data)):
            X.append(features[i-sequence_length:i])
            y.append(target[i])
        
        return np.array(X), np.array(y)


class AnomalyDetector:
    """
    Advanced anomaly detection for identifying unusual patterns
    in conflict data using multiple algorithms
    """
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.clustering_model = None
        self.pca_model = PCA(n_components=0.95)
        self.is_fitted = False
        
    def detect_anomalies(self, data: pd.DataFrame, method: str = 'isolation_forest') -> Dict[str, Any]:
        """
        Detect anomalies in conflict data
        
        Args:
            data: Input data for anomaly detection
            method: Detection method ('isolation_forest', 'clustering', 'statistical')
            
        Returns:
            Anomaly detection results
        """
        try:
            logger.info(f"Detecting anomalies using {method} method...")
            
            # Prepare data
            numeric_data = data.select_dtypes(include=[np.number]).fillna(0)
            
            if len(numeric_data) == 0:
                return {'error': 'No numeric data available for anomaly detection'}
            
            # Apply PCA for dimensionality reduction
            data_pca = self.pca_model.fit_transform(numeric_data)
            
            anomalies = {
                'method': method,
                'total_samples': len(data),
                'anomalies': [],
                'anomaly_scores': [],
                'summary': {}
            }
            
            if method == 'isolation_forest':
                anomalies.update(self._isolation_forest_detection(data, data_pca))
            elif method == 'clustering':
                anomalies.update(self._clustering_based_detection(data, data_pca))
            elif method == 'statistical':
                anomalies.update(self._statistical_anomaly_detection(data, numeric_data))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {}
    
    def _isolation_forest_detection(self, original_data: pd.DataFrame, processed_data: np.ndarray) -> Dict[str, Any]:
        """Isolation Forest based anomaly detection"""
        try:
            # Fit and predict
            anomaly_labels = self.isolation_forest.fit_predict(processed_data)
            anomaly_scores = self.isolation_forest.score_samples(processed_data)
            
            # Identify anomalies
            anomaly_indices = np.where(anomaly_labels == -1)[0]
            
            anomalies = []
            for idx in anomaly_indices:
                anomaly_info = {
                    'index': int(idx),
                    'anomaly_score': float(anomaly_scores[idx]),
                    'data': original_data.iloc[idx].to_dict()
                }
                if 'timestamp' in original_data.columns:
                    anomaly_info['timestamp'] = str(original_data.iloc[idx]['timestamp'])
                
                anomalies.append(anomaly_info)
            
            return {
                'anomalies': anomalies,
                'anomaly_scores': anomaly_scores.tolist(),
                'summary': {
                    'total_anomalies': len(anomalies),
                    'anomaly_rate': len(anomalies) / len(original_data),
                    'mean_anomaly_score': float(np.mean(anomaly_scores[anomaly_indices])) if len(anomaly_indices) > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in isolation forest detection: {e}")
            return {}
    
    def _clustering_based_detection(self, original_data: pd.DataFrame, processed_data: np.ndarray) -> Dict[str, Any]:
        """Clustering-based anomaly detection using DBSCAN"""
        try:
            # Apply DBSCAN clustering
            clustering = DBSCAN(eps=0.5, min_samples=5).fit(processed_data)
            labels = clustering.labels_
            
            # Points labeled as -1 are considered anomalies
            anomaly_indices = np.where(labels == -1)[0]
            
            anomalies = []
            for idx in anomaly_indices:
                anomaly_info = {
                    'index': int(idx),
                    'cluster_label': int(labels[idx]),
                    'data': original_data.iloc[idx].to_dict()
                }
                if 'timestamp' in original_data.columns:
                    anomaly_info['timestamp'] = str(original_data.iloc[idx]['timestamp'])
                
                anomalies.append(anomaly_info)
            
            # Calculate cluster statistics
            unique_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            return {
                'anomalies': anomalies,
                'summary': {
                    'total_anomalies': len(anomalies),
                    'anomaly_rate': len(anomalies) / len(original_data),
                    'clusters_found': unique_clusters,
                    'noise_points': len(anomaly_indices)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in clustering-based detection: {e}")
            return {}
    
    def _statistical_anomaly_detection(self, original_data: pd.DataFrame, numeric_data: pd.DataFrame) -> Dict[str, Any]:
        """Statistical anomaly detection using Z-score and IQR methods"""
        try:
            anomalies = []
            
            for column in numeric_data.columns:
                values = numeric_data[column]
                
                # Z-score method
                z_scores = np.abs(stats.zscore(values))
                z_anomalies = np.where(z_scores > 3)[0]
                
                # IQR method
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                iqr_anomalies = np.where((values < lower_bound) | (values > upper_bound))[0]
                
                # Combine anomalies
                combined_anomalies = np.unique(np.concatenate([z_anomalies, iqr_anomalies]))
                
                for idx in combined_anomalies:
                    anomaly_info = {
                        'index': int(idx),
                        'column': column,
                        'value': float(values.iloc[idx]),
                        'z_score': float(z_scores[idx]),
                        'method': 'statistical',
                        'data': original_data.iloc[idx].to_dict()
                    }
                    if 'timestamp' in original_data.columns:
                        anomaly_info['timestamp'] = str(original_data.iloc[idx]['timestamp'])
                    
                    anomalies.append(anomaly_info)
            
            return {
                'anomalies': anomalies,
                'summary': {
                    'total_anomalies': len(anomalies),
                    'anomaly_rate': len(anomalies) / len(original_data),
                    'columns_analyzed': list(numeric_data.columns)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in statistical anomaly detection: {e}")
            return {}


class PatternAnalyzer:
    """
    Advanced pattern analysis for identifying recurring patterns
    and cycles in conflict data
    """
    
    def __init__(self):
        self.kmeans_model = None
        self.pattern_library = {}
        
    def identify_patterns(self, data: pd.DataFrame, pattern_type: str = 'temporal') -> Dict[str, Any]:
        """
        Identify patterns in conflict data
        
        Args:
            data: Input data for pattern analysis
            pattern_type: Type of patterns to identify ('temporal', 'spatial', 'actor')
            
        Returns:
            Identified patterns and their characteristics
        """
        try:
            logger.info(f"Identifying {pattern_type} patterns...")
            
            patterns = {
                'pattern_type': pattern_type,
                'patterns_found': [],
                'pattern_strength': {},
                'recommendations': []
            }
            
            if pattern_type == 'temporal':
                patterns.update(self._analyze_temporal_patterns(data))
            elif pattern_type == 'spatial':
                patterns.update(self._analyze_spatial_patterns(data))
            elif pattern_type == 'actor':
                patterns.update(self._analyze_actor_patterns(data))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            return {}
    
    def _analyze_temporal_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal patterns in conflict data"""
        try:
            if 'timestamp' not in data.columns:
                return {'error': 'No timestamp column found'}
            
            # Convert timestamp to datetime
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.set_index('timestamp')
            
            patterns = []
            
            # Daily patterns
            if 'risk_score' in data.columns:
                daily_avg = data.groupby(data.index.hour)['risk_score'].mean()
                peak_hours = daily_avg.nlargest(3).index.tolist()
                patterns.append({
                    'type': 'daily_cycle',
                    'peak_hours': peak_hours,
                    'pattern_strength': float(daily_avg.std())
                })
            
            # Weekly patterns
            weekly_avg = data.groupby(data.index.dayofweek)['risk_score'].mean() if 'risk_score' in data.columns else None
            if weekly_avg is not None:
                peak_days = weekly_avg.nlargest(2).index.tolist()
                patterns.append({
                    'type': 'weekly_cycle',
                    'peak_days': peak_days,
                    'pattern_strength': float(weekly_avg.std())
                })
            
            # Seasonal patterns
            if len(data) > 90:  # Need at least 3 months of data
                monthly_avg = data.groupby(data.index.month)['risk_score'].mean() if 'risk_score' in data.columns else None
                if monthly_avg is not None:
                    peak_months = monthly_avg.nlargest(3).index.tolist()
                    patterns.append({
                        'type': 'seasonal_cycle',
                        'peak_months': peak_months,
                        'pattern_strength': float(monthly_avg.std())
                    })
            
            return {'patterns_found': patterns}
            
        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {e}")
            return {}
    
    def _analyze_spatial_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spatial patterns in conflict data"""
        try:
            if 'latitude' not in data.columns or 'longitude' not in data.columns:
                return {'error': 'No spatial coordinates found'}
            
            # Extract coordinates
            coordinates = data[['latitude', 'longitude']].dropna()
            
            if len(coordinates) < 10:
                return {'error': 'Insufficient spatial data'}
            
            # Apply clustering to find spatial patterns
            kmeans = KMeans(n_clusters=min(5, len(coordinates)//2), random_state=42)
            clusters = kmeans.fit_predict(coordinates)
            
            patterns = []
            
            # Analyze each cluster
            for cluster_id in range(kmeans.n_clusters):
                cluster_points = coordinates[clusters == cluster_id]
                cluster_center = kmeans.cluster_centers_[cluster_id]
                
                patterns.append({
                    'type': 'spatial_cluster',
                    'cluster_id': int(cluster_id),
                    'center_lat': float(cluster_center[0]),
                    'center_lon': float(cluster_center[1]),
                    'point_count': len(cluster_points),
                    'radius_km': float(self._calculate_cluster_radius(cluster_points, cluster_center))
                })
            
            return {'patterns_found': patterns}
            
        except Exception as e:
            logger.error(f"Error analyzing spatial patterns: {e}")
            return {}
    
    def _analyze_actor_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in actor involvement"""
        try:
            if 'actors' not in data.columns:
                return {'error': 'No actor data found'}
            
            patterns = []
            
            # Actor frequency analysis
            all_actors = []
            for actors_str in data['actors'].dropna():
                if isinstance(actors_str, str):
                    actors = actors_str.split(',')
                    all_actors.extend([actor.strip() for actor in actors])
            
            if all_actors:
                from collections import Counter
                actor_counts = Counter(all_actors)
                top_actors = actor_counts.most_common(10)
                
                patterns.append({
                    'type': 'actor_frequency',
                    'top_actors': [{'name': actor, 'count': count} for actor, count in top_actors]
                })
            
            # Co-occurrence patterns
            actor_pairs = []
            for actors_str in data['actors'].dropna():
                if isinstance(actors_str, str):
                    actors = [actor.strip() for actor in actors_str.split(',')]
                    if len(actors) > 1:
                        for i in range(len(actors)):
                            for j in range(i+1, len(actors)):
                                actor_pairs.append(tuple(sorted([actors[i], actors[j]])))
            
            if actor_pairs:
                pair_counts = Counter(actor_pairs)
                top_pairs = pair_counts.most_common(5)
                
                patterns.append({
                    'type': 'actor_cooccurrence',
                    'top_pairs': [{'actors': list(pair), 'count': count} for pair, count in top_pairs]
                })
            
            return {'patterns_found': patterns}
            
        except Exception as e:
            logger.error(f"Error analyzing actor patterns: {e}")
            return {}
    
    def _calculate_cluster_radius(self, points: pd.DataFrame, center: np.ndarray) -> float:
        """Calculate the radius of a spatial cluster in kilometers"""
        from geopy.distance import geodesic
        
        max_distance = 0
        center_point = (center[0], center[1])
        
        for _, point in points.iterrows():
            point_coords = (point['latitude'], point['longitude'])
            distance = geodesic(center_point, point_coords).kilometers
            max_distance = max(max_distance, distance)
        
        return max_distance


class SentimentTrendAnalyzer:
    """
    Analyze sentiment trends across different regions and time periods
    """
    
    def __init__(self):
        self.sentiment_history = {}
        
    def analyze_sentiment_trends(self, data: pd.DataFrame, groupby_column: str = 'region') -> Dict[str, Any]:
        """
        Analyze sentiment trends across different dimensions
        
        Args:
            data: Data with sentiment scores
            groupby_column: Column to group analysis by
            
        Returns:
            Sentiment trend analysis results
        """
        try:
            if 'sentiment_score' not in data.columns:
                return {'error': 'No sentiment score data found'}
            
            # Ensure timestamp is datetime
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            trends = {
                'analysis_type': f'sentiment_by_{groupby_column}',
                'trends': {},
                'overall_sentiment': {},
                'alerts': []
            }
            
            # Overall sentiment statistics
            trends['overall_sentiment'] = {
                'mean_sentiment': float(data['sentiment_score'].mean()),
                'sentiment_volatility': float(data['sentiment_score'].std()),
                'positive_ratio': float((data['sentiment_score'] > 0).mean()),
                'negative_ratio': float((data['sentiment_score'] < 0).mean())
            }
            
            # Group-wise analysis
            if groupby_column in data.columns:
                for group_name, group_data in data.groupby(groupby_column):
                    group_trends = self._analyze_group_sentiment(group_data)
                    trends['trends'][str(group_name)] = group_trends
                    
                    # Check for sentiment alerts
                    if group_trends['recent_change'] < -0.3:
                        trends['alerts'].append({
                            'type': 'negative_sentiment_spike',
                            'group': str(group_name),
                            'severity': 'high',
                            'change': group_trends['recent_change']
                        })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment trends: {e}")
            return {}
    
    def _analyze_group_sentiment(self, group_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sentiment for a specific group"""
        try:
            sentiment_scores = group_data['sentiment_score']
            
            # Basic statistics
            analysis = {
                'mean_sentiment': float(sentiment_scores.mean()),
                'median_sentiment': float(sentiment_scores.median()),
                'sentiment_range': float(sentiment_scores.max() - sentiment_scores.min()),
                'volatility': float(sentiment_scores.std()),
                'sample_count': len(sentiment_scores)
            }
            
            # Trend analysis if timestamp available
            if 'timestamp' in group_data.columns and len(group_data) > 1:
                # Sort by timestamp
                group_data_sorted = group_data.sort_values('timestamp')
                
                # Calculate recent change (last 7 days vs previous period)
                if len(group_data_sorted) >= 14:
                    recent_data = group_data_sorted.tail(7)
                    previous_data = group_data_sorted.iloc[-14:-7]
                    
                    recent_mean = recent_data['sentiment_score'].mean()
                    previous_mean = previous_data['sentiment_score'].mean()
                    
                    analysis['recent_change'] = float(recent_mean - previous_mean)
                    analysis['trend_direction'] = 'improving' if analysis['recent_change'] > 0 else 'deteriorating'
                else:
                    analysis['recent_change'] = 0
                    analysis['trend_direction'] = 'stable'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing group sentiment: {e}")
            return {}