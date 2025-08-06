# 🚀 Guía de Despliegue - Dashboard RiskMap

## 📋 Prerrequisitos

### Sistema Operativo
- Windows 10/11, macOS 10.15+, o Linux Ubuntu 18.04+
- Python 3.8 o superior
- Node.js 14+ (opcional, para desarrollo frontend)

### Hardware Recomendado
- RAM: 4GB mínimo, 8GB recomendado
- Almacenamiento: 2GB disponibles
- CPU: 2 núcleos mínimo

## 🔧 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/riskmap.git
cd riskmap
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crear archivo `.env`:
```env
SENTINELHUB_CLIENT_ID=tu_client_id
SENTINELHUB_CLIENT_SECRET=tu_client_secret
GDELT_API_KEY=tu_api_key_opcional
OPENAI_API_KEY=tu_openai_key_opcional
GROQ_API_KEY=tu_groq_key_opcional
```

### 5. Inicializar Base de Datos
```bash
python app_BUENA.py
```

## 🌐 Acceso al Dashboard

### Desarrollo Local
```
http://localhost:5000
```

### Páginas Disponibles
- `/` - Página principal
- `/dashboard` - Dashboard unificado
- `/mapa-calor` - Mapa de calor interactivo
- `/gdelt-dashboard` - Dashboard GDELT
- `/analysis-interconectado` - Análisis interconectado
- `/earth-3d` - Modelo 3D de la Tierra
- `/about` - Información del proyecto

## 🚀 Despliegue en Producción

### Docker (Recomendado)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app_BUENA.py"]
```

### Nginx Configuración
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔐 Seguridad

### Recomendaciones
- Usar HTTPS en producción
- Configurar firewall
- Actualizar dependencias regularmente
- Implementar autenticación
- Configurar respaldos de BD

## 📊 Monitoreo

### Logs
- `automation_*.log` - Logs de automatización
- `app.log` - Logs de aplicación
- `validation_final_report.html` - Reporte de validación

### Métricas
- CPU y RAM usage
- Requests per second
- Response times
- Error rates

## 🆘 Solución de Problemas

### Error: Puerto en uso
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:5000 | xargs kill -9
```

### Error: Base de datos corrupta
```bash
rm data/riskmap.db
python app_BUENA.py
```

### Error: Dependencias faltantes
```bash
pip install --upgrade -r requirements.txt
```

## 📞 Soporte

Para soporte técnico:
- 📧 Email: support@riskmap.com
- 📚 Documentación: ./README.md
- 🐛 Issues: GitHub Issues
