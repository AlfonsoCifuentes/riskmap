"""
RiskMap CV Detection Pipeline
================================
Runs YOLO + custom classifiers on stored images to detect:
  - Conflict INDICATORS: tanks, military vehicles, weapons, destroyed buildings, troops
  - Disaster SIGNALS: fire, smoke, flood, structural damage, debris

Stores results in `detections` and `signals` tables.

Usage:
    python -m src.pipeline.detect
"""

import os
import sys
import io
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CV-DETECT] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YOLO class mappings to conflict/disaster categories
# ---------------------------------------------------------------------------

CONFLICT_CLASSES = {
    'truck', 'bus', 'car',  # potential military vehicles
    'airplane', 'helicopter',  # military aircraft
    'person',  # troops / combatants (in military context)
    'boat',  # naval
}

DISASTER_CLASSES = {
    'fire', 'smoke',  # wildfire, explosion
    'flood', 'water',  # flood detection
}

# Custom keywords for YOLO class names in fine-tuned models
INDICATOR_KEYWORDS = [
    'tank', 'military', 'weapon', 'missile', 'artillery', 'armored',
    'destroyed', 'damage', 'explosion', 'rubble', 'crater',
    'soldier', 'troop', 'uniform', 'barricade',
]

SIGNAL_KEYWORDS = [
    'fire', 'smoke', 'flood', 'debris', 'collapse', 'landslide',
    'destruction', 'damage', 'ruin', 'wreckage',
]


def load_yolo_model():
    """Load YOLO model (ultralytics)."""
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')  # nano model for speed
        logger.info("✅ YOLOv8n loaded")
        return model
    except Exception as e:
        logger.warning(f"YOLO load failed: {e}")
        return None


def classify_detections(classes: List[Dict]) -> Tuple[bool, bool, str]:
    """
    Classify YOLO detections as conflict indicators or disaster signals.
    Returns: (is_conflict, is_disaster, detection_type)
    """
    class_names = [c.get('class', '').lower() for c in classes]
    all_text = ' '.join(class_names)

    is_conflict = any(kw in all_text for kw in INDICATOR_KEYWORDS)
    is_disaster = any(kw in all_text for kw in SIGNAL_KEYWORDS)

    # Standard YOLO classes in military context
    if not is_conflict:
        military_vehicles = sum(1 for c in class_names if c in ('truck', 'airplane'))
        if military_vehicles >= 3:  # multiple military-type objects
            is_conflict = True

    if is_conflict and is_disaster:
        detection_type = 'indicator'  # conflict takes priority
    elif is_conflict:
        detection_type = 'indicator'
    elif is_disaster:
        detection_type = 'signal'
    else:
        detection_type = 'neutral'

    return is_conflict, is_disaster, detection_type


def run_detection_on_image(model, image_data: bytes) -> Optional[List[Dict]]:
    """Run YOLO on image bytes, return list of detections."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_data))
        results = model(img, conf=0.3, verbose=False)

        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names.get(cls_id, f'class_{cls_id}')
                score = float(box.conf[0])
                bbox = box.xyxy[0].tolist()

                detections.append({
                    'class': cls_name,
                    'score': round(score, 3),
                    'bbox': [round(x, 1) for x in bbox],
                })

        return detections
    except Exception as e:
        logger.debug(f"Detection failed: {e}")
        return None


def process_undetected_images():
    """Find images without detections and run CV on them."""
    db = get_db()
    ph = db.placeholder

    # Get images that haven't been processed
    rows = db.execute(
        """SELECT i.id, i.image_data, i.source_type, i.latitude, i.longitude,
                  i.event_id, i.aoi_id, i.image_format
           FROM images i
           LEFT JOIN detections d ON d.image_id = i.id
           WHERE d.id IS NULL
             AND i.image_data IS NOT NULL
             AND i.image_format != 'json'
           ORDER BY i.stored_at DESC
           LIMIT 50""",
        fetch=True,
    )

    if not rows:
        logger.info("No unprocessed images found")
        return

    logger.info(f"Processing {len(rows)} images…")

    model = load_yolo_model()
    if not model:
        logger.error("Cannot proceed without YOLO model")
        return

    detected_count = 0
    signal_count = 0

    for row in rows:
        image_id = row['id']
        image_data = row.get('image_data')
        if not image_data:
            continue

        # Handle memoryview/bytes
        if isinstance(image_data, memoryview):
            image_data = bytes(image_data)

        detections = run_detection_on_image(model, image_data)
        if detections is None:
            continue

        if not detections:
            # No objects detected — store empty detection
            db.execute(
                f"""INSERT INTO detections
                    (image_id, event_id, detector, detection_type,
                     classes_json, top_class, top_score, total_objects,
                     is_conflict, is_disaster)
                    VALUES ({ph},{ph},'yolov8n','neutral',
                            '[]', NULL, 0, 0, 0, 0)""",
                (image_id, row.get('event_id')),
            )
            continue

        # Classify
        is_conflict, is_disaster, detection_type = classify_detections(detections)

        # Sort by score desc
        detections.sort(key=lambda x: x['score'], reverse=True)
        top_class = detections[0]['class']
        top_score = detections[0]['score']

        db.execute(
            f"""INSERT INTO detections
                (image_id, event_id, detector, detection_type,
                 classes_json, top_class, top_score, total_objects,
                 is_conflict, is_disaster, explanation)
                VALUES ({ph},{ph},'yolov8n',{ph},
                        {ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                image_id, row.get('event_id'), detection_type,
                json.dumps(detections), top_class, top_score,
                len(detections),
                1 if is_conflict else 0,
                1 if is_disaster else 0,
                f"Detected {len(detections)} objects: {', '.join(d['class'] for d in detections[:5])}",
            ),
        )
        detected_count += 1

        # Create signal if conflict/disaster detected
        if is_conflict or is_disaster:
            signal_type = 'conflict_indicator' if is_conflict else 'disaster_signal'
            severity = top_score

            # Get detection ID
            det_rows = db.execute(
                "SELECT id FROM detections ORDER BY id DESC LIMIT 1", fetch=True
            )
            detection_id = det_rows[0]['id'] if det_rows else None

            db.execute(
                f"""INSERT INTO signals
                    (event_id, detection_id, image_id, signal_type,
                     severity, title, description, latitude, longitude)
                    VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
                (
                    row.get('event_id'), detection_id, image_id,
                    signal_type, severity,
                    f"{detection_type.title()}: {top_class} detected",
                    f"YOLOv8 detected {len(detections)} objects. "
                    f"Top: {top_class} ({top_score:.0%}). "
                    f"{'⚔️ Conflict' if is_conflict else '🌪️ Disaster'} signal.",
                    row.get('latitude'), row.get('longitude'),
                ),
            )
            signal_count += 1

    logger.info(f"✅ Processed {len(rows)} images: "
                f"{detected_count} with objects, {signal_count} signals generated")


def main():
    logger.info("=" * 60)
    logger.info("RiskMap CV Detection Pipeline")
    logger.info("=" * 60)
    process_undetected_images()
    logger.info("Detection complete")


if __name__ == '__main__':
    main()
