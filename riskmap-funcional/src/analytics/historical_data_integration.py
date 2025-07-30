"""
Historical Data Integration Module
Integrates and processes historical datasets from UCDP, EM-DAT, and other verified international sources
for comprehensive geopolitical and disaster analysis spanning the last 100 years.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import requests
import json
import sqlite3
from pathlib import Path
import zipfile
import io
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enumeration of supported historical data sources"""
    UCDP_GED = "ucdp_ged"  # Uppsala Conflict Data Program - Georeferenced Event Dataset
    UCDP_PRIO = "ucdp_prio"  # UCDP/PRIO Armed Conflict Dataset
    EMDAT = "emdat"  # Emergency Events Database
    ACLED = "acled"  # Armed Conflict Location & Event Data Project
    GDELT = "gdelt"  # Global Database of Events, Language, and Tone
    WORLD_BANK = "world_bank"  # World Bank Indicators
    WHO_HEALTH = "who_health"  # WHO Health Emergency Events
    FAOSTAT = "faostat"  # FAO Food Security Data
    UNHCR = "unhcr"  # UNHCR Refugee Data

@dataclass
class HistoricalEvent:
    """Standardized structure for historical events"""
    event_id: str
    source: DataSource
    event_type: str
    date: datetime
    location: Dict[str, Any]  # lat, lon, country, region
    actors: List[str]
    casualties: Optional[int]
    economic_impact: Optional[float]
    severity_score: float
    description: str
    metadata: Dict[str, Any]

class HistoricalDataIntegrator:
    """
    Main class for integrating and processing historical datasets
    from multiple verified international sources
    """
    
    def __init__(self, data_dir: str = "datasets/historical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "historical_events.db"
        self.source_configs = self._load_source_configurations()
        self.session = None
        
    def _load_source_configurations(self) -> Dict[str, Dict]:
        """Load configuration for each data source"""
        return {
            DataSource.UCDP_GED.value: {
                "url": "https://ucdpapi.pcr.uu.se/api/gedevents/23.1",
                "format": "json",
                "update_frequency": "monthly",
                "fields_mapping": {
                    "id": "event_id",
                    "date_start": "date",
                    "latitude": "lat",
                    "longitude": "lon",
                    "country": "country",
                    "deaths_a": "casualties_a",
                    "deaths_b": "casualties_b",
                    "deaths_civilians": "casualties_civilians",
                    "type_of_violence": "violence_type"
                }
            },
            DataSource.EMDAT.value: {
                "url": "https://www.emdat.be/emdat_db/",
                "format": "csv",
                "update_frequency": "quarterly",
                "fields_mapping": {
                    "DisNo": "event_id",
                    "Start Date": "date",
                    "Country": "country",
                    "Disaster Type": "disaster_type",
                    "Total Deaths": "casualties",
                    "Total Affected": "affected_population",
                    "Total Damages ('000 US$)": "economic_damage"
                }
            },
            DataSource.ACLED.value: {
                "url": "https://api.acleddata.com/acled/read",
                "format": "json",
                "update_frequency": "weekly",
                "fields_mapping": {
                    "data_date": "date",
                    "latitude": "lat",
                    "longitude": "lon",
                    "country": "country",
                    "event_type": "event_type",
                    "fatalities": "casualties",
                    "actor1": "actor_1",
                    "actor2": "actor_2"
                }
            },
            DataSource.WORLD_BANK.value: {
                "url": "https://api.worldbank.org/v2/country/all/indicator",
                "format": "json",
                "indicators": [
                    "NY.GDP.MKTP.CD",  # GDP
                    "SP.POP.TOTL",     # Population
                    "SL.UEM.TOTL.ZS",  # Unemployment
                    "FP.CPI.TOTL.ZG",  # Inflation
                    "MS.MIL.XPND.GD.ZS"  # Military expenditure
                ]
            }
        }
    
    async def initialize_database(self):
        """Initialize SQLite database for historical data storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create main events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_events (
                    event_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    event_type TEXT,
                    date DATE NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    country TEXT,
                    region TEXT,
                    actors TEXT,
                    casualties INTEGER,
                    economic_impact REAL,
                    severity_score REAL,
                    description TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create economic indicators table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economic_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country TEXT NOT NULL,
                    indicator_code TEXT NOT NULL,
                    indicator_name TEXT,
                    year INTEGER NOT NULL,
                    value REAL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(country, indicator_code, year)
                )
            """)
            
            # Create conflict actors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conflict_actors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_name TEXT NOT NULL,
                    actor_type TEXT,
                    country TEXT,
                    active_from DATE,
                    active_to DATE,
                    description TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(actor_name, country)
                )
            """)
            
            # Create disaster types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disaster_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disaster_type TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    description TEXT,
                    average_duration_days INTEGER,
                    typical_impact_scale TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(disaster_type, category)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON historical_events(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_country ON historical_events(country)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON historical_events(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON historical_events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_country_year ON economic_indicators(country, year)")
            
            conn.commit()
            conn.close()
            
            logger.info("Historical database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def fetch_ucdp_data(self, start_year: int = 1989, end_year: int = None) -> List[HistoricalEvent]:
        """
        Fetch data from Uppsala Conflict Data Program (UCDP)
        
        Args:
            start_year: Starting year for data collection
            end_year: Ending year (defaults to current year)
            
        Returns:
            List of standardized historical events
        """
        try:
            if end_year is None:
                end_year = datetime.now().year
            
            logger.info(f"Fetching UCDP data from {start_year} to {end_year}")
            
            events = []
            config = self.source_configs[DataSource.UCDP_GED.value]
            
            async with aiohttp.ClientSession() as session:
                for year in range(start_year, end_year + 1):
                    url = f"{config['url']}?StartDate={year}-01-01&EndDate={year}-12-31&pagesize=1000"
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for item in data.get('Result', []):
                                event = self._parse_ucdp_event(item)
                                if event:
                                    events.append(event)
                        else:
                            logger.warning(f"Failed to fetch UCDP data for year {year}: {response.status}")
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
            
            logger.info(f"Fetched {len(events)} UCDP events")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching UCDP data: {e}")
            return []
    
    def _parse_ucdp_event(self, item: Dict) -> Optional[HistoricalEvent]:
        """Parse UCDP event data into standardized format"""
        try:
            # Calculate total casualties
            casualties = 0
            for field in ['deaths_a', 'deaths_b', 'deaths_civilians', 'deaths_unknown']:
                if field in item and item[field]:
                    casualties += int(item[field])
            
            # Calculate severity score based on casualties and violence type
            severity_score = min(10.0, casualties / 100.0)
            if item.get('type_of_violence') == '1':  # State-based conflict
                severity_score *= 1.2
            elif item.get('type_of_violence') == '3':  # One-sided violence
                severity_score *= 1.1
            
            # Parse actors
            actors = []
            if item.get('side_a'):
                actors.append(item['side_a'])
            if item.get('side_b'):
                actors.append(item['side_b'])
            
            return HistoricalEvent(
                event_id=f"ucdp_{item['id']}",
                source=DataSource.UCDP_GED,
                event_type=f"conflict_type_{item.get('type_of_violence', 'unknown')}",
                date=datetime.strptime(item['date_start'], '%Y-%m-%d'),
                location={
                    'lat': float(item.get('latitude', 0)),
                    'lon': float(item.get('longitude', 0)),
                    'country': item.get('country', ''),
                    'region': item.get('region', '')
                },
                actors=actors,
                casualties=casualties,
                economic_impact=None,
                severity_score=severity_score,
                description=f"{item.get('where_description', '')} - {item.get('source_article', '')}",
                metadata={
                    'conflict_name': item.get('conflict_name'),
                    'dyad_name': item.get('dyad_name'),
                    'source_headline': item.get('source_headline'),
                    'source_date': item.get('source_date'),
                    'precision': item.get('where_prec')
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing UCDP event: {e}")
            return None
    
    async def fetch_emdat_data(self, start_year: int = 1900) -> List[HistoricalEvent]:
        """
        Fetch disaster data from EM-DAT (Emergency Events Database)
        Note: EM-DAT requires registration and API key for full access
        """
        try:
            logger.info(f"Fetching EM-DAT data from {start_year}")
            
            # For demonstration, we'll use a sample dataset structure
            # In production, this would connect to the actual EM-DAT API
            events = []
            
            # Sample disaster types and their characteristics
            disaster_types = {
                'Earthquake': {'avg_duration': 1, 'impact_scale': 'high'},
                'Flood': {'avg_duration': 7, 'impact_scale': 'medium'},
                'Drought': {'avg_duration': 365, 'impact_scale': 'high'},
                'Cyclone': {'avg_duration': 3, 'impact_scale': 'high'},
                'Wildfire': {'avg_duration': 14, 'impact_scale': 'medium'},
                'Volcanic activity': {'avg_duration': 30, 'impact_scale': 'high'},
                'Landslide': {'avg_duration': 1, 'impact_scale': 'medium'},
                'Extreme temperature': {'avg_duration': 7, 'impact_scale': 'medium'}
            }
            
            # Store disaster type information
            await self._store_disaster_types(disaster_types)
            
            logger.info("EM-DAT data structure prepared")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching EM-DAT data: {e}")
            return []
    
    async def fetch_world_bank_indicators(self, countries: List[str] = None, 
                                        start_year: int = 1960) -> Dict[str, List[Dict]]:
        """
        Fetch economic and social indicators from World Bank API
        
        Args:
            countries: List of country codes (ISO 3-letter)
            start_year: Starting year for data collection
            
        Returns:
            Dictionary of indicators by country
        """
        try:
            logger.info("Fetching World Bank indicators")
            
            if countries is None:
                countries = ['all']
            
            indicators_data = {}
            config = self.source_configs[DataSource.WORLD_BANK.value]
            
            async with aiohttp.ClientSession() as session:
                for indicator in config['indicators']:
                    for country in countries:
                        url = f"{config['url']}/{indicator}?country={country}&date={start_year}:{datetime.now().year}&format=json&per_page=1000"
                        
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if len(data) > 1 and data[1]:  # World Bank API returns metadata in first element
                                    for item in data[1]:
                                        if item['value'] is not None:
                                            country_code = item['country']['id']
                                            if country_code not in indicators_data:
                                                indicators_data[country_code] = []
                                            
                                            indicators_data[country_code].append({
                                                'indicator_code': indicator,
                                                'indicator_name': item['indicator']['value'],
                                                'year': int(item['date']),
                                                'value': float(item['value']),
                                                'country_name': item['country']['value']
                                            })
                            
                            await asyncio.sleep(0.1)  # Rate limiting
            
            logger.info(f"Fetched World Bank data for {len(indicators_data)} countries")
            return indicators_data
            
        except Exception as e:
            logger.error(f"Error fetching World Bank data: {e}")
            return {}
    
    async def store_historical_events(self, events: List[HistoricalEvent]):
        """Store historical events in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for event in events:
                cursor.execute("""
                    INSERT OR REPLACE INTO historical_events 
                    (event_id, source, event_type, date, latitude, longitude, country, region,
                     actors, casualties, economic_impact, severity_score, description, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.source.value,
                    event.event_type,
                    event.date.isoformat(),
                    event.location.get('lat'),
                    event.location.get('lon'),
                    event.location.get('country'),
                    event.location.get('region'),
                    json.dumps(event.actors),
                    event.casualties,
                    event.economic_impact,
                    event.severity_score,
                    event.description,
                    json.dumps(event.metadata)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored {len(events)} historical events")
            
        except Exception as e:
            logger.error(f"Error storing historical events: {e}")
            raise
    
    async def store_economic_indicators(self, indicators_data: Dict[str, List[Dict]]):
        """Store economic indicators in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for country_code, indicators in indicators_data.items():
                for indicator in indicators:
                    cursor.execute("""
                        INSERT OR REPLACE INTO economic_indicators 
                        (country, indicator_code, indicator_name, year, value, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        country_code,
                        indicator['indicator_code'],
                        indicator['indicator_name'],
                        indicator['year'],
                        indicator['value'],
                        DataSource.WORLD_BANK.value
                    ))
            
            conn.commit()
            conn.close()
            
            total_indicators = sum(len(indicators) for indicators in indicators_data.values())
            logger.info(f"Stored {total_indicators} economic indicators")
            
        except Exception as e:
            logger.error(f"Error storing economic indicators: {e}")
            raise
    
    async def _store_disaster_types(self, disaster_types: Dict[str, Dict]):
        """Store disaster type information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for disaster_type, info in disaster_types.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO disaster_types 
                    (disaster_type, category, average_duration_days, typical_impact_scale)
                    VALUES (?, ?, ?, ?)
                """, (
                    disaster_type,
                    'natural_disaster',
                    info['avg_duration'],
                    info['impact_scale']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing disaster types: {e}")
    
    async def get_historical_events(self, start_date: datetime = None, end_date: datetime = None,
                                  country: str = None, event_type: str = None,
                                  source: DataSource = None) -> pd.DataFrame:
        """
        Retrieve historical events with filtering options
        
        Args:
            start_date: Filter events from this date
            end_date: Filter events until this date
            country: Filter by country
            event_type: Filter by event type
            source: Filter by data source
            
        Returns:
            DataFrame with filtered historical events
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM historical_events WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date.isoformat())
            
            if country:
                query += " AND country = ?"
                params.append(country)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if source:
                query += " AND source = ?"
                params.append(source.value)
            
            query += " ORDER BY date DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse JSON fields
            if not df.empty:
                df['actors'] = df['actors'].apply(lambda x: json.loads(x) if x else [])
                df['metadata'] = df['metadata'].apply(lambda x: json.loads(x) if x else {})
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving historical events: {e}")
            return pd.DataFrame()
    
    async def get_economic_indicators(self, countries: List[str] = None, 
                                    indicators: List[str] = None,
                                    start_year: int = None, end_year: int = None) -> pd.DataFrame:
        """
        Retrieve economic indicators with filtering options
        
        Args:
            countries: List of country codes to filter
            indicators: List of indicator codes to filter
            start_year: Filter from this year
            end_year: Filter until this year
            
        Returns:
            DataFrame with economic indicators
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM economic_indicators WHERE 1=1"
            params = []
            
            if countries:
                placeholders = ','.join(['?' for _ in countries])
                query += f" AND country IN ({placeholders})"
                params.extend(countries)
            
            if indicators:
                placeholders = ','.join(['?' for _ in indicators])
                query += f" AND indicator_code IN ({placeholders})"
                params.extend(indicators)
            
            if start_year:
                query += " AND year >= ?"
                params.append(start_year)
            
            if end_year:
                query += " AND year <= ?"
                params.append(end_year)
            
            query += " ORDER BY country, indicator_code, year"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving economic indicators: {e}")
            return pd.DataFrame()
    
    async def update_all_sources(self):
        """Update data from all configured sources"""
        try:
            logger.info("Starting comprehensive data update from all sources")
            
            # Initialize database
            await self.initialize_database()
            
            # Fetch UCDP conflict data
            ucdp_events = await self.fetch_ucdp_data(start_year=1989)
            if ucdp_events:
                await self.store_historical_events(ucdp_events)
            
            # Fetch EM-DAT disaster data
            emdat_events = await self.fetch_emdat_data(start_year=1900)
            if emdat_events:
                await self.store_historical_events(emdat_events)
            
            # Fetch World Bank economic indicators
            wb_indicators = await self.fetch_world_bank_indicators(start_year=1960)
            if wb_indicators:
                await self.store_economic_indicators(wb_indicators)
            
            logger.info("Historical data update completed successfully")
            
        except Exception as e:
            logger.error(f"Error updating historical data sources: {e}")
            raise
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of stored historical data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            summary = {}
            
            # Events summary
            events_query = """
                SELECT 
                    source,
                    COUNT(*) as event_count,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    AVG(severity_score) as avg_severity,
                    SUM(CASE WHEN casualties IS NOT NULL THEN casualties ELSE 0 END) as total_casualties
                FROM historical_events 
                GROUP BY source
            """
            
            events_df = pd.read_sql_query(events_query, conn)
            summary['events_by_source'] = events_df.to_dict('records')
            
            # Economic indicators summary
            indicators_query = """
                SELECT 
                    indicator_code,
                    indicator_name,
                    COUNT(DISTINCT country) as countries_count,
                    COUNT(*) as data_points,
                    MIN(year) as earliest_year,
                    MAX(year) as latest_year
                FROM economic_indicators 
                GROUP BY indicator_code, indicator_name
            """
            
            indicators_df = pd.read_sql_query(indicators_query, conn)
            summary['economic_indicators'] = indicators_df.to_dict('records')
            
            # Overall statistics
            total_events = pd.read_sql_query("SELECT COUNT(*) as count FROM historical_events", conn).iloc[0]['count']
            total_indicators = pd.read_sql_query("SELECT COUNT(*) as count FROM economic_indicators", conn).iloc[0]['count']
            
            summary['overall'] = {
                'total_events': total_events,
                'total_economic_indicators': total_indicators,
                'data_sources': len(events_df),
                'last_updated': datetime.now().isoformat()
            }
            
            conn.close()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating data summary: {e}")
            return {}