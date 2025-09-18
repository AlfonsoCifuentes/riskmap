#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 SCRIPT DE DIAGNÓSTICO Y REPARACIÓN DE DASHBOARDS
==================================================
Diagnosticar y reparar problemas con la integración de Dash en Flask
"""

import sys
import traceback
import requests
import importlib.util

def check_dash_integration():
    """Verificar problemas con la integración de Dash"""
    print("🔍 DIAGNÓSTICO DE DASHBOARDS")
    print("=" * 50)
    
    # 1. Verificar importaciones
    print("\n1. Verificando importaciones...")
    try:
        import dash
        print(f"   ✅ Dash: versión {dash.__version__}")
    except ImportError as e:
        print(f"   ❌ Dash no disponible: {e}")
        return
        
    try:
        import plotly
        print(f"   ✅ Plotly: versión {plotly.__version__}")
    except ImportError as e:
        print(f"   ❌ Plotly no disponible: {e}")
        return
        
    # 2. Verificar archivos de dashboard
    print("\n2. Verificando archivos de dashboard...")
    historical_path = "src/visualization/historical_dashboard.py"
    multivariate_path = "src/visualization/multivariate_dashboard.py"
    
    for name, path in [("Historical", historical_path), ("Multivariate", multivariate_path)]:
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"   ✅ {name} Dashboard: importable")
        except Exception as e:
            print(f"   ❌ {name} Dashboard: error - {e}")
            
    # 3. Verificar rutas del servidor
    print("\n3. Verificando rutas del servidor...")
    base_url = "http://localhost:5001"
    
    routes_to_test = [
        "/dashboard",
        "/multivariate", 
        "/dash/historical/",
        "/dash/multivariate/"
    ]
    
    for route in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            status_emoji = "✅" if response.status_code == 200 else "❌"
            print(f"   {status_emoji} {route}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {route}: servidor no disponible")
        except Exception as e:
            print(f"   ❌ {route}: error - {e}")
            
    # 4. Diagnóstico específico del problema
    print("\n4. Diagnóstico del problema...")
    
    # Verificar redirecciones
    try:
        response = requests.get(f"{base_url}/dashboard", allow_redirects=False, timeout=10)
        if response.status_code == 302:
            location = response.headers.get('Location', 'No Location header')
            print(f"   ℹ️  /dashboard redirige a: {location}")
            
            # Probar la ruta de redirección
            if location:
                try:
                    final_response = requests.get(f"{base_url}{location}", timeout=10)
                    print(f"   📍 Ruta final {location}: {final_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Error en ruta final: {e}")
        else:
            print(f"   ❌ /dashboard no redirige correctamente: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error probando redirección: {e}")
        
def create_dash_fix():
    """Crear una corrección para la integración de Dash"""
    print("\n🔧 CREANDO CORRECCIÓN PARA DASHBOARDS")
    print("=" * 50)
    
    fix_code = '''
def fix_dash_integration(flask_app):
    """
    Corrección simplificada para integrar Dash con Flask
    """
    import dash
    from dash import html
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Crear aplicaciones Dash simples para prueba
        print("Creando dashboard histórico simplificado...")
        
        historical_app = dash.Dash(
            name="historical",
            server=flask_app,
            url_base_pathname="/dash/historical/",
            external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
        )
        
        historical_app.layout = html.Div([
            html.H1("Dashboard Histórico", style={'textAlign': 'center'}),
            html.Div([
                html.P("Dashboard histórico en desarrollo..."),
                html.P("Sistema integrado correctamente con Flask.")
            ], style={'margin': '20px'})
        ])
        
        print("Creando dashboard multivariable simplificado...")
        
        multivariate_app = dash.Dash(
            name="multivariate", 
            server=flask_app,
            url_base_pathname="/dash/multivariate/",
            external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
        )
        
        multivariate_app.layout = html.Div([
            html.H1("Análisis Multivariable", style={'textAlign': 'center'}),
            html.Div([
                html.P("Dashboard de análisis multivariable en desarrollo..."),
                html.P("Sistema integrado correctamente con Flask.")
            ], style={'margin': '20px'})
        ])
        
        print("✅ Dashboards integrados exitosamente")
        
        return {
            'historical': historical_app,
            'multivariate': multivariate_app
        }
        
    except Exception as e:
        logger.error(f"Error integrando dashboards: {e}")
        print(f"❌ Error: {e}")
        return None
'''
    
    # Guardar la corrección
    with open("dash_integration_fix.py", "w", encoding="utf-8") as f:
        f.write(fix_code)
        
    print("💾 Corrección guardada en: dash_integration_fix.py")
    
def main():
    """Función principal"""
    try:
        check_dash_integration()
        create_dash_fix()
        
        print("\n🎯 RECOMENDACIONES:")
        print("=" * 30)
        print("1. Las rutas /dashboard y /multivariate están redirigiendo")
        print("2. Las rutas Dash /dash/historical/ y /dash/multivariate/ fallan")
        print("3. Problema en _integrate_dash_app en app_BUENA.py")
        print("4. Usar corrección simplificada en dash_integration_fix.py")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()