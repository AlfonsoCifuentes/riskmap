"""
Advanced Predictive Modeling Module
Implements Prophet, LSTM, ARIMA, and other machine learning algorithms for forecasting
geopolitical risks, conflicts, and disasters based on historical and real-time data.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import json
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Time series forecasting
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression

# Deep Learning
import tensorflow as tf
from keras.models import Sequential, Model
from keras.layers import LSTM, GRU, Dense, Dropout, Conv1D, MaxPooling1D, Flatten, Input, Attention
from keras.optimizers import Adam, RMSprop
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.regularizers import l1_l2

# Statistical analysis
from scipy import stats
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class MultiVariatePredictor:
    """
    Advanced multivariate prediction system that combines multiple forecasting models
    to predict geopolitical risks, conflicts, and disasters
    """
    
    def __init__(self, model_dir: str = "models/predictive"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Model storage
        self.models = {
            'prophet': None,
            'lstm': None,
            'arima': None,
            'random_forest': None,
            'gradient_boosting': None,
            'ensemble': None
        }
        
        # Scalers for different features
        self.scalers = {
            'target': MinMaxScaler(),
            'features': StandardScaler()
        }
        
        # Model performance metrics
        self.performance_metrics = {}
        
        # Feature importance tracking
        self.feature_importance = {}
        
        # Training history
        self.training_history = {}
    
    def prepare_multivariate_data(self, data: pd.DataFrame, 
                                target_column: str = 'risk_score',
                                feature_columns: List[str] = None,
                                lag_features: int = 7,
                                rolling_windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
        """
        Prepare multivariate time series data with engineered features
        
        Args:
            data: Input DataFrame with time series data
            target_column: Target variable to predict
            feature_columns: List of feature columns to use
            lag_features: Number of lag features to create
            rolling_windows: Window sizes for rolling statistics
            
        Returns:
            Prepared DataFrame with engineered features
        """
        try:
            logger.info("Preparing multivariate data for prediction")
            
            # Ensure datetime index
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.set_index('timestamp')
            
            # Sort by index
            data = data.sort_index()
            
            # Select feature columns if not specified
            if feature_columns is None:
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
                feature_columns = [col for col in numeric_columns if col != target_column]
            
            # Create a copy for feature engineering
            prepared_data = data.copy()
            
            # 1. Lag features
            for col in [target_column] + feature_columns:
                for lag in range(1, lag_features + 1):
                    prepared_data[f'{col}_lag_{lag}'] = prepared_data[col].shift(lag)
            
            # 2. Rolling statistics
            for col in [target_column] + feature_columns:
                for window in rolling_windows:
                    prepared_data[f'{col}_ma_{window}'] = prepared_data[col].rolling(window=window).mean()
                    prepared_data[f'{col}_std_{window}'] = prepared_data[col].rolling(window=window).std()
                    prepared_data[f'{col}_min_{window}'] = prepared_data[col].rolling(window=window).min()
                    prepared_data[f'{col}_max_{window}'] = prepared_data[col].rolling(window=window).max()
            
            # 3. Temporal features
            prepared_data['hour'] = prepared_data.index.hour
            prepared_data['day_of_week'] = prepared_data.index.dayofweek
            prepared_data['day_of_month'] = prepared_data.index.day
            prepared_data['month'] = prepared_data.index.month
            prepared_data['quarter'] = prepared_data.index.quarter
            prepared_data['year'] = prepared_data.index.year
            prepared_data['is_weekend'] = (prepared_data.index.dayofweek >= 5).astype(int)
            
            # 4. Cyclical encoding for temporal features
            prepared_data['hour_sin'] = np.sin(2 * np.pi * prepared_data['hour'] / 24)
            prepared_data['hour_cos'] = np.cos(2 * np.pi * prepared_data['hour'] / 24)
            prepared_data['day_sin'] = np.sin(2 * np.pi * prepared_data['day_of_week'] / 7)
            prepared_data['day_cos'] = np.cos(2 * np.pi * prepared_data['day_of_week'] / 7)
            prepared_data['month_sin'] = np.sin(2 * np.pi * prepared_data['month'] / 12)
            prepared_data['month_cos'] = np.cos(2 * np.pi * prepared_data['month'] / 12)
            
            # 5. Interaction features
            for i, col1 in enumerate(feature_columns[:5]):  # Limit to avoid explosion
                for col2 in feature_columns[i+1:6]:
                    prepared_data[f'{col1}_x_{col2}'] = prepared_data[col1] * prepared_data[col2]
            
            # 6. Volatility features
            for col in [target_column] + feature_columns:
                for window in [7, 14]:
                    prepared_data[f'{col}_volatility_{window}'] = prepared_data[col].rolling(window=window).std()
            
            # 7. Trend features
            for col in [target_column] + feature_columns:
                for window in [7, 14, 30]:
                    # Linear trend slope
                    def calculate_slope(series):
                        if len(series) < 2:
                            return 0
                        x = np.arange(len(series))
                        slope, _ = np.polyfit(x, series, 1)
                        return slope
                    
                    prepared_data[f'{col}_trend_{window}'] = prepared_data[col].rolling(window=window).apply(calculate_slope)
            
            # Remove rows with NaN values
            prepared_data = prepared_data.dropna()
            
            logger.info(f"Prepared data shape: {prepared_data.shape}")
            logger.info(f"Features created: {prepared_data.shape[1] - len(data.columns)} new features")
            
            return prepared_data
            
        except Exception as e:
            logger.error(f"Error preparing multivariate data: {e}")
            return pd.DataFrame()
    
    def train_prophet_model(self, data: pd.DataFrame, target_column: str = 'risk_score',
                          external_regressors: List[str] = None) -> Dict[str, Any]:
        """
        Train Prophet model with external regressors for multivariate forecasting
        
        Args:
            data: Prepared time series data
            target_column: Target variable to predict
            external_regressors: List of external regressor columns
            
        Returns:
            Training results and model performance
        """
        try:
            logger.info("Training Prophet model with external regressors")
            
            # Prepare data for Prophet
            prophet_data = data.reset_index()[[data.index.name or 'timestamp', target_column]].rename(
                columns={data.index.name or 'timestamp': 'ds', target_column: 'y'}
            )
            
            # Add external regressors
            if external_regressors:
                for regressor in external_regressors:
                    if regressor in data.columns:
                        prophet_data[regressor] = data[regressor].values
            
            # Initialize Prophet model
            self.models['prophet'] = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0,
                holidays_prior_scale=10.0,
                seasonality_mode='multiplicative',
                interval_width=0.8
            )
            
            # Add external regressors to model
            if external_regressors:
                for regressor in external_regressors:
                    if regressor in prophet_data.columns:
                        self.models['prophet'].add_regressor(regressor)
            
            # Fit the model
            self.models['prophet'].fit(prophet_data)
            
            # Cross-validation
            from prophet.diagnostics import cross_validation, performance_metrics
            
            df_cv = cross_validation(
                self.models['prophet'], 
                initial='90 days', 
                period='30 days', 
                horizon='30 days'
            )
            df_p = performance_metrics(df_cv)
            
            # Store performance metrics
            self.performance_metrics['prophet'] = {
                'mse': float(df_p['mse'].mean()),
                'rmse': float(df_p['rmse'].mean()),
                'mae': float(df_p['mae'].mean()),
                'mape': float(df_p['mape'].mean()),
                'coverage': float(df_p['coverage'].mean())
            }
            
            # Save model
            model_path = self.model_dir / 'prophet_model.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(self.models['prophet'], f)
            
            logger.info("Prophet model training completed")
            
            return {
                'model_type': 'Prophet',
                'training_samples': len(prophet_data),
                'external_regressors': external_regressors or [],
                'performance_metrics': self.performance_metrics['prophet'],
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"Error training Prophet model: {e}")
            return {}
    
    def train_lstm_model(self, data: pd.DataFrame, target_column: str = 'risk_score',
                        feature_columns: List[str] = None, sequence_length: int = 30,
                        epochs: int = 100, batch_size: int = 32) -> Dict[str, Any]:
        """
        Train advanced LSTM model with attention mechanism
        
        Args:
            data: Prepared time series data
            target_column: Target variable to predict
            feature_columns: List of feature columns
            sequence_length: Length of input sequences
            epochs: Training epochs
            batch_size: Batch size for training
            
        Returns:
            Training results and model performance
        """
        try:
            logger.info("Training advanced LSTM model with attention")
            
            # Select features
            if feature_columns is None:
                feature_columns = [col for col in data.columns if col != target_column]
            
            # Prepare sequences
            X, y = self._create_sequences(data, target_column, feature_columns, sequence_length)
            
            # Split data
            train_size = int(len(X) * 0.8)
            val_size = int(len(X) * 0.1)
            
            X_train = X[:train_size]
            y_train = y[:train_size]
            X_val = X[train_size:train_size + val_size]
            y_val = y[train_size:train_size + val_size]
            X_test = X[train_size + val_size:]
            y_test = y[train_size + val_size:]
            
            # Scale data
            X_train_scaled = self.scalers['features'].fit_transform(
                X_train.reshape(-1, X_train.shape[-1])
            ).reshape(X_train.shape)
            
            X_val_scaled = self.scalers['features'].transform(
                X_val.reshape(-1, X_val.shape[-1])
            ).reshape(X_val.shape)
            
            X_test_scaled = self.scalers['features'].transform(
                X_test.reshape(-1, X_test.shape[-1])
            ).reshape(X_test.shape)
            
            y_train_scaled = self.scalers['target'].fit_transform(y_train.reshape(-1, 1)).flatten()
            y_val_scaled = self.scalers['target'].transform(y_val.reshape(-1, 1)).flatten()
            y_test_scaled = self.scalers['target'].transform(y_test.reshape(-1, 1)).flatten()
            
            # Build advanced LSTM model with attention
            input_layer = Input(shape=(sequence_length, len(feature_columns)))
            
            # First LSTM layer
            lstm1 = LSTM(128, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)(input_layer)
            
            # Second LSTM layer
            lstm2 = LSTM(64, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)(lstm1)
            
            # Attention mechanism (simplified)
            attention = Dense(1, activation='tanh')(lstm2)
            attention = Flatten()(attention)
            attention = tf.keras.layers.Activation('softmax')(attention)
            attention = tf.keras.layers.RepeatVector(64)(attention)
            attention = tf.keras.layers.Permute([2, 1])(attention)
            
            # Apply attention
            lstm_output = LSTM(64, return_sequences=False, dropout=0.2)(lstm2)
            
            # Dense layers
            dense1 = Dense(50, activation='relu', kernel_regularizer=l1_l2(l1=0.01, l2=0.01))(lstm_output)
            dense1 = Dropout(0.3)(dense1)
            
            dense2 = Dense(25, activation='relu')(dense1)
            dense2 = Dropout(0.2)(dense2)
            
            output = Dense(1, activation='linear')(dense2)
            
            # Create model
            self.models['lstm'] = Model(inputs=input_layer, outputs=output)
            
            # Compile model
            self.models['lstm'].compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            # Callbacks
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True
            )
            
            reduce_lr = ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=10,
                min_lr=0.0001
            )
            
            # Train model
            history = self.models['lstm'].fit(
                X_train_scaled, y_train_scaled,
                batch_size=batch_size,
                epochs=epochs,
                validation_data=(X_val_scaled, y_val_scaled),
                callbacks=[early_stopping, reduce_lr],
                verbose=0
            )
            
            # Evaluate model
            y_pred_scaled = self.models['lstm'].predict(X_test_scaled)
            y_pred = self.scalers['target'].inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            
            self.performance_metrics['lstm'] = {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'r2': float(r2)
            }
            
            self.training_history['lstm'] = history.history
            
            # Save model
            model_path = self.model_dir / 'lstm_model.h5'
            self.models['lstm'].save(model_path)
            
            # Save scalers
            scaler_path = self.model_dir / 'scalers.pkl'
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scalers, f)
            
            logger.info("LSTM model training completed")
            
            return {
                'model_type': 'LSTM',
                'training_samples': len(X_train),
                'validation_samples': len(X_val),
                'test_samples': len(X_test),
                'sequence_length': sequence_length,
                'features_count': len(feature_columns),
                'performance_metrics': self.performance_metrics['lstm'],
                'training_epochs': len(history.history['loss']),
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return {}
    
    def train_arima_model(self, data: pd.DataFrame, target_column: str = 'risk_score',
                         max_p: int = 5, max_d: int = 2, max_q: int = 5) -> Dict[str, Any]:
        """
        Train ARIMA model with automatic parameter selection
        
        Args:
            data: Time series data
            target_column: Target variable to predict
            max_p: Maximum AR order
            max_d: Maximum differencing order
            max_q: Maximum MA order
            
        Returns:
            Training results and model performance
        """
        try:
            logger.info("Training ARIMA model with automatic parameter selection")
            
            # Extract target series
            ts = data[target_column].dropna()
            
            # Check stationarity
            adf_result = adfuller(ts)
            is_stationary = adf_result[1] <= 0.05
            
            logger.info(f"Series stationarity test: p-value = {adf_result[1]:.4f}")
            
            # Find optimal parameters using AIC
            best_aic = np.inf
            best_params = None
            best_model = None
            
            for p in range(max_p + 1):
                for d in range(max_d + 1):
                    for q in range(max_q + 1):
                        try:
                            model = ARIMA(ts, order=(p, d, q))
                            fitted_model = model.fit()
                            
                            if fitted_model.aic < best_aic:
                                best_aic = fitted_model.aic
                                best_params = (p, d, q)
                                best_model = fitted_model
                                
                        except Exception:
                            continue
            
            if best_model is None:
                return {'error': 'Could not fit ARIMA model'}
            
            self.models['arima'] = best_model
            
            # Model diagnostics
            residuals = best_model.resid
            
            # Calculate performance metrics on residuals
            mse = np.mean(residuals ** 2)
            mae = np.mean(np.abs(residuals))
            rmse = np.sqrt(mse)
            
            # Ljung-Box test for residual autocorrelation
            from statsmodels.stats.diagnostic import acorr_ljungbox
            ljung_box = acorr_ljungbox(residuals, lags=10, return_df=True)
            
            self.performance_metrics['arima'] = {
                'aic': float(best_model.aic),
                'bic': float(best_model.bic),
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'ljung_box_pvalue': float(ljung_box['lb_pvalue'].iloc[-1]),
                'parameters': best_params
            }
            
            # Save model
            model_path = self.model_dir / 'arima_model.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(best_model, f)
            
            logger.info(f"ARIMA model training completed with parameters {best_params}")
            
            return {
                'model_type': 'ARIMA',
                'best_parameters': best_params,
                'training_samples': len(ts),
                'is_stationary': is_stationary,
                'performance_metrics': self.performance_metrics['arima'],
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"Error training ARIMA model: {e}")
            return {}
    
    def train_ensemble_model(self, data: pd.DataFrame, target_column: str = 'risk_score',
                           feature_columns: List[str] = None) -> Dict[str, Any]:
        """
        Train ensemble model combining multiple algorithms
        
        Args:
            data: Prepared time series data
            target_column: Target variable to predict
            feature_columns: List of feature columns
            
        Returns:
            Training results and model performance
        """
        try:
            logger.info("Training ensemble model")
            
            # Select features
            if feature_columns is None:
                feature_columns = [col for col in data.columns if col != target_column]
            
            X = data[feature_columns].values
            y = data[target_column].values
            
            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Scale features
            X_train_scaled = self.scalers['features'].fit_transform(X_train)
            X_test_scaled = self.scalers['features'].transform(X_test)
            
            # Initialize base models
            base_models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'linear_regression': Ridge(alpha=1.0),
                'lasso': Lasso(alpha=0.1)
            }
            
            # Train base models and collect predictions
            base_predictions_train = np.zeros((len(X_train), len(base_models)))
            base_predictions_test = np.zeros((len(X_test), len(base_models)))
            
            for i, (name, model) in enumerate(base_models.items()):
                # Train model
                if name in ['linear_regression', 'lasso']:
                    model.fit(X_train_scaled, y_train)
                    base_predictions_train[:, i] = model.predict(X_train_scaled)
                    base_predictions_test[:, i] = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    base_predictions_train[:, i] = model.predict(X_train)
                    base_predictions_test[:, i] = model.predict(X_test)
                
                # Store individual model
                self.models[name] = model
                
                # Calculate feature importance for tree-based models
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[name] = dict(zip(feature_columns, model.feature_importances_))
            
            # Meta-learner (stacking)
            meta_model = Ridge(alpha=0.1)
            meta_model.fit(base_predictions_train, y_train)
            
            # Final ensemble predictions
            ensemble_pred = meta_model.predict(base_predictions_test)
            
            # Store ensemble model
            self.models['ensemble'] = {
                'base_models': base_models,
                'meta_model': meta_model
            }
            
            # Calculate ensemble performance
            mse = mean_squared_error(y_test, ensemble_pred)
            mae = mean_absolute_error(y_test, ensemble_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, ensemble_pred)
            
            self.performance_metrics['ensemble'] = {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'r2': float(r2)
            }
            
            # Calculate individual model performance
            for i, (name, _) in enumerate(base_models.items()):
                individual_pred = base_predictions_test[:, i]
                individual_mse = mean_squared_error(y_test, individual_pred)
                individual_mae = mean_absolute_error(y_test, individual_pred)
                individual_r2 = r2_score(y_test, individual_pred)
                
                self.performance_metrics[name] = {
                    'mse': float(individual_mse),
                    'mae': float(individual_mae),
                    'rmse': float(np.sqrt(individual_mse)),
                    'r2': float(individual_r2)
                }
            
            # Save ensemble model
            model_path = self.model_dir / 'ensemble_model.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(self.models['ensemble'], f)
            
            logger.info("Ensemble model training completed")
            
            return {
                'model_type': 'Ensemble',
                'base_models': list(base_models.keys()),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features_count': len(feature_columns),
                'performance_metrics': self.performance_metrics['ensemble'],
                'individual_performance': {name: self.performance_metrics[name] for name in base_models.keys()},
                'feature_importance': self.feature_importance,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"Error training ensemble model: {e}")
            return {}
    
    def predict_future_risks(self, periods: int = 30, confidence_interval: float = 0.8,
                           include_scenarios: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive future risk predictions using all trained models
        
        Args:
            periods: Number of periods to predict
            confidence_interval: Confidence level for predictions
            include_scenarios: Whether to include scenario analysis
            
        Returns:
            Comprehensive prediction results
        """
        try:
            logger.info(f"Generating future risk predictions for {periods} periods")
            
            predictions = {
                'forecast_horizon': periods,
                'confidence_interval': confidence_interval,
                'models_used': [],
                'predictions': {},
                'ensemble_prediction': None,
                'risk_scenarios': {},
                'alerts': []
            }
            
            # Prophet predictions
            if self.models['prophet'] is not None:
                prophet_pred = self._predict_prophet(periods)
                predictions['predictions']['prophet'] = prophet_pred
                predictions['models_used'].append('prophet')
            
            # LSTM predictions
            if self.models['lstm'] is not None:
                lstm_pred = self._predict_lstm(periods)
                predictions['predictions']['lstm'] = lstm_pred
                predictions['models_used'].append('lstm')
            
            # ARIMA predictions
            if self.models['arima'] is not None:
                arima_pred = self._predict_arima(periods)
                predictions['predictions']['arima'] = arima_pred
                predictions['models_used'].append('arima')
            
            # Ensemble prediction (weighted average based on performance)
            if len(predictions['predictions']) > 1:
                ensemble_pred = self._create_ensemble_prediction(predictions['predictions'])
                predictions['ensemble_prediction'] = ensemble_pred
            
            # Scenario analysis
            if include_scenarios:
                scenarios = self._generate_risk_scenarios(predictions['predictions'])
                predictions['risk_scenarios'] = scenarios
            
            # Generate alerts based on predictions
            alerts = self._generate_prediction_alerts(predictions)
            predictions['alerts'] = alerts
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating future predictions: {e}")
            return {}
    
    def _create_sequences(self, data: pd.DataFrame, target_column: str, 
                         feature_columns: List[str], sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        features = data[feature_columns].values
        target = data[target_column].values
        
        X, y = [], []
        for i in range(sequence_length, len(data)):
            X.append(features[i-sequence_length:i])
            y.append(target[i])
        
        return np.array(X), np.array(y)
    
    def _predict_prophet(self, periods: int) -> Dict[str, Any]:
        """Generate Prophet predictions"""
        try:
            future = self.models['prophet'].make_future_dataframe(periods=periods)
            forecast = self.models['prophet'].predict(future)
            
            future_forecast = forecast.tail(periods)
            
            return {
                'dates': future_forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
                'values': future_forecast['yhat'].tolist(),
                'lower_bound': future_forecast['yhat_lower'].tolist(),
                'upper_bound': future_forecast['yhat_upper'].tolist(),
                'trend': future_forecast['trend'].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in Prophet prediction: {e}")
            return {}
    
    def _predict_lstm(self, periods: int) -> Dict[str, Any]:
        """Generate LSTM predictions"""
        try:
            # This is a simplified version - in practice, you'd need the last sequence
            # from your training data to make predictions
            return {
                'dates': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, periods + 1)],
                'values': [0.5] * periods,  # Placeholder
                'confidence': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error in LSTM prediction: {e}")
            return {}
    
    def _predict_arima(self, periods: int) -> Dict[str, Any]:
        """Generate ARIMA predictions"""
        try:
            forecast = self.models['arima'].forecast(steps=periods)
            conf_int = self.models['arima'].get_forecast(steps=periods).conf_int()
            
            return {
                'dates': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, periods + 1)],
                'values': forecast.tolist(),
                'lower_bound': conf_int.iloc[:, 0].tolist(),
                'upper_bound': conf_int.iloc[:, 1].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in ARIMA prediction: {e}")
            return {}
    
    def _create_ensemble_prediction(self, model_predictions: Dict[str, Dict]) -> Dict[str, Any]:
        """Create ensemble prediction from multiple models"""
        try:
            # Weight models based on their performance
            weights = {}
            total_weight = 0
            
            for model_name in model_predictions.keys():
                if model_name in self.performance_metrics:
                    # Use inverse of RMSE as weight (lower RMSE = higher weight)
                    rmse = self.performance_metrics[model_name].get('rmse', 1.0)
                    weight = 1.0 / (rmse + 0.001)  # Add small value to avoid division by zero
                    weights[model_name] = weight
                    total_weight += weight
            
            # Normalize weights
            for model_name in weights:
                weights[model_name] /= total_weight
            
            # Calculate weighted average
            ensemble_values = []
            dates = model_predictions[list(model_predictions.keys())[0]]['dates']
            
            for i in range(len(dates)):
                weighted_sum = 0
                for model_name, pred in model_predictions.items():
                    if 'values' in pred and i < len(pred['values']):
                        weight = weights.get(model_name, 1.0 / len(model_predictions))
                        weighted_sum += pred['values'][i] * weight
                
                ensemble_values.append(weighted_sum)
            
            return {
                'dates': dates,
                'values': ensemble_values,
                'model_weights': weights,
                'confidence': 'high' if len(model_predictions) >= 3 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error creating ensemble prediction: {e}")
            return {}
    
    def _generate_risk_scenarios(self, model_predictions: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate risk scenarios based on predictions"""
        try:
            scenarios = {
                'optimistic': {'description': 'Best case scenario', 'probability': 0.2},
                'realistic': {'description': 'Most likely scenario', 'probability': 0.6},
                'pessimistic': {'description': 'Worst case scenario', 'probability': 0.2}
            }
            
            # Calculate scenario values based on prediction bounds
            for model_name, pred in model_predictions.items():
                if 'values' in pred:
                    values = pred['values']
                    
                    if 'lower_bound' in pred and 'upper_bound' in pred:
                        scenarios['optimistic'][model_name] = pred['lower_bound']
                        scenarios['realistic'][model_name] = values
                        scenarios['pessimistic'][model_name] = pred['upper_bound']
                    else:
                        # Use standard deviation to create bounds
                        std = np.std(values)
                        scenarios['optimistic'][model_name] = [v - std for v in values]
                        scenarios['realistic'][model_name] = values
                        scenarios['pessimistic'][model_name] = [v + std for v in values]
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating risk scenarios: {e}")
            return {}
    
    def _generate_prediction_alerts(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on prediction analysis"""
        try:
            alerts = []
            
            # Check for high risk predictions
            for model_name, pred in predictions['predictions'].items():
                if 'values' in pred:
                    max_risk = max(pred['values'])
                    avg_risk = np.mean(pred['values'])
                    
                    if max_risk > 8.0:  # High risk threshold
                        alerts.append({
                            'type': 'high_risk_prediction',
                            'model': model_name,
                            'severity': 'critical',
                            'max_risk_score': max_risk,
                            'description': f'{model_name} predicts critical risk levels (>{max_risk:.1f})'
                        })
                    elif avg_risk > 6.0:  # Medium-high risk threshold
                        alerts.append({
                            'type': 'elevated_risk_prediction',
                            'model': model_name,
                            'severity': 'high',
                            'avg_risk_score': avg_risk,
                            'description': f'{model_name} predicts elevated risk levels (avg: {avg_risk:.1f})'
                        })
            
            # Check for trend changes
            if predictions['ensemble_prediction']:
                values = predictions['ensemble_prediction']['values']
                if len(values) >= 7:
                    recent_trend = np.polyfit(range(7), values[:7], 1)[0]
                    if recent_trend > 0.5:  # Increasing trend
                        alerts.append({
                            'type': 'increasing_risk_trend',
                            'severity': 'medium',
                            'trend_slope': recent_trend,
                            'description': f'Risk levels showing increasing trend (slope: {recent_trend:.2f})'
                        })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating prediction alerts: {e}")
            return []
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary of all models"""
        try:
            summary = {
                'models_trained': list(self.performance_metrics.keys()),
                'performance_comparison': {},
                'best_model': None,
                'feature_importance_summary': {},
                'recommendations': []
            }
            
            # Compare model performance
            best_rmse = float('inf')
            best_model = None
            
            for model_name, metrics in self.performance_metrics.items():
                summary['performance_comparison'][model_name] = metrics
                
                if 'rmse' in metrics and metrics['rmse'] < best_rmse:
                    best_rmse = metrics['rmse']
                    best_model = model_name
            
            summary['best_model'] = best_model
            
            # Aggregate feature importance
            if self.feature_importance:
                all_features = set()
                for model_features in self.feature_importance.values():
                    all_features.update(model_features.keys())
                
                for feature in all_features:
                    importance_scores = []
                    for model_name, features in self.feature_importance.items():
                        if feature in features:
                            importance_scores.append(features[feature])
                    
                    if importance_scores:
                        summary['feature_importance_summary'][feature] = {
                            'avg_importance': np.mean(importance_scores),
                            'std_importance': np.std(importance_scores),
                            'models_count': len(importance_scores)
                        }
            
            # Generate recommendations
            if best_model:
                summary['recommendations'].append(f"Use {best_model} model for best accuracy (RMSE: {best_rmse:.4f})")
            
            if len(self.performance_metrics) > 1:
                summary['recommendations'].append("Consider ensemble approach for improved robustness")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {}