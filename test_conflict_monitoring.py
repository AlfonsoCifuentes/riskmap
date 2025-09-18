#!/usr/bin/env python3

import requests
import json

# Test the API endpoints
base_url = "http://localhost:5001"

# Test statistics endpoint
print("Testing statistics endpoint:")
try:
    response = requests.get(f"{base_url}/api/statistics")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Statistics data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection error: {e}")

print("\n" + "="*50 + "\n")

# Test conflict monitoring endpoint
print("Testing conflict monitoring endpoint:")
try:
    response = requests.get(f"{base_url}/api/conflict-monitoring/real-data")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Conflict monitoring data:")
        print(f"Success: {data.get('success')}")
        print(f"Number of conflicts: {len(data.get('conflicts', []))}")
        stats = data.get('statistics', {})
        print(f"Statistics: {json.dumps(stats, indent=2)}")
        print(f"Data source: {data.get('data_source')}")
        
        # Show first 3 conflicts as sample
        conflicts = data.get('conflicts', [])[:3]
        print("\nSample conflicts:")
        for i, conflict in enumerate(conflicts, 1):
            print(f"{i}. {conflict.get('title', 'No title')}")
            print(f"   Location: {conflict.get('location', 'No location')}")
            print(f"   Risk: {conflict.get('risk_level', 'No risk')}")
            print(f"   Country: {conflict.get('country', 'No country')}")
            print()
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection error: {e}")

print("\n" + "="*50 + "\n")

# Test articles endpoint for comparison
print("Testing articles endpoint:")
try:
    response = requests.get(f"{base_url}/api/articles")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Articles found: {len(data.get('articles', []))}")
        print(f"Success: {data.get('success')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection error: {e}")