#!/usr/bin/env python3
"""
Script para forzar recarga inmediata de filtros sin reiniciar servidor
"""
import requests
import time
import json
from datetime import datetime

def test_current_articles():
    """Prueba los artículos actuales para verificar filtros"""
    
    print("🧪 PROBANDO FILTROS ACTUALES")
    print("=" * 60)
    
    try:
        print("📰 Obteniendo artículos actuales...")
        response = requests.get("http://localhost:5001/api/articles?limit=10", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"📊 Total artículos obtenidos: {len(articles)}")
            print()
            
            # Categorizar artículos
            geopolitical = []
            entertainment = []
            technology = []
            sports = []
            other = []
            
            for article in articles:
                title = article.get('title', '').lower()
                source = article.get('source', '')
                
                # Clasificar por contenido
                if any(x in title for x in ['emmy', 'film', 'festival', 'oscar', 'hamnet', 'variety', 'actor']):
                    entertainment.append(article)
                elif any(x in title for x in ['iphone', 'apple', '9to5mac', 'tech', 'smartphone']):
                    technology.append(article)
                elif any(x in title for x in ['sport', 'game', 'nfl', 'nba', 'team']):
                    sports.append(article)
                elif any(x in title for x in ['ukraine', 'russia', 'war', 'military', 'conflict', 'china', 'israel', 'palestine', 'gaza', 'nato']):
                    geopolitical.append(article)
                else:
                    other.append(article)
            
            # Mostrar resultados
            print("🎯 ANÁLISIS DE FILTROS:")
            print("-" * 40)
            
            print(f"✅ Geopolíticos: {len(geopolitical)}")
            for art in geopolitical[:3]:
                print(f"   📰 {art.get('title', '')[:60]}... - {art.get('source', '')}")
            
            print(f"❌ Entretenimiento: {len(entertainment)}")
            for art in entertainment:
                print(f"   🎭 {art.get('title', '')[:60]}... - {art.get('source', '')}")
                
            print(f"❌ Tecnología: {len(technology)}")
            for art in technology:
                print(f"   💻 {art.get('title', '')[:60]}... - {art.get('source', '')}")
                
            print(f"❌ Deportes: {len(sports)}")
            for art in sports:
                print(f"   ⚽ {art.get('title', '')[:60]}... - {art.get('source', '')}")
                
            print(f"❓ Otros: {len(other)}")
            for art in other[:2]:
                print(f"   ❓ {art.get('title', '')[:60]}... - {art.get('source', '')}")
            
            # Veredicto final
            non_geo = len(entertainment) + len(technology) + len(sports)
            
            print()
            print("=" * 60)
            print("📊 VEREDICTO FINAL:")
            
            if non_geo == 0:
                print("✅ FILTROS FUNCIONANDO - Solo contenido geopolítico")
                print("🎯 Objetivo alcanzado correctamente")
                return True
            else:
                print(f"❌ FILTROS FALLANDO - {non_geo} artículos no geopolíticos detectados")
                print("🔧 Se requiere corrección de filtros")
                return False
                
        else:
            print(f"❌ Error obteniendo artículos: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def force_cache_clear():
    """Intenta limpiar caché/forzar recarga"""
    
    print("🔄 INTENTANDO LIMPIAR CACHÉ DEL SERVIDOR")
    print("-" * 50)
    
    methods = [
        ("POST", "/api/cache/clear", "Limpiar caché"),
        ("POST", "/api/system/refresh", "Refrescar sistema"),
        ("GET", "/api/articles?force_reload=true", "Forzar recarga"),
        ("GET", "/api/articles?cache=false", "Deshabilitar caché"),
        ("POST", "/api/reload", "Recarga general")
    ]
    
    for method, endpoint, description in methods:
        try:
            print(f"🧪 Probando: {description}")
            
            if method == "POST":
                response = requests.post(f"http://localhost:5001{endpoint}", timeout=5)
            else:
                response = requests.get(f"http://localhost:5001{endpoint}", timeout=5)
                
            if response.status_code in [200, 201]:
                print(f"✅ {description}: EXITOSO")
                return True
            elif response.status_code == 404:
                print(f"❌ {description}: No disponible")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
    
    print("⚠️ No se encontraron métodos de recarga automática")
    return False

def main():
    """Función principal"""
    
    print("🔧 CORRECTOR DE FILTROS GEOPOLÍTICOS")
    print("=" * 60)
    print(f"🕒 Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Paso 1: Probar filtros actuales
    print("PASO 1: Verificar estado actual")
    filters_working = test_current_articles()
    
    if filters_working:
        print("\n🎉 ¡FILTROS YA FUNCIONAN CORRECTAMENTE!")
        return
    
    print(f"\nPASO 2: Intentar recarga automática")
    cache_cleared = force_cache_clear()
    
    if cache_cleared:
        print("\n⏱️ Esperando recarga del servidor...")
        time.sleep(3)
        
        print("\nPASO 3: Verificar después de recarga")
        filters_working = test_current_articles()
    
    print("\n" + "=" * 60)
    
    if filters_working:
        print("🎉 PROBLEMA RESUELTO")
        print("✅ Solo artículos geopolíticos se muestran ahora")
    else:
        print("❌ PROBLEMA PERSISTE")
        print("💡 SOLUCIÓN REQUERIDA:")
        print("   1. Los filtros SQL se han actualizado en app_CORREGIDO.py")
        print("   2. El servidor necesita reiniciar para cargar cambios:")
        print("      - Detén servidor: Ctrl+C") 
        print("      - Inicia nuevamente: python app_CORREGIDO.py")
        print("   3. O usa 'python app_BUENA.py' para versión completa")
    
    print(f"\n🕒 Finalizado: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()