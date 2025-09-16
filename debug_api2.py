import requests
import json

try:
    print("Testing API connection...")
    r = requests.get("http://localhost:5001/api/articles?limit=3", timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Type of response: {type(data)}")
        print(f"Length: {len(data)}")
        
        print("\nFirst item:")
        print(f"Type: {type(data[0])}")
        print(f"Content: {data[0]}")
        
        print("\nRaw response text (first 500 chars):")
        print(r.text[:500])
        
    else:
        print(f"Error: {r.text}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()