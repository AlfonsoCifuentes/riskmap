#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test completo de los endpoints corregidos
"""

import requests
import json

def test_corrected_endpoints():
    """Test de todos los endpoints en el servidor corregido"""
    base_url = "http://127.0.0.1:5003"
    
    endpoints = [
        ("/test", "Test básico"),
        ("/api/articles", "Artículos del mosaico"),
        ("/api/hero-article", "Artículo hero")
    ]
    
    print("🚀 Testing endpoints corregidos...")
    print("=" * 50)
    
    all_success = True
    
    for endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        
        try:
            print(f"\n🔍 Testing: {description}")
            print(f"🌐 URL: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if endpoint == "/test":
                        print(f"✅ Test OK: {data.get('message', 'N/A')}")
                    
                    elif endpoint == "/api/articles":
                        if isinstance(data, list):
                            print(f"✅ Articles: {len(data)} artículos")
                            if len(data) > 0:
                                first = data[0]
                                print(f"   Primer artículo:")
                                print(f"   - ID: {first.get('id')}")
                                print(f"   - Título: {first.get('title', '')[:60]}...")
                                print(f"   - Riesgo: {first.get('risk_score')}")
                                print(f"   - Imagen: {'✅ Sí' if first.get('image_url') else '❌ No'}")
                            else:
                                print("❌ Lista vacía")
                                all_success = False
                        else:
                            print("❌ Respuesta no es lista")
                            all_success = False
                    
                    elif endpoint == "/api/hero-article":
                        if isinstance(data, dict) and 'id' in data:
                            print(f"✅ Hero article:")
                            print(f"   - ID: {data.get('id')}")
                            print(f"   - Título: {data.get('title', '')[:60]}...")
                            print(f"   - Riesgo: {data.get('risk_score')}")
                        else:
                            print("⚠️ Sin hero article o formato incorrecto")
                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Error: {e}")
                    all_success = False
            
            elif response.status_code == 404 and endpoint == "/api/hero-article":
                print("⚠️ No hero article encontrado (404 OK)")
            
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                all_success = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            all_success = False
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 ¡TODOS LOS TESTS EXITOSOS!")
        print("✅ El endpoint /api/articles está funcionando correctamente")
        print("✅ El frontend debería poder cargar el mosaico ahora")
    else:
        print("❌ Algunos tests fallaron")
    
    return all_success

if __name__ == "__main__":
    test_corrected_endpoints()