#!/usr/bin/env python3
"""
Test rápido de endpoints específicos
"""
import requests
import json

def quick_test():
    print("🔍 TEST RÁPIDO DE ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    # Test 1: Status básico
    try:
        print("\n1️⃣ Test de estado...")
        response = requests.get(f"{base_url}/api/status", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            print(f"📊 Total artículos: {data.get('articles_total', 0)}")
        else:
            print("❌ Error en status")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Artículos deduplicados (el problema principal)
    try:
        print("\n2️⃣ Test de artículos deduplicados...")
        response = requests.get(f"{base_url}/api/articles/deduplicated", timeout=15)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            mosaic = data.get('mosaic', [])
            print(f"📰 Mosaico: {len(mosaic)} artículos")
            
            if len(mosaic) == 0:
                print("⚠️ PROBLEMA: Mosaico vacío")
                print(f"Error: {data.get('error', 'No error')}")
            else:
                print("✅ Mosaico con artículos - CORRECTO")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Favicon
    try:
        print("\n3️⃣ Test de favicon...")
        response = requests.get(f"{base_url}/favicon.ico", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Favicon OK")
        else:
            print(f"❌ Favicon error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error favicon: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completado")

if __name__ == "__main__":
    quick_test()