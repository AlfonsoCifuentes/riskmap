#!/usr/bin/env python3
"""
Quick test to verify the conflict monitoring API response structure
"""

import requests
import json

def test_conflict_api():
    """Test the conflict monitoring API and show response structure"""
    try:
        print("🔍 Testing conflict monitoring API...")
        
        response = requests.get('http://localhost:5001/api/conflict-monitoring/real-data', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Response successful")
            print(f"📊 Success: {data.get('success', False)}")
            print(f"📅 Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"🗃️ Data source: {data.get('data_source', 'N/A')}")
            
            # Check statistics structure
            if 'statistics' in data:
                stats = data['statistics']
                print("\n📈 Statistics available:")
                print(f"   • Total conflicts: {stats.get('total_conflicts', 0)}")
                print(f"   • High risk conflicts: {stats.get('high_risk_conflicts', 0)}")
                print(f"   • Medium risk conflicts: {stats.get('medium_risk_conflicts', 0)}")
                print(f"   • Active sources: {stats.get('active_sources', 0)}")
                print(f"   • Affected countries: {stats.get('affected_countries', 0)}")
                print(f"   • Average sentiment: {stats.get('average_sentiment', 0)}")
                print(f"   • Last updated: {stats.get('last_updated', 'N/A')}")
            else:
                print("❌ No statistics found in response")
            
            # Check conflicts data
            if 'conflicts' in data:
                conflicts_count = len(data['conflicts'])
                print(f"\n🎯 Conflicts data: {conflicts_count} items")
                
                if conflicts_count > 0:
                    sample = data['conflicts'][0]
                    print("   Sample conflict structure:")
                    for key in sample.keys():
                        print(f"      - {key}: {type(sample[key]).__name__}")
            else:
                print("❌ No conflicts data found in response")
                
            print(f"\n🌍 Total with coordinates: {data.get('total_with_coordinates', 0)}")
            
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_conflict_api()
