import requests

# Probar la nueva ruta de prueba en puerto 5001
try:
    response = requests.get("http://localhost:5001/api/test-bert")
    print(f"Test BERT Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error test-bert: {e}")

# Probar el endpoint de análisis
try:
    test_data = {
        "title": "Military conflict escalates in Ukraine with nuclear threats",
        "content": "The situation shows severe military escalation with nuclear implications",
        "location": "Ukraine",
        "risk_level": "critical"
    }
    response = requests.post("http://localhost:5001/api/analyze-importance", json=test_data)
    print(f"\nAnalyze Importance Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Importance Factor: {result.get('importance_factor')}")
        print(f"Risk Factor: {result.get('risk_factor')}")
        print(f"BERT Analysis: {result.get('bert_analysis')}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error analyze-importance: {e}")
