#!/usr/bin/env python3
"""
Script para verificar que los endpoints corregidos funcionen correctamente
"""

import requests
import json

def test_fixed_endpoints():
    """Probar los endpoints que se han corregido"""
    
    base_url = "http://localhost:5001"
    
    print("🔧 VERIFICANDO ENDPOINTS CORREGIDOS")
    print("=" * 50)
    
    # Endpoints que deberian funcionar ahora
    test_cases = [
        {
            "name": "Página About",
            "url": "/about",
            "expected": 200,
            "description": "Página de información de RISKMAP"
        },
        {
            "name": "API News Conflicts",
            "url": "/api/news/conflicts",
            "expected": 200,
            "description": "Conflictos del análisis de noticias"
        },
        {
            "name": "API Analytics Conflicts", 
            "url": "/api/analytics/conflicts",
            "expected": 200,
            "description": "Conflictos del pipeline integrado"
        },
        {
            "name": "API Analytics GeoJSON",
            "url": "/api/analytics/geojson", 
            "expected": 200,
            "description": "GeoJSON para análisis satelital"
        },
        {
            "name": "Servidor de Imágenes",
            "url": "/data/images/test.jpg",
            "expected": 200,
            "description": "Servir archivos de imagen"
        },
        {
            "name": "Dashboard Redirect",
            "url": "/dashboard",
            "expected": [302, 404],  # Puede ser redirect o 404 por Dash
            "description": "Redirection al dashboard histórico"
        },
        {
            "name": "Multivariate Redirect",
            "url": "/multivariate", 
            "expected": [302, 404],  # Puede ser redirect o 404 por Dash
            "description": "Redirection al dashboard multivariable"
        }
    ]
    
    working_endpoints = []
    problem_endpoints = []
    
    for test in test_cases:
        try:
            response = requests.get(f"{base_url}{test['url']}", timeout=10, allow_redirects=False)
            expected = test['expected']
            
            # Verificar si el status code está en los esperados
            if isinstance(expected, list):
                is_success = response.status_code in expected
            else:
                is_success = response.status_code == expected
            
            if is_success:
                print(f"✅ {test['name']}")
                print(f"   URL: {test['url']}")
                print(f"   Status: {response.status_code}")
                print(f"   📝 {test['description']}")
                working_endpoints.append(test['name'])
            else:
                print(f"❌ {test['name']}")
                print(f"   URL: {test['url']}")
                print(f"   Status: {response.status_code} (esperado: {expected})")
                print(f"   📝 {test['description']}")
                problem_endpoints.append(test['name'])
                
            print()
                
        except requests.exceptions.RequestException as e:
            print(f"🔌 {test['name']} → Error: {e}")
            problem_endpoints.append(test['name'])
            print()
    
    print("=" * 50)
    print(f"📊 RESUMEN DE LA CORRECCIÓN:")
    print(f"   ✅ Endpoints funcionando: {len(working_endpoints)}")
    print(f"   ❌ Endpoints con problemas: {len(problem_endpoints)}")
    
    if working_endpoints:
        print(f"\n🎉 ENDPOINTS CORREGIDOS EXITOSAMENTE:")
        for endpoint in working_endpoints:
            print(f"   - {endpoint}")
    
    if problem_endpoints:
        print(f"\n🚨 ENDPOINTS QUE AÚN NECESITAN ATENCIÓN:")
        for endpoint in problem_endpoints:
            print(f"   - {endpoint}")
    
    # Probar una respuesta JSON específica
    print(f"\n🧪 PROBANDO CONTENIDO DE API:")
    try:
        response = requests.get(f"{base_url}/api/news/conflicts")
        if response.status_code == 200:
            data = response.json()
            print(f"   📍 /api/news/conflicts → ✅ JSON válido")
            print(f"   📦 Conflictos encontrados: {len(data.get('conflicts', []))}")
            if data.get('statistics'):
                print(f"   📊 Estadísticas: {data['statistics']}")
        else:
            print(f"   📍 /api/news/conflicts → ❌ Error {response.status_code}")
    except Exception as e:
        print(f"   📍 /api/news/conflicts → ❌ Error: {e}")

if __name__ == "__main__":
    test_fixed_endpoints()
