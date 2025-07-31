import requests
import json

# Prueba simple del endpoint
url = "http://localhost:5000/api/analyze-importance"
data = {
    "title": "Test article about conflict",
    "content": "This is a test content about military conflict"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
