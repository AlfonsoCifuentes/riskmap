# RiskMap AI Coding Instructions

This is a geopolitical intelligence platform that combines data ingestion, NLP processing, satellite analysis, and real-time monitoring.

**❌ NEVER EXECUTE THE SERVER:** The user runs the server in a separate process. DO NOT use `run_in_terminal` to start any application servers.

**Don´t use netstat or similar commands to check for open ports.** Use Python scripts or browser access instead.

## 🏗️ Architecture Overview

**Main Application Entry Points:**
- `RISKMAP.py` - **CURRENT WORKING APPLICATION** (USER RUNS THIS) - Located at project root
- `start_riskmap.py` - User-friendly launcher with auto-browser opening
- `quick_system_check.py` - System health verification
- Database: SQLite at `./data/geopolitical_intel.db` with **UNIFIED SCHEMA**

**Core System Components:**
- **Orchestrators**: `GeopoliticalIntelligenceOrchestrator`, `EnhancedHistoricalOrchestrator` coordinate all operations
- **Data Pipeline**: RSS feeds → NLP processing → AI analysis → **unified_articles** table → Web interface
- **Processing Flow**: Ingestion (1h) → NLP (2h) → Historical Analysis (6h) → External Feeds (6h)

## �️ Database Schema (CURRENT - September 2025)

**Main Table: `unified_articles` (79 columns)**
- Primary storage for ALL news articles
- Columns: id, title, content, summary, url, source, published_at, created_at
- Geopolitical fields: geopolitical_relevance, risk_level, risk_score, conflict_type
- Image fields: image_url, original_image_url, cv_analysis, mosaic_position
- AI fields: ai_importance, auto_generated_summary, enrichment_status
- Location fields: country, region, location, latitude, longitude

**Supporting Tables:**
- `alerts` - System alerts and notifications
- `conflict_zones` - Active conflict monitoring zones  
- `enrichment_log` - AI enrichment tracking
- `feed_updates` - RSS feed update history
- `gpr_index` - Geopolitical Risk Index data
- `satellite_alerts` - Satellite monitoring alerts
- `satellite_predictions` - Satellite-based predictions
- `satellite_timeline` - Satellite event timeline

**⚠️ CRITICAL: NO MORE `articles` TABLE**
- All legacy references to `articles` table have been eliminated
- Everything now uses `unified_articles` exclusively

## �🔧 Development Conventions

**❌ SERVER EXECUTION RULES:**
- NEVER execute servers with `run_in_terminal` (RISKMAP.py, etc.)
- NEVER use `python RISKMAP.py` commands in terminal
- User handles server execution in separate process
- Only create/modify files and test endpoints if needed

**PowerShell Commands (Windows):**
- ALWAYS append `; echo ""` to terminal commands
- Never use `&&` - use PowerShell semicolon syntax instead
- Never use bash-style string concatenation

**Current Working Application:**
```
RISKMAP.py - Primary working application with all features (renamed from app_BUENA.py)
```

**Configuration:**
- All credentials in `.env` file at project root
- Database path: `DATABASE_URL=sqlite:///data/geopolitical_intel.db`
- API keys: NewsAPI, OpenAI, Groq, DeepSeek, SentinelHub, HuggingFace
- Templates: Located in `src/web/templates/`

## 🔄 Current System Status

**FIXED ISSUES (September 2025):**
- ✅ Database unified to single `unified_articles` table (79 columns)
- ✅ All legacy `articles` table references eliminated
- ✅ SQL column mismatch fixed (`description` → `summary`)
- ✅ 500 errors on `/api/articles` endpoint resolved
- ✅ 500 errors on `/api/hero-article` endpoint resolved  
- ✅ 500 errors on `/api/articles/deduplicated` endpoint resolved
- ✅ Main executable moved to `RISKMAP.py` at project root
- ✅ Templates correctly located in `src/web/templates/`
- ✅ System uses unified schema exclusively
- ✅ Ultra-strict geopolitical filtering implemented
- ✅ Image validation improved (accepts valid HTTPS images)
- ✅ SSL certificate errors patched with robust fallbacks
- ✅ YOLO model loading fixed (PyTorch weights_only compatibility)
- ✅ All dependencies installed and compatible (sentence-transformers 2.7.0)
- ✅ CCTV tracking modernized (motpy replaces sort-tracker)
- ✅ Permanent patches applied for YOLO and SSL robustness
- ✅ All indentation errors fixed (RISKMAP.py, ultra_hd_satellite_system.py)

**CURRENT ISSUES BEING ADDRESSED:**
- ⚠️ Geopolitical filtering needs ultra-strict enforcement ✅ FIXED
- ⚠️ Image validation too restrictive (rejecting valid images) ✅ FIXED
- ⚠️ SSL certificate errors with external sources (IFRI, GDELT, GPR) ✅ FIXED
- ⚠️ YOLO model loading errors (PyTorch weights_only issue) ✅ FIXED
- ⚠️ NewsAPI returning 0 articles for non-English languages
- ⚠️ Dependency compatibility issues ✅ FIXED

**Current Endpoints (Port 5001):**
- GET `/` - Main page
- GET `/api/status` - System status
- GET `/api/articles` - Geopolitical articles with real images
- GET `/api/hero-article` - Main article (must not duplicate in mosaic)
- GET `/api/articles/deduplicated` - Deduplicated articles

## 🧠 NLP & AI System

**Processing Pipeline:**
1. **Data Ingestion**: RSS feeds + NewsAPI + Intelligence sources
2. **NLP Analysis**: BERT/RoBERTa models + sentiment + entity extraction
3. **AI Enhancement**: Groq/Ollama APIs for summaries and insights
4. **Storage**: Advanced NLP results in `unified_articles` table

**Key Classes:**
- `AdvancedNLPAnalyzer` - Core NLP processing
- `BERTRiskAnalyzer` - Geopolitical risk classification
- `IntelligentDataEnrichment` - Automated article enhancement

**Database Schema Pattern:**
- Articles: `unified_articles` table with ALL data (79 columns)
- No separate processing tables - everything integrated
- Always use `geopolitical_relevance = 1` for filtering

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
- All queries must use `unified_articles` table exclusively
- Use `geopolitical_relevance = 1` for filtering geopolitical content
- Batch processing for large datasets

**Real Data Policy:**
- NEVER use simulated/mock data for testing
- Always use real RSS feeds, APIs, and live data
- Fallback to cached/historical data when APIs fail
- Ultra-strict image validation: only real HTTPS URLs allowed

## 🔄 Background Processing

**Automatic Cycles:**
- Data ingestion runs every 1 hour
- NLP processing every 2 hours  
- Historical analysis every 6 hours
- All managed by `TaskScheduler` and threading

**Manual Processing Scripts:**
- `ultra_strict_geopolitical_filter.py` - Ultra-strict filtering system
- `quick_system_check.py` - System health verification
- `start_riskmap.py` - User-friendly launcher

## 🌐 Web Interface

**Flask Routes:** Multiple integrated dashboards
- Main: `http://localhost:5001`
- Dashboard: `/dashboard` (historical analysis)
- Multivariate: `/multivariate` (correlations)
- News Analysis: `/news-analysis` (redirects to main)
- API: `/api/v1/docs`

**Dash Integration:** 
- Historical dashboard at `/dashboard`
- Multivariate analysis at `/multivariate`
- Both integrated into Flask app via `url_base_pathname`

**Templates Location:**
- All templates in `src/web/templates/`
- Flask configured with `template_folder='src/web/templates'`

## ⚠️ Critical Rules

- **NEVER execute server applications** - User runs server in separate process
- **NEVER use `python RISKMAP.py` commands in terminal**
- **NEVER use `run_in_terminal` for server startup**
- Current working application: `RISKMAP.py` (user runs this)
- Launcher available: `python start_riskmap.py`
- All API keys in `.env` - never hardcode credentials  
- Keep automation pipeline in mind - changes affect background processes
- Use latest MCP libraries, avoid deprecated functions
- Real data only - no simulations or mockups
- PowerShell syntax for Windows terminal commands
- **ALWAYS use unified_articles table** - no legacy table references
- **Hero article MUST NOT appear in mosaic** - exclude by ID
- **ALWAYS reference this context file** - this is the authoritative source
