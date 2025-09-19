# ESTRUCTURA DEL PROYECTO RISKMAP
=====================================

## 🏗️ Organización Post-Unificación

### 📁 `/core/` - Aplicaciones Principales
- `app_BUENA.py` - Aplicación web principal (Flask + Dash)
- `main.py` - Interfaz CLI para testing de componentes  
- `activate_agent.py` - Activación del sistema de agentes

### 📁 `/processors/` - Pipeline de Datos
- `advanced_geopolitical_nlp.py` - Sistema NLP avanzado
- `mass_article_processor.py` - Procesamiento masivo de artículos
- `database_unification.py` - Unificación de esquemas de BD
- `migrate_to_unified_articles.py` - Migración de endpoints
- `enriquecimiento_masivo_nuevo.py` - Enriquecimiento de datos

### 📁 `/utils/` - Utilidades y Helpers
- `free_translation_v4.py` - Sistema de traducción (LibreTranslate + Groq)
- `ai_importance_calculator.py` - Cálculo de importancia con IA
- `advanced_image_extractor.py` - Extracción avanzada de imágenes
- `check_db_simple.py` - Verificación rápida de BD
- `show_all_databases.py` - Enumeración de todas las tablas

### 📁 `/archived/` - Scripts Obsoletos
- Scripts de debug, test y experimentación
- Versiones antiguas de componentes
- Automation blocks obsoletos

## 🗄️ Base de Datos Unificada

### Tabla Principal: `unified_articles` (79 columnas)
- ✅ Contiene todos los artículos y metadatos
- ✅ Incluye resultados de NLP avanzado
- ✅ Optimizada con índices de rendimiento
- ✅ Única fuente de verdad para artículos

### Tablas Eliminadas (Redundantes):
- ❌ `articles` - Migrado a unified_articles
- ❌ `processed_data` - Integrado en unified_articles
- ❌ 10 tablas vacías eliminadas

## 🌐 Frontend Optimizado

### Templates Principales:
- `src/web/templates/dashboard_BUENO.html` - Dashboard principal
- `src/web/templates/conflict_monitoring.html` - Monitoreo de conflictos
- `src/web/templates/satellite_analysis.html` - Análisis satelital
- `src/web/templates/executive_reports.html` - Reportes ejecutivos

### Archivados:
- 37 templates obsoletos/duplicados archivados
- Estructura limpia y mantenible

## ⚡ Rendimiento

### Optimizaciones Implementadas:
- ✅ Índices optimizados en unified_articles
- ✅ Queries unificadas (eliminando JOINs complejos)
- ✅ Base de datos compactada (VACUUM)
- ✅ 82 queries actualizadas automáticamente

## 🔄 Próximos Pasos

1. **Validación**: Probar todos los endpoints después del reinicio
2. **Monitoreo**: Verificar rendimiento en primeras 24 horas  
3. **Mantenimiento**: Usar scripts de /utils/ para verificaciones
4. **Desarrollo**: Nuevos features en estructura organizada

## 📊 Estadísticas de Unificación

- **Tablas eliminadas**: 12
- **Scripts organizados**: 50+
- **Templates limpiados**: 37
- **Queries actualizadas**: 82
- **Estructura optimizada**: ✅ Completa

---
Generado automáticamente - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
