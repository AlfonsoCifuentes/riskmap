#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del endpoint en el servidor simple
"""

import requests
import json

def test_simple_endpoint():
    """Test el endpoint en el servidor simple"""
    url = "http://127.0.0.1:5002/api/articles"
    
    try:
        print(f"🔍 Testing simple server: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ JSON válido recibido")
            print(f"📰 Número de artículos: {len(data)}")
            
            if len(data) > 0:
                print(f"\n🎯 Primer artículo:")
                first = data[0]
                for key in ['id', 'title', 'risk_score', 'image_url']:
                    print(f"  {key}: {first.get(key, 'N/A')}")
                
                print(f"\n✅ SUCCESS: El endpoint funciona correctamente!")
                return True
            else:
                print(f"❌ FAIL: Lista vacía")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_simple_endpoint()