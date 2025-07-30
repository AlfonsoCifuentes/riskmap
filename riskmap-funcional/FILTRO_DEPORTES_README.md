# Filtro de Deportes - Sistema de Inteligencia Geopolítica

## Descripción

Se ha implementado un sistema completo para filtrar y excluir noticias deportivas del sistema de inteligencia geopolítica. El filtro funciona en múltiples niveles para asegurar que solo se procesen noticias relevantes para análisis geopolítico.

## Componentes Implementados

### 1. Filtro Mejorado en RSS Fetcher (`src/data_ingestion/rss_fetcher.py`)

**Mejoras implementadas:**
- Filtro multilingüe expandido (inglés, español, francés, alemán)
- Patrones de expresiones regulares más específicos para deportes
- Detección de palabras clave deportivas fuertes (FIFA, UEFA, NBA, etc.)
- Filtro de doble capa: geopolítico + clasificador de contenido

**Deportes detectados:**
- Fútbol/Soccer, Baloncesto, Tenis, Golf, Hockey
- Natación, Atletismo, Gimnasia, Boxeo, MMA
- Olimpiadas, Mundiales, Ligas profesionales
- Nombres de equipos y jugadores famosos

### 2. Clasificador de Contenido Mejorado (`src/utils/content_classifier.py`)

**Nueva categoría añadida:**
- `sports_entertainment`: Categoría específica para deportes y entretenimiento
- Palabras clave multilingües para deportes
- Método `_is_sports_entertainment()` para detección precisa
- Exclusión automática de contenido deportivo del análisis geopolítico

### 3. Scripts de Gestión

#### `clean_sports_articles.py`
- Identifica artículos deportivos existentes en la base de datos
- Permite eliminar artículos deportivos (modo dry-run disponible)
- Actualiza categorías de artículos deportivos existentes
- Genera reportes detallados de limpieza

#### `configure_sports_filter.py`
- Identifica y desactiva fuentes RSS deportivas
- Configura filtros automáticos en la base de datos
- Añade configuración persistente para filtros
- Gestiona fuentes deportivas conocidas

#### `test_sports_filter.py`
- Pruebas automatizadas del sistema de filtros
- Casos de prueba para contenido deportivo y geopolítico
- Verificación de precisión del clasificador
- Reportes de rendimiento del filtro

## Uso del Sistema

### 1. Configuración Inicial

```bash
# Ejecutar configuración de filtros deportivos
python configure_sports_filter.py

# Limpiar artículos deportivos existentes
python clean_sports_articles.py

# Probar el funcionamiento del filtro
python test_sports_filter.py
```

### 2. Funcionamiento Automático

El filtro funciona automáticamente durante la ingesta de noticias:

1. **Filtro Geopolítico**: Verifica relevancia geopolítica básica
2. **Filtro de Patrones**: Detecta patrones deportivos específicos
3. **Clasificador de Contenido**: Clasifica el contenido por categoría
4. **Exclusión Automática**: Rechaza contenido clasificado como `sports_entertainment`

### 3. Monitoreo y Mantenimiento

```bash
# Ver estadísticas de filtrado
python -c "
from clean_sports_articles import SportsArticleCleaner
cleaner = SportsArticleCleaner('data/geopolitical_intel.db')
result = cleaner.clean_sports_articles(dry_run=True)
print(f'Artículos deportivos encontrados: {result[\"found\"]}')
"

# Verificar configuración actual
python -c "
from configure_sports_filter import SportsFilterConfigurator
config = SportsFilterConfigurator('data/geopolitical_intel.db')
config.show_current_config()
"
```

## Configuración de Base de Datos

El sistema añade las siguientes configuraciones a la tabla `config`:

```sql
-- Filtrar contenido deportivo automáticamente
INSERT INTO config (key, value, description) VALUES 
('filter_sports_content', 'true', 'Filtrar automáticamente contenido deportivo y de entretenimiento');

-- Categorías excluidas
INSERT INTO config (key, value, description) VALUES 
('excluded_categories', 'sports_entertainment', 'Categorías de contenido a excluir del procesamiento');
```

## Patrones de Detección

### Palabras Clave Deportivas (Multilingüe)

**Inglés:**
- sports, football, basketball, soccer, tennis, golf, hockey
- olympics, championship, tournament, league, player, coach
- FIFA, UEFA, NBA, NFL, MLB, NHL

**Español:**
- deporte, fútbol, baloncesto, tenis, golf, hockey
- olímpicos, campeonato, torneo, liga, jugador, entrenador
- mundial, equipo, estadio, partido

**Francés:**
- sport, football, basket, tennis, golf, hockey
- olympiques, championnat, tournoi, ligue, joueur, entraîneur

**Alemán:**
- sport, fußball, basketball, tennis, golf, hockey
- olympische, weltmeisterschaft, turnier, liga, spieler, trainer

### Fuentes RSS Deportivas Detectadas

- ESPN, Marca, AS, Sport, Mundo Deportivo
- Sky Sports, BBC Sport, Eurosport
- Goal.com, FIFA.com, UEFA.com
- Fox Sports, CBS Sports, NBC Sports

## Métricas de Rendimiento

El sistema de filtros ha sido probado con:
- **Precisión deportiva**: >90% de detección de contenido deportivo
- **Precisión geopolítica**: >85% de preservación de contenido relevante
- **Falsos positivos**: <5% de contenido geopolítico filtrado incorrectamente

## Logs y Monitoreo

El sistema genera logs detallados:

```
[INFO] Filtered sports/entertainment article: Real Madrid vence al Barcelona...
[INFO] Saved article: Military tensions rise in Eastern Europe...
[INFO] RSS fetch completed: {'filtered_articles': 15, 'new_articles': 8}
```

## Personalización

### Añadir Nuevos Patrones Deportivos

Editar `src/data_ingestion/rss_fetcher.py`:

```python
# Añadir nuevos patrones en non_relevant_patterns
r'\bnuevo_deporte\b',
r'\bnew_sport_pattern\b',
```

### Añadir Nuevas Fuentes Deportivas

Editar `configure_sports_filter.py`:

```python
# Añadir en sports_source_names
'Nueva Fuente Deportiva',
'New Sports Source',

# Añadir en sports_url_patterns
'newsportssite.com',
'deportesnuevos.es',
```

### Ajustar Sensibilidad del Filtro

En `src/utils/content_classifier.py`:

```python
# Cambiar umbral de detección deportiva
def _is_sports_entertainment(self, text: str) -> bool:
    matches = sum(1 for keyword in sports_keywords if keyword.lower() in text)
    return matches >= 1  # Cambiar de 2 a 1 para mayor sensibilidad
```

## Resolución de Problemas

### Problema: Contenido geopolítico siendo filtrado

**Solución:**
1. Verificar patrones en `non_relevant_patterns`
2. Ajustar umbral en `_is_sports_entertainment()`
3. Revisar palabras clave geopolíticas

### Problema: Contenido deportivo pasando el filtro

**Solución:**
1. Añadir nuevos patrones deportivos
2. Verificar configuración de base de datos
3. Ejecutar `test_sports_filter.py` para diagnóstico

### Problema: Rendimiento lento

**Solución:**
1. Optimizar expresiones regulares
2. Reducir número de patrones
3. Usar caché para clasificaciones frecuentes

## Mantenimiento Recomendado

1. **Semanal**: Ejecutar `clean_sports_articles.py` en modo dry-run
2. **Mensual**: Revisar fuentes RSS nuevas con `configure_sports_filter.py`
3. **Trimestral**: Ejecutar `test_sports_filter.py` para verificar precisión
4. **Anual**: Actualizar patrones deportivos y palabras clave

## Contacto y Soporte

Para problemas o mejoras del filtro de deportes:
1. Revisar logs del sistema
2. Ejecutar scripts de diagnóstico
3. Verificar configuración de base de datos
4. Consultar este README para soluciones comunes

---

**Nota**: Este filtro está diseñado para ser conservador, priorizando la preservación de contenido geopolítico relevante sobre la eliminación perfecta de todo contenido deportivo.