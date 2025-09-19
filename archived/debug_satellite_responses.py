#!/usr/bin/env python3
"""Script para debuggear las respuestas de los endpoints satelitales."""

import requests
import json

def debug_endpoint_response(endpoint, method="GET"):
    """Debug específico de un endpoint."""
    base_url = "http://localhost:8050"
    
    print(f"\n🔍 DEBUGGING {endpoint}")
    print("=" * 60)
    
    try:
        if method == "POST":
            response = requests.post(f"{base_url}{endpoint}", timeout=15)
        else:
            response = requests.get(f"{base_url}{endpoint}", timeout=15)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Raw JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Debug endpoints específicos que tienen problemas
    debug_endpoint_response("/api/satellite/gallery-images")
    debug_endpoint_response("/api/satellite/critical-alerts") 
    debug_endpoint_response("/api/satellite/evolution-predictions")
    debug_endpoint_response("/api/satellite/analysis-timeline")
