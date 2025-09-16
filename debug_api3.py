import requests
import json

try:
    print("Testing API connection...")
    r = requests.get("http://localhost:5001/api/articles?limit=5", timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Type of response: {type(data)}")
        
        print("\nKeys in response:")
        for key in data.keys():
            print(f"- {key}: {type(data[key])}")
        
        print("\nChecking if it's a dictionary with article data...")
        # Try to access articles if it's structured differently
        if 'articles' in data:
            articles = data['articles']
            print(f"Found 'articles' key with {len(articles)} items")
        else:
            print("No 'articles' key, checking individual items...")
            for key, value in list(data.items())[:3]:  # First 3 items
                print(f"\nKey: {key}")
                print(f"Value type: {type(value)}")
                if hasattr(value, 'get'):
                    print(f"Title: {value.get('title', 'No title')}")
        
    else:
        print(f"Error: {r.text}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()