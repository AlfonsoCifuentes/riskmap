from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import sqlite3
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path para las importaciones
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Importar configuración y utilidades
try:
    from src.utils.config import config
    from src.monitoring.system_monitor import system_monitor
    from src.data_quality.validator import data_validator
    from src.utils.perf import PerfMiddleware, get_stats
except ImportError as e:
    logger.warning(f"Import error: {e}")
    # Configuración por defecto si no se pueden importar
    class DefaultConfig:
        class database:
            path = str(root_dir / "data" / "geopolitical_intel.db")
    config = DefaultConfig()
    
    # Mock objects para evitar errores
    class MockMonitor:
        def check_system_health(self):
            return {"status": "ok", "message": "System running"}
    
    class MockValidator:
        def get_quality_report(self, days=7):
            return {"quality": "good", "issues": 0}
    
    system_monitor = MockMonitor()
    data_validator = MockValidator()
    
    # Middleware simple si no está disponible
    class SimplePerfMiddleware:
        def __init__(self, app):
            pass
    PerfMiddleware = SimplePerfMiddleware

app = FastAPI(title="Riskmap Dashboard", version="1.0")
try:
    app.add_middleware(PerfMiddleware)
except:
    pass

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount('/static', StaticFiles(directory=str(Path(__file__).parent/'static')), name='static')

# Utilidad para cargar traducciones
I18N_DIR = Path(__file__).parent / "i18n"
LANGS = [f.stem for f in I18N_DIR.glob("*.json")]
def load_translations(lang):
    try:
        with open(I18N_DIR / f"{lang}.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(I18N_DIR / "en.json", encoding="utf-8") as f:
            return json.load(f)

from typing import List, Dict, Any
import sqlite3

DB_PATH = config.database.path

@app.get("/events.geojson", response_class=JSONResponse)
def events_geojson() -> Dict[str, Any]:
    """GeoJSON FeatureCollection de eventos recientes para el mapa."""
    features = []
    for ev in events_api():
        if ev["latlon"] and len(ev["latlon"]) == 2:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [ev["latlon"][1], ev["latlon"][0]]
                },
                "properties": {k: v for k, v in ev.items() if k != "latlon"}
            })
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/historical.geojson", response_class=JSONResponse)
def historical_geojson() -> Dict[str, Any]:
    """GeoJSON FeatureCollection para eventos históricos (100 años)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT lat, lon, title, description, published_at, source, type, fatalities
            FROM historical_events
            WHERE lat IS NOT NULL AND lon IS NOT NULL
            ORDER BY published_at DESC
            LIMIT 5000
            """
        )
        rows = cursor.fetchall()
        features = []
        for lat, lon, title, desc, ts, src, ev_type, fat in rows:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "title": title,
                    "description": desc,
                    "timestamp": ts,
                    "source": src,
                    "type": ev_type,
                    "fatalities": fat
                }
            })
        conn.close()
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        logger.error(f"Error historical geojson: {e}")
        return {"type": "FeatureCollection", "features": []}

# --- RISK GEOJSON ------------------------------------------------------------
@app.get("/risk_geojson", response_class=JSONResponse)
def risk_geojson() -> Dict[str, Any]:
    """Return country centroids colored by risk score (0-100)."""
    try:
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("SELECT iso3,risk FROM country_risk")
        rows=cur.fetchall();conn.close()
        try:
            from src.utils.geo import country_code_to_latlon
        except ImportError:
            # Fallback con coordenadas básicas
            def country_code_to_latlon(iso):
                coords = {
                    'US': (39.8283, -98.5795), 'GB': (55.3781, -3.4360), 'DE': (51.1657, 10.4515),
                    'FR': (46.2276, 2.2137), 'ES': (40.4637, -3.7492), 'IT': (41.8719, 12.5674),
                    'CN': (35.8617, 104.1954), 'JP': (36.2048, 138.2529), 'RU': (61.5240, 105.3188),
                    'IN': (20.5937, 78.9629), 'BR': (-14.2350, -51.9253), 'CA': (56.1304, -106.3468)
                }
                return coords.get(iso, None)
        
        feats=[]
        for iso,score in rows:
            latlon=country_code_to_latlon(iso)
            if not latlon:continue
            feats.append({"type":"Feature","geometry":{"type":"Point","coordinates":[latlon[1],latlon[0]]},"properties":{"iso":iso,"risk":score}})
        return {"type":"FeatureCollection","features":feats}
    except Exception as e:
        logger.error(f"risk_geojson: {e}");return {"type":"FeatureCollection","features":[]}

@app.get('/keywords_json', response_class=JSONResponse)
def keywords_json() -> List[Dict[str, Any]]:
    """Return top keywords from last 7 days events for word cloud."""
    stop={'THE','AND','OF','IN','ON','TO','A','AN','FOR','WITH','BY','AT','FROM','IS','ARE','AS','NEW','AFTER','OVER','ABOUT','BE','WAS','HAS'}
    try:
        conn=sqlite3.connect(DB_PATH);cur=conn.cursor()
        cur.execute("SELECT title FROM events WHERE published_at>=datetime('now','-7 days')")
        words={}
        for (title,) in cur.fetchall():
            for w in title.upper().split():
                w=re.sub(r'[^A-Z]','',w)
                if len(w)<4 or w in stop:continue
                words[w]=words.get(w,0)+1
        conn.close()
        top=sorted(words.items(),key=lambda x:x[1],reverse=True)[:50]
        return [{"text":k.title(),"size":10+v} for k,v in top]
    except Exception as e:
        logger.error(f"keywords_json error: {e}");return []

@app.get("/analysis_energy_conflict", response_class=JSONResponse)
def analysis_energy_conflict() -> List[Dict[str, Any]]:
    """Return global oil production (kbd) and conflict fatalities per year for correlation plot."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Sum fatalities per year
        cur.execute("SELECT substr(published_at,1,4) as yr, SUM(COALESCE(fatalities,0)) FROM historical_events GROUP BY yr")
        fatal_rows = {row[0]: row[1] for row in cur.fetchall()}
        # Sum global oil production per year
        cur.execute("SELECT year, SUM(oil_production_kbd) FROM country_energy GROUP BY year")
        oil_rows = {str(row[0]): row[1] for row in cur.fetchall()}
        years = sorted(set(fatal_rows.keys()).intersection(oil_rows.keys()))
        data = [{"year": int(y), "oil_kbd": oil_rows[y], "fatalities": fatal_rows[y]} for y in years if oil_rows[y] and fatal_rows[y]]
        conn.close()
        return data
    except Exception as e:
        logger.error(f"analysis_energy_conflict error: {e}")
        return []

@app.get("/analysis_data", response_class=JSONResponse)
def analysis_data() -> List[Dict[str, Any]]:
    """Aggregate fatalities per year from historical_events (100y)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT substr(published_at,1,4) as yr, SUM(COALESCE(fatalities,0))
            FROM historical_events
            WHERE yr IS NOT NULL
            GROUP BY yr
            ORDER BY yr
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"year": int(r[0]), "fatalities": int(r[1])} for r in rows if r[0]]
    except Exception as e:
        logger.error(f"analysis_data error: {e}")
        return []

@app.get("/risk_json", response_class=JSONResponse)
def risk_json() -> List[Dict[str, Any]]:
    try:
        conn=sqlite3.connect(DB_PATH);cur=conn.cursor()
        cur.execute("SELECT iso3,risk FROM country_risk ORDER BY risk DESC")
        rows=[{"iso":r[0],"risk":r[1]} for r in cur.fetchall()]
        conn.close();return rows
    except Exception as e:
        logger.error(f"risk_json error: {e}");return []

@app.get("/risk", response_class=HTMLResponse)
def risk_page(request: Request, lang:str="en"):
    translations=load_translations(lang)
    return templates.TemplateResponse("risk.html",{"request":request,"lang":lang,"translations":translations})

@app.get("/analysis", response_class=HTMLResponse)
def analysis_page(request: Request, lang: str = "en"):
    translations = load_translations(lang)
    return templates.TemplateResponse("analysis.html", {"request": request, "lang": lang, "translations": translations})

@app.get("/events", response_class=JSONResponse)
def events_api() -> List[Dict[str, Any]]:
    """Devuelve eventos recientes (últimos 7 días) en formato JSON para el mapa."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT title, content, published_at, source, location, type, magnitude FROM events
            WHERE published_at >= datetime('now', '-7 days')
            ORDER BY published_at DESC
            LIMIT 1000
            """
        )
        rows = cursor.fetchall()
        events = []
        for row in rows:
            try:
                latlon = json.loads(row[4]) if row[4] else None
            except Exception:
                latlon = None
            events.append({
                "title": row[0],
                "description": row[1],
                "timestamp": row[2],
                "source": row[3],
                "latlon": latlon,
                "type": row[5],
                "magnitude": row[6],
            })
        conn.close()
        return events
    except Exception as e:
        logger.error(f"Error fetching events for API: {e}")
        return []


@app.get("/favicon.ico")
async def favicon():
    """Servir el favicon"""
    from fastapi.responses import FileResponse
    favicon_path = Path(__file__).parent / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    else:
        return JSONResponse({"error": "Favicon not found"}, status_code=404)

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, lang: str = "en"):
    status = system_monitor.check_system_health()
    quality = data_validator.get_quality_report(days=7)
    translations = load_translations(lang)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "status": status,
            "quality": quality,
            "translations": translations,
            "lang": lang,
            "langs": LANGS
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.run_dashboard:app", host="0.0.0.0", port=8080, reload=True)
