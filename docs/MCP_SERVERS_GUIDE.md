# Guía de Servidores MCP - Geointelligence Dashboard

Esta guía documenta todos los servidores MCP (Model Context Protocol) configurados para el proyecto de inteligencia geográfica. Los servidores están organizados por categorías funcionales.

## 📋 Índice

1. [Servidores Core](#servidores-core)
2. [Análisis de Código y Desarrollo](#análisis-de-código-y-desarrollo)
3. [Navegación Web y Búsqueda](#navegación-web-y-búsqueda)
4. [Bases de Datos](#bases-de-datos)
5. [Servicios en la Nube](#servicios-en-la-nube)
6. [Comunicación y Colaboración](#comunicación-y-colaboración)
7. [Procesamiento de Datos](#procesamiento-de-datos)
8. [Seguridad y Monitoreo](#seguridad-y-monitoreo)
9. [DevOps y Automatización](#devops-y-automatización)
10. [Utilidades del Sistema](#utilidades-del-sistema)

---

## 🔧 Servidores Core

### filesystem
**Propósito**: Operaciones básicas del sistema de archivos
**Comando**: `uvx mcp-server-filesystem --base-dir E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap`
**Uso**: Leer, escribir, crear, eliminar archivos y directorios

### git
**Propósito**: Control de versiones con Git
**Comando**: `uvx mcp-server-git --repository E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap`
**Uso**: Commits, branches, merges, historial

### fetch
**Propósito**: Realizar peticiones HTTP y obtener datos web
**Comando**: `uvx mcp-server-fetch`
**Uso**: APIs REST, descargas, webhooks

### python
**Propósito**: Gestión del entorno Python
**Comando**: `uvx mcp-server-python`
**Uso**: Paquetes pip, virtual environments, ejecución de scripts

### shell
**Propósito**: Ejecución de comandos del sistema
**Comando**: `uvx mcp-server-shell`
**Uso**: Automatización, scripts bash/cmd, procesos del sistema

---

## 🧠 Análisis de Código y Desarrollo

### desktop-commander
**Propósito**: Control avanzado del terminal y edición de código
**Comando**: `npx -y @wonderwhy-er/desktop-commander`
**Características**:
- Control de terminal con procesos interactivos
- Edición de código con búsqueda/reemplazo fuzzy
- Gestión de procesos en background
- Operaciones de filesystem avanzadas

### serena
**Propósito**: Análisis semántico de código con Language Server Protocol
**Comando**: `uvx --from git+https://github.com/oraios/serena serena start-mcp-server`
**Características**:
- Análisis simbólico de código
- Refactoring inteligente
- Navegación por definiciones y referencias
- Soporte multi-lenguaje (Python, TypeScript, Java, etc.)

### code-analysis
**Propósito**: Análisis complejo y refactoring de código
**Comando**: `uvx mcp-server-code-analysis --project-dir E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap`
**Uso**: Detección de code smells, sugerencias de mejora

### linter
**Propósito**: Análisis estático para encontrar problemas en el código
**Comando**: `uvx mcp-server-linter --project-dir E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap`
**Uso**: Verificación de sintaxis, estándares de código

### testing
**Propósito**: Ejecución de pruebas unitarias e integración
**Comando**: `uvx mcp-server-testing --project-dir E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap`
**Uso**: Test runners, cobertura, reportes

---

## 🌐 Navegación Web y Búsqueda

### browser-mcp
**Propósito**: Automatización y navegación web
**Comando**: `npx -y browser-mcp-server`
**Uso**: Scraping, automatización de formularios, testing E2E

### duckduckgo-search
**Propósito**: Búsqueda web y obtención de contenido
**Comando**: `uvx duckduckgo-mcp-server`
**Características**:
- Búsqueda en DuckDuckGo
- Extracción de contenido web
- Rate limiting automático

### mcp-compass
**Propósito**: Descubrimiento y recomendación de servicios MCP
**Comando**: `npx -y @liuyoshio/mcp-compass`
**Uso**: Encontrar nuevos servidores MCP, recomendaciones

### scraping
**Propósito**: Extracción de datos de sitios web
**Comando**: `uvx mcp-server-scraping`
**Uso**: Web scraping, parsing HTML, extracción de datos estructurados

---

## 🗄️ Bases de Datos

### sqlite / sqlite-enhanced
**Propósito**: Operaciones con bases de datos SQLite
**Comando**: `uvx mcp-server-sqlite --db-path E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap/data`
**Uso**: Consultas SQL, gestión de esquemas, análisis de datos

### postgres
**Propósito**: Operaciones con PostgreSQL
**Comando**: `uvx mcp-server-postgres`
**Uso**: Bases de datos empresariales, transacciones complejas

### mongodb
**Propósito**: Operaciones con MongoDB
**Comando**: `npx -y mongodb-mcp-server`
**Uso**: Bases de datos NoSQL, documentos JSON

### redis
**Propósito**: Cache y almacenamiento en memoria
**Comando**: `npx -y redis-mcp-server`
**Uso**: Cache, sesiones, colas de mensajes

### vector-db
**Propósito**: Almacenamiento vectorial para IA
**Comando**: `uvx mcp-server-vector-db --db-path E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap/data/vector_store`
**Uso**: Embeddings, búsqueda semántica, memory persistente

---

## ☁️ Servicios en la Nube

### aws
**Propósito**: Operaciones con Amazon Web Services
**Comando**: `npx -y aws-mcp-server`
**Uso**: EC2, S3, Lambda, CloudFormation

### azure
**Propósito**: Operaciones con Microsoft Azure
**Comando**: `npx -y azure-mcp-server`
**Uso**: Azure Functions, Storage, Cognitive Services

### gcp
**Propósito**: Operaciones con Google Cloud Platform
**Comando**: `npx -y gcp-mcp-server`
**Uso**: Compute Engine, Cloud Storage, AI Platform

---

## 💬 Comunicación y Colaboración

### github / gitlab
**Propósito**: Integración con plataformas de desarrollo
**Comando**: `npx -y github-mcp-server` / `npx -y gitlab-mcp-server`
**Uso**: Issues, PRs, releases, wikis

### slack / discord
**Propósito**: Integración con plataformas de comunicación
**Comando**: `npx -y slack-mcp-server` / `npx -y discord-mcp-server`
**Uso**: Notificaciones, bots, canales

### email
**Propósito**: Gestión de correo electrónico
**Comando**: `npx -y email-mcp-server`
**Uso**: Envío de emails, notificaciones automáticas

---

## 📊 Procesamiento de Datos

### json-processor / csv-processor
**Propósito**: Manipulación de datos estructurados
**Comando**: `uvx mcp-server-json` / `npx -y csv-mcp-server`
**Uso**: Transformación, validación, análisis de datos

### pdf-processor
**Propósito**: Procesamiento de documentos PDF
**Comando**: `npx -y pdf-mcp-server`
**Uso**: Extracción de texto, generación de PDFs

### image-processing
**Propósito**: Procesamiento y análisis de imágenes
**Comando**: `uvx mcp-server-image`
**Uso**: Redimensión, filtros, análisis visual

### markdown / html / xml / yaml / toml
**Propósito**: Procesamiento de diferentes formatos de archivo
**Comando**: `uvx markdown-mcp-server`, etc.
**Uso**: Conversión, validación, parsing

---

## 🔒 Seguridad y Monitoreo

### security-scanner
**Propósito**: Escaneo de vulnerabilidades
**Comando**: `uvx security-mcp-server`
**Uso**: Análisis de seguridad, detección de vulnerabilidades

### vulnerability-scanner
**Propósito**: Análisis de dependencias vulnerables
**Comando**: `npx -y vulnerability-mcp-server`
**Uso**: Auditoría de paquetes, reportes de seguridad

### monitoring
**Propósito**: Monitoreo del sistema
**Comando**: `uvx monitoring-mcp-server`
**Uso**: Métricas, alertas, dashboards

### log-analyzer
**Propósito**: Análisis de logs
**Comando**: `npx -y log-analyzer-mcp-server`
**Uso**: Parsing de logs, detección de patrones

### encryption
**Propósito**: Utilidades de cifrado
**Comando**: `npx -y encryption-mcp-server`
**Uso**: Cifrado/descifrado, gestión de claves

---

## 🚀 DevOps y Automatización

### docker
**Propósito**: Gestión de contenedores Docker
**Comando**: `uvx mcp-server-docker`
**Uso**: Builds, deployments, orchestración

### kubernetes
**Propósito**: Gestión de clusters Kubernetes
**Comando**: `npx -y k8s-mcp-server`
**Uso**: Pods, services, deployments, scaling

### terraform / ansible
**Propósito**: Infrastructure as Code
**Comando**: `npx -y terraform-mcp-server` / `npx -y ansible-mcp-server`
**Uso**: Provisionamiento, configuración automatizada

### cicd
**Propósito**: Pipelines de CI/CD
**Comando**: `uvx cicd-mcp-server`
**Uso**: Builds automáticos, testing, deployments

### build-automation
**Propósito**: Automatización de builds
**Comando**: `npx -y build-mcp-server`
**Uso**: Compilación, packaging, distribución

---

## 🛠️ Utilidades del Sistema

### 1mcp-agent
**Propósito**: Agregador unificado de servidores MCP
**Comando**: `npx -y @1mcp/agent`
**Características**:
- Punto único de entrada para múltiples MCPs
- Filtrado por tags
- Gestión centralizada

### memory
**Propósito**: Almacenamiento persistente entre sesiones
**Comando**: `npx -y @modelcontextprotocol/server-memory`
**Uso**: Contexto persistente, memoria a largo plazo

### search
**Propósito**: Búsqueda indexada en el codebase
**Comando**: `uvx mcp-server-search --index-path E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap/.index`
**Uso**: Búsqueda full-text, indexación

### janitor
**Propósito**: Limpieza de archivos temporales
**Comando**: `uvx mcp-server-janitor --path E:/Proyectos/VisualStudio/Upgrade_Data_AI/riskmap`
**Uso**: Eliminar __pycache__, .DS_Store, node_modules

### everything-search (Windows)
**Propósito**: Búsqueda ultrarrápida de archivos en Windows
**Comando**: `npx -y everything-mcp-server`
**Uso**: Localización instantánea de archivos

### time / calendar / weather
**Propósito**: Servicios de información temporal y clima
**Comando**: `uvx mcp-server-time`, etc.
**Uso**: Fechas, eventos, pronósticos

### compression / backup
**Propósito**: Utilidades de archivado
**Comando**: `uvx compression-mcp-server` / `npx -y backup-mcp-server`
**Uso**: Compresión, respaldos automatizados

---

## 🔧 Configuración y Uso

### Activación Selectiva
Los servidores están configurados pero pueden activarse selectivamente según las necesidades:

```bash
# Solo servidores core
--tags="core"

# Desarrollo de código
--tags="development,code-analysis"

# Análisis de datos
--tags="database,data-processing"
```

### Variables de Entorno
Los servidores utilizan configuraciones del archivo `.env`:
- API keys para servicios externos
- Rutas de directorios
- Configuraciones de conexión

### Monitoreo
Use el servidor `monitoring` para supervisar el rendimiento y uso de los MCPs.

---

## 📚 Referencias

- [Model Context Protocol](https://modelcontextprotocol.org/)
- [Desktop Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP)
- [Serena](https://github.com/oraios/serena)
- [1MCP](https://github.com/1mcp-app/agent)
- [MCP Compass](https://github.com/liuyoshio/mcp-compass)

---

*Última actualización: $(Get-Date)*
*Total de servidores configurados: 80+*
