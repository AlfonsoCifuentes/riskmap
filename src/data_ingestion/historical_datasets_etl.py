"""
Historical Datasets ETL System
=====================================

Comprehensive data collection, standardization and processing for historical analysis.
Supports multiple geopolitical data sources with unified schema.

Datasets supported:
- ACLED (violence and protests)
- GDELT v2 (media events)
- EIA (energy/oil/gas prices)
- ENTSOG (gas flows to EU)
- UNHCR (refugees/displaced persons)
- Fragile States Index
- World Governance Indicators
- FAO Food Price Index
"""

import os
import requests
import pandas as pd
import geopandas as gpd
import sqlite3
import json
import zipfile
import io
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalDataETL:
    """Main ETL orchestrator for historical geopolitical datasets"""
    
    def __init__(self, config_path: str = "./config/datasets.json"):
        self.config_path = config_path
        self.data_dir = Path("./data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.cache_dir = self.data_dir / "cache"
        
        # Create directories
        for dir_path in [self.raw_dir, self.processed_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Load API keys from environment
        self.api_keys = {
            'ACLED_KEY': os.getenv('ACLED_KEY'),
            'EIA_KEY': os.getenv('EIA_KEY')
        }
        
        # Database setup
        self.db_path = self.data_dir / "historical_analysis.db"
        self.init_database()
        
        # Standard schema columns
        self.standard_columns = ['iso3', 'country', 'date', 'indicator', 'value', 'source', 'category']
        
    def init_database(self):
        """Initialize SQLite database with unified schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Main events table with standardized schema
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historical_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iso3 TEXT,
                    country TEXT,
                    date TEXT,
                    indicator TEXT,
                    value REAL,
                    source TEXT,
                    category TEXT,
                    subcategory TEXT,
                    latitude REAL,
                    longitude REAL,
                    description TEXT,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Metadata table for tracking dataset updates
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dataset_metadata (
                    dataset_name TEXT PRIMARY KEY,
                    last_updated TIMESTAMP,
                    records_count INTEGER,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            logger.info("✅ Historical analysis database initialized")

    def cache_data(self, path: str, url: str, force: bool = False) -> str:
        """Smart caching system for downloaded data"""
        cache_file = self.cache_dir / Path(url).name
        
        # Check if cached file exists and is recent (< 24 hours)
        if cache_file.exists() and not force:
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age < 86400:  # 24 hours in seconds
                logger.info(f"📁 Using cached data: {cache_file}")
                return str(cache_file)
        
        # Download fresh data
        try:
            logger.info(f"🌐 Downloading: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"💾 Cached: {cache_file}")
            return str(cache_file)
            
        except Exception as e:
            logger.error(f"❌ Download failed for {url}: {e}")
            if cache_file.exists():
                logger.info(f"📁 Falling back to cached version: {cache_file}")
                return str(cache_file)
            raise

    # DATASET 1: ACLED (Violence and Protests)
    def collect_acled_data(self, days_back: int = 30) -> pd.DataFrame:
        """Collect ACLED conflict events data"""
        if not self.api_keys['ACLED_KEY']:
            logger.warning("⚠️ ACLED_KEY not found, using mock data")
            return self._generate_mock_acled_data()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        url = f"https://api.acleddata.com/acled/read"
        params = {
            'key': self.api_keys['ACLED_KEY'],
            'limit': 50000,
            'event_date': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            'region': 'Middle East|Europe Eastern'
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data['data'])
            
            # Standardize columns
            standardized = pd.DataFrame({
                'iso3': df['iso3'],
                'country': df['country'],
                'date': pd.to_datetime(df['event_date']),
                'indicator': 'acled_events',
                'value': 1,  # Event count
                'source': 'ACLED',
                'category': 'conflict',
                'subcategory': df['event_type'],
                'latitude': pd.to_numeric(df['latitude'], errors='coerce'),
                'longitude': pd.to_numeric(df['longitude'], errors='coerce'),
                'description': df['notes']
            })
            
            logger.info(f"✅ ACLED: {len(standardized)} events collected")
            return standardized
            
        except Exception as e:
            logger.error(f"❌ ACLED collection failed: {e}")
            return self._generate_mock_acled_data()

    def _generate_mock_acled_data(self) -> pd.DataFrame:
        """Generate realistic mock ACLED data"""
        import random
        from datetime import datetime, timedelta
        
        countries = [
            ('PSE', 'Palestine', 31.5, 34.5),
            ('ISR', 'Israel', 31.5, 35.0),
            ('UKR', 'Ukraine', 50.0, 30.0),
            ('SYR', 'Syria', 35.0, 38.0),
            ('IRQ', 'Iraq', 33.0, 44.0)
        ]
        
        events = []
        for i in range(200):
            country = random.choice(countries)
            date = datetime.now() - timedelta(days=random.randint(0, 30))
            
            events.append({
                'iso3': country[0],
                'country': country[1],
                'date': date,
                'indicator': 'acled_events',
                'value': 1,
                'source': 'ACLED_MOCK',
                'category': 'conflict',
                'subcategory': random.choice(['Violence against civilians', 'Battles', 'Protests', 'Riots']),
                'latitude': country[2] + random.uniform(-1, 1),
                'longitude': country[3] + random.uniform(-1, 1),
                'description': f"Mock conflict event in {country[1]}"
            })
        
        return pd.DataFrame(events)

    # DATASET 2: GDELT v2 (Media Events)
    def collect_gdelt_data(self, days_back: int = 7) -> pd.DataFrame:
        """Collect GDELT media events data"""
        try:
            events = []
            for i in range(days_back):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime('%Y%m%d')
                
                url = f"https://data.gdeltproject.org/events/{date_str}.export.CSV.zip"
                
                try:
                    cache_file = self.cache_data(f"gdelt_{date_str}.zip", url)
                    
                    # Read compressed CSV
                    with zipfile.ZipFile(cache_file, 'r') as zip_ref:
                        csv_filename = f"{date_str}.export.CSV"
                        if csv_filename in zip_ref.namelist():
                            with zip_ref.open(csv_filename) as csv_file:
                                # Read only first 10000 rows to avoid memory issues
                                df = pd.read_csv(csv_file, sep='\t', nrows=10000, header=None, 
                                               low_memory=False, on_bad_lines='skip')
                                
                                if len(df.columns) >= 6:
                                    # Basic GDELT columns processing
                                    df.columns = [f'col_{i}' for i in range(len(df.columns))]
                                    
                                    # Extract relevant events (focus on conflict-related)
                                    relevant_df = df[df['col_4'].astype(str).str.contains('20|21|22', na=False)][:500]
                                    
                                    for _, row in relevant_df.iterrows():
                                        events.append({
                                            'iso3': 'UNK',
                                            'country': 'Unknown',
                                            'date': date,
                                            'indicator': 'gdelt_events',
                                            'value': 1,
                                            'source': 'GDELT',
                                            'category': 'media',
                                            'subcategory': 'conflict_related',
                                            'latitude': None,
                                            'longitude': None,
                                            'description': f"GDELT event on {date_str}"
                                        })
                                        
                except Exception as e:
                    logger.warning(f"⚠️ GDELT data for {date_str} failed: {e}")
                    continue
                    
            logger.info(f"✅ GDELT: {len(events)} events collected")
            return pd.DataFrame(events) if events else pd.DataFrame(columns=self.standard_columns)
            
        except Exception as e:
            logger.error(f"❌ GDELT collection failed: {e}")
            return self._generate_mock_gdelt_data()

    def _generate_mock_gdelt_data(self) -> pd.DataFrame:
        """Generate mock GDELT data"""
        events = []
        for i in range(100):
            date = datetime.now() - timedelta(days=random.randint(0, 7))
            events.append({
                'iso3': random.choice(['UKR', 'RUS', 'PSE', 'ISR', 'SYR']),
                'country': random.choice(['Ukraine', 'Russia', 'Palestine', 'Israel', 'Syria']),
                'date': date,
                'indicator': 'gdelt_events',
                'value': 1,
                'source': 'GDELT_MOCK',
                'category': 'media',
                'subcategory': 'conflict_related',
                'latitude': None,
                'longitude': None,
                'description': f"Mock GDELT event"
            })
        return pd.DataFrame(events)

    # DATASET 3: EIA (Energy Data)
    def collect_eia_data(self) -> pd.DataFrame:
        """Collect EIA energy production and price data"""
        if not self.api_keys['EIA_KEY']:
            logger.warning("⚠️ EIA_KEY not found, using mock data")
            return self._generate_mock_eia_data()
        
        countries = ['RUS', 'SAU', 'IRQ', 'IRN', 'USA']
        all_data = []
        
        for country in countries:
            url = "https://api.eia.gov/v2/international/data/"
            params = {
                'api_key': self.api_keys['EIA_KEY'],
                'frequency': 'monthly',
                'data': ['production'],
                'facets[productName]': ['Total Oil Supply'],
                'facets[countryRegionId]': [country],
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'length': 24  # Last 2 years
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if 'response' in data and 'data' in data['response']:
                    for item in data['response']['data']:
                        all_data.append({
                            'iso3': country,
                            'country': item.get('countryRegionName', country),
                            'date': pd.to_datetime(item['period'] + '-01'),
                            'indicator': 'oil_production',
                            'value': float(item['value']) if item['value'] else 0,
                            'source': 'EIA',
                            'category': 'energy',
                            'subcategory': 'production',
                            'latitude': None,
                            'longitude': None,
                            'description': f"Oil production in {country}"
                        })
                        
            except Exception as e:
                logger.warning(f"⚠️ EIA data for {country} failed: {e}")
                continue
        
        logger.info(f"✅ EIA: {len(all_data)} records collected")
        return pd.DataFrame(all_data) if all_data else self._generate_mock_eia_data()

    def _generate_mock_eia_data(self) -> pd.DataFrame:
        """Generate mock EIA energy data"""
        countries = [('RUS', 'Russia'), ('SAU', 'Saudi Arabia'), ('IRQ', 'Iraq'), ('IRN', 'Iran'), ('USA', 'United States')]
        data = []
        
        for country_code, country_name in countries:
            base_production = random.uniform(5000, 15000)  # Thousand barrels per day
            for i in range(24):  # 24 months
                date = datetime.now() - timedelta(days=30*i)
                variation = random.uniform(0.8, 1.2)
                
                data.append({
                    'iso3': country_code,
                    'country': country_name,
                    'date': date,
                    'indicator': 'oil_production',
                    'value': base_production * variation,
                    'source': 'EIA_MOCK',
                    'category': 'energy',
                    'subcategory': 'production',
                    'latitude': None,
                    'longitude': None,
                    'description': f"Mock oil production in {country_name}"
                })
        
        return pd.DataFrame(data)

    # DATASET 4: ENTSOG (EU Gas Flows)
    def collect_entsog_data(self, days_back: int = 30) -> pd.DataFrame:
        """Collect ENTSOG gas flow data to EU"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Key pipeline entry points
        entry_points = [
            'UKR-TSO-0001ITP-00001',  # Ukraine entry
            'RUS-TSO-0001ITP-00001',  # Russia entry (hypothetical)
        ]
        
        all_data = []
        
        for point_key in entry_points:
            url = "https://transparency.entsog.eu/api/v1/operationaldatas.csv"
            params = {
                'pointKey': point_key,
                'indicator': 'Physical Flow',
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'directionKey': 'entry'
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    # Parse CSV response
                    csv_data = pd.read_csv(io.StringIO(response.text))
                    
                    for _, row in csv_data.iterrows():
                        all_data.append({
                            'iso3': 'EUR',  # EU aggregate
                            'country': 'European Union',
                            'date': pd.to_datetime(row.get('gasDayStart', row.get('date', ''))),
                            'indicator': 'gas_flow',
                            'value': float(row.get('value', 0)) if row.get('value') else 0,
                            'source': 'ENTSOG',
                            'category': 'energy',
                            'subcategory': 'gas_imports',
                            'latitude': None,
                            'longitude': None,
                            'description': f"Gas flow from {point_key}"
                        })
                        
            except Exception as e:
                logger.warning(f"⚠️ ENTSOG data for {point_key} failed: {e}")
                continue
        
        if not all_data:
            return self._generate_mock_entsog_data()
        
        logger.info(f"✅ ENTSOG: {len(all_data)} records collected")
        return pd.DataFrame(all_data)

    def _generate_mock_entsog_data(self) -> pd.DataFrame:
        """Generate mock ENTSOG gas flow data"""
        data = []
        base_flow = 50000  # mcm/day
        
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            variation = random.uniform(0.7, 1.3)
            
            data.append({
                'iso3': 'EUR',
                'country': 'European Union',
                'date': date,
                'indicator': 'gas_flow',
                'value': base_flow * variation,
                'source': 'ENTSOG_MOCK',
                'category': 'energy',
                'subcategory': 'gas_imports',
                'latitude': None,
                'longitude': None,
                'description': "Mock EU gas imports"
            })
            
        return pd.DataFrame(data)

    # DATASET 5: UNHCR (Refugees and IDPs)
    def collect_unhcr_data(self) -> pd.DataFrame:
        """Collect UNHCR refugee and IDP data"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        urls = {
            'refugees': f"https://data.unhcr.org/population/get/timeseries?export=csv&frequency=month&population_group=REF&fromDate=2020-01-01&toDate={today}",
            'idp': f"https://data.unhcr.org/population/get/timeseries?export=csv&frequency=month&population_group=IDP&fromDate=2020-01-01&toDate={today}"
        }
        
        all_data = []
        
        for data_type, url in urls.items():
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    csv_data = pd.read_csv(io.StringIO(response.text))
                    
                    for _, row in csv_data.iterrows():
                        all_data.append({
                            'iso3': row.get('iso3', 'UNK'),
                            'country': row.get('country', 'Unknown'),
                            'date': pd.to_datetime(row.get('date', row.get('time_period', ''))),
                            'indicator': f'unhcr_{data_type}',
                            'value': float(row.get('individuals', row.get('value', 0))),
                            'source': 'UNHCR',
                            'category': 'displacement',
                            'subcategory': data_type,
                            'latitude': None,
                            'longitude': None,
                            'description': f"UNHCR {data_type} data"
                        })
                        
            except Exception as e:
                logger.warning(f"⚠️ UNHCR {data_type} data failed: {e}")
                continue
        
        if not all_data:
            return self._generate_mock_unhcr_data()
        
        logger.info(f"✅ UNHCR: {len(all_data)} records collected")
        return pd.DataFrame(all_data)

    def _generate_mock_unhcr_data(self) -> pd.DataFrame:
        """Generate mock UNHCR displacement data"""
        countries = [('SYR', 'Syria'), ('UKR', 'Ukraine'), ('AFG', 'Afghanistan'), ('PSE', 'Palestine')]
        data = []
        
        for country_code, country_name in countries:
            base_refugees = random.randint(100000, 2000000)
            base_idps = random.randint(50000, 1000000)
            
            for i in range(12):  # 12 months
                date = datetime.now() - timedelta(days=30*i)
                
                # Refugees
                data.append({
                    'iso3': country_code,
                    'country': country_name,
                    'date': date,
                    'indicator': 'unhcr_refugees',
                    'value': base_refugees * random.uniform(0.9, 1.1),
                    'source': 'UNHCR_MOCK',
                    'category': 'displacement',
                    'subcategory': 'refugees',
                    'latitude': None,
                    'longitude': None,
                    'description': f"Mock refugee data for {country_name}"
                })
                
                # IDPs
                data.append({
                    'iso3': country_code,
                    'country': country_name,
                    'date': date,
                    'indicator': 'unhcr_idp',
                    'value': base_idps * random.uniform(0.8, 1.2),
                    'source': 'UNHCR_MOCK',
                    'category': 'displacement',
                    'subcategory': 'idp',
                    'latitude': None,
                    'longitude': None,
                    'description': f"Mock IDP data for {country_name}"
                })
                
        return pd.DataFrame(data)

    # DATASET 6: Fragile States Index
    def collect_fsi_data(self) -> pd.DataFrame:
        """Collect Fragile States Index data"""
        url = "https://fragilestatesindex.org/wp-content/uploads/2024/05/FSI2024-Data.xlsx"
        
        try:
            cache_file = self.cache_data("fsi_2024.xlsx", url)
            df = pd.read_excel(cache_file)
            
            # Standardize FSI data
            standardized = []
            
            for _, row in df.iterrows():
                if 'Country' in row and 'Total' in row:
                    standardized.append({
                        'iso3': row.get('ISO3', 'UNK'),
                        'country': row['Country'],
                        'date': datetime(2024, 1, 1),  # FSI is annual
                        'indicator': 'fragile_states_index',
                        'value': float(row['Total']) if pd.notna(row['Total']) else 0,
                        'source': 'FSI',
                        'category': 'governance',
                        'subcategory': 'fragility',
                        'latitude': None,
                        'longitude': None,
                        'description': f"Fragile States Index score for {row['Country']}"
                    })
            
            logger.info(f"✅ FSI: {len(standardized)} records collected")
            return pd.DataFrame(standardized)
            
        except Exception as e:
            logger.warning(f"⚠️ FSI collection failed: {e}")
            return self._generate_mock_fsi_data()

    def _generate_mock_fsi_data(self) -> pd.DataFrame:
        """Generate mock FSI data"""
        countries = [
            ('SYR', 'Syria', 110), ('SOM', 'Somalia', 108), ('UKR', 'Ukraine', 85),
            ('AFG', 'Afghanistan', 105), ('YEM', 'Yemen', 102), ('IRQ', 'Iraq', 95)
        ]
        
        data = []
        for iso3, country, base_score in countries:
            data.append({
                'iso3': iso3,
                'country': country,
                'date': datetime(2024, 1, 1),
                'indicator': 'fragile_states_index',
                'value': base_score + random.uniform(-5, 5),
                'source': 'FSI_MOCK',
                'category': 'governance',
                'subcategory': 'fragility',
                'latitude': None,
                'longitude': None,
                'description': f"Mock FSI score for {country}"
            })
            
        return pd.DataFrame(data)

    # DATASET 7: World Governance Indicators
    def collect_wgi_data(self) -> pd.DataFrame:
        """Collect World Governance Indicators (Political Stability)"""
        url = "https://info.worldbank.org/governance/wgi/WGI_csv.zip"
        
        try:
            cache_file = self.cache_data("wgi_data.zip", url)
            
            with zipfile.ZipFile(cache_file, 'r') as zip_ref:
                # Look for WGI data file
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                
                if csv_files:
                    with zip_ref.open(csv_files[0]) as csv_file:
                        df = pd.read_csv(csv_file)
                        
                        # Filter for Political Stability indicator
                        pv_data = df[df['Indicator Name'].str.contains('Political Stability', na=False)]
                        
                        standardized = []
                        for _, row in pv_data.iterrows():
                            # Get latest year with data
                            year_cols = [col for col in row.index if col.isdigit() and int(col) >= 2020]
                            
                            for year_col in year_cols:
                                if pd.notna(row[year_col]):
                                    standardized.append({
                                        'iso3': row.get('Country Code', 'UNK'),
                                        'country': row.get('Country Name', 'Unknown'),
                                        'date': datetime(int(year_col), 1, 1),
                                        'indicator': 'political_stability',
                                        'value': float(row[year_col]),
                                        'source': 'WGI',
                                        'category': 'governance',
                                        'subcategory': 'stability',
                                        'latitude': None,
                                        'longitude': None,
                                        'description': f"Political Stability score for {row.get('Country Name', 'Unknown')}"
                                    })
                        
                        logger.info(f"✅ WGI: {len(standardized)} records collected")
                        return pd.DataFrame(standardized)
                        
        except Exception as e:
            logger.warning(f"⚠️ WGI collection failed: {e}")
            
        return self._generate_mock_wgi_data()

    def _generate_mock_wgi_data(self) -> pd.DataFrame:
        """Generate mock WGI political stability data"""
        countries = [
            ('SYR', 'Syria', -2.5), ('UKR', 'Ukraine', -1.2), ('IRQ', 'Iraq', -1.8),
            ('AFG', 'Afghanistan', -2.3), ('PSE', 'Palestine', -1.5), ('ISR', 'Israel', 0.2)
        ]
        
        data = []
        for iso3, country, base_score in countries:
            for year in [2022, 2023, 2024]:
                data.append({
                    'iso3': iso3,
                    'country': country,
                    'date': datetime(year, 1, 1),
                    'indicator': 'political_stability',
                    'value': base_score + random.uniform(-0.3, 0.3),
                    'source': 'WGI_MOCK',
                    'category': 'governance',
                    'subcategory': 'stability',
                    'latitude': None,
                    'longitude': None,
                    'description': f"Mock political stability score for {country}"
                })
                
        return pd.DataFrame(data)

    # DATASET 8: FAO Food Price Index
    def collect_fao_data(self) -> pd.DataFrame:
        """Collect FAO Food Price Index data"""
        url = "https://fenixservices.fao.org/api/faostat/api/v1/en/Commodity_Prices/FPMA?download=CSV"
        
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                
                standardized = []
                for _, row in df.iterrows():
                    if pd.notna(row.get('Value', row.get('value', None))):
                        standardized.append({
                            'iso3': row.get('Area Code (ISO3)', row.get('iso3', 'GLOBAL')),
                            'country': row.get('Area', row.get('country', 'Global')),
                            'date': pd.to_datetime(row.get('Date', row.get('date', ''))),
                            'indicator': 'food_price_index',
                            'value': float(row.get('Value', row.get('value', 0))),
                            'source': 'FAO',
                            'category': 'food_security',
                            'subcategory': 'prices',
                            'latitude': None,
                            'longitude': None,
                            'description': f"FAO Food Price Index"
                        })
                
                logger.info(f"✅ FAO: {len(standardized)} records collected")
                return pd.DataFrame(standardized)
                
        except Exception as e:
            logger.warning(f"⚠️ FAO collection failed: {e}")
            
        return self._generate_mock_fao_data()

    def _generate_mock_fao_data(self) -> pd.DataFrame:
        """Generate mock FAO food price data"""
        data = []
        base_index = 100
        
        for i in range(24):  # 24 months
            date = datetime.now() - timedelta(days=30*i)
            variation = random.uniform(0.9, 1.2)
            
            data.append({
                'iso3': 'GLOBAL',
                'country': 'Global',
                'date': date,
                'indicator': 'food_price_index',
                'value': base_index * variation,
                'source': 'FAO_MOCK',
                'category': 'food_security',
                'subcategory': 'prices',
                'latitude': None,
                'longitude': None,
                'description': "Mock FAO Food Price Index"
            })
            
        return pd.DataFrame(data)

    def run_full_etl(self, force_refresh: bool = False) -> Dict[str, int]:
        """Run complete ETL process for all datasets"""
        logger.info("🚀 Starting comprehensive historical data ETL...")
        
        results = {}
        all_data = []
        
        # Collection functions mapping
        collectors = {
            'ACLED': self.collect_acled_data,
            'GDELT': self.collect_gdelt_data,
            'EIA': self.collect_eia_data,
            'ENTSOG': self.collect_entsog_data,
            'UNHCR': self.collect_unhcr_data,
            'FSI': self.collect_fsi_data,
            'WGI': self.collect_wgi_data,
            'FAO': self.collect_fao_data
        }
        
        # Collect data from all sources
        for dataset_name, collector_func in collectors.items():
            try:
                logger.info(f"📊 Collecting {dataset_name} data...")
                df = collector_func()
                
                if not df.empty:
                    # Add dataset metadata
                    df['dataset'] = dataset_name
                    all_data.append(df)
                    results[dataset_name] = len(df)
                    
                    # Update metadata
                    self.update_dataset_metadata(dataset_name, len(df), 'success')
                else:
                    results[dataset_name] = 0
                    self.update_dataset_metadata(dataset_name, 0, 'empty')
                    
            except Exception as e:
                logger.error(f"❌ {dataset_name} collection failed: {e}")
                results[dataset_name] = 0
                self.update_dataset_metadata(dataset_name, 0, f'error: {str(e)}')
        
        # Combine and save all data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Save to database
            self.save_to_database(combined_df)
            
            # Save processed files
            self.save_processed_files(combined_df)
            
            logger.info(f"✅ ETL Complete! Total records: {len(combined_df)}")
        else:
            logger.warning("⚠️ No data collected from any source")
            
        return results

    def save_to_database(self, df: pd.DataFrame):
        """Save standardized data to SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql('historical_events', conn, if_exists='replace', index=False)
            logger.info(f"💾 Saved {len(df)} records to database")

    def save_processed_files(self, df: pd.DataFrame):
        """Save processed data files by category"""
        categories = df['category'].unique()
        
        for category in categories:
            category_df = df[df['category'] == category]
            filename = self.processed_dir / f"{category}_processed.csv"
            category_df.to_csv(filename, index=False)
            logger.info(f"📁 Saved {category} data: {len(category_df)} records")

    def update_dataset_metadata(self, dataset_name: str, record_count: int, status: str):
        """Update dataset metadata in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO dataset_metadata 
                (dataset_name, last_updated, records_count, status)
                VALUES (?, ?, ?, ?)
            ''', (dataset_name, datetime.now(), record_count, status))
            conn.commit()

    def get_statistics(self) -> Dict:
        """Get ETL statistics and data overview"""
        with sqlite3.connect(self.db_path) as conn:
            # Total records
            total_query = "SELECT COUNT(*) as total FROM historical_events"
            total_records = pd.read_sql_query(total_query, conn)['total'].iloc[0]
            
            # Records by source
            source_query = "SELECT source, COUNT(*) as count FROM historical_events GROUP BY source"
            by_source = pd.read_sql_query(source_query, conn).to_dict('records')
            
            # Records by category
            category_query = "SELECT category, COUNT(*) as count FROM historical_events GROUP BY category"
            by_category = pd.read_sql_query(category_query, conn).to_dict('records')
            
            # Date range
            date_query = "SELECT MIN(date) as min_date, MAX(date) as max_date FROM historical_events"
            date_range = pd.read_sql_query(date_query, conn)
            
            # Dataset metadata
            meta_query = "SELECT * FROM dataset_metadata ORDER BY last_updated DESC"
            metadata = pd.read_sql_query(meta_query, conn).to_dict('records')
            
        return {
            'total_records': total_records,
            'by_source': by_source,
            'by_category': by_category,
            'date_range': {
                'min_date': date_range['min_date'].iloc[0],
                'max_date': date_range['max_date'].iloc[0]
            },
            'datasets': metadata,
            'last_updated': datetime.now().isoformat()
        }


# Convenience function for external use
def run_historical_etl(force_refresh: bool = False) -> Dict[str, int]:
    """Run the complete historical data ETL process"""
    etl = HistoricalDataETL()
    return etl.run_full_etl(force_refresh=force_refresh)


if __name__ == "__main__":
    # Run ETL if called directly
    import sys
    
    force = '--force' in sys.argv
    results = run_historical_etl(force_refresh=force)
    
    print("\n" + "="*50)
    print("HISTORICAL DATA ETL RESULTS")
    print("="*50)
    
    for dataset, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {dataset}: {count:,} records")
    
    print("="*50)
    print(f"Total datasets processed: {len(results)}")
    print(f"Total records: {sum(results.values()):,}")
