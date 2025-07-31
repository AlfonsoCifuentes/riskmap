import requests

# Probar la nueva ruta de prueba
try:
    response = requests.get("http://localhost:5000/api/test-bert")
    print(f"Test BERT Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Probar el endpoint de análisis
try:
    response = requests.post("http://localhost:5000/api/analyze-importance", json={"title":"test"})
    print(f"Analyze Importance Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
