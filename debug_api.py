import requests
import json

try:
    print("Testing API connection...")
    r = requests.get("http://localhost:5001/api/articles?limit=3", timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Articles returned: {len(data)}")
        
        for i, article in enumerate(data):
            print(f"\nArticle {i+1}:")
            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  Has image: {'image_url' in article and bool(article.get('image_url'))}")
            print(f"  Image URL: {article.get('image_url', 'None')}")
    else:
        print(f"Error: {r.text}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()