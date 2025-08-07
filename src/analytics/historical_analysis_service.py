"""
Historical Analysis Dashboard Backend
===================================

Flask API endpoints and data processing for the comprehensive historical analysis dashboard.
Supports multi-dataset analysis, correlation studies, and real-time alerting.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import jsonify, request
import json
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Import our ETL system
from .historical_datasets_etl import HistoricalDataETL

logger = logging.getLogger(__name__)

class HistoricalAnalysisService:
    """Service class for historical analysis operations"""
    
    def __init__(self, db_path: str = "./data/historical_analysis.db"):
        self.db_path = db_path
        self.etl = HistoricalDataETL()
        
        # Ensure database exists
        if not Path(db_path).exists():
            self.etl.init_database()
    
    def get_dashboard_data(self, 
                          date_from: Optional[str] = None,
                          date_to: Optional[str] = None,
                          countries: Optional[List[str]] = None,
                          categories: Optional[List[str]] = None) -> Dict:
        """Get comprehensive dashboard data with filters"""
        
        # Default date range (last 90 days)
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        if not date_from:
            date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            # Build dynamic query
            where_conditions = ["date >= ? AND date <= ?"]
            params = [date_from, date_to]
            
            if countries:
                placeholders = ','.join(['?' for _ in countries])
                where_conditions.append(f"iso3 IN ({placeholders})")
                params.extend(countries)
            
            if categories:
                placeholders = ','.join(['?' for _ in categories])
                where_conditions.append(f"category IN ({placeholders})")
                params.extend(categories)
            
            where_clause = " AND ".join(where_conditions)
            
            # Main data query
            query = f"""
                SELECT iso3, country, date, indicator, value, source, category, 
                       subcategory, latitude, longitude, description
                FROM historical_events 
                WHERE {where_clause}
                ORDER BY date DESC
            """
            
            main_data = pd.read_sql_query(query, conn, params=params)
            
            # Summary statistics
            stats = self._calculate_summary_stats(conn, where_clause, params)
            
            # Category breakdown
            category_breakdown = self._get_category_breakdown(conn, where_clause, params)
            
            # Geographic distribution
            geo_data = self._get_geographic_data(conn, where_clause, params)
            
            # Time series data
            time_series = self._get_time_series_data(conn, where_clause, params)
            
            # Alert conditions
            alerts = self._check_alert_conditions(conn)
            
        return {
            'summary_stats': stats,
            'category_breakdown': category_breakdown,
            'geographic_data': geo_data,
            'time_series': time_series,
            'recent_events': main_data.head(50).to_dict('records'),
            'alerts': alerts,
            'filters_applied': {
                'date_from': date_from,
                'date_to': date_to,
                'countries': countries or [],
                'categories': categories or []
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_summary_stats(self, conn, where_clause: str, params: List) -> Dict:
        """Calculate summary statistics for the dashboard"""
        
        # Total events
        total_query = f"SELECT COUNT(*) as total FROM historical_events WHERE {where_clause}"
        total_events = pd.read_sql_query(total_query, conn, params=params)['total'].iloc[0]
        
        # Events by category
        category_query = f"""
            SELECT category, COUNT(*) as count 
            FROM historical_events 
            WHERE {where_clause} 
            GROUP BY category
        """
        by_category = pd.read_sql_query(category_query, conn, params=params)
        
        # Recent activity (last 7 days)
        recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent_params = params + [recent_date]
        recent_query = f"""
            SELECT COUNT(*) as recent_count 
            FROM historical_events 
            WHERE {where_clause} AND date >= ?
        """
        recent_events = pd.read_sql_query(recent_query, conn, params=recent_params)['recent_count'].iloc[0]
        
        # Countries affected
        countries_query = f"""
            SELECT COUNT(DISTINCT iso3) as countries 
            FROM historical_events 
            WHERE {where_clause} AND iso3 != 'UNK'
        """
        countries_affected = pd.read_sql_query(countries_query, conn, params=params)['countries'].iloc[0]
        
        return {
            'total_events': int(total_events),
            'recent_events': int(recent_events),
            'countries_affected': int(countries_affected),
            'categories': by_category.to_dict('records'),
            'avg_events_per_day': round(total_events / max(1, (datetime.now() - datetime.strptime(params[0], '%Y-%m-%d')).days), 1)
        }
    
    def _get_category_breakdown(self, conn, where_clause: str, params: List) -> List[Dict]:
        """Get detailed breakdown by category and subcategory"""
        query = f"""
            SELECT category, subcategory, COUNT(*) as count,
                   AVG(value) as avg_value,
                   MIN(date) as earliest_date,
                   MAX(date) as latest_date
            FROM historical_events 
            WHERE {where_clause}
            GROUP BY category, subcategory
            ORDER BY count DESC
        """
        
        breakdown = pd.read_sql_query(query, conn, params=params)
        return breakdown.to_dict('records')
    
    def _get_geographic_data(self, conn, where_clause: str, params: List) -> List[Dict]:
        """Get geographic distribution of events"""
        query = f"""
            SELECT iso3, country, 
                   COUNT(*) as event_count,
                   AVG(latitude) as avg_lat,
                   AVG(longitude) as avg_lon,
                   category,
                   MAX(date) as last_activity
            FROM historical_events 
            WHERE {where_clause} AND iso3 != 'UNK'
            GROUP BY iso3, country, category
            ORDER BY event_count DESC
        """
        
        geo_data = pd.read_sql_query(query, conn, params=params)
        return geo_data.to_dict('records')
    
    def _get_time_series_data(self, conn, where_clause: str, params: List) -> Dict:
        """Get time series data for various indicators"""
        
        # Daily event counts
        daily_query = f"""
            SELECT DATE(date) as day, 
                   category,
                   COUNT(*) as count,
                   AVG(value) as avg_value
            FROM historical_events 
            WHERE {where_clause}
            GROUP BY DATE(date), category
            ORDER BY day
        """
        
        daily_data = pd.read_sql_query(daily_query, conn, params=params)
        
        # Format for frontend charting
        time_series = {}
        
        for category in daily_data['category'].unique():
            category_data = daily_data[daily_data['category'] == category]
            time_series[category] = {
                'dates': category_data['day'].tolist(),
                'counts': category_data['count'].tolist(),
                'values': category_data['avg_value'].tolist()
            }
        
        return time_series
    
    def _check_alert_conditions(self, conn) -> List[Dict]:
        """Check for alert conditions based on configurable thresholds"""
        alerts = []
        
        # Alert 1: High violence in last 7 days
        violence_query = """
            SELECT iso3, country, COUNT(*) as events
            FROM historical_events 
            WHERE category = 'conflict' 
            AND date >= date('now', '-7 days')
            GROUP BY iso3, country
            HAVING events >= 10
            ORDER BY events DESC
        """
        
        violence_alerts = pd.read_sql_query(violence_query, conn)
        for _, row in violence_alerts.iterrows():
            alerts.append({
                'type': 'violence_spike',
                'severity': 'high',
                'country': row['country'],
                'message': f"High violence activity: {row['events']} events in last 7 days",
                'timestamp': datetime.now().isoformat()
            })
        
        # Alert 2: Political stability decline
        stability_query = """
            SELECT iso3, country, value, date
            FROM historical_events 
            WHERE indicator = 'political_stability'
            AND date >= date('now', '-30 days')
            AND value < -1.5
            ORDER BY value ASC
        """
        
        stability_alerts = pd.read_sql_query(stability_query, conn)
        for _, row in stability_alerts.iterrows():
            alerts.append({
                'type': 'stability_decline',
                'severity': 'medium',
                'country': row['country'],
                'message': f"Political stability score: {row['value']:.2f} (concerning level)",
                'timestamp': row['date']
            })
        
        # Alert 3: Energy supply disruption
        energy_query = """
            SELECT iso3, country, indicator, value, date
            FROM historical_events 
            WHERE category = 'energy'
            AND date >= date('now', '-14 days')
            AND value < (SELECT AVG(value) * 0.7 FROM historical_events WHERE category = 'energy' AND indicator = value)
        """
        
        try:
            energy_alerts = pd.read_sql_query(energy_query, conn)
            for _, row in energy_alerts.iterrows():
                alerts.append({
                    'type': 'energy_disruption',
                    'severity': 'medium',
                    'country': row['country'],
                    'message': f"Energy supply below normal: {row['indicator']}",
                    'timestamp': row['date']
                })
        except:
            pass  # Skip if query fails
        
        # Alert 4: Large displacement movements
        displacement_query = """
            SELECT iso3, country, value, date
            FROM historical_events 
            WHERE category = 'displacement'
            AND date >= date('now', '-30 days')
            AND value > 100000
            ORDER BY value DESC
        """
        
        displacement_alerts = pd.read_sql_query(displacement_query, conn)
        for _, row in displacement_alerts.iterrows():
            alerts.append({
                'type': 'mass_displacement',
                'severity': 'high',
                'country': row['country'],
                'message': f"Large displacement: {int(row['value']):,} people",
                'timestamp': row['date']
            })
        
        return alerts[:20]  # Limit to 20 most recent alerts
    
    def get_correlation_analysis(self, indicators: List[str], time_window: int = 90) -> Dict:
        """Perform correlation analysis between different indicators"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get data for specified indicators
            placeholders = ','.join(['?' for _ in indicators])
            query = f"""
                SELECT date, indicator, iso3, country, value
                FROM historical_events 
                WHERE indicator IN ({placeholders})
                AND date >= ? AND date <= ?
                AND value IS NOT NULL
            """
            
            params = indicators + [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
            data = pd.read_sql_query(query, conn, params=params)
        
        if data.empty:
            return {'correlations': {}, 'message': 'No data available for correlation analysis'}
        
        # Pivot data for correlation analysis
        pivot_data = data.pivot_table(
            values='value',
            index=['date', 'iso3'],
            columns='indicator',
            aggfunc='mean'
        ).reset_index()
        
        # Calculate correlations
        correlation_matrix = pivot_data[indicators].corr()
        
        # Convert to dictionary format
        correlations = {}
        for i, indicator1 in enumerate(indicators):
            correlations[indicator1] = {}
            for j, indicator2 in enumerate(indicators):
                if pd.notna(correlation_matrix.iloc[i, j]):
                    correlations[indicator1][indicator2] = round(correlation_matrix.iloc[i, j], 3)
        
        # Find strongest correlations
        strong_correlations = []
        for indicator1 in indicators:
            for indicator2 in indicators:
                if indicator1 != indicator2:
                    corr_value = correlations.get(indicator1, {}).get(indicator2, 0)
                    if abs(corr_value) > 0.5:
                        strong_correlations.append({
                            'indicator1': indicator1,
                            'indicator2': indicator2,
                            'correlation': corr_value,
                            'strength': 'strong' if abs(corr_value) > 0.7 else 'moderate'
                        })
        
        return {
            'correlations': correlations,
            'strong_correlations': strong_correlations,
            'sample_size': len(pivot_data),
            'time_window': time_window,
            'analysis_date': datetime.now().isoformat()
        }
    
    def get_available_filters(self) -> Dict:
        """Get available filter options for the dashboard"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Available countries
            countries_query = """
                SELECT DISTINCT iso3, country 
                FROM historical_events 
                WHERE iso3 != 'UNK' AND country IS NOT NULL
                ORDER BY country
            """
            countries = pd.read_sql_query(countries_query, conn)
            
            # Available categories
            categories_query = """
                SELECT DISTINCT category, COUNT(*) as count
                FROM historical_events 
                GROUP BY category
                ORDER BY count DESC
            """
            categories = pd.read_sql_query(categories_query, conn)
            
            # Available indicators
            indicators_query = """
                SELECT DISTINCT indicator, COUNT(*) as count
                FROM historical_events 
                GROUP BY indicator
                ORDER BY count DESC
            """
            indicators = pd.read_sql_query(indicators_query, conn)
            
            # Date range
            date_range_query = """
                SELECT MIN(date) as min_date, MAX(date) as max_date
                FROM historical_events
            """
            date_range = pd.read_sql_query(date_range_query, conn)
        
        return {
            'countries': countries.to_dict('records'),
            'categories': categories.to_dict('records'),
            'indicators': indicators.to_dict('records'),
            'date_range': {
                'min_date': date_range['min_date'].iloc[0] if not date_range.empty else None,
                'max_date': date_range['max_date'].iloc[0] if not date_range.empty else None
            }
        }
    
    def trigger_etl_update(self, force_refresh: bool = False) -> Dict:
        """Trigger ETL update process"""
        try:
            logger.info("🔄 Triggering historical data ETL update...")
            results = self.etl.run_full_etl(force_refresh=force_refresh)
            
            return {
                'success': True,
                'results': results,
                'message': f'ETL completed successfully. Total records: {sum(results.values()):,}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ ETL update failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'ETL update failed',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_etl_status(self) -> Dict:
        """Get current ETL status and statistics"""
        return self.etl.get_statistics()


# Flask route functions
def register_historical_analysis_routes(app):
    """Register all historical analysis routes with the Flask app"""
    
    service = HistoricalAnalysisService()
    
    @app.route('/api/historical/dashboard', methods=['GET'])
    def get_historical_dashboard():
        """Get comprehensive historical dashboard data"""
        try:
            # Get query parameters
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            countries = request.args.getlist('countries')
            categories = request.args.getlist('categories')
            
            data = service.get_dashboard_data(
                date_from=date_from,
                date_to=date_to,
                countries=countries if countries else None,
                categories=categories if categories else None
            )
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"❌ Historical dashboard error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to load historical dashboard data'
            }), 500
    
    @app.route('/api/historical/correlation', methods=['POST'])
    def get_correlation_analysis():
        """Get correlation analysis between indicators"""
        try:
            data = request.get_json()
            indicators = data.get('indicators', [])
            time_window = data.get('time_window', 90)
            
            if not indicators:
                return jsonify({
                    'success': False,
                    'error': 'No indicators specified'
                }), 400
            
            analysis = service.get_correlation_analysis(indicators, time_window)
            
            return jsonify({
                'success': True,
                'data': analysis
            })
            
        except Exception as e:
            logger.error(f"❌ Correlation analysis error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to perform correlation analysis'
            }), 500
    
    @app.route('/api/historical/filters', methods=['GET'])
    def get_historical_filters():
        """Get available filter options"""
        try:
            filters = service.get_available_filters()
            
            return jsonify({
                'success': True,
                'data': filters
            })
            
        except Exception as e:
            logger.error(f"❌ Historical filters error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to load filter options'
            }), 500
    
    @app.route('/api/historical/etl/trigger', methods=['POST'])
    def trigger_historical_etl():
        """Trigger historical data ETL update"""
        try:
            data = request.get_json() or {}
            force_refresh = data.get('force_refresh', False)
            
            result = service.trigger_etl_update(force_refresh=force_refresh)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ ETL trigger error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to trigger ETL update'
            }), 500
    
    @app.route('/api/historical/etl/status', methods=['GET'])
    def get_historical_etl_status():
        """Get ETL status and statistics"""
        try:
            status = service.get_etl_status()
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            logger.error(f"❌ ETL status error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to get ETL status'
            }), 500
    
    logger.info("✅ Historical analysis routes registered")
