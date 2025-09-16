# RiskMap AI Coding Instructions

This is a geopolitical intelligence platform that combines data ingestion, NLP processing, satellite analysis, and real-time monitoring.

**❌ NEVER EXECUTE THE SERVER:** The user runs the server in a separate process. DO NOT use `run_in_terminal` to start any application servers.

**Don´t use netstat or similar commands to check for open ports.** Use Python scripts or browser access instead.

## 🏗️ Architecture Overview

**Main Application Entry Points:**
- `app_CORREGIDO.py` - CURRENT WORKING APPLICATION (USER RUNS THIS)
- `app_BUENA.py` - Legacy application with dependency issues (DO NOT USE)
- `app_SIMPLE.py` - Basic fallback application
- `main.py` - CLI interface for testing components
- Database: SQLite at `./data/geopolitical_intel.db`

**Core System Components:**
- **Orchestrators**: `GeopoliticalIntelligenceOrchestrator`, `EnhancedHistoricalOrchestrator` coordinate all operations
- **Data Pipeline**: RSS feeds → NLP processing → AI analysis → Database storage → Web interface
- **Processing Flow**: Ingestion (1h) → NLP (2h) → Historical Analysis (6h) → External Feeds (6h)

## 🔧 Development Conventions

**❌ SERVER EXECUTION RULES:**
- NEVER execute servers with `run_in_terminal` (app_BUENA.py, app_CORREGIDO.py, etc.)
- NEVER use `python app_*.py` commands
- User handles server execution in separate process
- Only create/modify files and test endpoints if needed

**PowerShell Commands (Windows):**
- ALWAYS append `; echo ""` to terminal commands
- Never use `&&` - use PowerShell semicolon syntax instead
- Never use bash-style string concatenation

**Current Working Application:**
```
app_CORREGIDO.py - Fixed version with proper SQL column handling
```

**Configuration:**
- All credentials in `.env` file at project root
- Database path: `DATABASE_URL=sqlite:///data/geopolitical_intel.db`
- API keys: NewsAPI, OpenAI, Groq, DeepSeek, SentinelHub, HuggingFace

## 🔄 Current System Status

**FIXED ISSUES (September 2025):**
- ✅ SQL column mismatch fixed (`description` → `summary`)
- ✅ 500 errors on `/api/articles` endpoint resolved
- ✅ 500 errors on `/api/hero-article` endpoint resolved  
- ✅ 500 errors on `/api/articles/deduplicated` endpoint resolved
- ✅ Geopolitical filtering ultra-strict (only geopolitical + real images)
- ✅ No placeholder/mockup images allowed

**Current Endpoints (Port 5001):**
- GET `/` - Main page
- GET `/api/status` - System status
- GET `/api/articles` - Geopolitical articles with real images
- GET `/api/hero-article` - Main article
- GET `/api/articles/deduplicated` - Deduplicated articles

## 🧠 NLP & AI System

**Processing Pipeline:**
1. **Data Ingestion**: RSS feeds + NewsAPI + Intelligence sources
2. **NLP Analysis**: BERT/RoBERTa models + sentiment + entity extraction
3. **AI Enhancement**: Groq/Ollama APIs for summaries and insights
4. **Storage**: Advanced NLP results in `processed_data` table

**Key Classes:**
- `AdvancedNLPAnalyzer` - Core NLP processing
- `BERTRiskAnalyzer` - Geopolitical risk classification
- `IntelligentDataEnrichment` - Automated article enhancement

**Database Schema Pattern:**
- Articles: `articles` table with basic data
- Processing: `processed_data` table with NLP results
- Always check for existing `advanced_nlp` column before processing

## 🛰️ Satellite & External Data

**Satellite Integration:**
- SentinelHub API for satellite imagery
- `AutomatedSatelliteMonitor` for conflict zone monitoring
- GeoJSON generation for spatial analysis

**External Sources:**
- GDELT events, ACLED conflicts, GPR index
- `ExternalIntelligenceFeeds` class handles all feeds
- Fallback data generation when APIs unavailable

## 🎯 Key Patterns

**Error Handling:**
- Ultra-robust exception handling with graceful degradation
- Mock classes when modules unavailable (CCTV, Satellite, etc.)
- Always continue operation even if components fail

**Module Loading:**
```python
try:
    from module import Component
    COMPONENT_AVAILABLE = True
except ImportError as e:
    COMPONENT_AVAILABLE = False
    # Create mock class
    class Component:
        pass
```

**Database Operations:**
- Always use context managers for SQLite connections
- Check column existence before altering tables
- Batch processing for large datasets

**Real Data Policy:**
- NEVER use simulated/mock data for testing
- Always use real RSS feeds, APIs, and live data
- Fallback to cached/historical data when APIs fail

## 🔄 Background Processing

**Automatic Cycles:**
- Data ingestion runs every 1 hour
- NLP processing every 2 hours  
- Historical analysis every 6 hours
- All managed by `TaskScheduler` and threading

**Manual Processing Scripts:**
- `process_all_articles_nlp.py` - Batch NLP processing
- `enriquecimiento_masivo_nuevo.py` - Mass enrichment
- `integrate_advanced_nlp.py` - NLP integration

## 🌐 Web Interface

**Flask Routes:** Multiple integrated dashboards
- Main: `http://localhost:5001`
- Dashboard: `/dashboard` (historical analysis)
- Multivariate: `/multivariate` (correlations)
- API: `/api/v1/docs`

**Dash Integration:** 
- Historical dashboard at `/dashboard`
- Multivariate analysis at `/multivariate`
- Both integrated into Flask app via `url_base_pathname`

## ⚠️ Critical Rules

- **NEVER execute server applications** - User runs server in separate process
- **NEVER use `python app_*.py` commands**
- **NEVER use `run_in_terminal` for server startup**
- Current working application: `app_CORREGIDO.py` (user runs this)
- All API keys in `.env` - never hardcode credentials  
- Keep automation pipeline in mind - changes affect background processes
- Use latest MCP libraries, avoid deprecated functions
- Real data only - no simulations or mockups
- PowerShell syntax for Windows terminal commands
- **ALWAYS reference this context file** - this is the authoritative source
