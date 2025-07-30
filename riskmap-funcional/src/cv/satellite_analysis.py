"""Satellite imagery analysis pipeline (skeleton).

Downloads Sentinel-2 true-color tiles via SentinelHub and runs YOLOv8 pretrained
weights (e.g., fire/ship detection) to identify anomalies such as fires,
explosions, heavy smoke or military equipment. Detected bounding boxes are
converted to geospatial points and stored in `events` with type
`satellite_detected`. Requires environment variables:

SENTINEL_CLIENT_ID, SENTINEL_CLIENT_SECRET

This is a skeleton with stubbed functions ready for real implementation.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import sqlite3
import requests
from requests.auth import HTTPBasicAuth

from utils.config import config, logger
from utils.geo import country_code_to_latlon
from data_ingestion.real_sources import store_events

# pylint: disable=unused-import
try:
    from ultralytics import YOLO  # Ensure ultralytics package is installed
except ImportError:  # pragma: no cover
    YOLO = None  # placeholder if not installed


SENTINEL_ID = os.getenv("SENTINEL_CLIENT_ID", "")
SENTINEL_SECRET = os.getenv("SENTINEL_CLIENT_SECRET", "")
SENTINEL_INSTANCE_ID = os.getenv("SENTINEL_INSTANCE_ID", "")  # e.g., e71ddff3-8d0b-47a2-89d3-31e8408055b4


def download_tile(lat: float, lon: float, date: str) -> str:
    """Download Sentinel-2 true-color tile image (JPEG) via Sentinel Hub."""
    if not SENTINEL_ID or not SENTINEL_SECRET or not SENTINEL_INSTANCE_ID:
        logger.warning("Sentinel Hub credentials missing; skipping download")
        return ""

    # Get OAuth token
    token_url = "https://services.sentinel-hub.com/oauth/token"
    auth = HTTPBasicAuth(SENTINEL_ID, SENTINEL_SECRET)
    data = {"grant_type": "client_credentials"}
    try:
        response = requests.post(token_url, auth=auth, data=data, timeout=30)
        response.raise_for_status()
        token = response.json()["access_token"]
    except Exception as e:
        logger.error(f"Failed to get Sentinel Hub token: {e}")
        return ""

    # Process API request for true color image
    process_url = "https://services.sentinel-hub.com/api/v1/process"
    headers = {"Authorization": f"Bearer {token}"}
    # Define bbox: small area around lat,lon (e.g., 0.1 deg)
    bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]
    payload = {
        "input": {
            "bounds": {"bbox": bbox},
            "data": [{"dataFilter": {"timeRange": {"from": f"{date}T00:00:00Z", "to": f"{date}T23:59:59Z"}}, "type": "sentinel-2-l1c"}]
        },
        "output": {"width": 512, "height": 512},
        "evalscript": "//VERSION=3\nfunction setup() { return { input: [\"B02\", \"B03\", \"B04\"], output: {bands: 3} }; }\nfunction evaluatePixel(sample) { return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02]; }"
    }
    try:
        response = requests.post(process_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        # Save to file
        img_path = f"data/satellite_tiles/{date}_{lat}_{lon}.jpg"
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Downloaded Sentinel-2 tile to {img_path}")
        return img_path
    except Exception as e:
        logger.error(f"Failed to download Sentinel-2 tile: {e}")
        return ""


def detect_anomalies(image_path: str) -> List[Dict[str, Any]]:
    """Run YOLOv8 detection on image and return list of detections."""
    if not YOLO:
        logger.warning("YOLOv8 not available; skipping detection")
        return []
    model = YOLO("yolov8n.pt")  # default weights; replace with custom fine-tuned
    results = model(image_path, verbose=False)
    detections = []
    for r in results:
        boxes = r.boxes.cpu().numpy()  # type: ignore
        for b in boxes:
            detections.append({
                "cls": int(b.cls[0]),
                "conf": float(b.conf[0]),
                "xyxy": b.xyxy[0].tolist()
            })
    return detections


def store_satellite_events(lat: float, lon: float, detections: List[Dict[str, Any]], timestamp: str):
    events = []
    for det in detections:
        cls = det["cls"]
        label = f"yolo_cls_{cls}"
        events.append({
            "title": f"Satellite detection {label}",
            "content": str(det),
            "url": "",  # could link to image path in storage
            "published_at": timestamp,
            "source": "SentinelHub+YOLO",
            "location": [lat, lon],
            "type": "satellite_detected",
            "magnitude": det["conf"]
        })
    store_events(events, table="events")


def run_satellite_pipeline(lat: float, lon: float):
    date = datetime.utcnow().strftime("%Y-%m-%d")
    img = download_tile(lat, lon, date)
    if not img:
        return
    detections = detect_anomalies(img)
    if detections:
        store_satellite_events(lat, lon, detections, datetime.utcnow().isoformat())
        logger.info(f"Stored {len(detections)} satellite detections at {lat},{lon}")


if __name__ == "__main__":
    # Example: run on fixed coords (Kyiv)
    run_satellite_pipeline(50.45, 30.523)
