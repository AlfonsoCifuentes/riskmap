# Enhanced Multivariate Historical Analysis System

## Overview

The Enhanced Multivariate Historical Analysis System is a comprehensive platform that integrates and analyzes relationships between energy sources, oil prices/production, climate variables, public policies, disease outbreaks, resource availability, and their impact on geopolitical conflict risk. This system provides both historical analysis and real-time monitoring capabilities with advanced predictive modeling.

## Key Features

### 🔗 **Multivariate Relational Analysis**
- **Cross-Domain Integration**: Energy, climate, political, health, and resource variables
- **Correlation Detection**: Pearson, Spearman, Kendall, and distance correlations
- **Causality Analysis**: Granger causality testing with optimal lag detection
- **Threshold Effects**: Non-linear relationship detection and regime switching
- **Network Analysis**: Variable relationship networks with centrality measures

### 📊 **Comprehensive Data Integration**
- **Energy Data**: EIA Open Data, BP Statistical Review, World Bank Energy Data
- **Climate Data**: NOAA, NASA Earthdata, EM-DAT extreme events
- **Political Data**: World Bank Indicators, V-Dem, Freedom House
- **Health Data**: WHO, FAO disease outbreaks and food security
- **Resource Data**: World Bank, FAO, Global Forest Watch
- **Conflict Data**: UCDP, ACLED, GDELT

### 🤖 **Advanced Analytics**
- **Supervised Learning**: Random Forest, Gradient Boosting, Neural Networks
- **Unsupervised Learning**: K-means, DBSCAN, Gaussian Mixture Models
- **Time Series Models**: Prophet, LSTM, ARIMA with multivariate extensions
- **Dimensionality Reduction**: PCA, t-SNE, UMAP for visualization
- **Feature Importance**: Multiple methods with aggregated rankings

### 📈 **Interactive Visualization**
- **Multivariate Dashboard**: Comprehensive relationship exploration
- **Correlation Matrices**: Interactive heatmaps with significance testing
- **Network Graphs**: Variable relationship networks with community detection
- **Time Series Analysis**: Cross-correlation and lagged relationships
- **Threshold Visualization**: Regime switching and effect size analysis

### ⚡ **Real-Time Capabilities**
- **Streaming Analysis**: Real-time pattern detection and alerts
- **Batch Processing**: Automated analysis cycles with configurable intervals
- **Early Warning**: Threshold-based alert systems
- **Comparative Analysis**: Current vs historical pattern comparison

## System Architecture

```
Enhanced Multivariate Analysis System
├── Data Integration Layer
│   ├── Energy Sources (EIA, BP, World Bank)
│   ├── Climate Sources (NOAA, NASA, EM-DAT)
│   ├── Political Sources (V-Dem, Freedom House, WB)
│   ├── Health Sources (WHO, FAO)
│   ├── Resource Sources (World Bank, GFW)
│   └── Unified Data Storage (SQLite/PostgreSQL)
├── Analytics Engine
│   ├── Correlation Analysis
│   ├── Causality Testing
│   ├── Feature Importance
│   ├── Threshold Detection
│   ├── Network Analysis
│   └── Predictive Modeling
├── Visualization Layer
│   ├── Multivariate Dashboard
│   ├── Interactive Charts
│   ├── Network Graphs
│   └── Real-time Monitoring
└── Orchestration Layer
    ├── Data Pipeline Management
    ├── Analysis Coordination
    ├── Real-time Processing
    └── Automated Reporting
```

## Installation

### Prerequisites
- Python 3.8+
- 16GB+ RAM (recommended for large multivariate datasets)
- 20GB+ disk space for historical data
- Optional: GPU for deep learning acceleration

### Install Enhanced Dependencies
```bash
# Install enhanced multivariate requirements
pip install -r requirements_enhanced_historical.txt

# Or install core components
pip install prophet scikit-learn tensorflow plotly dash networkx statsmodels
```

### Optional Components
```bash
# Advanced time series analysis
pip install sktime darts kats

# GPU acceleration (if NVIDIA GPU available)
pip install tensorflow-gpu cupy

# Big data processing
pip install pyspark dask ray

# Advanced visualization
pip install altair holoviews

# Financial data sources
pip install yfinance alpha_vantage fredapi
```

## Quick Start

### 1. Initialize Enhanced System
```bash
# Full enhanced system initialization
python run_enhanced_historical_analysis.py --mode full

# Initialize with specific data sources
python run_enhanced_historical_analysis.py --mode init \
    --energy-sources eia_oil world_bank_energy \
    --climate-sources noaa_climate nasa_earthdata
```

### 2. Update Multivariate Data
```bash
# Update all data sources
python run_enhanced_historical_analysis.py --mode update

# Force update with custom parameters
python run_enhanced_historical_analysis.py --mode update \
    --force-update \
    --significance-level 0.01 \
    --min-correlation 0.2
```

### 3. Run Comprehensive Analysis
```bash
# Full multivariate analysis
python run_enhanced_historical_analysis.py --mode multivariate

# Custom analysis period and target
python run_enhanced_historical_analysis.py --mode multivariate \
    --start-date 2020-01-01 \
    --end-date 2023-12-31 \
    --target-variable conflict_risk \
    --max-lags 24
```

### 4. Start Interactive Dashboards
```bash
# Multivariate relationship dashboard
python run_enhanced_historical_analysis.py --mode multivariate-dashboard

# Base historical dashboard
python run_enhanced_historical_analysis.py --mode dashboard

# Both dashboards with custom ports
python run_enhanced_historical_analysis.py --mode multivariate-dashboard \
    --multivariate-port 8052 --port 8051
```

### 5. Real-Time Analysis
```bash
# Run real-time analysis
python run_enhanced_historical_analysis.py --mode real-time

# Automated cycle with real-time monitoring
python run_enhanced_historical_analysis.py --mode auto \
    --auto-interval 6 \
    --batch-interval 6
```

## Configuration Options

### Data Sources Configuration
```bash
# Energy data sources
--energy-sources eia_oil eia_production world_bank_energy

# Climate data sources  
--climate-sources noaa_climate nasa_earthdata

# Political data sources
--political-sources vdem freedom_house world_bank_governance

# Health data sources
--health-sources who_health fao_food

# Resource data sources
--resource-sources world_bank_resources global_forest_watch
```

### Analysis Parameters
```bash
# Correlation analysis
--correlation-methods pearson spearman kendall
--min-correlation 0.1
--significance-level 0.05

# Causality analysis
--max-lags 12

# Network analysis
--network-threshold 0.3

# Prediction models
--models prophet lstm arima ensemble
--forecast-days 30
--confidence 0.8
```

### Processing Configuration
```bash
# Parallel processing
--no-parallel  # Disable parallel processing

# Real-time analysis
--no-real-time  # Disable real-time capabilities

# Update frequencies
--update-frequency 24  # Hours between data updates
--batch-interval 6     # Hours between batch processing
```

## API Usage

### Programmatic Access
```python
import asyncio
from src.analytics.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator

async def run_multivariate_analysis():
    # Initialize enhanced orchestrator
    orchestrator = EnhancedHistoricalOrchestrator()
    
    # Initialize system
    await orchestrator.initialize_enhanced_system()
    
    # Update multivariate data
    await orchestrator.update_multivariate_data()
    
    # Run comprehensive analysis
    results = await orchestrator.run_comprehensive_multivariate_analysis(
        target_variable='conflict_risk'
    )
    
    # Get system status
    status = await orchestrator.get_enhanced_system_status()
    
    return results, status

# Run analysis
results, status = asyncio.run(run_multivariate_analysis())
```

### Individual Components
```python
# Multivariate Data Integration
from src.analytics.multivariate_relational_analysis import MultivariateDataIntegrator

integrator = MultivariateDataIntegrator()
integrated_data = await integrator.integrate_all_data(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# Relationship Analysis
from src.analytics.correlation_relationship_analyzer import CorrelationRelationshipAnalyzer

analyzer = CorrelationRelationshipAnalyzer()
correlations = analyzer.compute_comprehensive_correlations(data, 'conflict_risk')
causality = analyzer.analyze_granger_causality(data, 'conflict_risk')
importance = analyzer.analyze_feature_importance(data, 'conflict_risk')
thresholds = analyzer.detect_threshold_effects(data, 'conflict_risk')
network = analyzer.build_relationship_network()

# Multivariate Dashboard
from src.visualization.multivariate_dashboard import MultivariateRelationshipDashboard

dashboard = MultivariateRelationshipDashboard(
    data_integrator=integrator,
    relationship_analyzer=analyzer,
    port=8052
)
dashboard.run_dashboard()
```

## Dashboard Features

### Multivariate Relationship Dashboard (Port 8052)

#### Overview Tab
- Relationship summary statistics
- Key correlation heatmap
- Variable importance overview
- Time series comparison

#### Correlation Matrix Tab
- Full correlation matrix with multiple methods
- Significance testing visualization
- Partial correlation analysis
- Nonlinear association detection

#### Time Series Analysis Tab
- Multivariate time series plots
- Cross-correlation analysis
- Lagged relationship detection
- Rolling correlation evolution

#### Causality Network Tab
- Interactive relationship network
- Centrality measures visualization
- Community detection
- Influence path analysis

#### Feature Importance Tab
- Multiple importance method comparison
- Importance by variable category
- Feature stability analysis
- Permutation importance

#### Threshold Effects Tab
- Threshold detection overview
- Regime switching visualization
- Effect size analysis
- Distribution analysis

#### Interactive Explorer Tab
- Custom variable selection
- Multi-dimensional scatter plots
- Variable distribution analysis
- Correlation evolution over time

## Data Sources Details

### Energy Data Sources
- **EIA (Energy Information Administration)**
  - Oil prices and production data
  - Energy consumption statistics
  - Renewable energy metrics
  - Update frequency: Daily/Monthly

- **BP Statistical Review**
  - Global energy statistics
  - Historical energy data
  - Regional breakdowns
  - Update frequency: Annual

- **World Bank Energy Data**
  - Energy access indicators
  - Energy intensity metrics
  - Renewable energy shares
  - Update frequency: Annual

### Climate Data Sources
- **NOAA (National Oceanic and Atmospheric Administration)**
  - Temperature and precipitation data
  - Climate indices and anomalies
  - Extreme weather events
  - Update frequency: Monthly

- **NASA Earthdata**
  - Satellite climate observations
  - Vegetation indices
  - Sea surface temperatures
  - Update frequency: Daily/Monthly

### Political Data Sources
- **V-Dem (Varieties of Democracy)**
  - Democracy indices
  - Political institutions data
  - Civil liberties metrics
  - Update frequency: Annual

- **Freedom House**
  - Freedom scores
  - Political rights assessments
  - Civil liberties evaluations
  - Update frequency: Annual

- **World Bank Governance Indicators**
  - Government effectiveness
  - Rule of law
  - Control of corruption
  - Update frequency: Annual

### Health Data Sources
- **WHO (World Health Organization)**
  - Disease outbreak data
  - Health system indicators
  - Mortality statistics
  - Update frequency: Annual/Event-based

- **FAO (Food and Agriculture Organization)**
  - Food security indicators
  - Malnutrition statistics
  - Agricultural disease outbreaks
  - Update frequency: Annual

### Resource Data Sources
- **World Bank Natural Resources**
  - Water stress indicators
  - Arable land statistics
  - Natural resource rents
  - Update frequency: Annual

- **Global Forest Watch**
  - Forest loss data
  - Deforestation rates
  - Forest cover statistics
  - Update frequency: Annual

## Analysis Methodologies

### Correlation Analysis
- **Pearson Correlation**: Linear relationships
- **Spearman Correlation**: Monotonic relationships
- **Kendall's Tau**: Rank-based correlation
- **Distance Correlation**: All types of dependence
- **Partial Correlation**: Controlling for other variables
- **Mutual Information**: Nonlinear associations

### Causality Testing
- **Granger Causality**: Predictive causality
- **Vector Autoregression (VAR)**: Multivariate time series
- **Cointegration Testing**: Long-term relationships
- **Impulse Response Analysis**: Shock propagation

### Feature Importance
- **Random Forest Importance**: Tree-based importance
- **Permutation Importance**: Model-agnostic importance
- **LASSO Regularization**: Sparse feature selection
- **Mutual Information**: Information-theoretic importance
- **F-Statistics**: Statistical significance

### Threshold Detection
- **Regime Switching Models**: Structural breaks
- **Threshold Autoregression**: Non-linear dynamics
- **Change Point Detection**: Temporal breaks
- **Effect Size Analysis**: Practical significance

### Network Analysis
- **Centrality Measures**: Node importance
- **Community Detection**: Variable groupings
- **Path Analysis**: Influence propagation
- **Network Topology**: Structural properties

## Performance Optimization

### Parallel Processing
```bash
# Enable parallel processing (default)
python run_enhanced_historical_analysis.py --mode multivariate

# Disable for debugging
python run_enhanced_historical_analysis.py --mode multivariate --no-parallel
```

### Memory Management
```bash
# For large datasets, use sampling
python run_enhanced_historical_analysis.py --mode multivariate --sample-size 50000

# Use efficient data formats
python run_enhanced_historical_analysis.py --mode multivariate --use-parquet
```

### GPU Acceleration
```python
# Check GPU availability
import tensorflow as tf
print("GPU Available:", tf.config.list_physical_devices('GPU'))

# Enable GPU for deep learning models
config = {
    'use_gpu': True,
    'gpu_memory_limit': 8192  # MB
}
```

### Distributed Computing
```python
# Use Dask for large-scale processing
import dask
from dask.distributed import Client

client = Client('scheduler-address:8786')
# Run analysis with Dask backend
```

## Real-Time Monitoring

### Alert System
- **Correlation Alerts**: Significant relationship changes
- **Threshold Alerts**: Variable crossing critical thresholds
- **Anomaly Alerts**: Unusual patterns detected
- **Data Quality Alerts**: Missing or corrupted data

### Monitoring Dashboard
- Real-time correlation tracking
- Live threshold monitoring
- Anomaly detection visualization
- System health indicators

### Automated Reporting
- Executive summary generation
- Key findings extraction
- Trend analysis reports
- Policy recommendation alerts

## Troubleshooting

### Common Issues

#### Memory Issues
```bash
# Reduce data size or enable sampling
python run_enhanced_historical_analysis.py --mode multivariate --sample-size 10000

# Use chunked processing
python run_enhanced_historical_analysis.py --mode multivariate --chunk-size 1000
```

#### API Rate Limits
```bash
# Increase delays between requests
python run_enhanced_historical_analysis.py --mode update --rate-limit-delay 2.0

# Use cached data when available
python run_enhanced_historical_analysis.py --mode multivariate --use-cache
```

#### Analysis Failures
```bash
# Use subset of analysis methods
python run_enhanced_historical_analysis.py --mode multivariate \
    --correlation-methods pearson spearman \
    --max-lags 6

# Skip problematic components
python run_enhanced_historical_analysis.py --mode multivariate \
    --skip-causality --skip-threshold
```

#### Dashboard Issues
```bash
# Try different ports
python run_enhanced_historical_analysis.py --mode multivariate-dashboard \
    --multivariate-port 8053

# Enable debug mode
python run_enhanced_historical_analysis.py --mode multivariate-dashboard --debug
```

### Logging and Debugging
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python run_enhanced_historical_analysis.py --mode multivariate --debug

# Check log files
tail -f logs/enhanced_historical_analysis.log
```

## Contributing

### Adding New Data Sources
1. Extend `DataCategory` enum in `multivariate_relational_analysis.py`
2. Add source configuration in `_initialize_source_configs()`
3. Implement fetch method in `MultivariateDataIntegrator`
4. Update variable registry with metadata
5. Add tests and documentation

### Adding New Analysis Methods
1. Implement method in `CorrelationRelationshipAnalyzer`
2. Add configuration options
3. Update dashboard visualization
4. Add performance evaluation
5. Document methodology and interpretation

### Adding New Visualizations
1. Create chart method in `MultivariateRelationshipDashboard`
2. Add to appropriate dashboard tab
3. Register interactive callbacks
4. Update layout and styling
5. Add user documentation

## Performance Benchmarks

### Typical Performance
- **Data Integration**: 1-5 minutes for 3 years of data
- **Correlation Analysis**: 30 seconds for 100 variables
- **Causality Testing**: 2-10 minutes depending on lags
- **Network Analysis**: 1-3 minutes for 100 nodes
- **Dashboard Loading**: 5-15 seconds initial load

### Scalability
- **Variables**: Tested up to 500 variables
- **Time Points**: Tested up to 1M observations
- **Memory Usage**: 2-16GB depending on analysis
- **Processing Time**: Linear scaling with data size

## License

This enhanced system is part of the RiskMap project and follows the same licensing terms.

## Support and Documentation

### Getting Help
1. Check this comprehensive documentation
2. Review troubleshooting section
3. Examine log files for error details
4. Verify all dependencies are installed
5. Ensure data sources are accessible

### Additional Resources
- [Statistical Methods Documentation](docs/statistical_methods.md)
- [Data Source API Documentation](docs/data_sources.md)
- [Visualization Guide](docs/visualization_guide.md)
- [Performance Tuning Guide](docs/performance_tuning.md)

## Roadmap

### Planned Enhancements
- **Advanced ML Models**: Transformer networks, Graph Neural Networks
- **Real-time Streaming**: Apache Kafka integration
- **Cloud Deployment**: AWS/Azure/GCP support
- **Mobile Interface**: Responsive web design
- **API Endpoints**: RESTful API for external integration
- **Advanced Alerts**: Machine learning-based anomaly detection
- **Collaborative Features**: Multi-user analysis and sharing

### Research Directions
- **Causal Discovery**: Automated causal graph learning
- **Explainable AI**: Advanced model interpretability
- **Uncertainty Quantification**: Bayesian approaches
- **Multi-scale Analysis**: Temporal and spatial hierarchies
- **Domain Adaptation**: Transfer learning across regions/periods