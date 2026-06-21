"""
Riskmap A.I. CV Detection Pipeline
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
    # Vehicles that may be military (context-dependent)
    'truck', 'bus', 'car', 'vehicle', 'military vehicle',
    'airplane', 'helicopter', 'aircraft',
    'person', 'boat', 'ship',
}

DISASTER_CLASSES = {
    'fire', 'smoke', 'flood', 'water',
}

# Keywords in YOLO class names (standard or fine-tuned models)
INDICATOR_KEYWORDS = [
    # Military hardware
    'tank', 'apc', 'armored', 'armoured', 'military', 'combat',
    'weapon', 'missile', 'rocket', 'artillery', 'cannon', 'gun',
    'aircraft carrier', 'warship', 'fighter',
    # Personnel
    'soldier', 'troop', 'uniform', 'combatant', 'sniper', 'gunman',
    # Destruction
    'destroyed', 'damage', 'explosion', 'rubble', 'crater', 'debris',
    'ruin', 'wreckage', 'collapse', 'bombed', 'shelled',
    # Barriers / conflict infrastructure
    'barricade', 'checkpoint', 'bunker', 'trench', 'fortification',
]

SIGNAL_KEYWORDS = [
    'fire', 'smoke', 'column', 'plume', 'flood', 'debris', 'collapse',
    'landslide', 'destruction', 'damage', 'ruin', 'wreckage', 'hazmat',
]

# Groq Vision: what elements to detect in conflict imagery
VISION_DETECTION_PROMPT = """\
Analyse this satellite or news photograph for geopolitical / conflict / disaster indicators.
List ONLY what you can clearly see. Reply in VALID JSON:
{
  "elements": [
    "<element 1>",
    "<element 2>"
  ],
  "conflict_indicators": ["tanks","troops","artillery","destroyed buildings","smoke columns",
                           "missile launchers","military aircraft","warships","explosions",
                           "trenches","armored vehicles","weapons","armed personnel"],
  "disaster_signals": ["fire","smoke plume","flood","rubble","landslide","structural collapse"],
  "refugee_displacement": true/false,
  "is_conflict_scene": true/false,
  "is_disaster_scene": true/false,
  "primary_subject": "<one sentence>",
  "confidence": 0.0-1.0
}
Only include keys that are relevant. Omit speculation."""


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


def describe_image_with_ai(image_data: bytes) -> Optional[Dict]:
    """Use Groq Vision (llama-3.2-11b-vision-preview) to describe conflict/disaster elements.

    Returns parsed JSON dict or None on failure.
    This serves as a high-accuracy fallback when YOLO finds nothing or only generic objects.
    """
    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        return None

    import base64
    import requests

    # Encode image to base64
    b64 = base64.b64encode(image_data).decode('utf-8')

    # Detect MIME type from first bytes
    if image_data[:3] == b'\xff\xd8\xff':
        mime = 'image/jpeg'
    elif image_data[:4] == b'\x89PNG':
        mime = 'image/png'
    elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
        mime = 'image/webp'
    else:
        mime = 'image/jpeg'  # default

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.2-11b-vision-preview',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:{mime};base64,{b64}',
                                    'detail': 'low',
                                },
                            },
                            {
                                'type': 'text',
                                'text': VISION_DETECTION_PROMPT,
                            },
                        ],
                    }
                ],
                'max_tokens': 300,
                'temperature': 0.1,
                'response_format': {'type': 'json_object'},
            },
            timeout=20,
        )
        content = resp.json()['choices'][0]['message']['content'].strip()
        return json.loads(content)
    except Exception as e:
        logger.debug(f"Groq Vision failed: {e}")
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
        return 0

    logger.info(f"Processing {len(rows)} images…")

    model = load_yolo_model()
    # model may be None — we'll fall back to AI vision in that case

    detected_count = 0
    signal_count = 0
    ai_vision_count = 0
    # Rate-limit AI vision calls (Groq Vision has limited free quota)
    ai_vision_used = 0
    AI_VISION_MAX = 10  # max per pipeline run

    for row in rows:
        image_id = row['id']
        image_data = row.get('image_data')
        if not image_data:
            continue

        # Handle memoryview/bytes
        if isinstance(image_data, memoryview):
            image_data = bytes(image_data)

        detections = None
        ai_desc = None
        detector_name = 'yolov8n'

        # Primary: YOLO detection
        if model:
            detections = run_detection_on_image(model, image_data)

        # Determine if we need AI vision:
        # - YOLO not available, OR
        # - YOLO found only generic non-conflict objects and AI quota not exhausted
        yolo_only_generic = (
            detections is not None
            and not any(
                any(kw in d.get('class', '').lower() for kw in INDICATOR_KEYWORDS + SIGNAL_KEYWORDS)
                for d in (detections or [])
            )
        )
        use_ai_vision = (
            (model is None or yolo_only_generic or not detections)
            and ai_vision_used < AI_VISION_MAX
        )

        if use_ai_vision:
            ai_desc = describe_image_with_ai(image_data)
            if ai_desc:
                ai_vision_used += 1
                detector_name = 'yolov8n+groq_vision' if model else 'groq_vision'
                # Convert AI description to detection-list format
                ai_classes = (
                    ai_desc.get('conflict_indicators', []) +
                    ai_desc.get('disaster_signals', []) +
                    ai_desc.get('elements', [])
                )
                ai_detections = [
                    {'class': cls, 'score': float(ai_desc.get('confidence', 0.7)), 'bbox': []}
                    for cls in ai_classes
                ]
                if ai_detections:
                    detections = ai_detections  # replace or supplement YOLO
                ai_vision_count += 1

        if detections is None:
            continue

        if not detections:
            # No objects detected — store empty detection
            db.execute(
                f"""INSERT INTO detections
                    (image_id, event_id, detector, detection_type,
                     classes_json, top_class, top_score, total_objects,
                     is_conflict, is_disaster)
                    VALUES ({ph},{ph},{ph},'neutral',
                            '[]', NULL, 0, 0, 0, 0)""",
                (image_id, row.get('event_id'), detector_name),
            )
            continue

        # Classify
        is_conflict, is_disaster, detection_type = classify_detections(detections)

        # Override with AI description flags if available
        if ai_desc:
            if ai_desc.get('is_conflict_scene'):
                is_conflict = True
                detection_type = 'indicator'
            if ai_desc.get('is_disaster_scene'):
                is_disaster = True
                if not is_conflict:
                    detection_type = 'signal'
            if ai_desc.get('refugee_displacement'):
                is_conflict = True
                detection_type = 'indicator'

        # Sort by score desc
        detections_with_score = [d for d in detections if d.get('score', 0) > 0]
        if detections_with_score:
            detections_with_score.sort(key=lambda x: x['score'], reverse=True)
            top_class = detections_with_score[0]['class']
            top_score = detections_with_score[0]['score']
        else:
            top_class = detections[0]['class']
            top_score = float(ai_desc.get('confidence', 0.5)) if ai_desc else 0.5

        # Build explanation
        ai_primary = ai_desc.get('primary_subject', '') if ai_desc else ''
        explanation = (
            f"{'[AI+YOLO]' if ai_desc else '[YOLO]'} "
            f"Detected {len(detections)} objects: {', '.join(d['class'] for d in detections[:5])}."
            + (f" AI: {ai_primary}" if ai_primary else '')
        )

        db.execute(
            f"""INSERT INTO detections
                (image_id, event_id, detector, detection_type,
                 classes_json, top_class, top_score, total_objects,
                 is_conflict, is_disaster, explanation)
                VALUES ({ph},{ph},{ph},{ph},
                        {ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                image_id, row.get('event_id'), detector_name, detection_type,
                json.dumps(detections), top_class, top_score,
                len(detections),
                1 if is_conflict else 0,
                1 if is_disaster else 0,
                explanation,
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
                    f"{detector_name} detected {len(detections)} objects. "
                    f"Top: {top_class} ({top_score:.0%}). "
                    f"{'⚔️ Conflict' if is_conflict else '🌪️ Disaster'} signal."
                    + (f" {ai_desc.get('primary_subject', '')}" if ai_desc else ''),
                    row.get('latitude'), row.get('longitude'),
                ),
            )
            signal_count += 1

    logger.info(f"✅ Processed {len(rows)} images: "
                f"{detected_count} with objects, {signal_count} signals generated, "
                f"{ai_vision_count} AI-vision analyses")
    return detected_count


def main():
    logger.info("=" * 60)
    logger.info("Riskmap A.I. CV Detection Pipeline")
    logger.info("=" * 60)
    process_undetected_images()
    logger.info("Detection complete")


if __name__ == '__main__':
    main()
