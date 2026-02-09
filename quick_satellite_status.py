#!/usr/bin/env python3
"""
Quick status check for satellite API fix after server restart
"""

import requests
import json

def quick_satellite_status():
    """Quick check if satellite endpoints are now working"""
    
    print("🔄 QUICK SATELLITE API STATUS CHECK")
    print("="*50)
    
    base_url = "http://localhost:5001"
    endpoints = [
        ('Critical Alerts', '/api/satellite/critical-alerts'),
        ('Gallery Images', '/api/satellite/gallery-images'), 
        ('Analysis Timeline', '/api/satellite/analysis-timeline'),
        ('Evolution Predictions', '/api/satellite/evolution-predictions')
    ]
    
    working_count = 0
    total_count = len(endpoints)
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ {name}: WORKING")
                    working_count += 1
                else:
                    print(f"❌ {name}: API Error - {data.get('error', 'Unknown')}")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"🔌 {name}: Server not responding")
            break
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    print("-"*50)
    
    if working_count == total_count:
        print("🎉 ALL SATELLITE ENDPOINTS WORKING!")
        print("✅ 500 errors have been successfully fixed")
        print("🌐 Satellite analysis frontend should now load properly")
    elif working_count > 0:
        print(f"⚠️ {working_count}/{total_count} endpoints working")
        print("🔧 Some endpoints may need additional fixes")
    else:
        print("❌ No endpoints working")
        print("🔧 Check if server was restarted and is running")
    
    return working_count == total_count

if __name__ == "__main__":
    quick_satellite_status()