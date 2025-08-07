# Historical Analysis System - Complete Documentation

## 🚀 Overview

The Historical Analysis System is a comprehensive, multi-dataset analytical platform that provides:

- **Multi-source data integration** (ACLED, GDELT, EIA, ENTSOG, UNHCR, FSI, WGI, FAO)
- **Unified data standardization** with common schema across all datasets
- **Interactive dashboard** with glassmorphic, modern UI design
- **Real-time alerting** based on configurable thresholds
- **Correlation analysis** between different geopolitical indicators
- **Automated ETL pipeline** with daily scheduling and error handling
- **Comprehensive test suite** with performance benchmarks

## 📋 System Components

### 1. ETL Pipeline (`historical_datasets_etl.py`)
- **Multi-dataset fetching**: ACLED conflicts, GDELT events, energy data, displacement stats
- **Robust caching**: Reduces API calls and improves performance
- **Data standardization**: All datasets normalized to unified schema
- **Error handling**: Graceful degradation with mock data fallbacks
- **SQLite integration**: Local database with optimized queries

### 2. API Service (`historical_analysis_service.py`)
- **RESTful endpoints**: Complete API for dashboard data, correlations, filters
- **Dashboard data**: Summary statistics, geographic data, time series
- **Alert system**: Configurable thresholds for violence, stability, energy, displacement
- **Correlation analysis**: Statistical analysis between indicators
- **ETL management**: Trigger updates, check status, view statistics

### 3. Modern Dashboard (`historical_analysis_modern.html`)
- **Glassmorphic design**: Matches project's cyan-gradient aesthetic
- **Interactive maps**: Leaflet-based geospatial visualization
- **Multiple tabs**: Events, Resources, Risks, Displacement, Alerts, Correlations
- **Real-time charts**: Plotly.js integration for dynamic visualization
- **Responsive design**: Mobile-friendly interface

### 4. Automation (`make_historical_data.py`)
- **Scheduled execution**: Daily ETL runs with configurable timing
- **Email notifications**: Success and failure alerts
- **Error tracking**: Consecutive failure monitoring
- **Configuration management**: JSON-based settings
- **Command line interface**: Manual execution and status checking

### 5. Test Suite (`test_historical_analysis.py`)
- **Unit tests**: ETL, API, data validation
- **Integration tests**: End-to-end workflow testing
- **Performance tests**: Large dataset handling and query optimization
- **Mock testing**: API response simulation
- **Data validation**: Schema compliance and data integrity

## 🛠 Installation & Setup

### 1. Install Dependencies
```powershell
# Install additional packages
pip install -r historical_analysis_requirements.txt; echo ""
```

### 2. Initialize Database
```powershell
# Create database and tables
python -c "from historical_datasets_etl import HistoricalDataETL; etl = HistoricalDataETL(); etl.init_database()"; echo ""
```

### 3. Initial Data Load
```powershell
# Run initial ETL to populate data
python make_historical_data.py --run-now --force-refresh; echo ""
```

### 4. Start Application
```powershell
# Launch the main application
python app_BUENA.py; echo ""
```

## 📊 Data Sources & Schema

### Unified Schema
All datasets are standardized to this common format:

| Column | Type | Description |
|--------|------|-------------|
| `iso3` | VARCHAR(3) | ISO 3166-1 alpha-3 country code |
| `country` | VARCHAR(100) | Country name |
| `date` | DATE | Event/observation date (YYYY-MM-DD) |
| `indicator` | VARCHAR(100) | Specific metric/indicator name |
| `value` | FLOAT | Numeric value |
| `source` | VARCHAR(50) | Data source (ACLED, GDELT, etc.) |
| `category` | VARCHAR(50) | High-level category |
| `subcategory` | VARCHAR(50) | Detailed subcategory |
| `latitude` | FLOAT | Geographic latitude |
| `longitude` | FLOAT | Geographic longitude |
| `description` | TEXT | Human-readable description |

---

**🎯 Complete system ready for deployment with automated ETL, modern dashboard, and comprehensive testing.**
