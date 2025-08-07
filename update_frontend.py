#!/usr/bin/env python3
"""
Script para actualizar el frontend para usar el endpoint corregido
"""

import os
import re

def update_frontend_endpoints():
    """
    Buscar y actualizar referencias al endpoint de conflictos en el frontend
    """
    
    print("🔍 BUSCANDO ARCHIVOS DE FRONTEND PARA ACTUALIZAR...")
    print("=" * 60)
    
    # Buscar archivos JavaScript y HTML en src/web
    frontend_dirs = [
        "src/web/static",
        "src/web/templates", 
        "src/dashboards",
        "templates",
        "static"
    ]
    
    files_to_check = []
    
    for directory in frontend_dirs:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.js', '.html', '.htm', '.jsx', '.ts', '.tsx')):
                        files_to_check.append(os.path.join(root, file))
    
    if not files_to_check:
        print("ℹ️ No se encontraron archivos de frontend para actualizar")
        return
    
    print(f"📁 Revisando {len(files_to_check)} archivos...")
    
    updated_files = []
    endpoint_pattern = re.compile(r'/api/analytics/conflicts(?!-corrected)', re.IGNORECASE)
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar referencias al endpoint original
            if '/api/analytics/conflicts' in content and '/api/analytics/conflicts-corrected' not in content:
                print(f"📝 Encontrado endpoint en: {file_path}")
                
                # Mostrar líneas que contienen el endpoint
                lines = content.split('\\n')
                for i, line in enumerate(lines, 1):
                    if '/api/analytics/conflicts' in line and '/api/analytics/conflicts-corrected' not in line:
                        print(f"   Línea {i}: {line.strip()[:80]}...")
                
                updated_files.append(file_path)
        
        except Exception as e:
            print(f"⚠️ Error leyendo {file_path}: {e}")
    
    if updated_files:
        print(f"\\n📋 ARCHIVOS QUE NECESITAN ACTUALIZACIÓN:")
        print("-" * 45)
        for file_path in updated_files:
            print(f"   📄 {file_path}")
        
        print("\\n🔧 INSTRUCCIONES PARA ACTUALIZAR:")
        print("-" * 40)
        print("   1. En cada archivo listado:")
        print("   2. Busca: '/api/analytics/conflicts'")
        print("   3. Reemplaza por: '/api/analytics/conflicts-corrected'")
        print("   4. O añade un parámetro de configuración para el endpoint")
    else:
        print("✅ No se encontraron referencias al endpoint original en el frontend")

def create_endpoint_config():
    """
    Crear una configuración para cambiar fácilmente entre endpoints
    """
    
    config_js = '''
// Configuración de endpoints para RiskMap
const RISKMAP_CONFIG = {
    API_BASE_URL: window.location.origin,
    ENDPOINTS: {
        // Endpoint CORREGIDO - usa este para datos filtrados correctamente
        CONFLICTS: '/api/analytics/conflicts-corrected',
        
        // Endpoint original - puede tener problemas de filtrado
        CONFLICTS_ORIGINAL: '/api/analytics/conflicts',
        
        // Otros endpoints
        NEWS: '/api/news',
        SATELLITE: '/api/analytics/satellite-zones',
        GEOJSON: '/api/analytics/geojson'
    },
    
    // Configuración del mapa
    MAP_CONFIG: {
        DEFAULT_CENTER: [31.0461, 34.8516], // Israel (zona con más conflictos)
        DEFAULT_ZOOM: 6,
        CLUSTER_DISTANCE: 50
    },
    
    // Configuración de filtros
    FILTERS: {
        RISK_LEVELS: ['high', 'medium', 'low'],
        TIMEFRAMES: ['24h', '7d', '30d', '90d']
    }
};

// Función helper para obtener datos de conflictos
async function fetchConflicts(timeframe = '7d') {
    try {
        const response = await fetch(`${RISKMAP_CONFIG.API_BASE_URL}${RISKMAP_CONFIG.ENDPOINTS.CONFLICTS}?timeframe=${timeframe}`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Obtenidos ${data.conflicts.length} conflictos del sistema corregido`);
            return data;
        } else {
            console.error('❌ Error obteniendo conflictos:', data.error);
            return null;
        }
    } catch (error) {
        console.error('❌ Error de red obteniendo conflictos:', error);
        return null;
    }
}

// Función helper para obtener noticias filtradas
async function fetchFilteredNews(limit = 20) {
    try {
        const response = await fetch(`${RISKMAP_CONFIG.API_BASE_URL}${RISKMAP_CONFIG.ENDPOINTS.NEWS}?limit=${limit}&filtered=true`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Obtenidas ${data.articles.length} noticias geopolíticas filtradas`);
            return data;
        } else {
            console.error('❌ Error obteniendo noticias:', data.error);
            return null;
        }
    } catch (error) {
        console.error('❌ Error de red obteniendo noticias:', error);
        return null;
    }
}

console.log('🔧 RiskMap Config cargado con endpoints corregidos');
'''
    
    # Crear el archivo de configuración
    config_path = "src/web/static/js/riskmap-config.js"
    
    # Crear directorios si no existen
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_js)
    
    print(f"\\n📄 ARCHIVO DE CONFIGURACIÓN CREADO:")
    print("-" * 40)
    print(f"   📁 Ubicación: {config_path}")
    print("   🔧 Incluye endpoints corregidos")
    print("   ⚙️ Funciones helper para obtener datos")
    print("   🗺️ Configuración de mapa optimizada")
    
    print("\\n📋 CÓMO USAR LA CONFIGURACIÓN:")
    print("-" * 35)
    print("   1. Incluye en tu HTML:")
    print(f"      <script src='/static/js/riskmap-config.js'></script>")
    print("   2. En tu JavaScript:")
    print("      const data = await fetchConflicts('7d');")
    print("      const news = await fetchFilteredNews(20);")

if __name__ == "__main__":
    update_frontend_endpoints()
    create_endpoint_config()
