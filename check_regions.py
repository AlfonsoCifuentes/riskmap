#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("Region Analysis:")
print("=" * 50)

# Check distinct regions
cursor.execute("SELECT DISTINCT region FROM articles WHERE region IS NOT NULL AND region != '' LIMIT 10")
regions = cursor.fetchall()
print(f"Distinct regions in database: {len(regions)}")
for region in regions:
    print(f"  - {region[0]}")

# Check distinct countries  
cursor.execute("SELECT DISTINCT country FROM articles WHERE country IS NOT NULL AND country != '' LIMIT 10")
countries = cursor.fetchall()
print(f"\nDistinct countries in database: {len(countries)}")
for country in countries:
    print(f"  - {country[0]}")

# Check high risk articles with location
cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high' AND (country IS NOT NULL OR region IS NOT NULL)")
high_risk_with_location = cursor.fetchone()[0]
print(f"\nHigh risk articles with location: {high_risk_with_location}")

# Check distinct high-risk countries/regions
cursor.execute("SELECT DISTINCT COALESCE(country, region) FROM articles WHERE risk_level = 'high' AND (country IS NOT NULL OR region IS NOT NULL)")
conflict_regions = cursor.fetchall()
print(f"High-risk regions/countries: {len(conflict_regions)}")
for region in conflict_regions:
    print(f"  - {region[0]}")

# Check the actual query used in the API
cursor.execute("SELECT COUNT(DISTINCT country) FROM articles WHERE country IS NOT NULL AND risk_level = 'high'")
api_result = cursor.fetchone()[0]
print(f"\nCurrent API query result: {api_result}")

conn.close()