#!/usr/bin/env python3
"""
Simplified GDELT integration for geolocation analyzer
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

def extract_event_location(text: str) -> str:
    """Extract location from text using simple pattern matching"""
    if not text:
        return ""
    
    # Simple location patterns
    location_patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:city|City)',
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'\b([A-Z][a-z]+),\s*([A-Z][a-z]+)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return ""

def fetch_gdelt_events(days: int = 1) -> List[Dict[str, Any]]:
    """
    Descarga eventos recientes de GDELT (https://www.gdeltproject.org/)
    Versión simplificada sin dependencias externas
    """
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "conflict OR protest OR war OR military OR explosion OR attack OR disaster",
        "mode": "ArtList",
        "maxrecords": 50,
        "format": "json"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        
        try:
            data = response.json()
        except ValueError as ve:
            logger.warning(f"GDELT returned invalid JSON: {ve}")
            return []
            
        results = []
        articles = data.get("articles", [])
        
        for art in articles[:20]:  # Limitar a 20 eventos recientes
            # Extract location from title and content
            title = art.get("title", "")
            content = art.get("seendate", "") + " " + art.get("sourcecountry", "")
            
            location = extract_event_location(title) or extract_event_location(content)
            
            results.append({
                "title": title,
                "content": content,
                "url": art.get("url"),
                "published_at": art.get("seendate"),
                "source": art.get("sourceurl", "GDELT"),
                "location": location,
                "type": art.get("domain", "news"),
                "country": art.get("sourcecountry", "")
            })
            
        logger.info(f"✅ Obtenidos {len(results)} eventos GDELT")
        return results
        
    except requests.exceptions.HTTPError as he:
        logger.warning(f"Error fetching GDELT events (HTTP): {he}")
        return []
    except Exception as e:
        logger.error(f"Error fetching GDELT events: {e}")
        return []
