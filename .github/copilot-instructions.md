# RiskMap AI Coding Instructions

**🎯 ÚNICO ARCHIVO DE CONTEXTO AUTORIZADO - ESTE Y NO OTRO**
**📍 RUTA: E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\.github\copilot-instructions.md**
**📅 Last Updated: September 25, 2025**
**🔒 CONTEXTO PERMANENTE: Configurado en .vscode/settings.json para persistir en todas las sesiones**

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

## 🗄️ Database Schema (CURRENT - September 2025)

**Main Table: `unified_articles` (87 columns) - i18N ENABLED**
- Primary storage for ALL news articles with full internationalization support
- **Core Fields**: id, title, content, summary, url, source, published_at, created_at
- **i18N Fields**: language (DEFAULT 'es'), original_language, is_translated (0/1)
- **Geopolitical Fields**: geopolitical_relevance, risk_level, risk_score, conflict_type, conflict_intensity
- **Location Fields**: country, region, latitude, longitude, location_extracted, coordinates_source
- **Image Fields**: image_url, original_image_url, cv_analysis, satellite_image_url, has_image
- **AI/ML Fields**: ai_importance, ai_summary, auto_generated_summary, ai_sentiment, ai_tags, enrichment_status
- **Entity Extraction**: entities_json, extracted_entities_json, countries_involved, politicians_involved
- **Analysis Fields**: sentiment_score, quality_score, processing_confidence, enrichment_confidence
- **Metadata**: source_country, source_bias, source_credibility, metadata_json, processing_notes

**Language Distribution (Current):**
- English (en): 246 articles
- Spanish (es): 13 articles  
- System supports: Automatic translation, language detection, bilingual content

**Supporting Tables (21 total):**
- `alerts` - System alerts and notifications
- `conflict_zones` - Active conflict monitoring zones  
- `enrichment_log` - AI enrichment tracking
- `feed_updates` - RSS feed update history
- `gpr_index` - Geopolitical Risk Index data
- `satellite_alerts` - Satellite monitoring alerts
- `satellite_predictions` - Satellite-based predictions
- `satellite_timeline` - Satellite event timeline
- `acled_events` - Armed Conflict Location & Event Data
- `gdelt_events` - Global Database of Events, Language, and Tone
- `critical_events` - High-priority geopolitical events
- `image_analysis` - Computer vision analysis results
- `satellite_images` - Satellite imagery metadata
- `zone_satellite_images` - Zone-specific satellite data

**⚠️ CRITICAL DATABASE NOTES:**
- **Legacy `articles` table still exists** but is being phased out
- **Primary table is `unified_articles`** (87 columns vs legacy 79)
- **i18N capability**: Full Spanish/English bilingual support
- **Translation pipeline**: Automatic translation with `is_translated` flag
- **Total articles**: 625 (444 geopolitical)

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

**🔧 PowerShell & String Literal Safety Rules:**

**Quote Handling in PowerShell:**
- **NEVER use single quotes inside single quotes without escaping**
- **NEVER use double quotes inside double quotes without escaping**
- **ALWAYS use backtick escaping for special characters in PowerShell**
- Examples:
  ```powershell
  # ❌ WRONG - Will cause errors
  python -c 'print("Hello World")'
  
  # ✅ CORRECT - Use backticks for escaping
  python -c 'print(`"Hello World`")'
  
  # ✅ ALTERNATIVE - Mix quote types
  python -c "print('Hello World')"
  ```

**String Literal Safety:**
- **ALWAYS validate string termination before sending terminal commands**
- **NEVER leave unterminated strings in Python code or terminal commands**
- **ALWAYS use raw strings (r"string") for paths with backslashes**
- **ALWAYS escape backslashes properly in JSON strings**
- Examples:
  ```python
  # ❌ WRONG - Unterminated string
  print("Hello World
  
  # ✅ CORRECT - Properly terminated
  print("Hello World")
  
  # ❌ WRONG - Windows path issues
  path = "C:\Users\data\file.txt"
  
  # ✅ CORRECT - Raw string for paths
  path = r"C:\Users\data\file.txt"
  ```

**Terminal Command Safety:**
- **ALWAYS validate command syntax before execution**
- **NEVER send commands with unmatched quotes or braces**
- **ALWAYS use proper escaping for special characters**
- **Test complex commands in small parts first**

## 🌐 Internationalization (i18N) System

**Language Support:**
- **Primary Languages**: Spanish (es), English (en)
- **Default Language**: Spanish ('es') for new articles
- **Translation System**: Automatic translation with detection and validation
- **Bilingual Content**: Full support for content in both languages

**Database i18N Fields:**
- `language`: Current article language ('es' or 'en'), DEFAULT 'es'  
- `original_language`: Source language before any translation
- `is_translated`: Boolean flag (0/1) indicating if article was translated
- `source_country`: Origin country of the news source

**Translation Pipeline:**
- Auto-detect source language on article ingestion
- Translate non-Spanish articles to Spanish when needed
- Preserve original language metadata
- Flag translated content for quality tracking
- Support for mixed-language datasets

**Frontend i18N:**
- Templates support bilingual content rendering
- Dynamic language switching capability
- Locale-aware formatting for dates, numbers
- SEO-friendly multilingual URLs

**Current Distribution:**
- English articles: 246 (39.4%)
- Spanish articles: 13 (2.1%)
- Remaining: Mixed/Other languages
- **Total corpus**: 625 articles (444 geopolitically relevant)

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

## 🔄 Current System Status

**FIXED ISSUES (September 2025):**
- ✅ Database unified to single `unified_articles` table (87 columns)
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
- ✅ Health check system migrated to unified_articles schema
- ✅ OpenAI deprecated - Primary AI services: Groq + DeepSeek
- ✅ Template inheritance fixed - dashboard_BUENO.html converted to standalone template
- ✅ Jinja2 syntax errors resolved - all remaining {% endblock %} tags removed
- ✅ Dashboard restoration complete - hero and mosaic sections fully functional

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

**Primary AI Services (September 2025):**
- **Groq API**: Primary AI service (Llama-3.1-70B-Versatile)
- **DeepSeek API**: Alternative AI service for analysis and summaries  
- **OpenAI API**: DEPRECATED - Only maintained for translation fallback
- **NewsAPI**: Primary news data source (real-time articles)
- **HuggingFace**: Local NLP models (BERT, sentence-transformers)

**Processing Pipeline:**
1. **Data Ingestion**: RSS feeds + NewsAPI + Intelligence sources
2. **NLP Analysis**: BERT/RoBERTa models + sentiment + entity extraction
3. **AI Enhancement**: Groq/DeepSeek APIs for summaries and insights (OpenAI deprecated)
4. **Storage**: Advanced NLP results in `unified_articles` table

**Key Classes:**
- `AdvancedNLPAnalyzer` - Core NLP processing
- `BERTRiskAnalyzer` - Geopolitical risk classification
- `IntelligentDataEnrichment` - Automated article enhancement

**Database Schema Pattern:**
- Articles: `unified_articles` table with ALL data (87 columns)
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

## 🚫 **TEMPLATE INHERITANCE RULES - CRITICAL**

**❌ TEMPLATE INHERITANCE ERRORS TO AVOID:**
- **NEVER extend base_navigation.html** - It's a complete HTML document, not a base template
- **ALWAYS check if base template has content blocks** before extending
- **REMOVE ALL {% block %} and {% endblock %} when converting to standalone**
- **ADD proper HTML structure** when making templates standalone: `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`

**✅ TEMPLATE BEST PRACTICES:**
- **dashboard_BUENO.html is STANDALONE** - no template inheritance
- **Check for Jinja2 syntax errors** - `{% endblock %}` without matching `{% block %}`  
- **Test template loading** - 500 errors often indicate template syntax issues
- **Clear template cache** - Use `self.flask_app.jinja_env.cache = {}` when debugging
- **Validate template syntax** before deployment

**🔍 DEBUGGING TEMPLATE ISSUES:**
1. Check Flask error logs for Jinja2 syntax errors
2. Search for unmatched `{% endblock %}` tags  
3. Verify base template structure if using inheritance
4. Test with minimal template first, then add complexity
5. Use direct string returns to bypass template rendering when debugging

**LESSON LEARNED (Sept 2025):** Template inheritance with incompatible base templates causes 500 errors and prevents dashboard loading. Always verify base template structure before extending.

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

**🏥 System Health Check Protocol:**
- **ALWAYS check latest health report** in `logs/health_check_*.json` before starting work
- **MANDATORY health check** for any system-related issues or debugging
- **Monitor performance metrics**: articles/hour, validation rate, API status
- **Database integrity**: unified_articles table, geopolitical filtering, recent articles
- **API status verification**: NewsAPI, Groq, DeepSeek (OpenAI deprecated - only for translation fallback)
- **Quality scoring**: Track articles with missing quality_score
- **Recent data ingestion**: Verify articles from last 24 hours
- **Log analysis**: Check for critical errors in geopolitical_intel.log
- Use command: `python -c "from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator; orchestrator = GeopoliticalIntelligenceOrchestrator(); orchestrator.health_check()"`

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
- **🎯 ESTE ES EL ÚNICO ARCHIVO DE CONTEXTO: E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\.github\copilot-instructions.md**
