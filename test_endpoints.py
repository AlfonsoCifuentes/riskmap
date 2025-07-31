import requests

# Probar diferentes endpoints para ver cuáles están disponibles
endpoints = [
    "/",
    "/api/dashboard/stats",
    "/api/articles",
    "/api/analyze-importance"
]

for endpoint in endpoints:
    try:
        if endpoint == "/api/analyze-importance":
            response = requests.post(f"http://localhost:5000{endpoint}", json={"title":"test"})
        else:
            response = requests.get(f"http://localhost:5000{endpoint}")
        print(f"{endpoint}: {response.status_code}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {e}")
