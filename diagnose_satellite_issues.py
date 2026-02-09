#!/usr/bin/env python3
"""
Diagnostic script to identify why satellite API endpoints are still failing
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

def diagnose_satellite_issues():
    """Comprehensive diagnosis of satellite API issues"""
    
    print("🔍 SATELLITE API DIAGNOSTICS")
    print("="*60)
    
    # Check database
    print("\n1️⃣ DATABASE CHECK")
    print("-"*30)
    
    db_path = './data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print(f"❌ Database missing: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check satellite_alerts table
            cursor.execute("SELECT COUNT(*) FROM satellite_alerts")
            alerts_count = cursor.fetchone()[0]
            print(f"✅ satellite_alerts table: {alerts_count} rows")
            
            # Check sample data in satellite_alerts
            cursor.execute("SELECT id, alert_type, confidence FROM satellite_alerts LIMIT 3")
            sample_alerts = cursor.fetchall()
            for alert in sample_alerts:
                print(f"   📋 ID {alert[0]}: {alert[1]} (confidence: {alert[2]})")
            
            # Check satellite_images table
            cursor.execute("SELECT COUNT(*) FROM satellite_images")
            images_count = cursor.fetchone()[0]
            print(f"✅ satellite_images table: {images_count} rows")
            
            # Check satellite_timeline table  
            cursor.execute("SELECT COUNT(*) FROM satellite_timeline")
            timeline_count = cursor.fetchone()[0]
            print(f"✅ satellite_timeline table: {timeline_count} rows")
            
            # Check image_analysis table
            cursor.execute("SELECT COUNT(*) FROM image_analysis")
            analysis_count = cursor.fetchone()[0]
            print(f"✅ image_analysis table: {analysis_count} rows")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Check server connection
    print("\n2️⃣ SERVER CONNECTION CHECK")
    print("-"*30)
    
    try:
        response = requests.get("http://localhost:5001/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Server is responding")
        else:
            print(f"⚠️ Server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is RISKMAP.py running?")
        return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Test each endpoint with detailed error analysis
    print("\n3️⃣ ENDPOINT DETAILED ANALYSIS")
    print("-"*30)
    
    endpoints = {
        'critical-alerts': '/api/satellite/critical-alerts',
        'gallery-images': '/api/satellite/gallery-images', 
        'analysis-timeline': '/api/satellite/analysis-timeline',
        'evolution-predictions': '/api/satellite/evolution-predictions'
    }
    
    for name, endpoint in endpoints.items():
        print(f"\n🔍 Testing {name}:")
        
        try:
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"  ✅ Working correctly")
                    
                    # Show data counts
                    if 'alerts' in data:
                        print(f"     📊 {len(data['alerts'])} alerts returned")
                    elif 'images' in data:
                        print(f"     📊 {len(data['images'])} images returned")
                    elif 'timeline' in data:
                        print(f"     📊 {len(data['timeline'])} timeline entries returned")
                    elif 'predictions' in data:
                        print(f"     📊 {len(data['predictions'])} predictions returned")
                else:
                    print(f"  ❌ API returned error: {data.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"     Error: {error_data.get('error', 'No error message')}")
                except:
                    print(f"     Response: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
    
    print("\n4️⃣ RECOMMENDED ACTIONS")
    print("-"*30)
    print("🔧 If endpoints are still failing:")
    print("   1. Restart the RISKMAP.py server to pick up code changes")
    print("   2. Check the server logs for detailed error messages")
    print("   3. Verify database permissions and file access")
    print("   4. Ensure all required tables have been created")
    
    print(f"\n✅ Diagnostic completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    diagnose_satellite_issues()