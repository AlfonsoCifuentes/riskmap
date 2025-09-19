import requests
import json

# Test all API endpoints
base_url = "http://127.0.0.1:5001"

endpoints = [
    "/api/dashboard/stats",
    "/api/articles/latest?limit=5",
    "/api/articles/high-risk?limit=5",
    "/api/articles/featured",
    "/api/charts/categories",
    "/api/charts/timeline"
]

print("Testing API endpoints...")
print("=" * 50)

for endpoint in endpoints:
    try:
        print(f"\nTesting: {endpoint}")
        response = requests.get(f"{base_url}{endpoint}", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                if 'error' in data:
                    print(f"ERROR: {data['error']}")
            elif isinstance(data, list):
                print(f"List length: {len(data)}")
                if len(data) > 0:
                    print(f"First item: {data[0]}")
            else:
                print(f"Data: {str(data)[:200]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

print("\n" + "=" * 50)
print("Test completed")