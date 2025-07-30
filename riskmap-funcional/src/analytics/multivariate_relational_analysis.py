"""
Multivariate Relational Analysis Module
Advanced analysis system for identifying, visualizing, and predicting the influence and correlation
between energy sources, oil prices/production, climate variables, public policies, disease outbreaks,
resource availability, and their impact on geopolitical conflict risk.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import json
from pathlib import Path
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Statistical and ML libraries
from scipy import stats
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA, FastICA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression

# Deep learning
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, Attention
from tensorflow.keras.optimizers import Adam

# Time series analysis
from statsmodels.tsa.stattools import granger_causality
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.stats.stattools import durbin_watson
import networkx as nx

logger = logging.getLogger(__name__)

class DataCategory(Enum):
    """Categories of data sources for multivariate analysis"""
    ENERGY = "energy"
    CLIMATE = "climate"
    POLITICAL = "political"
    HEALTH = "health"
    RESOURCES = "resources"
    CONFLICTS = "conflicts"

@dataclass
class VariableMetadata:
    """Metadata for analysis variables"""
    name: str
    category: DataCategory
    source: str
    unit: str
    description: str
    update_frequency: str
    lag_effect_days: int = 0
    transformation: str = "none"  # log, diff, pct_change, etc.

class MultivariateDataIntegrator:
    """
    Integrates and normalizes data from multiple sources for relational analysis
    """
    
    def __init__(self, data_dir: str = "datasets/multivariate"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data source configurations
        self.source_configs = self._initialize_source_configs()
        
        # Variable metadata registry
        self.variable_registry = self._initialize_variable_registry()
        
        # Cached data
        self.integrated_data = pd.DataFrame()
        self.metadata = {}
        
    def _initialize_source_configs(self) -> Dict[str, Dict]:
        """Initialize configuration for all data sources"""
        return {
            # Energy Data Sources
            "eia_oil": {
                "url": "https://api.eia.gov/v2/petroleum/pri/spt/data/",
                "api_key_required": True,
                "category": DataCategory.ENERGY,
                "update_frequency": "daily",
                "variables": ["crude_oil_price", "gasoline_price", "heating_oil_price"]
            },
            "eia_production": {
                "url": "https://api.eia.gov/v2/petroleum/crd/crpdn/data/",
                "api_key_required": True,
                "category": DataCategory.ENERGY,
                "update_frequency": "monthly",
                "variables": ["crude_oil_production", "refinery_capacity"]
            },
            "world_bank_energy": {
                "url": "https://api.worldbank.org/v2/country/all/indicator/",
                "category": DataCategory.ENERGY,
                "update_frequency": "annual",
                "indicators": [
                    "EG.USE.PCAP.KG.OE",  # Energy use per capita
                    "EG.ELC.ACCS.ZS",     # Access to electricity
                    "EG.FEC.RNEW.ZS",     # Renewable energy consumption
                    "EG.EGY.PRIM.PP.KD"   # Energy intensity
                ]
            },
            
            # Climate Data Sources
            "noaa_climate": {
                "url": "https://www.ncei.noaa.gov/data/global-summary-of-the-month/access/",
                "category": DataCategory.CLIMATE,
                "update_frequency": "monthly",
                "variables": ["temperature", "precipitation", "extreme_events"]
            },
            "nasa_earthdata": {
                "url": "https://earthdata.nasa.gov/",
                "category": DataCategory.CLIMATE,
                "update_frequency": "daily",
                "variables": ["sea_surface_temp", "vegetation_index", "drought_index"]
            },
            
            # Political Data Sources
            "vdem": {
                "url": "https://www.v-dem.net/",
                "category": DataCategory.POLITICAL,
                "update_frequency": "annual",
                "variables": ["democracy_index", "civil_liberties", "political_stability"]
            },
            "freedom_house": {
                "url": "https://freedomhouse.org/",
                "category": DataCategory.POLITICAL,
                "update_frequency": "annual",
                "variables": ["freedom_score", "political_rights", "civil_liberties"]
            },
            "world_bank_governance": {
                "url": "https://api.worldbank.org/v2/country/all/indicator/",
                "category": DataCategory.POLITICAL,
                "update_frequency": "annual",
                "indicators": [
                    "CC.EST",  # Control of Corruption
                    "GE.EST",  # Government Effectiveness
                    "PV.EST",  # Political Stability
                    "RL.EST",  # Rule of Law
                    "RQ.EST",  # Regulatory Quality
                    "VA.EST"   # Voice and Accountability
                ]
            },
            
            # Health Data Sources
            "who_health": {
                "url": "https://apps.who.int/gho/data/",
                "category": DataCategory.HEALTH,
                "update_frequency": "annual",
                "variables": ["disease_outbreaks", "health_expenditure", "mortality_rates"]
            },
            "fao_food": {
                "url": "https://www.fao.org/faostat/en/",
                "category": DataCategory.HEALTH,
                "update_frequency": "annual",
                "variables": ["food_security", "malnutrition", "crop_diseases"]
            },
            
            # Natural Resources
            "world_bank_resources": {
                "url": "https://api.worldbank.org/v2/country/all/indicator/",
                "category": DataCategory.RESOURCES,
                "update_frequency": "annual",
                "indicators": [
                    "AG.LND.ARBL.ZS",     # Arable land
                    "ER.H2O.FWTL.K3",     # Fresh water withdrawal
                    "AG.PRD.FOOD.XD",     # Food production index
                    "NY.GDP.TOTL.RT.ZS"   # Total natural resources rents
                ]
            },
            "global_forest_watch": {
                "url": "https://data.globalforestwatch.org/",
                "category": DataCategory.RESOURCES,
                "update_frequency": "annual",
                "variables": ["forest_loss", "deforestation_rate", "forest_cover"]
            }
        }
    
    def _initialize_variable_registry(self) -> Dict[str, VariableMetadata]:
        """Initialize registry of all variables with metadata"""
        registry = {}
        
        # Energy variables
        energy_vars = [
            ("crude_oil_price", "USD/barrel", "Daily crude oil spot price", "daily", 7),
            ("oil_production", "Million barrels/day", "Global oil production", "monthly", 30),
            ("energy_consumption", "kg oil equivalent per capita", "Energy use per capita", "annual", 365),
            ("renewable_energy", "% of total energy", "Renewable energy share", "annual", 365),
        ]
        
        for name, unit, desc, freq, lag in energy_vars:
            registry[name] = VariableMetadata(
                name=name, category=DataCategory.ENERGY, source="Multiple",
                unit=unit, description=desc, update_frequency=freq, lag_effect_days=lag
            )
        
        # Climate variables
        climate_vars = [
            ("temperature_anomaly", "°C", "Temperature anomaly from baseline", "monthly", 30),
            ("precipitation_anomaly", "mm", "Precipitation anomaly", "monthly", 30),
            ("drought_index", "Index", "Palmer Drought Severity Index", "monthly", 60),
            ("extreme_weather_events", "Count", "Number of extreme weather events", "monthly", 0),
        ]
        
        for name, unit, desc, freq, lag in climate_vars:
            registry[name] = VariableMetadata(
                name=name, category=DataCategory.CLIMATE, source="NOAA/NASA",
                unit=unit, description=desc, update_frequency=freq, lag_effect_days=lag
            )
        
        # Political variables
        political_vars = [
            ("democracy_index", "Index 0-1", "V-Dem Democracy Index", "annual", 180),
            ("political_stability", "Index", "Political Stability and Absence of Violence", "annual", 90),
            ("government_effectiveness", "Index", "Government Effectiveness", "annual", 180),
            ("corruption_control", "Index", "Control of Corruption", "annual", 365),
        ]
        
        for name, unit, desc, freq, lag in political_vars:
            registry[name] = VariableMetadata(
                name=name, category=DataCategory.POLITICAL, source="World Bank/V-Dem",
                unit=unit, description=desc, update_frequency=freq, lag_effect_days=lag
            )
        
        # Health variables
        health_vars = [
            ("disease_outbreaks", "Count", "Number of disease outbreaks", "monthly", 14),
            ("food_insecurity", "% population", "Food insecurity prevalence", "annual", 90),
            ("health_expenditure", "% GDP", "Health expenditure", "annual", 365),
        ]
        
        for name, unit, desc, freq, lag in health_vars:
            registry[name] = VariableMetadata(
                name=name, category=DataCategory.HEALTH, source="WHO/FAO",
                unit=unit, description=desc, update_frequency=freq, lag_effect_days=lag
            )
        
        # Resource variables
        resource_vars = [
            ("water_stress", "Index", "Water stress level", "annual", 180),
            ("arable_land", "% of land area", "Arable land percentage", "annual", 365),
            ("forest_loss", "Hectares", "Annual forest loss", "annual", 365),
            ("mineral_rents", "% GDP", "Mineral rents", "annual", 365),
        ]
        
        for name, unit, desc, freq, lag in resource_vars:
            registry[name] = VariableMetadata(
                name=name, category=DataCategory.RESOURCES, source="World Bank/GFW",
                unit=unit, description=desc, update_frequency=freq, lag_effect_days=lag
            )
        
        return registry
    
    async def fetch_energy_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch energy-related data from multiple sources"""
        try:
            logger.info("Fetching energy data...")
            
            energy_data = []
            
            # Simulate EIA oil price data (in production, use actual API)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Oil price with trend and volatility
            base_price = 70
            trend = np.linspace(0, 20, len(dates))
            volatility = np.random.normal(0, 5, len(dates))
            seasonal = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            oil_prices = base_price + trend + volatility + seasonal
            
            # Oil production (monthly data interpolated to daily)
            production_base = 100  # Million barrels/day
            production_trend = np.linspace(0, 10, len(dates))
            production_noise = np.random.normal(0, 2, len(dates))
            oil_production = production_base + production_trend + production_noise
            
            # Energy consumption (annual data, forward-filled)
            energy_consumption = np.repeat(
                np.random.uniform(2000, 4000, len(dates) // 365 + 1),
                365
            )[:len(dates)]
            
            energy_df = pd.DataFrame({
                'date': dates,
                'crude_oil_price': oil_prices,
                'oil_production': oil_production,
                'energy_consumption': energy_consumption,
                'renewable_energy': np.random.uniform(10, 30, len(dates))
            })
            
            return energy_df
            
        except Exception as e:
            logger.error(f"Error fetching energy data: {e}")
            return pd.DataFrame()
    
    async def fetch_climate_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch climate and weather data"""
        try:
            logger.info("Fetching climate data...")
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Temperature anomaly with climate change trend
            temp_trend = np.linspace(0, 2, len(dates))  # 2°C warming over period
            temp_seasonal = 3 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            temp_noise = np.random.normal(0, 1, len(dates))
            temperature_anomaly = temp_trend + temp_seasonal + temp_noise
            
            # Precipitation anomaly
            precip_seasonal = 50 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25 + np.pi/2)
            precip_noise = np.random.normal(0, 30, len(dates))
            precipitation_anomaly = precip_seasonal + precip_noise
            
            # Drought index (Palmer Drought Severity Index)
            drought_base = np.random.normal(0, 2, len(dates))
            drought_index = pd.Series(drought_base).rolling(window=90).mean().fillna(0)
            
            # Extreme weather events (Poisson process)
            extreme_events = np.random.poisson(0.1, len(dates))
            
            climate_df = pd.DataFrame({
                'date': dates,
                'temperature_anomaly': temperature_anomaly,
                'precipitation_anomaly': precipitation_anomaly,
                'drought_index': drought_index,
                'extreme_weather_events': extreme_events
            })
            
            return climate_df
            
        except Exception as e:
            logger.error(f"Error fetching climate data: {e}")
            return pd.DataFrame()
    
    async def fetch_political_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch political stability and governance data"""
        try:
            logger.info("Fetching political data...")
            
            # Annual data, forward-filled to daily
            years = pd.date_range(start=start_date, end=end_date, freq='YS')
            
            # Democracy index with gradual changes
            democracy_trend = np.random.normal(0, 0.05, len(years))
            democracy_base = 0.6
            democracy_values = np.cumsum([democracy_base] + list(democracy_trend))
            democracy_values = np.clip(democracy_values, 0, 1)
            
            # Political stability
            stability_base = np.random.normal(0, 0.5, len(years))
            stability_values = np.clip(stability_base, -2.5, 2.5)
            
            # Government effectiveness
            effectiveness_values = np.random.normal(0, 0.8, len(years))
            effectiveness_values = np.clip(effectiveness_values, -2.5, 2.5)
            
            # Corruption control
            corruption_values = np.random.normal(0, 0.7, len(years))
            corruption_values = np.clip(corruption_values, -2.5, 2.5)
            
            # Create daily data by forward-filling annual values
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            political_data = []
            
            for date in dates:
                year_idx = min(date.year - start_date.year, len(years) - 1)
                political_data.append({
                    'date': date,
                    'democracy_index': democracy_values[year_idx],
                    'political_stability': stability_values[year_idx],
                    'government_effectiveness': effectiveness_values[year_idx],
                    'corruption_control': corruption_values[year_idx]
                })
            
            political_df = pd.DataFrame(political_data)
            
            return political_df
            
        except Exception as e:
            logger.error(f"Error fetching political data: {e}")
            return pd.DataFrame()
    
    async def fetch_health_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch health and disease outbreak data"""
        try:
            logger.info("Fetching health data...")
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Disease outbreaks (Poisson process with seasonal variation)
            seasonal_factor = 1 + 0.5 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            outbreak_rate = 0.05 * seasonal_factor
            disease_outbreaks = np.random.poisson(outbreak_rate)
            
            # Food insecurity (annual data with trend)
            food_insecurity_trend = np.linspace(15, 25, len(dates) // 365 + 1)
            food_insecurity = np.repeat(food_insecurity_trend, 365)[:len(dates)]
            food_insecurity += np.random.normal(0, 2, len(dates))
            
            # Health expenditure (annual data)
            health_exp_base = np.random.uniform(5, 15, len(dates) // 365 + 1)
            health_expenditure = np.repeat(health_exp_base, 365)[:len(dates)]
            
            health_df = pd.DataFrame({
                'date': dates,
                'disease_outbreaks': disease_outbreaks,
                'food_insecurity': food_insecurity,
                'health_expenditure': health_expenditure
            })
            
            return health_df
            
        except Exception as e:
            logger.error(f"Error fetching health data: {e}")
            return pd.DataFrame()
    
    async def fetch_resource_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch natural resource data"""
        try:
            logger.info("Fetching resource data...")
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Water stress (annual data with climate impact)
            water_stress_base = np.random.uniform(1, 4, len(dates) // 365 + 1)
            water_stress = np.repeat(water_stress_base, 365)[:len(dates)]
            
            # Arable land (slowly decreasing)
            arable_land_trend = np.linspace(0, -2, len(dates))
            arable_land_base = 35
            arable_land = arable_land_base + arable_land_trend + np.random.normal(0, 0.5, len(dates))
            
            # Forest loss (annual data)
            forest_loss_base = np.random.exponential(1000, len(dates) // 365 + 1)
            forest_loss = np.repeat(forest_loss_base, 365)[:len(dates)]
            
            # Mineral rents
            mineral_rents_base = np.random.uniform(0, 20, len(dates) // 365 + 1)
            mineral_rents = np.repeat(mineral_rents_base, 365)[:len(dates)]
            
            resource_df = pd.DataFrame({
                'date': dates,
                'water_stress': water_stress,
                'arable_land': arable_land,
                'forest_loss': forest_loss,
                'mineral_rents': mineral_rents
            })
            
            return resource_df
            
        except Exception as e:
            logger.error(f"Error fetching resource data: {e}")
            return pd.DataFrame()
    
    async def integrate_all_data(self, start_date: datetime, end_date: datetime,
                               countries: List[str] = None) -> pd.DataFrame:
        """Integrate data from all sources into unified dataset"""
        try:
            logger.info("Integrating data from all sources...")
            
            # Fetch data from all sources in parallel
            tasks = [
                self.fetch_energy_data(start_date, end_date),
                self.fetch_climate_data(start_date, end_date),
                self.fetch_political_data(start_date, end_date),
                self.fetch_health_data(start_date, end_date),
                self.fetch_resource_data(start_date, end_date)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all dataframes
            integrated_df = None
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in data source {i}: {result}")
                    continue
                
                if result.empty:
                    continue
                
                if integrated_df is None:
                    integrated_df = result.set_index('date')
                else:
                    result_indexed = result.set_index('date')
                    integrated_df = integrated_df.join(result_indexed, how='outer')
            
            if integrated_df is None:
                return pd.DataFrame()
            
            # Add conflict risk target variable (synthetic for demonstration)
            # In production, this would come from UCDP/ACLED data
            conflict_risk = self._generate_conflict_risk_target(integrated_df)
            integrated_df['conflict_risk'] = conflict_risk
            
            # Apply transformations and handle missing values
            integrated_df = self._apply_transformations(integrated_df)
            integrated_df = self._handle_missing_values(integrated_df)
            
            # Store metadata
            self._update_metadata(integrated_df, start_date, end_date)
            
            self.integrated_data = integrated_df
            
            logger.info(f"Data integration completed. Shape: {integrated_df.shape}")
            
            return integrated_df
            
        except Exception as e:
            logger.error(f"Error integrating data: {e}")
            return pd.DataFrame()
    
    def _generate_conflict_risk_target(self, data: pd.DataFrame) -> pd.Series:
        """Generate synthetic conflict risk target based on integrated variables"""
        try:
            # Create conflict risk as weighted combination of factors
            risk_components = []
            
            # Energy stress component
            if 'crude_oil_price' in data.columns:
                oil_volatility = data['crude_oil_price'].rolling(30).std()
                oil_stress = (oil_volatility - oil_volatility.mean()) / oil_volatility.std()
                risk_components.append(0.2 * oil_stress)
            
            # Climate stress component
            if 'temperature_anomaly' in data.columns and 'drought_index' in data.columns:
                climate_stress = (
                    0.5 * data['temperature_anomaly'] + 
                    0.5 * abs(data['drought_index'])
                )
                climate_stress = (climate_stress - climate_stress.mean()) / climate_stress.std()
                risk_components.append(0.25 * climate_stress)
            
            # Political instability component
            if 'political_stability' in data.columns:
                political_stress = -data['political_stability']  # Lower stability = higher risk
                political_stress = (political_stress - political_stress.mean()) / political_stress.std()
                risk_components.append(0.3 * political_stress)
            
            # Resource scarcity component
            if 'water_stress' in data.columns and 'arable_land' in data.columns:
                resource_stress = (
                    0.6 * data['water_stress'] + 
                    0.4 * (data['arable_land'].max() - data['arable_land'])
                )
                resource_stress = (resource_stress - resource_stress.mean()) / resource_stress.std()
                risk_components.append(0.15 * resource_stress)
            
            # Health crisis component
            if 'disease_outbreaks' in data.columns:
                health_stress = data['disease_outbreaks'].rolling(30).sum()
                health_stress = (health_stress - health_stress.mean()) / health_stress.std()
                risk_components.append(0.1 * health_stress)
            
            # Combine components
            if risk_components:
                conflict_risk = sum(risk_components)
                # Add some noise and ensure positive values
                conflict_risk += np.random.normal(0, 0.1, len(conflict_risk))
                conflict_risk = np.maximum(conflict_risk, 0)
                
                # Scale to 0-10 range
                conflict_risk = 5 + 2 * conflict_risk
                conflict_risk = np.clip(conflict_risk, 0, 10)
            else:
                conflict_risk = pd.Series(np.random.uniform(3, 7, len(data)), index=data.index)
            
            return conflict_risk
            
        except Exception as e:
            logger.error(f"Error generating conflict risk target: {e}")
            return pd.Series(np.random.uniform(3, 7, len(data)), index=data.index)
    
    def _apply_transformations(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply transformations to variables based on metadata"""
        try:
            transformed_data = data.copy()
            
            # Log transformations for skewed variables
            log_vars = ['crude_oil_price', 'oil_production', 'forest_loss']
            for var in log_vars:
                if var in transformed_data.columns:
                    transformed_data[f'{var}_log'] = np.log1p(transformed_data[var])
            
            # Percentage changes for trend analysis
            pct_vars = ['crude_oil_price', 'energy_consumption', 'arable_land']
            for var in pct_vars:
                if var in transformed_data.columns:
                    transformed_data[f'{var}_pct_change'] = transformed_data[var].pct_change()
            
            # Moving averages for smoothing
            ma_vars = ['temperature_anomaly', 'precipitation_anomaly', 'conflict_risk']
            for var in ma_vars:
                if var in transformed_data.columns:
                    transformed_data[f'{var}_ma7'] = transformed_data[var].rolling(7).mean()
                    transformed_data[f'{var}_ma30'] = transformed_data[var].rolling(30).mean()
            
            # Volatility measures
            vol_vars = ['crude_oil_price', 'conflict_risk']
            for var in vol_vars:
                if var in transformed_data.columns:
                    transformed_data[f'{var}_volatility'] = transformed_data[var].rolling(30).std()
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error applying transformations: {e}")
            return data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values using appropriate strategies"""
        try:
            # Forward fill for slowly changing variables
            slow_change_vars = ['democracy_index', 'political_stability', 'arable_land']
            for var in slow_change_vars:
                if var in data.columns:
                    data[var] = data[var].fillna(method='ffill')
            
            # Interpolate for continuous variables
            continuous_vars = ['temperature_anomaly', 'precipitation_anomaly', 'crude_oil_price']
            for var in continuous_vars:
                if var in data.columns:
                    data[var] = data[var].interpolate(method='linear')
            
            # Fill remaining with median
            for col in data.select_dtypes(include=[np.number]).columns:
                data[col] = data[col].fillna(data[col].median())
            
            return data
            
        except Exception as e:
            logger.error(f"Error handling missing values: {e}")
            return data
    
    def _update_metadata(self, data: pd.DataFrame, start_date: datetime, end_date: datetime):
        """Update metadata about the integrated dataset"""
        self.metadata = {
            'integration_timestamp': datetime.now().isoformat(),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'variables': {
                'total_count': len(data.columns),
                'by_category': {},
                'transformations_applied': []
            },
            'data_quality': {
                'completeness': (1 - data.isnull().sum().sum() / (data.shape[0] * data.shape[1])),
                'missing_values': data.isnull().sum().to_dict()
            }
        }
        
        # Count variables by category
        for var_name in data.columns:
            if var_name in self.variable_registry:
                category = self.variable_registry[var_name].category.value
                if category not in self.metadata['variables']['by_category']:
                    self.metadata['variables']['by_category'][category] = 0
                self.metadata['variables']['by_category'][category] += 1
    
    def get_variable_info(self, variable_name: str) -> Optional[VariableMetadata]:
        """Get metadata for a specific variable"""
        return self.variable_registry.get(variable_name)
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of data integration process"""
        return {
            'metadata': self.metadata,
            'data_shape': self.integrated_data.shape if not self.integrated_data.empty else (0, 0),
            'variable_registry_size': len(self.variable_registry),
            'source_configs': len(self.source_configs)
        }