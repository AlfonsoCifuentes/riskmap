#!/usr/bin/env python3
"""
Script to get available Groq models
"""
import os
from dotenv import load_dotenv
import groq

# Load .env
load_dotenv()

# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("❌ GROQ_API_KEY not found in .env")
    exit(1)

try:
    client = groq.Groq(api_key=groq_api_key)
    models = client.models.list()
    
    print("✅ Available Groq models:")
    for model in models.data:
        print(f"  - {model.id}")
        
    # Find recommended models for our use case
    recommended = []
    for model in models.data:
        model_id = model.id.lower()
        if any(keyword in model_id for keyword in ['llama', 'mixtral', 'gemma']):
            recommended.append(model.id)
    
    print("\n🎯 Recommended models for geolocation analysis:")
    for model in recommended[:5]:  # Top 5
        print(f"  - {model}")
        
except Exception as e:
    print(f"❌ Error getting Groq models: {e}")
