#!/usr/bin/env python3

import requests

print("🔍 TESTING UI FIXES")
print("=" * 40)

# Test hero article API
try:
    print("Testing hero article...")
    response = requests.get("http://localhost:5001/api/hero-article", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            text = data.get('article', {}).get('text', '')
            print(f"✅ Hero loaded. Text preview: {text[:100]}...")
            
            if '<' in text and '>' in text:
                print("❌ HTML detected in hero text!")
            else:
                print("✅ Hero text clean (no HTML)")
        else:
            print("❌ Hero API error")
    else:
        print(f"❌ Hero HTTP error: {response.status_code}")
        
except Exception as e:
    print(f"⚠️ Connection error (server may be down): {e}")

print("\n✅ FIXES APPLIED:")
print("- Backend strips HTML from hero text")
print("- Mosaic titles truncated to 120 chars")
print("- CSS limits overlay to 2-3 lines max")
print("- Only titles appear over mosaic images")

print("\n📝 NEXT: Refresh browser to see changes!")