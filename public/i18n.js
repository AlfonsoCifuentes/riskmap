


/**
 * RiskMap A.I. — Internationalization System
 * Supports: Spanish (es, default), English (en)
 * Usage:
 *   HTML: <span data-i18n="nav.news">Análisis de Noticias</span>
 *   JS:   i18n.t('risk.critical')  → "Crítico" or "Critical"
 *   Toggle: i18n.toggle()  |  i18n.setLang('en')
 */
(function () {
  'use strict';

  var T = {
    /* ═══════════════════════════════════════════════════════════
       SPANISH (default)
       ═══════════════════════════════════════════════════════════ */
    es: {
      /* ── Navigation ── */
      'nav.news': 'Análisis de Noticias',
      'nav.conflicts': 'Monitor de Conflictos',
      'nav.trends': 'Análisis de Tendencias',
      'nav.earlyWarning': 'Alertas Tempranas',
      'nav.reports': 'Reportes Ejecutivos',
      'nav.dataIntel': 'Inteligencia de Datos',
      'nav.satellite': 'Análisis Satelital',
      'nav.video': 'Vigilancia por Video',
      'nav.historical': 'Análisis Histórico',
      'nav.about': 'Acerca de',
      'nav.logs': 'Registros',
      'nav.settings': 'Configuración',

      /* ── Common ── */
      'common.loading': 'Cargando...',
      'common.na': 'N/D',
      'common.now': 'Ahora',
      'common.noTitle': 'Sin título',
      'common.unknownSource': 'Fuente desconocida',
      'common.readSource': 'Leer fuente',
      'common.articles': 'artículos',
      'common.risk': 'Riesgo',
      'common.noData': 'Sin datos disponibles',
      'common.active': 'Activo',
      'common.noDataShort': 'Sin datos',

      /* ── Risk Levels ── */
      'risk.critical': 'Crítico',
      'risk.high': 'Alto',
      'risk.medium': 'Medio',
      'risk.low': 'Bajo',
      'risk.unknown': 'Sin clasificar',

      /* ──────────────────────────────────────────
         INDEX — Análisis de Noticias
         ────────────────────────────────────────── */
      'index.eyebrow': 'Inteligencia Geopolítica Operativa',
      'index.title': 'Monitoreo global de conflictos en tiempo real',
      'index.desc': 'Pipeline automatizado de ingesta multi-fuente, filtrado de conflictos geopolíticos y desastres naturales, curación editorial, análisis con IA y visualización geoespacial — sin simulaciones, solo datos operacionales.',
      'index.tag1': 'Ingesta multi-fuente',
      'index.tag2': 'Filtrado geopolítico',
      'index.tag3': 'Mapa de calor',
      'index.tag4': 'GDELT & ACLED',
      'index.tag5': 'Computer Vision',
      'index.featured': 'Destacado',
      'index.kpiArticles': 'Artículos geopolíticos',
      'index.kpiAlerts': 'Alertas críticas',
      'index.kpiRegions': 'Regiones en conflicto',
      'index.kpiSources': 'Fuentes activas',
      'index.pipeline': 'Pipeline de Inteligencia',
      'index.curatedNews': 'Noticias Curadas',
      'index.loadingArticles': 'Cargando artículos...',
      'index.hotspots': 'Hotspots Globales',
      'index.loadingHotspots': 'Calculando zonas...',
      'index.noFeatured': 'No hay noticia destacada disponible.',
      'index.noArticles': 'Sin artículos',
      'index.noArticlesDesc': 'No hay noticias curadas disponibles.',
      'index.noHotspots': 'Sin hotspots',
      'index.noHotspotsDesc': 'No hay zonas disponibles.',
      'index.unknownZone': 'Zona desconocida',
      /* Pipeline step labels */
      'pipe.ingest': 'Ingesta',
      'pipe.ingestDesc': 'Multi-fuente',
      'pipe.filter': 'Filtrado',
      'pipe.filterDesc': 'Geopolítico/desastre',
      'pipe.curation': 'Curación',
      'pipe.curationDesc': 'Dedup + calidad',
      'pipe.rewrite': 'Reescritura',
      'pipe.rewriteDesc': 'IA normalización',
      'pipe.heatmap': 'Heatmap',
      'pipe.heatmapDesc': 'Geoespacial',
      'pipe.gdelt': 'GDELT',
      'pipe.gdeltDesc': 'Correlación',
      'pipe.dashboards': 'Dashboards',
      'pipe.dashboardsDesc': 'Zonas activas',
      'pipe.cv': 'CV',
      'pipe.cvDesc': 'Señales visuales',

      /* ──────────────────────────────────────────
         CONFLICT MONITORING
         ────────────────────────────────────────── */
      'conflicts.title': 'Monitor Geoespacial de Conflictos',
      'conflicts.desc': 'Mapa operativo en tiempo real basado en artículos geolocalizados, señales y eventos. Todas las capas provienen de datos reales de la plataforma.',
      'conflicts.kpiPoints': 'Puntos geoespaciales',
      'conflicts.kpiZones': 'Zonas activas',
      'conflicts.kpiHigh': 'Riesgo alto',
      'conflicts.kpiArticles': 'Artículos analizados',
      'conflicts.topZones': 'Zonas de mayor prioridad',
      'conflicts.loadingZones': 'Cargando zonas...',
      'conflicts.noZones': 'Sin zonas',
      'conflicts.noZonesDesc': 'No hay conflictos geolocalizados.',
      'conflicts.unknownZone': 'Zona no identificada',

      /* ──────────────────────────────────────────
         TRENDS ANALYSIS
         ────────────────────────────────────────── */
      'trends.title': 'Tendencias de Riesgo y Cobertura',
      'trends.desc': 'Monitor de evolución temporal, distribución de riesgo y fuentes predominantes del sistema de inteligencia.',
      'trends.kpiArticles': 'Artículos geopolíticos',
      'trends.kpiRisk': 'Riesgo promedio',
      'trends.kpiSources': 'Fuentes activas',
      'trends.kpiZones': 'Zonas activas',
      'trends.dailyEvolution': 'Evolución diaria de noticias',
      'trends.riskDistribution': 'Distribución de riesgo',
      'trends.conflictCategories': 'Categorías de conflicto',
      'trends.topSources': 'Top fuentes',
      'trends.loadingSources': 'Cargando fuentes...',
      'trends.noSources': 'Sin fuentes',
      'trends.noSourcesDesc': 'No hay fuentes activas registradas.',
      'trends.errorAnalytics': 'No se pudo cargar analytics',

      /* ──────────────────────────────────────────
         EARLY WARNING
         ────────────────────────────────────────── */
      'earlyWarning.title': 'Centro de Alertas Tempranas',
      'earlyWarning.desc': 'Prioriza señales y noticias con mayor riesgo para acelerar respuesta operativa en conflictos y desastres.',
      'earlyWarning.kpiHighRisk': 'Noticias alto riesgo',
      'earlyWarning.kpiSignals': 'Señales activas',
      'earlyWarning.kpiCritical': 'Eventos críticos',
      'earlyWarning.kpiRegions': 'Regiones bajo presión',
      'earlyWarning.newsHighRisk': 'Noticias con riesgo alto/crítico',
      'earlyWarning.operationalSignals': 'Señales operativas y eventos',
      'earlyWarning.loadingNews': 'Cargando alertas de noticias...',
      'earlyWarning.loadingSignals': 'Cargando señales...',
      'earlyWarning.noDesc': 'Sin descripción',
      'earlyWarning.noAlerts': 'Sin alertas altas',
      'earlyWarning.noAlertsDesc': 'No hay noticias de riesgo alto en este momento.',
      'earlyWarning.noSignals': 'Sin señales',
      'earlyWarning.noSignalsDesc': 'No hay señales ni eventos críticos disponibles.',
      'earlyWarning.loadError': 'No se pudo cargar',
      'earlyWarning.loadErrorDesc': 'La fuente de datos no responde ahora mismo. No implica que no haya alertas — reintenta en unos segundos.',

      /* ──────────────────────────────────────────
         EXECUTIVE REPORTS
         ────────────────────────────────────────── */
      'reports.title': 'Informe Ejecutivo Dinámico',
      'reports.desc': 'Resumen estratégico generado con el estado actual de la plataforma, datos de conflicto, eventos y señales de riesgo.',
      'reports.kpiArticles': 'Artículos analizados',
      'reports.kpiAlerts': 'Alertas críticas',
      'reports.kpiCritical': 'Alertas críticas',
      'reports.kpiSignals': 'Signals activas',
      'reports.kpiEvents': 'Eventos en seguimiento',
      'reports.narrative': 'Narrativa Ejecutiva',
      'reports.hotspots': 'Focos prioritarios',
      'reports.btnRefresh': 'Actualizar informe',
      'reports.refresh': 'Actualizar informe',
      'reports.btnDownload': 'Descargar .md',
      'reports.download': 'Descargar .md',
      'reports.loading': 'Cargando informe...',
      'reports.issueDate': 'Fecha de emisión:',
      'reports.noHotspots': 'Sin focos',
      'reports.noHotspotsDesc': 'No hay hotspots disponibles.',

      /* ──────────────────────────────────────────
         DATA INTELLIGENCE
         ────────────────────────────────────────── */
      'dataIntel.title': 'Orquestación de Data Intelligence',
      'dataIntel.desc': 'Vista integral del flujo operativo: ingesta, filtrado, curación, reescritura, georreferenciación, contraste con eventos y análisis por visión computacional.',
      'dataIntel.kpiIngest': 'Ingesta total',
      'dataIntel.kpiGeo': 'Filtrado geopolítico',
      'dataIntel.kpiFiltered': 'Filtrado geopolítico',
      'dataIntel.kpiHeatmap': 'Puntos heatmap',
      'dataIntel.kpiHeat': 'Puntos heatmap',
      'dataIntel.kpiCV': 'Evidencia visual',
      'dataIntel.kpiVision': 'Evidencia visual',
      'dataIntel.pipeline': 'Pipeline end-to-end',
      'dataIntel.sources': 'Validación de fuentes',
      'dataIntel.sourceValidation': 'Validación de fuentes',
      'dataIntel.events': 'Eventos operativos recientes',
      'dataIntel.recentEvents': 'Eventos operativos recientes',
      'dataIntel.loadingAll': 'Cargando...',
      'dataIntel.noSources': 'Sin fuentes disponibles',
      'dataIntel.thSource': 'Fuente',
      'dataIntel.thArticles': 'Artículos',
      'dataIntel.thStatus': 'Estado',
      'dataIntel.noEvents': 'Sin eventos',
      'dataIntel.noEventsDesc': 'No se detectaron eventos recientes.',
      /* Pipeline steps */
      'dataIntel.step1': '1. Ingesta multi-medio',
      'dataIntel.step1Desc': 'Noticias incorporadas desde fuentes RSS/API.',
      'dataIntel.step2': '2. Filtrado geopolítico',
      'dataIntel.step2Desc': 'Artículos relevantes retenidos por el clasificador.',
      'dataIntel.step3': '3. Curación editorial',
      'dataIntel.step3Desc': 'Deduplicación y priorización de contenido.',
      'dataIntel.step4': '4. Reescritura IA',
      'dataIntel.step4Desc': 'Artículos con resumen IA / síntesis estructurada.',
      'dataIntel.step5': '5. Mapa de calor',
      'dataIntel.step5Desc': 'Puntos geográficos para monitorización cartográfica.',
      'dataIntel.step6': '6. Contraste eventos',
      'dataIntel.step6Desc': 'Eventos correlacionados en la base operacional.',
      'dataIntel.step7': '7. Dashboards analíticos',
      'dataIntel.step7Desc': 'Zonas activas para explotación analítica.',
      'dataIntel.step8': '8. Computer Vision',
      'dataIntel.step8Desc': 'Signals e imágenes para validación visual.',

      /* ──────────────────────────────────────────
         SATELLITE ANALYSIS
         ────────────────────────────────────────── */
      'satellite.title': 'Análisis Satelital y Evidencia Visual',
      'satellite.desc': 'Inventario de capturas satelitales/EO y señales asociadas para detección de actividad militar, daños estructurales y desastres.',
      'satellite.kpiImages': 'Imágenes registradas',
      'satellite.kpiGeo': 'Con geolocalización',
      'satellite.kpiSignals': 'Signals vinculadas',
      'satellite.kpiEvents': 'Eventos relacionados',
      'satellite.gallery': 'Galería de imágenes satelitales',
      'satellite.loadingImages': 'Cargando imágenes...',
      'satellite.openCapture': 'Abrir captura',
      'satellite.noPreview': 'Sin preview binario',
      'satellite.event': 'Evento:',
      'satellite.aoi': 'AOI:',
      'satellite.coords': 'Coords:',
      'satellite.captured': 'Capturada:',
      'satellite.noImages': 'Sin imágenes satelitales',
      'satellite.noImagesDesc': 'No hay registros source_type=satellite en la base actual.',

      /* ──────────────────────────────────────────
         VIDEO SURVEILLANCE
         ────────────────────────────────────────── */
      'video.title': 'Vigilancia Visual Operativa',
      'video.desc': 'Consolidación de capturas de cámaras públicas/feeds visuales y señales vinculadas para detección temprana de actividad anómala.',
      'video.kpiFeeds': 'Feeds detectados',
      'video.kpiSignals': 'Signals visuales',
      'video.kpiDetection': 'Con detección',
      'video.kpiDetections': 'Con detección',
      'video.kpiGeo': 'Feeds geolocalizados',
      'video.feedsSection': 'Feeds y evidencias',
      'video.feedsTitle': 'Feeds y evidencias',
      'video.loadingFeeds': 'Cargando feeds...',
      'video.openFeed': 'Abrir feed',
      'video.noFeeds': 'Sin feeds de video',
      'video.noFeedsDesc': 'No hay registros de cámaras/webcams en images.source_type.',
      'video.source': 'Source:',
      'video.coords': 'Coords:',
      'video.capture': 'Captura:',

      /* ──────────────────────────────────────────
         HISTORICAL ANALYSIS
         ────────────────────────────────────────── */
      'historical.title': 'Perspectiva Histórica de Cobertura',
      'historical.desc': 'Análisis temporal de publicaciones y concentración geográfica para detectar patrones persistentes de conflicto.',
      'historical.kpiArticles': 'Noticias analizadas',
      'historical.kpiLoaded': 'Noticias analizadas',
      'historical.kpiMonths': 'Meses con actividad',
      'historical.kpiCountries': 'Países con cobertura',
      'historical.kpiMax': 'Máx. artículos/mes',
      'historical.kpiTop': 'Máx. artículos/mes',
      'historical.timeSeries': 'Serie temporal (mensual)',
      'historical.topCountries': 'Países más cubiertos',
      'historical.loading': 'Cargando histórico...',
      'historical.loadingHistory': 'Cargando histórico...',
      'historical.noData': 'Sin histórico',
      'historical.noDataDesc': 'No hay artículos disponibles para serie histórica.',
      'historical.unspecified': 'No especificado',
      'historical.chartLabel': 'Artículos',

      /* ──────────────────────────────────────────
         ABOUT
         ────────────────────────────────────────── */
      'about.title': 'Arquitectura y Metodología',
      'about.desc': 'Riskmap A.I. integra OSINT, analítica geoespacial y señales visuales para inteligencia geopolítica y respuesta ante desastres.',
      'about.workflow': 'Flujo operativo implementado',
      'about.principles': 'Principios de diseño',
      'about.activeSources': 'Fuentes activas detectadas',
      'about.sourcesActive': 'Fuentes activas detectadas',
      'about.platformStatus': 'Estado de la plataforma',
      'about.step1': 'Ingesta automatizada multi-fuente con pipeline programado.',
      'about.step2': 'Filtrado geopolítico y de desastres con reglas de relevancia.',
      'about.step3': 'Curación y deduplicación de artículos para calidad de señal.',
      'about.step4': 'Reescritura/resumen para briefing ejecutivo.',
      'about.step5': 'Geolocalización y generación de mapa de calor.',
      'about.step6': 'Contraste con eventos y señales (incluyendo etiquetas GDELT cuando existan).',
      'about.step7': 'Dashboards de tendencias, alertas, histórico y reporting.',
      'about.step8': 'Correlación con evidencias visuales (satélite/cámara).',
      'about.principlesText': 'La nueva interfaz prioriza narrativa de datos, jerarquía visual clara y lectura rápida en contextos de alta presión operacional. Se ha aplicado una estética editorial inmersiva y navegación consistente para facilitar análisis continuo.',
      'about.loadingSources': 'Cargando fuentes...',
      'about.loadingStatus': 'Cargando estado...',
      'about.noSources': 'No hay fuentes disponibles.',
      'about.noStatus': 'No se pudo obtener estado del sistema.',
      'about.unknownSource': 'Fuente',
      'about.geoArticles': 'Artículos geopolíticos:',
      'about.critAlerts': 'Alertas críticas:',
      'about.criticalAlerts': 'Alertas críticas:',
      'about.regionsConflict': 'Regiones en conflicto:',
      'about.conflictRegions': 'Regiones en conflicto:',
      'about.activeSrcCount': 'Fuentes activas:',
      'about.activeSourcesCount': 'Fuentes activas:',

      /* ──────────────────────────────────────────
         LOGS
         ────────────────────────────────────────── */
      'logs.title': 'Health & Endpoint Logs',
      'logs.desc': 'Monitor de salud de endpoints críticos usados por el website y el pipeline operativo.',
      'logs.btnCheck': 'Comprobar endpoints',
      'logs.checkEndpoints': 'Comprobar endpoints',
      'logs.btnAutoOff': 'Auto-refresh: OFF',
      'logs.autoRefreshOff': 'Auto-refresh: OFF',
      'logs.btnAutoOn': 'Auto-refresh: ON',
      'logs.apiStatus': 'Estado de APIs',
      'logs.stream': 'Stream técnico',
      'logs.techStream': 'Stream técnico',
      'logs.thEndpoint': 'Endpoint',
      'logs.thStatus': 'Estado',
      'logs.thTime': 'Tiempo',
      'logs.thItems': 'Items',
      'logs.thLastCheck': 'Última comprobación',
      'logs.autoOn': 'Auto-refresh cada 60s activado',
      'logs.autoOff': 'Auto-refresh desactivado',
      'logs.startCheck': 'Iniciando comprobación de endpoints',

      /* ──────────────────────────────────────────
         SETTINGS
         ────────────────────────────────────────── */
      'settings.title': 'Preferencias Operativas',
      'settings.desc': 'Personaliza la experiencia del dashboard y guarda configuración local para tu sesión de análisis.',
      'settings.profile': 'Perfil de analista',
      'settings.panel': 'Comportamiento del panel',
      'settings.panelBehavior': 'Comportamiento del panel',
      'settings.analystName': 'Nombre del analista',
      'settings.namePlaceholder': 'Tu nombre',
      'settings.briefingFreq': 'Frecuencia de briefing',
      'settings.freq2h': 'Cada 2 horas',
      'settings.freq6h': 'Cada 6 horas',
      'settings.freq12h': 'Cada 12 horas',
      'settings.freqDaily': 'Diario',
      'settings.priorityRegions': 'Regiones prioritarias',
      'settings.watchRegions': 'Regiones prioritarias',
      'settings.regionsPlaceholder': 'Ejemplo: Oriente Medio, Mar Negro, Sahel',
      'settings.btnSave': 'Guardar configuración',
      'settings.save': 'Guardar configuración',
      'settings.btnReset': 'Restaurar valores',
      'settings.toggleAutoRefresh': 'Auto-refresh páginas de monitoreo',
      'settings.autoRefresh': 'Auto-refresh páginas de monitoreo',
      'settings.toggleAnimations': 'Animaciones reducidas',
      'settings.reduceMotion': 'Animaciones reducidas',
      'settings.toggleTimestamps': 'Mostrar timestamps absolutos',
      'settings.absoluteTime': 'Mostrar timestamps absolutos',
      'settings.toggleCompact': 'Modo compacto en tablas',
      'settings.compactTables': 'Modo compacto en tablas',
      'settings.apiQuickStatus': 'Estado rápido de API',
      'settings.checking': 'Comprobando...',
      'settings.apiActive': 'API activa',
      'settings.apiUnavailable': 'API no disponible',
      'settings.saved': 'Configuración guardada',
      'settings.reset': 'Configuración restablecida',
      'settings.resetDone': 'Configuración restablecida',
      'settings.criticalAlerts': 'alertas críticas',
    },

    /* ═══════════════════════════════════════════════════════════
       ENGLISH
       ═══════════════════════════════════════════════════════════ */
    en: {
      /* ── Navigation ── */
      'nav.news': 'News Analysis',
      'nav.conflicts': 'Conflict Monitor',
      'nav.trends': 'Trend Analysis',
      'nav.earlyWarning': 'Early Warnings',
      'nav.reports': 'Executive Reports',
      'nav.dataIntel': 'Data Intelligence',
      'nav.satellite': 'Satellite Analysis',
      'nav.video': 'Video Surveillance',
      'nav.historical': 'Historical Analysis',
      'nav.about': 'About',
      'nav.logs': 'Logs',
      'nav.settings': 'Settings',

      /* ── Common ── */
      'common.loading': 'Loading...',
      'common.na': 'N/A',
      'common.now': 'Now',
      'common.noTitle': 'No title',
      'common.unknownSource': 'Unknown source',
      'common.readSource': 'Read source',
      'common.articles': 'articles',
      'common.risk': 'Risk',
      'common.noData': 'No data available',
      'common.active': 'Active',
      'common.noDataShort': 'No data',

      /* ── Risk Levels ── */
      'risk.critical': 'Critical',
      'risk.high': 'High',
      'risk.medium': 'Medium',
      'risk.low': 'Low',
      'risk.unknown': 'Unrated',

      /* ── INDEX ── */
      'index.eyebrow': 'Operative Geopolitical Intelligence',
      'index.title': 'Real-time global conflict monitoring',
      'index.desc': 'Automated multi-source ingestion pipeline, geopolitical conflict and natural disaster filtering, editorial curation, AI analysis, and geospatial visualization — no simulations, only operational data.',
      'index.tag1': 'Multi-source ingestion',
      'index.tag2': 'Geopolitical filtering',
      'index.tag3': 'Heatmap',
      'index.tag4': 'GDELT & ACLED',
      'index.tag5': 'Computer Vision',
      'index.featured': 'Featured',
      'index.kpiArticles': 'Geopolitical articles',
      'index.kpiAlerts': 'Critical alerts',
      'index.kpiRegions': 'Conflict regions',
      'index.kpiSources': 'Active sources',
      'index.pipeline': 'Intelligence Pipeline',
      'index.curatedNews': 'Curated News',
      'index.loadingArticles': 'Loading articles...',
      'index.hotspots': 'Global Hotspots',
      'index.loadingHotspots': 'Calculating zones...',
      'index.noFeatured': 'No featured article available.',
      'index.noArticles': 'No articles',
      'index.noArticlesDesc': 'No curated news available.',
      'index.noHotspots': 'No hotspots',
      'index.noHotspotsDesc': 'No zones available.',
      'index.unknownZone': 'Unknown zone',
      'pipe.ingest': 'Ingestion',
      'pipe.ingestDesc': 'Multi-source',
      'pipe.filter': 'Filtering',
      'pipe.filterDesc': 'Geopolitical/disaster',
      'pipe.curation': 'Curation',
      'pipe.curationDesc': 'Dedup + quality',
      'pipe.rewrite': 'Rewriting',
      'pipe.rewriteDesc': 'AI normalization',
      'pipe.heatmap': 'Heatmap',
      'pipe.heatmapDesc': 'Geospatial',
      'pipe.gdelt': 'GDELT',
      'pipe.gdeltDesc': 'Correlation',
      'pipe.dashboards': 'Dashboards',
      'pipe.dashboardsDesc': 'Active zones',
      'pipe.cv': 'CV',
      'pipe.cvDesc': 'Visual signals',

      /* ── CONFLICT MONITORING ── */
      'conflicts.title': 'Geospatial Conflict Monitor',
      'conflicts.desc': 'Real-time operational map based on geolocated articles, signals, and events. All layers come from real platform data.',
      'conflicts.kpiPoints': 'Geospatial points',
      'conflicts.kpiZones': 'Active zones',
      'conflicts.kpiHigh': 'High risk',
      'conflicts.kpiArticles': 'Analyzed articles',
      'conflicts.topZones': 'Highest Priority Zones',
      'conflicts.loadingZones': 'Loading zones...',
      'conflicts.noZones': 'No zones',
      'conflicts.noZonesDesc': 'No geolocated conflicts found.',
      'conflicts.unknownZone': 'Unidentified zone',

      /* ── TRENDS ANALYSIS ── */
      'trends.title': 'Risk & Coverage Trends',
      'trends.desc': 'Temporal evolution monitor, risk distribution, and predominant sources from the intelligence system.',
      'trends.kpiArticles': 'Geopolitical articles',
      'trends.kpiRisk': 'Average risk',
      'trends.kpiSources': 'Active sources',
      'trends.kpiZones': 'Active zones',
      'trends.dailyEvolution': 'Daily news evolution',
      'trends.riskDistribution': 'Risk distribution',
      'trends.conflictCategories': 'Conflict categories',
      'trends.topSources': 'Top sources',
      'trends.loadingSources': 'Loading sources...',
      'trends.noSources': 'No sources',
      'trends.noSourcesDesc': 'No active sources registered.',
      'trends.errorAnalytics': 'Failed to load analytics',

      /* ── EARLY WARNING ── */
      'earlyWarning.title': 'Early Warning Center',
      'earlyWarning.desc': 'Prioritizes signals and news with highest risk to accelerate operational response in conflicts and disasters.',
      'earlyWarning.kpiHighRisk': 'High risk news',
      'earlyWarning.kpiSignals': 'Active signals',
      'earlyWarning.kpiCritical': 'Critical events',
      'earlyWarning.kpiRegions': 'Regions under pressure',
      'earlyWarning.newsHighRisk': 'High/Critical risk news',
      'earlyWarning.operationalSignals': 'Operational signals & events',
      'earlyWarning.loadingNews': 'Loading news alerts...',
      'earlyWarning.loadingSignals': 'Loading signals...',
      'earlyWarning.noDesc': 'No description',
      'earlyWarning.noAlerts': 'No high alerts',
      'earlyWarning.noAlertsDesc': 'No high-risk news at this time.',
      'earlyWarning.noSignals': 'No signals',
      'earlyWarning.noSignalsDesc': 'No critical signals or events available.',
      'earlyWarning.loadError': 'Could not load',
      'earlyWarning.loadErrorDesc': 'The data source is not responding right now. This does not mean there are no alerts — retry in a few seconds.',

      /* ── EXECUTIVE REPORTS ── */
      'reports.title': 'Dynamic Executive Report',
      'reports.desc': 'Strategic summary generated from the current platform state, conflict data, events, and risk signals.',
      'reports.kpiArticles': 'Analyzed articles',
      'reports.kpiAlerts': 'Critical alerts',
      'reports.kpiCritical': 'Critical alerts',
      'reports.kpiSignals': 'Active signals',
      'reports.kpiEvents': 'Events tracked',
      'reports.narrative': 'Executive Narrative',
      'reports.hotspots': 'Priority Hotspots',
      'reports.btnRefresh': 'Refresh report',
      'reports.refresh': 'Refresh report',
      'reports.btnDownload': 'Download .md',
      'reports.download': 'Download .md',
      'reports.loading': 'Loading report...',
      'reports.issueDate': 'Issue date:',
      'reports.noHotspots': 'No hotspots',
      'reports.noHotspotsDesc': 'No hotspots available.',

      /* ── DATA INTELLIGENCE ── */
      'dataIntel.title': 'Data Intelligence Orchestration',
      'dataIntel.desc': 'Comprehensive view of the operational flow: ingestion, filtering, curation, rewriting, georeferencing, event correlation, and computer vision analysis.',
      'dataIntel.kpiIngest': 'Total ingestion',
      'dataIntel.kpiGeo': 'Geopolitical filter',
      'dataIntel.kpiFiltered': 'Geopolitical filter',
      'dataIntel.kpiHeatmap': 'Heatmap points',
      'dataIntel.kpiHeat': 'Heatmap points',
      'dataIntel.kpiCV': 'Visual evidence',
      'dataIntel.kpiVision': 'Visual evidence',
      'dataIntel.pipeline': 'End-to-end Pipeline',
      'dataIntel.sources': 'Source validation',
      'dataIntel.sourceValidation': 'Source validation',
      'dataIntel.events': 'Recent operational events',
      'dataIntel.recentEvents': 'Recent operational events',
      'dataIntel.loadingAll': 'Loading...',
      'dataIntel.noSources': 'No sources available',
      'dataIntel.thSource': 'Source',
      'dataIntel.thArticles': 'Articles',
      'dataIntel.thStatus': 'Status',
      'dataIntel.noEvents': 'No events',
      'dataIntel.noEventsDesc': 'No recent events detected.',
      'dataIntel.step1': '1. Multi-media ingestion',
      'dataIntel.step1Desc': 'News ingested from RSS/API sources.',
      'dataIntel.step2': '2. Geopolitical filtering',
      'dataIntel.step2Desc': 'Relevant articles retained by classifier.',
      'dataIntel.step3': '3. Editorial curation',
      'dataIntel.step3Desc': 'Deduplication and content prioritization.',
      'dataIntel.step4': '4. AI rewriting',
      'dataIntel.step4Desc': 'Articles with AI summary / structured synthesis.',
      'dataIntel.step5': '5. Heatmap',
      'dataIntel.step5Desc': 'Geographic points for cartographic monitoring.',
      'dataIntel.step6': '6. Event correlation',
      'dataIntel.step6Desc': 'Events correlated in operational database.',
      'dataIntel.step7': '7. Analytical dashboards',
      'dataIntel.step7Desc': 'Active zones for analytical exploitation.',
      'dataIntel.step8': '8. Computer Vision',
      'dataIntel.step8Desc': 'Signals and images for visual validation.',

      /* ── SATELLITE ANALYSIS ── */
      'satellite.title': 'Satellite Analysis & Visual Evidence',
      'satellite.desc': 'Inventory of satellite/EO captures and associated signals for military activity detection, structural damage, and disasters.',
      'satellite.kpiImages': 'Registered images',
      'satellite.kpiGeo': 'Geolocated',
      'satellite.kpiSignals': 'Linked signals',
      'satellite.kpiEvents': 'Related events',
      'satellite.gallery': 'Satellite image gallery',
      'satellite.loadingImages': 'Loading images...',
      'satellite.openCapture': 'Open capture',
      'satellite.noPreview': 'No binary preview',
      'satellite.event': 'Event:',
      'satellite.aoi': 'AOI:',
      'satellite.coords': 'Coords:',
      'satellite.captured': 'Captured:',
      'satellite.noImages': 'No satellite images',
      'satellite.noImagesDesc': 'No source_type=satellite records in current database.',

      /* ── VIDEO SURVEILLANCE ── */
      'video.title': 'Operational Visual Surveillance',
      'video.desc': 'Consolidation of public camera captures/visual feeds and linked signals for early detection of anomalous activity.',
      'video.kpiFeeds': 'Detected feeds',
      'video.kpiSignals': 'Visual signals',
      'video.kpiDetection': 'With detection',
      'video.kpiDetections': 'With detection',
      'video.kpiGeo': 'Geolocated feeds',
      'video.feedsSection': 'Feeds & evidence',
      'video.feedsTitle': 'Feeds & evidence',
      'video.loadingFeeds': 'Loading feeds...',
      'video.openFeed': 'Open feed',
      'video.noFeeds': 'No video feeds',
      'video.noFeedsDesc': 'No camera/webcam records in images.source_type.',
      'video.source': 'Source:',
      'video.coords': 'Coords:',
      'video.capture': 'Capture:',

      /* ── HISTORICAL ANALYSIS ── */
      'historical.title': 'Historical Coverage Perspective',
      'historical.desc': 'Temporal analysis of publications and geographic concentration to detect persistent conflict patterns.',
      'historical.kpiArticles': 'Analyzed articles',
      'historical.kpiLoaded': 'Analyzed articles',
      'historical.kpiMonths': 'Active months',
      'historical.kpiCountries': 'Countries covered',
      'historical.kpiMax': 'Max articles/month',
      'historical.kpiTop': 'Max articles/month',
      'historical.timeSeries': 'Time series (monthly)',
      'historical.topCountries': 'Most covered countries',
      'historical.loading': 'Loading history...',
      'historical.loadingHistory': 'Loading history...',
      'historical.noData': 'No history',
      'historical.noDataDesc': 'No articles available for historical series.',
      'historical.unspecified': 'Unspecified',
      'historical.chartLabel': 'Articles',

      /* ── ABOUT ── */
      'about.title': 'Architecture & Methodology',
      'about.desc': 'Riskmap A.I. integrates OSINT, geospatial analytics, and visual signals for geopolitical intelligence and disaster response.',
      'about.workflow': 'Implemented operational workflow',
      'about.principles': 'Design principles',
      'about.activeSources': 'Detected active sources',
      'about.sourcesActive': 'Detected active sources',
      'about.platformStatus': 'Platform status',
      'about.step1': 'Automated multi-source ingestion with scheduled pipeline.',
      'about.step2': 'Geopolitical and disaster filtering with relevance rules.',
      'about.step3': 'Article curation and deduplication for signal quality.',
      'about.step4': 'Rewriting/summarization for executive briefing.',
      'about.step5': 'Geolocation and heatmap generation.',
      'about.step6': 'Correlation with events and signals (including GDELT tags when available).',
      'about.step7': 'Trend, alert, historical, and reporting dashboards.',
      'about.step8': 'Correlation with visual evidence (satellite/camera).',
      'about.principlesText': 'The new interface prioritizes data narrative, clear visual hierarchy, and fast reading in high-pressure operational contexts. An immersive editorial aesthetic and consistent navigation have been applied to facilitate continuous analysis.',
      'about.loadingSources': 'Loading sources...',
      'about.loadingStatus': 'Loading status...',
      'about.noSources': 'No sources available.',
      'about.noStatus': 'Could not retrieve system status.',
      'about.unknownSource': 'Source',
      'about.geoArticles': 'Geopolitical articles:',
      'about.critAlerts': 'Critical alerts:',
      'about.criticalAlerts': 'Critical alerts:',
      'about.regionsConflict': 'Conflict regions:',
      'about.conflictRegions': 'Conflict regions:',
      'about.activeSrcCount': 'Active sources:',
      'about.activeSourcesCount': 'Active sources:',

      /* ── LOGS ── */
      'logs.title': 'Health & Endpoint Logs',
      'logs.desc': 'Health monitor for critical endpoints used by the website and the operational pipeline.',
      'logs.btnCheck': 'Check endpoints',
      'logs.checkEndpoints': 'Check endpoints',
      'logs.btnAutoOff': 'Auto-refresh: OFF',
      'logs.autoRefreshOff': 'Auto-refresh: OFF',
      'logs.btnAutoOn': 'Auto-refresh: ON',
      'logs.apiStatus': 'API Status',
      'logs.stream': 'Technical Stream',
      'logs.techStream': 'Technical Stream',
      'logs.thEndpoint': 'Endpoint',
      'logs.thStatus': 'Status',
      'logs.thTime': 'Time',
      'logs.thItems': 'Items',
      'logs.thLastCheck': 'Last check',
      'logs.autoOn': 'Auto-refresh every 60s enabled',
      'logs.autoOff': 'Auto-refresh disabled',
      'logs.startCheck': 'Starting endpoint check',

      /* ── SETTINGS ── */
      'settings.title': 'Operational Preferences',
      'settings.desc': 'Customize the dashboard experience and save local configuration for your analysis session.',
      'settings.profile': 'Analyst profile',
      'settings.panel': 'Panel behavior',
      'settings.panelBehavior': 'Panel behavior',
      'settings.analystName': 'Analyst name',
      'settings.namePlaceholder': 'Your name',
      'settings.briefingFreq': 'Briefing frequency',
      'settings.freq2h': 'Every 2 hours',
      'settings.freq6h': 'Every 6 hours',
      'settings.freq12h': 'Every 12 hours',
      'settings.freqDaily': 'Daily',
      'settings.priorityRegions': 'Priority regions',
      'settings.watchRegions': 'Priority regions',
      'settings.regionsPlaceholder': 'Example: Middle East, Black Sea, Sahel',
      'settings.btnSave': 'Save settings',
      'settings.save': 'Save settings',
      'settings.btnReset': 'Restore defaults',
      'settings.toggleAutoRefresh': 'Auto-refresh monitoring pages',
      'settings.autoRefresh': 'Auto-refresh monitoring pages',
      'settings.toggleAnimations': 'Reduced animations',
      'settings.reduceMotion': 'Reduced animations',
      'settings.toggleTimestamps': 'Show absolute timestamps',
      'settings.absoluteTime': 'Show absolute timestamps',
      'settings.toggleCompact': 'Compact table mode',
      'settings.compactTables': 'Compact table mode',
      'settings.apiQuickStatus': 'Quick API status',
      'settings.checking': 'Checking...',
      'settings.apiActive': 'API active',
      'settings.apiUnavailable': 'API unavailable',
      'settings.saved': 'Settings saved',
      'settings.reset': 'Settings restored',
      'settings.resetDone': 'Settings restored',
      'settings.criticalAlerts': 'critical alerts',
    }
  };

  /* ───────────────────────────────────────────────────────────
     Engine
     ─────────────────────────────────────────────────────────── */
  var lang = localStorage.getItem('riskmap-lang') || 'es';

  function t(key) {
    return (T[lang] && T[lang][key]) || (T.es && T.es[key]) || key;
  }

  function setLang(newLang) {
    if (newLang !== 'es' && newLang !== 'en') return;
    lang = newLang;
    localStorage.setItem('riskmap-lang', lang);
    document.documentElement.lang = lang;
    apply();
    updateToggle();
    window.dispatchEvent(new CustomEvent('langchange', { detail: { lang: lang } }));
  }

  function toggle() {
    setLang(lang === 'es' ? 'en' : 'es');
  }

  function apply() {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      var val = t(key);
      if (val !== key) el.textContent = val;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      el.title = t(el.getAttribute('data-i18n-title'));
    });
  }

  function updateToggle() {
    var btn = document.querySelector('.lang-toggle');
    if (btn) btn.textContent = lang.toUpperCase();
  }

  function getLang() { return lang; }

  /* ── Expose ── */
  window.i18n = {
    t: t,
    setLang: setLang,
    toggle: toggle,
    getLang: getLang,
    apply: apply
  };

  /* ── Auto-apply on DOM ready ── */
  document.addEventListener('DOMContentLoaded', function () {
    document.documentElement.lang = lang;
    apply();
    updateToggle();
  });
})();
