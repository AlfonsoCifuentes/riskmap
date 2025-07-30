
import logging
import sys
from pathlib import Path
import json
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# --- Configuración Inicial ---
# Añadir el directorio raíz al path para importaciones consistentes
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Importaciones de Componentes del Sistema ---
# Usamos un bloque try-except para manejar posibles errores de importación
try:
    from src.utils.config import config
    from src.data_processing.nlp_analyzer import EnhancedNLPAnalyzer
    from src.data_ingestion.rss_fetcher import RSSFetcher
except ImportError as e:
    logger.error(f"Error crítico al importar módulos: {e}. Asegúrate de que la estructura del proyecto y los paths son correctos.")
    # Definir una configuración por defecto para que la app pueda arrancar mínimamente
    class FallbackConfig:
        class database:
            path = str(ROOT_DIR / "data" / "geopolitical_intel.db")
    config = FallbackConfig()
    EnhancedNLPAnalyzer = None
    RSSFetcher = None

# --- Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title="RiskMap Unified Dashboard",
    description="Plataforma centralizada para el análisis de inteligencia geopolítica.",
    version="2.0.0"
)

# --- Configuración de Plantillas y Archivos Estáticos ---
# Directorios basados en la nueva estructura unificada
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- Conexión a la Base de Datos ---
DB_PATH = config.database.path
logger.info(f"Conectando a la base de datos en: {DB_PATH}")

def get_db_connection():
    """Establece y retorna una conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error al conectar con la base de datos: {e}")
        return None

# --- Endpoints de la API de Datos ---

@app.get("/api/v1/health", summary="Chequeo de Salud del Servicio")
def health_check():
    """Verifica que el servicio y la conexión a la base de datos estén activos."""
    if get_db_connection() is not None:
        return JSONResponse(content={"status": "ok", "database": "connected"})
    return JSONResponse(content={"status": "error", "database": "disconnected"}, status_code=503)

@app.get("/api/v1/events/geojson", summary="Eventos Geográficos en formato GeoJSON")
def get_events_geojson():
    """Provee los eventos con coordenadas en formato GeoJSON para el mapa."""
    conn = get_db_connection()
    if not conn:
        return JSONResponse(content={"error": "Database connection failed"}, status_code=500)
    
    try:
        # Consulta optimizada para obtener solo artículos con coordenadas válidas
        query = """
            SELECT id, title, risk_score, latitude, longitude, source, published_at
            FROM articles
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY published_at DESC
            LIMIT 500;
        """
        articles = conn.execute(query).fetchall()
        conn.close()

        features = [{
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [article["longitude"], article["latitude"]]
            },
            "properties": {
                "id": article["id"],
                "title": article["title"],
                "risk_score": article["risk_score"],
                "source": article["source"],
                "published_at": article["published_at"]
            }
        } for article in articles]

        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        logger.error(f"Error al generar GeoJSON: {e}")
        return JSONResponse(content={"error": "Failed to generate GeoJSON"}, status_code=500)

@app.get("/api/v1/dashboard-data", summary="Datos Consolidados para el Dashboard")
def get_dashboard_data():
    """Endpoint único que provee todos los datos necesarios para el dashboard."""
    conn = get_db_connection()
    if not conn:
        return JSONResponse(content={"error": "Database connection failed"}, status_code=500)

    try:
        # Estadísticas generales
        total_articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        processed_articles = conn.execute("SELECT COUNT(*) FROM articles WHERE risk_score IS NOT NULL").fetchone()[0]
        critical_alerts = conn.execute("SELECT COUNT(*) FROM articles WHERE risk_score > 85").fetchone()[0]
        
        # Artículos de alto riesgo
        high_risk_articles = conn.execute("""
            SELECT title, source, risk_score, url, published_at FROM articles 
            WHERE risk_score > 75 ORDER BY risk_score DESC LIMIT 10
        """).fetchall()

        # Artículos recientes
        recent_articles = conn.execute("""
            SELECT title, source, risk_score, url, published_at FROM articles 
            ORDER BY published_at DESC LIMIT 10
        """).fetchall()

        # Análisis generado por IA (simulado o real)
        ai_analysis_query = "SELECT content FROM ai_generated_articles ORDER BY created_at DESC LIMIT 1"
        ai_article = conn.execute(ai_analysis_query).fetchone()
        
        conn.close()

        return {
            "stats": {
                "total_articles": total_articles,
                "processed_articles": processed_articles,
                "critical_alerts": critical_alerts,
                "ai_confidence": 95.5 # Simulado por ahora
            },
            "high_risk_articles": [dict(row) for row in high_risk_articles],
            "recent_articles": [dict(row) for row in recent_articles],
            "ai_analysis": dict(ai_article) if ai_article else {"content": "No AI analysis available."}
        }
    except Exception as e:
        logger.error(f"Error al obtener datos del dashboard: {e}")
        return JSONResponse(content={"error": "Failed to fetch dashboard data"}, status_code=500)


# --- Endpoints de Procesamiento (Nuevos) ---

@app.post("/api/v1/actions/run-ingestion", summary="Ejecutar Ingesta de Datos RSS")
async def run_ingestion():
    """Endpoint para iniciar manualmente el proceso de ingesta de datos."""
    logger.info("Solicitud para iniciar la ingesta de datos recibida.")
    try:
        # En un entorno de producción, esto debería ser una tarea en segundo plano (e.g., con Celery, ARQ)
        # Por simplicidad, lo ejecutamos directamente aquí.
        from src.data_ingestion.rss_fetcher import RSSFetcher
        
        # Cargar fuentes desde la configuración o un archivo
        # Ejemplo de fuentes (debería estar en un archivo de config)
        rss_sources = {
            "Reuters World News": "http://feeds.reuters.com/reuters/worldNews",
            "Associated Press": "https://apnews.com/hub/ap-top-news/rss.xml",
            "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml"
        }

        fetcher = RSSFetcher(DB_PATH, rss_sources)
        articles_added = fetcher.fetch_and_store_articles()
        fetcher.close_connection()
        
        return JSONResponse(content={"status": "success", "articles_added": articles_added})
    except Exception as e:
        logger.error(f"Error durante la ingesta manual: {e}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

@app.post("/api/v1/actions/run-analysis", summary="Ejecutar Análisis NLP")
async def run_analysis():
    """Endpoint para iniciar manualmente el proceso de análisis NLP de artículos no procesados."""
    logger.info("Solicitud para iniciar el análisis NLP recibida.")
    try:
        from src.data_processing.nlp_analyzer import EnhancedNLPAnalyzer

        analyzer = EnhancedNLPAnalyzer(DB_PATH)
        articles_processed = analyzer.analyze_unprocessed_articles()
        analyzer.close_connection()

        return JSONResponse(content={"status": "success", "articles_processed": articles_processed})
    except Exception as e:
        logger.error(f"Error durante el análisis manual: {e}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)


# --- Endpoint Principal de la Interfaz de Usuario ---

@app.get("/", response_class=HTMLResponse, summary="Página Principal del Dashboard")
async def get_unified_dashboard(request: Request):
    """Sirve la página principal del dashboard unificado."""
    # Aquí podrías pasar datos iniciales a la plantilla si fuera necesario
    # Por ahora, la mayoría de los datos se cargarán de forma asíncrona desde la API
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- Lógica de Arranque ---

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando el servidor del Dashboard Unificado de RiskMap...")
    uvicorn.run(
        "App:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
