#!/usr/bin/env python3
"""
Script para forzar recarga de app_BUENA.py en servidor corriendo
"""
import requests
import json
import time
import sys
from datetime import datetime

def test_server_endpoints():
    """Prueba todos los endpoints para verificar funcionamiento"""
    
    print("🔧 FORZANDO RECARGA DE app_BUENA.py")
    print("=" * 60)
    
    # Lista de endpoints críticos
    endpoints = {
        '/api/status': 'Estado del sistema',
        '/api/articles?limit=1': 'Artículos principales', 
        '/api/hero-article': 'Artículo héroe',
        '/api/articles/deduplicated?limit=1': 'Artículos deduplicated'
    }
    
    print("🧪 PROBANDO ENDPOINTS DESPUÉS DE CAMBIOS...")
    print("-" * 50)
    
    all_working = True
    results = {}
    
    for endpoint, description in endpoints.items():
        try:
            print(f"\n🔍 Probando {endpoint} - {description}")
            
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: FUNCIONANDO")
                data = response.json()
                
                # Verificaciones específicas
                if endpoint == '/api/status':
                    status = data.get('status', 'unknown')
                    print(f"   📊 Status: {status}")
                    
                elif 'articles' in data:
                    articles = data.get('articles', [])
                    print(f"   📰 Artículos retornados: {len(articles)}")
                    if articles:
                        first_article = articles[0]
                        print(f"   📝 Primer título: {first_article.get('title', 'Sin título')[:50]}...")
                        if first_article.get('image_url'):
                            print(f"   🖼️ Tiene imagen: SÍ")
                        else:
                            print(f"   🖼️ Tiene imagen: NO")
                            
                elif 'article' in data:
                    article = data.get('article', {})
                    print(f"   📝 Título héroe: {article.get('title', 'Sin título')[:50]}...")
                    
                results[endpoint] = {'status': 'OK', 'code': 200}
                
            elif response.status_code == 404:
                print(f"❌ {endpoint}: NO ENCONTRADO (404)")
                print("   💡 El endpoint no existe en la versión actual")
                results[endpoint] = {'status': 'NOT_FOUND', 'code': 404}
                all_working = False
                
            elif response.status_code == 500:
                print(f"❌ {endpoint}: ERROR INTERNO (500)")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Sin detalles')
                    print(f"   💥 Error: {error_msg[:100]}...")
                    
                    if "_get_real_articles_from_db" in error_msg:
                        print("   🔍 PROBLEMA: Método _get_real_articles_from_db falta")
                        print("   💡 SERVIDOR EJECUTANDO VERSIÓN ANTERIOR")
                        
                except:
                    print("   💥 Error parseando respuesta JSON")
                    
                results[endpoint] = {'status': 'ERROR', 'code': 500, 'error': error_msg if 'error_msg' in locals() else 'Unknown'}
                all_working = False
                
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                results[endpoint] = {'status': 'HTTP_ERROR', 'code': response.status_code}
                all_working = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: SERVIDOR NO DISPONIBLE")
            print("   💡 Servidor no está ejecutándose en puerto 5001")
            results[endpoint] = {'status': 'CONNECTION_ERROR', 'code': 0}
            all_working = False
            
        except Exception as e:
            print(f"❌ {endpoint}: ERROR - {e}")
            results[endpoint] = {'status': 'EXCEPTION', 'code': 0, 'error': str(e)}
            all_working = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    working_count = sum(1 for r in results.values() if r['status'] == 'OK')
    total_count = len(results)
    
    if all_working:
        print(f"✅ TODOS LOS ENDPOINTS FUNCIONANDO ({working_count}/{total_count})")
        print("🎯 app_BUENA.py está ejecutándose correctamente")
        print("🔄 Versión actualizada cargada exitosamente")
    else:
        print(f"❌ ALGUNOS ENDPOINTS FALLAN ({working_count}/{total_count})")
        
        # Análisis de problemas
        if any(r.get('error', '').find('_get_real_articles_from_db') >= 0 for r in results.values()):
            print("🔍 PROBLEMA IDENTIFICADO: Servidor ejecutando versión anterior")
            print("💡 SOLUCIÓN: Reiniciar servidor con versión actualizada")
            print()
            print("🚀 PASOS PARA REINICIAR:")
            print("   1. En terminal del servidor: Ctrl+C")
            print("   2. Ejecutar: python app_BUENA.py")
            print("   3. Verificar que cargue todos los cambios")
            
        elif any(r['status'] == 'CONNECTION_ERROR' for r in results.values()):
            print("🔍 PROBLEMA: Servidor no está ejecutándose")
            print("💡 SOLUCIÓN: Iniciar servidor con: python app_BUENA.py")
            
    print(f"\n🕒 Prueba completada: {datetime.now().strftime('%H:%M:%S')}")
    
    return all_working, results

def force_server_reload():
    """Intenta forzar recarga del servidor mediante diversos métodos"""
    
    print("🔄 INTENTANDO FORZAR RECARGA DEL SERVIDOR...")
    print("-" * 50)
    
    # Método 1: Endpoint de recarga si existe
    try:
        print("🧪 Probando endpoint de recarga...")
        response = requests.post("http://localhost:5001/api/system/reload", timeout=5)
        if response.status_code == 200:
            print("✅ Recarga exitosa via endpoint")
            return True
    except:
        print("❌ No hay endpoint de recarga disponible")
    
    # Método 2: Endpoint de reinicio si existe  
    try:
        print("🧪 Probando endpoint de reinicio...")
        response = requests.post("http://localhost:5001/api/system/restart", timeout=5)
        if response.status_code == 200:
            print("✅ Reinicio exitoso via endpoint")
            return True
    except:
        print("❌ No hay endpoint de reinicio disponible")
        
    print("⚠️ No se puede forzar recarga automática")
    print("💡 Reinicio manual requerido")
    return False

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO COMPLETO DE SERVIDOR")
    print("=" * 60)
    
    # Intentar forzar recarga
    reload_success = force_server_reload()
    
    if reload_success:
        print("⏱️ Esperando recarga del servidor...")
        time.sleep(3)
    
    # Probar endpoints
    all_working, results = test_server_endpoints()
    
    if not all_working:
        print("\n🚨 SERVIDOR NECESITA REINICIO MANUAL")
        print("💡 Ejecuta estos comandos:")
        print("   1. Detén servidor actual: Ctrl+C")
        print("   2. Inicia versión corregida: python app_BUENA.py")
    else:
        print("\n🎉 SERVIDOR FUNCIONANDO CORRECTAMENTE")
        print("✅ Todos los endpoints operativos")