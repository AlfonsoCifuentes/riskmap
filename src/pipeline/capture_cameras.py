"""
Visual Intelligence — camera frame capture (spec §89, experimental).

Fetches a single recent snapshot from each curated public webcam and stores it
as an image (source_type='camera') so the CV stage and the Visual Intelligence
page have real frames. Environmental phenomena only; no biometric/tracking use.

€0 + honest:
  * one frame per camera per run (adaptive sampling handled by cadence), not a
    continuous stream;
  * respects DISABLE_CAMERA_FETCH kill switch;
  * a camera that fails to return a valid image is skipped (its health degrades),
    never faked.

Usage: python -m src.pipeline.capture_cameras
"""
import io
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CAMERAS] %(message)s")
logger = logging.getLogger(__name__)

_MAX_BYTES = 4 * 1024 * 1024  # 4 MB cap per snapshot


def _looks_like_image(content_type: str, data: bytes) -> bool:
    if content_type and content_type.lower().startswith("image/"):
        return True
    # JPEG / PNG / WEBP magic bytes as a fallback.
    return (data[:3] == b"\xff\xd8\xff"
            or data[:4] == b"\x89PNG"
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP"))


def capture_all() -> int:
    if os.getenv("DISABLE_CAMERA_FETCH", "").lower() in ("1", "true", "yes"):
        logger.info("DISABLE_CAMERA_FETCH set — skipping camera capture")
        return 0

    import requests

    from src.core.cameras import load_registry
    from src.pipeline.acquire_images import store_image

    cameras = load_registry()
    if not cameras:
        logger.info("No cameras in registry")
        return 0

    headers = {"User-Agent": "RiskMap/2.0 VisualIntelligence (+https://github.com/AlfonsoCifuentes/riskmap)"}
    stored = 0
    for cam in cameras:
        url = cam.get("snapshot_url")
        if not url:
            continue
        try:
            resp = requests.get(url, headers=headers, timeout=20, stream=True)
            if resp.status_code != 200:
                logger.warning(f"  ✗ {cam['camera_id']} HTTP {resp.status_code}")
                continue
            data = resp.raw.read(_MAX_BYTES + 1, decode_content=True)
            if len(data) > _MAX_BYTES:
                logger.warning(f"  ✗ {cam['camera_id']} snapshot too large")
                continue
            if not _looks_like_image(resp.headers.get("Content-Type", ""), data):
                logger.warning(f"  ✗ {cam['camera_id']} not an image (BLOCKED/DEGRADED)")
                continue
            store_image(
                "camera", data,
                float(cam.get("latitude") or 0), float(cam.get("longitude") or 0),
                event_id=None, aoi_id=None, source_url=cam.get("source_page") or url,
                metadata={"camera_id": cam.get("camera_id"), "name": cam.get("name"),
                          "operator": cam.get("operator"),
                          "expected_content": cam.get("expected_content", [])},
            )
            stored += 1
            logger.info(f"  📷 {cam['camera_id']} frame stored")
        except Exception as e:  # noqa: BLE001 — one camera never breaks the run
            logger.warning(f"  ✗ {cam.get('camera_id')} failed: {e}")

    logger.info(f"✅ Captured {stored}/{len(cameras)} camera frames")
    return stored


def main():
    capture_all()


if __name__ == "__main__":
    main()
