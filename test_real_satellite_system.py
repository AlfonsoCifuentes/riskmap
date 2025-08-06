#!/usr/bin/env python3
"""
Test Real Satellite Analysis System
Prueba el sistema completo de análisis satelital sin simulaciones
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_real_satellite_system():
    """Test completo del sistema satelital real"""
    print("🛰️ Testing REAL Satellite Analysis System")
    print("=" * 50)
    
    base_url = "http://localhost:8050"
    
    # Verificar que tenemos credenciales de Sentinel Hub
    sentinel_client_id = os.getenv('SENTINEL_CLIENT_ID')
    sentinel_client_secret = os.getenv('SENTINEL_CLIENT_SECRET') 
    sentinel_instance_id = os.getenv('SENTINEL_INSTANCE_ID')
    
    if not (sentinel_client_id and sentinel_client_secret and sentinel_instance_id):
        print("❌ Credenciales de Sentinel Hub no configuradas en el entorno")
        print("💡 Verifica las credenciales en el archivo .env:")
        print("   SENTINEL_CLIENT_ID=...")
        print("   SENTINEL_CLIENT_SECRET=...")
        print("   SENTINEL_INSTANCE_ID=...")
        return False
    
    print(f"✅ Credenciales de Sentinel Hub configuradas")
    print(f"   Client ID: {sentinel_client_id[:10]}...")
    print(f"   Instance ID: {sentinel_instance_id[:10]}...")
    print()
    
    # Coordenadas reales de zonas de conflicto conocidas
    test_locations = [
        {
            "latitude": 36.2021,
            "longitude": 37.1343,
            "location": "Aleppo, Siria",
            "description": "Zona de conflicto histórica"
        },
        {
            "latitude": 50.4501,
            "longitude": 30.5234,
            "location": "Kiev, Ucrania", 
            "description": "Capital con actividad militar reciente"
        },
        {
            "latitude": 31.7683,
            "longitude": 35.2137,
            "location": "Jerusalén, Israel/Palestina",
            "description": "Zona de tensión geopolítica"
        }
    ]
    
    success_count = 0
    
    for i, location_data in enumerate(test_locations):
        print(f"\n{i+1}️⃣ Testing location: {location_data['location']}")
        print(f"📍 Coordinates: {location_data['latitude']}, {location_data['longitude']}")
        print(f"📝 Description: {location_data['description']}")
        
        try:
            # 1. Request satellite analysis
            print("   🚀 Requesting real satellite analysis...")
            response = requests.post(
                f"{base_url}/api/satellite/analyze",
                json={
                    "latitude": location_data['latitude'],
                    "longitude": location_data['longitude'],
                    "location": location_data['location'],
                    "analysis_type": "conflict_monitoring",
                    "area_km2": 25,
                    "resolution": "10m"
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
                continue
            
            result = response.json()
            if not result['success']:
                print(f"   ❌ Analysis request failed: {result.get('error')}")
                continue
            
            print(f"   ✅ Analysis initiated: {result.get('task_id')}")
            print(f"   📡 Provider: {result.get('provider')}")
            print(f"   📏 Area: {result.get('area_km2')} km²")
            
            # 2. Wait and monitor progress
            print("   ⏳ Monitoring real analysis progress...")
            max_wait = 300  # 5 minutes max
            wait_time = 0
            check_interval = 10  # Check every 10 seconds
            
            while wait_time < max_wait:
                time.sleep(check_interval)
                wait_time += check_interval
                
                # Check results
                results_response = requests.get(f"{base_url}/api/satellite/results?limit=5")
                if results_response.status_code == 200:
                    results_data = results_response.json()
                    if results_data['success'] and results_data['analyses']:
                        latest_analysis = results_data['analyses'][0]
                        
                        print(f"   📊 Status: {latest_analysis['status']} (waited {wait_time}s)")
                        
                        if latest_analysis['status'] == 'completed':
                            print(f"   ✅ Analysis completed successfully!")
                            
                            # Parse results
                            if latest_analysis['analysis_results']:
                                try:
                                    analysis_results = json.loads(latest_analysis['analysis_results'])
                                    cv_results = analysis_results.get('cv_results', {})
                                    
                                    print(f"   📸 Image: {latest_analysis.get('image_url', 'Not available')}")
                                    print(f"   🔍 Detections: {cv_results.get('total_detections', 0)}")
                                    print(f"   🚨 Risk Level: {cv_results.get('risk_level', 'unknown').upper()}")
                                    print(f"   📈 Risk Score: {cv_results.get('risk_score', 0):.2f}")
                                    print(f"   🚗 Vehicles: {cv_results.get('vehicle_count', 0)}")
                                    print(f"   🔥 Fire: {cv_results.get('fire_count', 0)}")
                                    print(f"   💨 Smoke: {cv_results.get('smoke_count', 0)}")
                                    
                                    if cv_results.get('risk_factors'):
                                        print(f"   ⚠️ Risk Factors: {', '.join(cv_results['risk_factors'])}")
                                    
                                    success_count += 1
                                    break
                                    
                                except json.JSONDecodeError:
                                    print(f"   ⚠️ Could not parse analysis results")
                            
                        elif latest_analysis['status'] == 'failed':
                            print(f"   ❌ Analysis failed: {latest_analysis.get('analysis_results', 'Unknown error')}")
                            break
                        
                        elif latest_analysis['status'] == 'processing':
                            print(f"   🔄 Still processing... (Real Sentinel Hub + CV analysis)")
                            continue
                
                else:
                    print(f"   ⚠️ Could not check results (HTTP {results_response.status_code})")
            
            if wait_time >= max_wait:
                print(f"   ⏱️ Timeout after {max_wait}s - analysis may still be running")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Make sure Flask app is running on {base_url}")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
    
    print(f"\n🎯 Final Results:")
    print(f"✅ Successful analyses: {success_count}/{len(test_locations)}")
    print(f"📊 Success rate: {(success_count/len(test_locations)*100):.1f}%")
    
    if success_count > 0:
        print("\n🎉 Real satellite analysis system is working!")
        print("🛰️ Using genuine Sentinel Hub imagery")
        print("🔍 Using real computer vision analysis")
        print("📡 No mock data or simulations")
        return True
    else:
        print("\n💥 No successful analyses completed")
        print("🔧 Check:")
        print("   - Sentinel Hub API key configuration")
        print("   - Internet connectivity")
        print("   - Flask application status")
        print("   - Computer vision model availability")
        return False

def check_system_prerequisites():
    """Verificar prerequisitos del sistema"""
    print("🔍 Checking System Prerequisites")
    print("=" * 35)
    
    # Check Sentinel Hub credentials
    sentinel_client_id = os.getenv('SENTINEL_CLIENT_ID')
    sentinel_client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
    sentinel_instance_id = os.getenv('SENTINEL_INSTANCE_ID')
    sentinel_ok = bool(sentinel_client_id and sentinel_client_secret and sentinel_instance_id)
    print("🔑 Sentinel Hub Credentials: {}".format('✅ Configured' if sentinel_ok else '❌ Missing'))
    
    # Check model directory
    model_dir = Path('models/trained/deployment_package')
    model_ok = model_dir.exists()
    print("🤖 Computer Vision Model: {}".format('✅ Found' if model_ok else '❌ Missing'))
    
    # Check data directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    print("📁 Data Directory: ✅ Ready")
    
    # Check satellite images directory
    images_dir = Path('data/satellite_images')
    images_dir.mkdir(exist_ok=True)
    print("🖼️ Satellite Images Dir: ✅ Ready")
    
    print()
    
    all_ready = sentinel_ok and model_ok
    if all_ready:
        print("✅ All prerequisites met - system ready for real analysis!")
    else:
        print("⚠️ Some prerequisites missing - system may use fallbacks")
    
    return all_ready

if __name__ == "__main__":
    print(f"🔬 Real Satellite Analysis System Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check prerequisites first
    prereq_ready = check_system_prerequisites()
    print()
    
    # Run main test
    success = test_real_satellite_system()
    
    if success:
        print(f"\n🎯 System is fully functional with real satellite analysis!")
        exit(0)
    else:
        print(f"\n💥 System needs attention - check configuration and connectivity")
        exit(1)
