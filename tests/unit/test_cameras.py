"""Tests for Visual Intelligence camera logic (spec §89). Experimental, no PII."""
from src.core import cameras


def test_registry_curated_5_to_15():
    reg = cameras.load_registry()
    assert 5 <= len(reg) <= 15
    for c in reg:
        # environmental content only; never a biometric/tracking purpose
        for d in c.get("expected_content", []):
            assert d in cameras.ALLOWED_DETECTIONS


def test_forbidden_detections_are_documented_and_excluded():
    # Boundary lock: no allowed detection is a forbidden one.
    assert cameras.ALLOWED_DETECTIONS.isdisjoint(cameras.FORBIDDEN_DETECTIONS)
    assert "face_recognition" in cameras.FORBIDDEN_DETECTIONS


def test_health_http200_not_automatically_online():
    # 200 + image but very stale capture -> DEGRADED, not ONLINE.
    st = cameras.health_state(http_ok=True, content_is_image=True,
                              consecutive_failures=0, last_success_age_s=10_000,
                              sampling_interval_s=120)
    assert st == "DEGRADED"
    ok = cameras.health_state(http_ok=True, content_is_image=True,
                              consecutive_failures=0, last_success_age_s=60,
                              sampling_interval_s=120)
    assert ok == "ONLINE"


def test_health_offline_and_blocked():
    assert cameras.health_state(http_ok=False, content_is_image=False,
                                consecutive_failures=5, last_success_age_s=None,
                                sampling_interval_s=120) == "OFFLINE"
    assert cameras.health_state(http_ok=True, content_is_image=False,
                                consecutive_failures=0, last_success_age_s=1,
                                sampling_interval_s=120) == "BLOCKED"


def test_adaptive_sampling_speeds_up_on_anomaly():
    base = 120
    assert cameras.next_sampling_interval(base_interval_s=base, anomaly_active=False, persisting=False) == 120
    assert cameras.next_sampling_interval(base_interval_s=base, anomaly_active=True, persisting=False) < 120
    assert cameras.next_sampling_interval(base_interval_s=base, anomaly_active=True, persisting=True) <= 20


def test_temporal_confirmation_requires_persistence():
    persistent = cameras.temporal_confirmation([0.82, 0.87, 0.91])
    transient = cameras.temporal_confirmation([0.79, 0.03, 0.80])
    assert persistent["confirmed"] is True
    assert transient["confirmed"] is False


def test_lone_camera_is_only_a_candidate():
    lone = cameras.corroboration(visual_confidence=0.88, firms_hotspot_nearby=False,
                                 news_event_nearby=False, official_alert=False)
    assert lone["status"] == "candidate_visual_signal"
    strong = cameras.corroboration(visual_confidence=0.88, firms_hotspot_nearby=True,
                                    news_event_nearby=True, official_alert=False)
    assert strong["status"] == "corroborated"
    assert strong["event_confidence"] > lone["event_confidence"]
