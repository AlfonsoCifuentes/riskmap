# Directorio de Informes Generados - RISKMAP

Este directorio almacena todos los informes generados automáticamente por el sistema RISKMAP.

## Estructura de Archivos

```
reports/
├── daily/           # Informes diarios
├── executive/       # Informes ejecutivos semanales
├── crisis/          # Informes de crisis especiales
├── assets/          # Recursos (logos, CSS, imágenes)
└── archive/         # Archivo histórico
```

## Tipos de Informes

### 📅 Informes Diarios
- **Archivo:** `riskmap_daily_YYYYMMDD.html`
- **Contenido:** Eventos del día, alertas críticas, resúmenes regionales
- **Frecuencia:** Diario a las 23:59

### 📊 Informes Ejecutivos
- **Archivo:** `riskmap_executive_YYYYMMDD_YYYYMMDD.html`
- **Contenido:** Análisis semanal completo, tendencias, recomendaciones estratégicas
- **Frecuencia:** Semanal (domingos)

### 🚨 Informes de Crisis
- **Archivo:** `riskmap_crisis_YYYYMMDD_HHMM.html`
- **Contenido:** Análisis urgente de eventos críticos
- **Frecuencia:** Bajo demanda (eventos críticos)

## Formatos de Salida

- **HTML:** Visualización interactiva con gráficos
- **PDF:** Versión imprimible para distribución
- **JSON:** Datos estructurados para APIs

## Configuración

Los informes se generan según la configuración en `config/config.yaml`:

```yaml
reporting:
  output_dir: "reports"
  formats: ["html", "pdf"]
  retention_days: 90
  archive_after_days: 30
```

## Acceso a Informes

- **Web Dashboard:** http://localhost:5000/reports
- **API:** http://localhost:5000/api/reports
- **Archivos locales:** Este directorio

---

*Generado automáticamente por RISKMAP Intelligence System*
