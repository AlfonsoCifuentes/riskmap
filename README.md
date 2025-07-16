# 🌍 Sistema de Inteligencia Geopolítica (RISKMAP)
### Plataforma OSINT Avanzada para Análisis Multilingüe en Tiempo Real

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg)

**Análisis automatizado de inteligencia geopolítica con fuentes de datos 100% reales**

</div>

---

## � Descripción General

Sistema avanzado de **Inteligencia de Fuentes Abiertas (OSINT)** alimentado por IA para **análisis geopolítico automatizado**. Diseñado siguiendo las especificaciones estrictas de `context.ipynb`, proporciona capacidades integrales de **recopilación de inteligencia multilingüe**, **evaluación de riesgos**, **reportes automatizados** y **análisis interactivo**.

### 🎯 Características Principales

#### 🔍 Recopilación de Inteligencia Avanzada
- **Fuentes de datos reales**: NewsAPI, RSS feeds globales, medios especializados
- **Soporte multilingüe**: Español, Inglés, Ruso, Chino, Árabe
- **Recolección en tiempo real** con validación automática de fuentes
- **Sin datos simulados o emulados** - exclusivamente fuentes verificadas

#### 🤖 Procesamiento NLP Robusto
- **Análisis de sentimientos** avanzado con múltiples modelos
- **Reconocimiento de entidades nombradas** (personas, organizaciones, lugares)
- **Detección automática de idioma** con traducción inteligente
- **Clasificación de riesgos** geopolíticos automatizada

#### 📊 Dashboard Interactivo
- **Visualizaciones en tiempo real** con métricas dinámicas
- **Mapas geopolíticos** interactivos con datos de riesgo
- **Líneas de tiempo** de eventos críticos
- **Alertas automáticas** para situaciones de alto riesgo

#### � Arquitectura Robusta
- **Manejo de errores** comprehensive con logging avanzado
- **Caché inteligente** para optimización de rendimiento
- **Validación de APIs** en tiempo real
- **Monitoreo de sistema** con métricas de salud

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Web Dashboard │   REST API      │   Interactive Chatbot   │
│   (Flask)       │   (Flask-CORS)  │   (Gradio)              │
└─────────────────┴─────────────────┴─────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                     │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Data Ingestion  │ NLP Processing  │ Intelligence Analysis   │
│ • NewsAPI       │ • Translation   │ • Risk Assessment       │
│ • RSS Feeds     │ • Sentiment     │ • Entity Recognition    │
│ • Web Scraping  │ • Classification│ • Geolocation Analysis  │
└─────────────────┴─────────────────┴─────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                    │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Data Storage    │ Monitoring      │ Quality Assurance       │
│ • SQLite DB     │ • Health Checks │ • Data Validation       │
│ • File Storage  │ • Performance   │ • Source Verification   │
│ • Report Cache  │ • System Metrics│ • Content Quality       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🛠️ Enhanced Installation & Quick Start

### Method 1: Quick Start Script (Recommended)

```bash
# Windows
./quick_start.bat

# Linux/macOS
./quick_start.sh
```

### Method 2: Docker Deployment (Production Ready)

```bash
# Clone repository
git clone <repository-url>
cd riskmap

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Access services
# Dashboard: http://localhost:5000
# API: http://localhost:5001
# Chatbot: http://localhost:7860
```

### Method 3: Manual Installation

```bash
# 1. Setup Python environment
python -m venv riskmap_env
source riskmap_env/bin/activate  # Linux/Mac
# or riskmap_env\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Configure environment
cp .env.example .env
# Add your API keys to .env

# 4. Initialize system
python setup.py

# 5. Run system health check
python main.py --health-check
```

## 🎮 Enhanced Usage Commands

### Core Operations
```bash
# Run complete intelligence pipeline
python main.py --full-pipeline

# Collect data only
python main.py --collect

# Process collected articles
python main.py --process

# Generate reports
python main.py --report daily
python main.py --report weekly
```

### New Monitoring & Maintenance Commands
```bash
# System health check
python main.py --health-check

# Data quality validation
python main.py --validate-data 7  # Last 7 days

# System maintenance
python main.py --maintenance

# View system status
python main.py --status

# Run scheduled tasks (continuous mode)
python main.py --schedule
```

### Individual Services
```bash
# Start web dashboard
python src/dashboard/app.py

# Start REST API server
python src/api/rest_api.py

# Start interactive chatbot
python src/chatbot/chatbot_app.py

# Run comprehensive tests
python tests/test_comprehensive.py
```

## 🌐 API Endpoints (New REST API)

### System Monitoring
- `GET /api/v1/health` - System health status
- `GET /api/v1/metrics` - Performance metrics
- `GET /api/v1/stats` - General statistics

### Data Access
- `GET /api/v1/articles` - List articles with filtering
- `GET /api/v1/articles/<id>` - Article details
- `GET /api/v1/search` - Advanced search

### Analytics
- `GET /api/v1/analytics/sentiment` - Sentiment trends
- `GET /api/v1/analytics/risk` - Risk level analysis
- `GET /api/v1/analytics/entities` - Entity mentions

### Data Quality
- `GET /api/v1/data-quality` - Quality reports
- `POST /api/v1/reports/generate` - Generate new reports

Example API usage:
```bash
# Get system health
curl http://localhost:5001/api/v1/health

# Search articles
curl "http://localhost:5001/api/v1/search?q=geopolitics&limit=10"

# Get sentiment analytics
curl "http://localhost:5001/api/v1/analytics/sentiment?days=7"
```

## 📊 Enhanced Dashboard Features

### Real-time Monitoring
- **System health** dashboard with live metrics
- **Data quality** indicators and trends
- **Processing performance** visualization
- **API usage** statistics

### Advanced Analytics
- **Interactive charts** for sentiment and risk analysis
- **Geographic intelligence** mapping
- **Entity relationship** networks
- **Temporal trend** analysis

### Management Interface
- **System configuration** management
- **Data quality** controls
- **Report generation** interface
- **Maintenance tools** access

## 🔧 Configuration & Environment Variables

### Required API Keys
```bash
# NewsAPI (for news collection)
NEWSAPI_KEY=your_newsapi_key_here

# OpenAI (for NLP processing)
OPENAI_API_KEY=your_openai_key_here
```

### System Configuration
```bash
# Database settings
DATABASE_PATH=data/riskmap.db

# Processing limits
MAX_ARTICLES_PER_RUN=100
BATCH_SIZE=10

# Monitoring settings
ENABLE_HEALTH_CHECKS=true
LOG_LEVEL=INFO

# Quality thresholds
MIN_QUALITY_SCORE=60
ENABLE_DATA_VALIDATION=true
```

## 🐳 Docker Deployment

### Development Environment
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d
```

### Production Environment
```bash
# Production deployment with SSL
docker-compose -f docker-compose.prod.yml up -d
```

### Container Management
```bash
# View logs
docker-compose logs -f riskmap-app

# Health check
docker-compose exec riskmap-app python main.py --health-check

# Update services
docker-compose pull && docker-compose up -d
```

## 🧪 Testing & Quality Assurance

### Run Test Suite
```bash
# Comprehensive test suite
python tests/test_comprehensive.py

# Legacy tests
python tests/test_system.py

# With coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Quality Checks
```bash
# Code quality
flake8 src/
black src/

# Security scan
bandit -r src/

# Type checking
mypy src/
```

## 📈 Performance & Monitoring

### System Metrics
- **CPU/Memory usage** monitoring
- **Database performance** tracking
- **API response times** measurement
- **Data processing** efficiency

### Quality Metrics
- **Article validation** rates
- **Source credibility** scores
- **Content quality** assessment
- **Duplicate detection** accuracy

### Health Monitoring
- **Automated health checks** every 5 minutes
- **Alert system** for critical issues
- **Performance degradation** detection
- **Resource exhaustion** warnings

## 🔒 Security Features

### Data Protection
- **Input validation** and sanitization
- **SQL injection** protection
- **XSS prevention** in web interfaces
- **API rate limiting**

### Access Control
- **API key authentication** (configurable)
- **Role-based access** (dashboard)
- **Secure configuration** management
- **Audit logging**

## 📚 Documentation Structure

- **README.md** - Main documentation (this file)
- **docs/DEPLOYMENT.md** - Comprehensive deployment guide
- **docs/API_REFERENCE.md** - Complete API documentation
- **context.ipynb** - Original project specifications
- **examples/** - Usage examples and demos

## 🔄 Maintenance & Updates

### Automated Maintenance
```bash
# Daily maintenance (recommended cron job)
0 2 * * * cd /path/to/riskmap && python main.py --maintenance

# Health monitoring
*/15 * * * * cd /path/to/riskmap && python main.py --health-check
```

### Manual Maintenance
```bash
# Clean up old data
python main.py --validate-data 30

# Optimize database
sqlite3 data/riskmap.db "VACUUM;"

# Update dependencies
pip install --upgrade -r requirements.txt
```

## 🚨 Troubleshooting

### Common Issues
1. **API Rate Limits** - Check API usage and configure delays
2. **Memory Issues** - Reduce batch sizes in configuration
3. **Database Locks** - Check for concurrent access issues
4. **SSL Errors** - Verify certificate configuration

### Diagnostic Commands
```bash
# System diagnostics
python main.py --health-check

# Data quality check
python main.py --validate-data 1

# Log analysis
grep ERROR logs/*.log | tail -20
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/enhancement`)
3. **Commit** changes (`git commit -am 'Add enhancement'`)
4. **Push** to branch (`git push origin feature/enhancement`)
5. **Create** Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for advanced NLP capabilities
- **NewsAPI** for reliable news data access
- **Hugging Face** for transformer models
- **Flask** ecosystem for web framework
- **Docker** for containerization support

---

**🔗 Quick Links:**
- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Reference](docs/API_REFERENCE.md)
- [Project Context](context.ipynb)
- [Docker Hub](https://hub.docker.com/) (when published)

**📞 Support:** For issues and questions, please check the documentation or create an issue in the repository.
