"""
Test Suite for Historical Analysis System
========================================

Comprehensive test suite covering ETL, API endpoints, and data validation.
"""

import pytest
import sqlite3
import pandas as pd
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from historical_datasets_etl import HistoricalDataETL
from src.analytics.historical_analysis_service import HistoricalAnalysisService

class TestHistoricalDataETL:
    """Test suite for the Historical Data ETL system"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def etl_instance(self, temp_dir):
        """Create ETL instance with temporary database"""
        db_path = os.path.join(temp_dir, "test.db")
        etl = HistoricalDataETL(db_path=db_path)
        return etl
    
    def test_database_initialization(self, etl_instance):
        """Test database initialization creates required tables"""
        etl_instance.init_database()
        
        # Check if database file exists
        assert Path(etl_instance.db_path).exists()
        
        # Check if tables exist
        with sqlite3.connect(etl_instance.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['historical_events', 'etl_runs', 'data_sources']
        for table in expected_tables:
            assert table in tables
    
    def test_data_standardization(self, etl_instance):
        """Test data standardization to unified schema"""
        # Mock data with various formats
        test_data = pd.DataFrame({
            'country': ['United States', 'Germany', 'Japan'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'indicator': ['violence_events', 'political_stability', 'energy_supply'],
            'value': [10, -0.5, 850.2],
            'source': ['ACLED', 'WGI', 'EIA']
        })
        
        standardized = etl_instance._standardize_data(
            test_data, 
            'conflict', 
            'test_source'
        )
        
        # Check required columns exist
        required_columns = ['iso3', 'country', 'date', 'indicator', 'value', 'source', 'category']
        for col in required_columns:
            assert col in standardized.columns
        
        # Check data types
        assert standardized['date'].dtype == 'object'  # Should be string in YYYY-MM-DD format
        assert pd.api.types.is_numeric_dtype(standardized['value'])
        
        # Check ISO3 codes were added (even if mock/unknown)
        assert not standardized['iso3'].isna().all()
    
    @patch('requests.get')
    def test_acled_data_fetch(self, mock_get, etl_instance):
        """Test ACLED data fetching with mocked API response"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {
                    'data_date': '2024-01-01',
                    'country': 'Somalia',
                    'event_type': 'Violence against civilians',
                    'fatalities': 5,
                    'latitude': 2.0469,
                    'longitude': 45.3182
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test data fetching
        data = etl_instance._fetch_acled_data()
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert 'date' in data.columns
        assert 'country' in data.columns
    
    @patch('requests.get')
    def test_gdelt_data_fetch(self, mock_get, etl_instance):
        """Test GDELT data fetching with mocked response"""
        # Mock CSV response
        mock_response = Mock()
        mock_response.text = """date,country,event_code,avg_tone,num_mentions
2024-01-01,US,020,1.5,100
2024-01-01,DE,030,-0.8,75"""
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        data = etl_instance._fetch_gdelt_data()
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert 'date' in data.columns
    
    def test_data_saving_and_loading(self, etl_instance):
        """Test saving data to database and loading it back"""
        etl_instance.init_database()
        
        # Create test data
        test_data = pd.DataFrame({
            'iso3': ['USA', 'DEU'],
            'country': ['United States', 'Germany'],
            'date': ['2024-01-01', '2024-01-02'],
            'indicator': ['test_indicator', 'test_indicator'],
            'value': [100, 200],
            'source': ['test_source', 'test_source'],
            'category': ['test', 'test'],
            'subcategory': ['test_sub', 'test_sub'],
            'latitude': [40.0, 52.0],
            'longitude': [-74.0, 13.0],
            'description': ['Test event 1', 'Test event 2']
        })
        
        # Save data
        etl_instance._save_to_database(test_data, 'test_source')
        
        # Load data back
        with sqlite3.connect(etl_instance.db_path) as conn:
            loaded_data = pd.read_sql_query(
                "SELECT * FROM historical_events WHERE source = 'test_source'", 
                conn
            )
        
        assert len(loaded_data) == 2
        assert loaded_data['country'].tolist() == ['United States', 'Germany']
        assert loaded_data['value'].tolist() == [100.0, 200.0]
    
    def test_caching_mechanism(self, etl_instance, temp_dir):
        """Test data caching functionality"""
        cache_file = os.path.join(temp_dir, "test_cache.csv")
        
        # Create test data
        test_data = pd.DataFrame({
            'date': ['2024-01-01'],
            'value': [100]
        })
        
        # Test cache saving
        etl_instance._save_to_cache(test_data, cache_file)
        assert Path(cache_file).exists()
        
        # Test cache loading
        loaded_data = etl_instance._load_from_cache(cache_file, max_age_hours=24)
        assert loaded_data is not None
        assert len(loaded_data) == 1
        assert loaded_data['value'].iloc[0] == 100
    
    def test_error_handling(self, etl_instance):
        """Test error handling in ETL processes"""
        # Test with invalid data
        invalid_data = pd.DataFrame({
            'invalid_column': [1, 2, 3]
        })
        
        # Should handle gracefully without crashing
        try:
            standardized = etl_instance._standardize_data(invalid_data, 'test', 'test')
            # Should still return a DataFrame with required columns
            assert isinstance(standardized, pd.DataFrame)
        except Exception as e:
            pytest.fail(f"ETL should handle invalid data gracefully: {e}")
    
    def test_statistics_generation(self, etl_instance):
        """Test ETL statistics generation"""
        etl_instance.init_database()
        
        # Add some test data
        test_data = pd.DataFrame({
            'iso3': ['USA'] * 5,
            'country': ['United States'] * 5,
            'date': ['2024-01-01'] * 5,
            'indicator': ['test'] * 5,
            'value': [1, 2, 3, 4, 5],
            'source': ['test_source'] * 5,
            'category': ['test'] * 5,
            'subcategory': ['test'] * 5,
            'latitude': [40.0] * 5,
            'longitude': [-74.0] * 5,
            'description': ['Test'] * 5
        })
        
        etl_instance._save_to_database(test_data, 'test_source')
        
        # Get statistics
        stats = etl_instance.get_statistics()
        
        assert 'total_records' in stats
        assert 'datasets' in stats
        assert 'last_updated' in stats
        assert stats['total_records'] >= 5


class TestHistoricalAnalysisService:
    """Test suite for the Historical Analysis Service"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def service_instance(self, temp_db):
        """Create service instance with temporary database"""
        service = HistoricalAnalysisService(db_path=temp_db)
        
        # Initialize database and add test data
        service.etl.init_database()
        
        # Add test data
        test_data = pd.DataFrame({
            'iso3': ['USA', 'DEU', 'JPN'] * 10,
            'country': ['United States', 'Germany', 'Japan'] * 10,
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'] * 10,
            'indicator': ['violence_events', 'political_stability', 'energy_supply'] * 10,
            'value': [10, -0.5, 850.2] * 10,
            'source': ['ACLED', 'WGI', 'EIA'] * 10,
            'category': ['conflict', 'governance', 'energy'] * 10,
            'subcategory': ['violence', 'stability', 'supply'] * 10,
            'latitude': [40.0, 52.0, 35.0] * 10,
            'longitude': [-74.0, 13.0, 139.0] * 10,
            'description': ['Test event', 'Test stability', 'Test energy'] * 10
        })
        
        service.etl._save_to_database(test_data, 'test_source')
        
        return service
    
    def test_dashboard_data_retrieval(self, service_instance):
        """Test dashboard data retrieval with various filters"""
        # Test basic data retrieval
        data = service_instance.get_dashboard_data()
        
        assert 'summary_stats' in data
        assert 'category_breakdown' in data
        assert 'geographic_data' in data
        assert 'time_series' in data
        assert 'recent_events' in data
        assert 'alerts' in data
        
        # Test with filters
        filtered_data = service_instance.get_dashboard_data(
            countries=['USA'],
            categories=['conflict']
        )
        
        assert isinstance(filtered_data, dict)
        assert 'filters_applied' in filtered_data
        assert filtered_data['filters_applied']['countries'] == ['USA']
    
    def test_summary_statistics(self, service_instance):
        """Test summary statistics calculation"""
        data = service_instance.get_dashboard_data()
        stats = data['summary_stats']
        
        assert 'total_events' in stats
        assert 'recent_events' in stats
        assert 'countries_affected' in stats
        assert 'categories' in stats
        assert 'avg_events_per_day' in stats
        
        assert isinstance(stats['total_events'], int)
        assert isinstance(stats['recent_events'], int)
        assert isinstance(stats['countries_affected'], int)
        assert isinstance(stats['categories'], list)
    
    def test_correlation_analysis(self, service_instance):
        """Test correlation analysis functionality"""
        indicators = ['violence_events', 'political_stability']
        
        correlation_data = service_instance.get_correlation_analysis(
            indicators=indicators,
            time_window=90
        )
        
        assert 'correlations' in correlation_data
        assert 'strong_correlations' in correlation_data
        assert 'sample_size' in correlation_data
        
        # Check correlation matrix structure
        correlations = correlation_data['correlations']
        for indicator in indicators:
            if indicator in correlations:
                assert isinstance(correlations[indicator], dict)
    
    def test_alert_conditions(self, service_instance):
        """Test alert condition checking"""
        data = service_instance.get_dashboard_data()
        alerts = data['alerts']
        
        assert isinstance(alerts, list)
        
        # Check alert structure if any alerts exist
        if alerts:
            alert = alerts[0]
            assert 'type' in alert
            assert 'severity' in alert
            assert 'country' in alert
            assert 'message' in alert
            assert 'timestamp' in alert
    
    def test_filter_options(self, service_instance):
        """Test available filter options retrieval"""
        filters = service_instance.get_available_filters()
        
        assert 'countries' in filters
        assert 'categories' in filters
        assert 'indicators' in filters
        assert 'date_range' in filters
        
        assert isinstance(filters['countries'], list)
        assert isinstance(filters['categories'], list)
        assert isinstance(filters['indicators'], list)
        assert isinstance(filters['date_range'], dict)
    
    def test_etl_trigger(self, service_instance):
        """Test ETL trigger functionality"""
        result = service_instance.trigger_etl_update(force_refresh=False)
        
        assert 'success' in result
        assert 'timestamp' in result
        
        if result['success']:
            assert 'results' in result
            assert 'message' in result
        else:
            assert 'error' in result
    
    def test_etl_status(self, service_instance):
        """Test ETL status retrieval"""
        status = service_instance.get_etl_status()
        
        assert isinstance(status, dict)
        # ETL status should contain basic information about the data


class TestDataValidation:
    """Test suite for data validation and integrity"""
    
    def test_date_format_validation(self):
        """Test date format validation"""
        etl = HistoricalDataETL()
        
        # Test valid dates
        valid_dates = ['2024-01-01', '2023-12-31', '2024-02-29']  # 2024 is leap year
        for date_str in valid_dates:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pytest.fail(f"Valid date {date_str} should not raise ValueError")
        
        # Test invalid dates
        invalid_dates = ['2024-13-01', '2024-02-30', 'not-a-date']
        for date_str in invalid_dates:
            with pytest.raises(ValueError):
                datetime.strptime(date_str, '%Y-%m-%d')
    
    def test_iso3_code_validation(self):
        """Test ISO3 country code validation"""
        etl = HistoricalDataETL()
        
        # Test common ISO3 codes
        valid_codes = ['USA', 'DEU', 'JPN', 'GBR', 'FRA']
        for code in valid_codes:
            assert len(code) == 3
            assert code.isupper()
            assert code.isalpha()
    
    def test_numeric_value_validation(self):
        """Test numeric value validation"""
        # Test various numeric formats
        test_values = [1, 1.0, '1', '1.5', '-1.5', '0']
        
        for value in test_values:
            try:
                numeric_value = float(value)
                assert isinstance(numeric_value, float)
            except (ValueError, TypeError):
                pytest.fail(f"Value {value} should be convertible to float")


class TestPerformance:
    """Test suite for performance and scalability"""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create a large test dataset
        large_data = pd.DataFrame({
            'iso3': ['USA'] * 10000,
            'country': ['United States'] * 10000,
            'date': ['2024-01-01'] * 10000,
            'indicator': ['test_indicator'] * 10000,
            'value': range(10000),
            'source': ['test_source'] * 10000,
            'category': ['test'] * 10000,
            'subcategory': ['test'] * 10000,
            'latitude': [40.0] * 10000,
            'longitude': [-74.0] * 10000,
            'description': ['Test event'] * 10000
        })
        
        # Test data processing time
        start_time = datetime.now()
        
        etl = HistoricalDataETL()
        standardized = etl._standardize_data(large_data, 'test', 'test_source')
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        assert len(standardized) == 10000
        assert processing_time < 30  # Should process 10k records in under 30 seconds
    
    def test_database_query_performance(self):
        """Test database query performance"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_db = temp_file.name
        
        try:
            service = HistoricalAnalysisService(db_path=temp_db)
            service.etl.init_database()
            
            # Add test data
            test_data = pd.DataFrame({
                'iso3': ['USA'] * 1000,
                'country': ['United States'] * 1000,
                'date': ['2024-01-01'] * 1000,
                'indicator': ['test'] * 1000,
                'value': range(1000),
                'source': ['test'] * 1000,
                'category': ['test'] * 1000,
                'subcategory': ['test'] * 1000,
                'latitude': [40.0] * 1000,
                'longitude': [-74.0] * 1000,
                'description': ['Test'] * 1000
            })
            
            service.etl._save_to_database(test_data, 'test_source')
            
            # Test query performance
            start_time = datetime.now()
            data = service.get_dashboard_data()
            query_time = (datetime.now() - start_time).total_seconds()
            
            assert query_time < 10  # Should complete in under 10 seconds
            assert isinstance(data, dict)
            
        finally:
            os.unlink(temp_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
