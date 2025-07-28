# Historical Analysis System

## Overview

The Historical Analysis System is a comprehensive module that integrates historical geopolitical and disaster data from verified international sources, performs advanced predictive modeling, and provides interactive visualization capabilities for risk assessment and forecasting.

## Key Features

### 🗄️ Historical Data Integration
- **UCDP (Uppsala Conflict Data Program)**: Armed conflict events from 1989-present
- **EM-DAT (Emergency Events Database)**: Natural disasters from 1900-present  
- **World Bank Indicators**: Economic and social indicators from 1960-present
- **ACLED**: Armed Conflict Location & Event Data
- **GDELT**: Global Database of Events, Language, and Tone

### 🤖 Advanced Predictive Modeling
- **Prophet**: Facebook's time series forecasting with seasonality
- **LSTM**: Deep learning for sequence prediction with attention mechanisms
- **ARIMA**: Statistical time series modeling with automatic parameter selection
- **Ensemble Methods**: Random Forest, Gradient Boosting, and meta-learning
- **Cross-validation**: Robust model evaluation and selection

### 🔍 Pattern Detection & Clustering
- **Unsupervised Learning**: K-means, DBSCAN, Gaussian Mixture Models
- **Anomaly Detection**: Isolation Forest, One-Class SVM, Local Outlier Factor
- **Dimensionality Reduction**: PCA, t-SNE, UMAP for visualization
- **Deep Autoencoders**: Feature extraction and anomaly detection
- **Temporal Pattern Analysis**: Seasonality, cycles, and trend detection

### 📊 Interactive Visualization
- **Real-time Dashboard**: Plotly Dash with Bootstrap components
- **Geospatial Maps**: Interactive world maps with risk overlays
- **Time Series Charts**: Historical trends and future predictions
- **Comparative Analysis**: Historical vs current event comparison
- **Pattern Visualization**: Cluster analysis and anomaly highlighting

## System Architecture

```
Historical Analysis System
├── Data Integration Layer
│   ├── UCDP API Integration
│   ├── EM-DAT Data Processing
│   ├── World Bank API
│   └── SQLite Database Storage
├── Analytics Engine
│   ├── Predictive Modeling
│   ├── Pattern Detection
│   └── Anomaly Detection
├── Visualization Layer
│   ├── Interactive Dashboard
│   ├── Geospatial Maps
│   └── Statistical Charts
└── Orchestration Layer
    ├── Data Pipeline Management
    ├── Model Training Coordination
    └── Automated Analysis Cycles
```

## Installation

### Prerequisites
- Python 3.8+
- 8GB+ RAM (recommended for large datasets)
- 10GB+ disk space for historical data

### Install Dependencies
```bash
# Install historical analysis requirements
pip install -r requirements_historical.txt

# Or install specific components
pip install prophet scikit-learn tensorflow plotly dash geopandas
```

### Optional GPU Support
```bash
# For GPU-accelerated deep learning (if NVIDIA GPU available)
pip install tensorflow-gpu
```

## Quick Start

### 1. Initialize the System
```bash
# Full system initialization with data update and analysis
python run_historical_analysis.py --mode full

# Initialize components only
python run_historical_analysis.py --mode init
```

### 2. Update Historical Data
```bash
# Update from all configured sources
python run_historical_analysis.py --mode update

# Force update even if recent data exists
python run_historical_analysis.py --mode update --force-update
```

### 3. Run Analysis
```bash
# Comprehensive analysis for last 2 years
python run_historical_analysis.py --mode analyze

# Custom date range and regions
python run_historical_analysis.py --mode analyze \
    --start-date 2020-01-01 \
    --end-date 2023-12-31 \
    --regions europe asia
```

### 4. Start Interactive Dashboard
```bash
# Start dashboard on default port 8051
python run_historical_analysis.py --mode dashboard

# Custom port and debug mode
python run_historical_analysis.py --mode dashboard --port 8080 --debug
```

### 5. Automated Analysis Cycle
```bash
# Run automated updates and analysis every 24 hours
python run_historical_analysis.py --mode auto

# Custom interval (every 6 hours)
python run_historical_analysis.py --mode auto --auto-interval 6
```

## Configuration Options

### Data Sources
```bash
--data-sources ucdp_ged emdat world_bank acled
```

### Prediction Models
```bash
--models prophet lstm arima ensemble
```

### Pattern Detection Methods
```bash
--pattern-methods kmeans dbscan isolation_forest gaussian_mixture
```

### Analysis Parameters
```bash
--forecast-days 30          # Forecast horizon
--confidence 0.8            # Confidence level
--update-frequency 24       # Update frequency in hours
```

## API Usage

### Programmatic Access
```python
import asyncio
from src.analytics.historical_analysis_orchestrator import HistoricalAnalysisOrchestrator

async def run_analysis():
    # Initialize orchestrator
    orchestrator = HistoricalAnalysisOrchestrator()
    
    # Initialize system
    await orchestrator.initialize_system()
    
    # Update data
    await orchestrator.update_historical_data()
    
    # Run analysis
    results = await orchestrator.run_comprehensive_analysis()
    
    # Get system status
    status = await orchestrator.get_system_status()
    
    return results, status

# Run analysis
results, status = asyncio.run(run_analysis())
```

### Individual Components
```python
# Historical Data Integration
from src.analytics.historical_data_integration import HistoricalDataIntegrator

integrator = HistoricalDataIntegrator()
await integrator.initialize_database()
events = await integrator.fetch_ucdp_data(start_year=2020)

# Predictive Modeling
from src.analytics.predictive_modeling import MultiVariatePredictor

predictor = MultiVariatePredictor()
prepared_data = predictor.prepare_multivariate_data(data)
prophet_results = predictor.train_prophet_model(prepared_data)
predictions = predictor.predict_future_risks(periods=30)

# Pattern Detection
from src.analytics.pattern_detection import AdvancedPatternDetector

detector = AdvancedPatternDetector()
processed_data = detector.preprocess_data(data)
clustering_results = detector.detect_clusters(processed_data)
anomalies = detector.detect_anomalies(processed_data)
```

## Dashboard Features

### Overview Tab
- Key metrics and statistics
- Event timeline visualization
- Risk distribution charts
- Global risk heatmap

### Temporal Analysis Tab
- Historical trend analysis
- Seasonal pattern detection
- Cyclical behavior identification
- Autocorrelation analysis

### Geospatial Analysis Tab
- Interactive world map with risk overlays
- Geographic event distribution
- Spatial clustering visualization
- Regional risk comparison

### Comparative Analysis Tab
- Historical vs current comparison
- Period-over-period analysis
- Regional risk benchmarking
- Trend deviation analysis

### Pattern Detection Tab
- Cluster visualization
- Anomaly highlighting
- Correlation matrix
- Pattern strength metrics

### Predictions Tab
- Future risk forecasts
- Model performance comparison
- Scenario analysis
- Confidence intervals

## Data Sources Details

### UCDP (Uppsala Conflict Data Program)
- **Coverage**: 1989-present
- **Content**: Armed conflicts, battle-related deaths, actors
- **Update Frequency**: Monthly
- **API**: https://ucdpapi.pcr.uu.se/

### EM-DAT (Emergency Events Database)
- **Coverage**: 1900-present
- **Content**: Natural disasters, technological disasters
- **Update Frequency**: Quarterly
- **Source**: Centre for Research on the Epidemiology of Disasters (CRED)

### World Bank Open Data
- **Coverage**: 1960-present
- **Content**: Economic indicators, development metrics
- **Update Frequency**: Annual/Quarterly
- **API**: https://api.worldbank.org/v2/

## Model Performance

### Typical Performance Metrics
- **Prophet**: MAPE 8-15%, good for seasonal patterns
- **LSTM**: RMSE 0.8-1.2, excellent for complex sequences
- **ARIMA**: MAE 0.6-1.0, reliable for stationary series
- **Ensemble**: Best overall performance, combines strengths

### Validation Approach
- Time series cross-validation
- Walk-forward validation
- Out-of-sample testing
- Multiple performance metrics (RMSE, MAE, MAPE, R²)

## Troubleshooting

### Common Issues

#### Memory Issues
```bash
# Reduce data size or enable sampling
python run_historical_analysis.py --mode analyze --sample-size 10000
```

#### API Rate Limits
```bash
# Increase delays between requests
python run_historical_analysis.py --mode update --rate-limit-delay 1.0
```

#### Model Training Failures
```bash
# Use subset of models
python run_historical_analysis.py --mode analyze --models prophet arima
```

#### Dashboard Not Loading
```bash
# Check port availability and try different port
python run_historical_analysis.py --mode dashboard --port 8052
```

### Logging
```bash
# Enable debug logging
python run_historical_analysis.py --mode full --debug

# Check log files
tail -f logs/historical_analysis.log
```

## Performance Optimization

### Parallel Processing
```bash
# Enable parallel processing (default)
python run_historical_analysis.py --mode analyze

# Disable for debugging
python run_historical_analysis.py --mode analyze --no-parallel
```

### Caching
```bash
# Enable result caching (default)
python run_historical_analysis.py --mode analyze

# Disable caching
python run_historical_analysis.py --mode analyze --no-cache
```

### GPU Acceleration
```python
# Check GPU availability
import tensorflow as tf
print("GPU Available:", tf.config.list_physical_devices('GPU'))
```

## Contributing

### Adding New Data Sources
1. Extend `DataSource` enum in `historical_data_integration.py`
2. Implement fetch method in `HistoricalDataIntegrator`
3. Add source configuration
4. Update database schema if needed

### Adding New Models
1. Implement model in `predictive_modeling.py`
2. Add training method to `MultiVariatePredictor`
3. Update configuration options
4. Add performance evaluation

### Adding New Visualizations
1. Create chart method in `historical_dashboard.py`
2. Add to appropriate dashboard tab
3. Register callback if interactive
4. Update layout structure

## License

This system is part of the RiskMap project and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Ensure all dependencies are installed
4. Verify data source availability

## Roadmap

### Planned Features
- Real-time data streaming integration
- Advanced deep learning models (Transformers, GNNs)
- Multi-language support for international data
- Mobile-responsive dashboard
- API endpoints for external integration
- Advanced scenario modeling
- Automated report generation

### Performance Improvements
- Distributed computing support
- Advanced caching strategies
- Incremental model updates
- Optimized data storage formats