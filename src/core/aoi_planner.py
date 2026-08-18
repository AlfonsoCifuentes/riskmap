"""Satellite AOI planner + capability guardrails (spec §172/§173, addendum B8).

Decides whether an event warrants an Earth-Observation acquisition, and which
sensor is appropriate — and REFUSES scientifically-invalid requests (e.g.
detecting individual vehicles on 10 m/px Sentinel-2). This is what keeps the
project honest: the system says "unsupported, use high-res benchmark" instead of
pretending a coarse sensor can do a fine task.

Cost discipline (§87.6): only high/critical events trigger EO, respecting a
daily budget the caller enforces.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

# Sensor ground sampling distance (metres/pixel).
SENSOR_GSD_M = {"sentinel-2": 10.0, "sentinel-1": 10.0}

# Minimum object size (metres) a sensor can *credibly* resolve for detection
# (needs several pixels on target). Used by the capability guardrail.
_MIN_DETECTABLE_M = {"sentinel-2": 30.0, "sentinel-1": 30.0}

# Approx real-world size of target classes (metres).
_TARGET_SIZE_M = {
    "individual_vehicle": 6,
    "tank": 7,
    "aircraft": 20,
    "building": 25,
    "flood_extent": 500,
    "burn_scar": 500,
    "smoke_plume": 1000,
    "urban_damage_area": 200,
}


@dataclass
class AOIPlan:
    should_request: bool
    sensor: str | None
    reason: str
    priority: str            # none | low | normal | high
    supported: bool

    def as_dict(self) -> dict:
        return asdict(self)


def capability_check(task: str, sensor: str) -> tuple[bool, str]:
    """Return (supported, reason). Rejects tasks whose target is too small for
    the sensor's resolution (spec §173)."""
    sensor = sensor.lower()
    if sensor not in SENSOR_GSD_M:
        return False, f"unknown sensor {sensor!r}"
    target = _TARGET_SIZE_M.get(task)
    if target is None:
        return True, f"{task}: no size constraint recorded"
    if target < _MIN_DETECTABLE_M[sensor]:
        return False, (
            f"UNSUPPORTED: {task} (~{target} m) is below the credible detection "
            f"limit of {sensor} (~{_MIN_DETECTABLE_M[sensor]} m at "
            f"{SENSOR_GSD_M[sensor]} m/px). Use high-resolution Replay/benchmark "
            f"imagery instead.")
    return True, f"{task} is compatible with {sensor}"


def plan(*, hazard: str, risk_level: str, cloud_cover: float | None = None) -> AOIPlan:
    """Decide the EO acquisition for an event.

    - wildfire  -> Sentinel-2 (burn scar / smoke) + FIRMS elsewhere
    - flood     -> Sentinel-1 SAR (sees through cloud); S2 only if clear
    - earthquake-> Sentinel-2 context / change
    - conflict  -> only large-scale damage context; NO live vehicle detection
    - low/medium risk -> no automatic request (cost discipline)
    """
    hazard = (hazard or "").lower()
    if risk_level not in ("high", "critical"):
        return AOIPlan(False, None,
                       "risk below high — no automatic EO (cost discipline)",
                       "none", True)

    priority = "high" if risk_level == "critical" else "normal"

    if hazard == "wildfire":
        return AOIPlan(True, "sentinel-2",
                       "wildfire: S2 burn-scar/smoke (10 m/px is appropriate)",
                       priority, True)
    if hazard == "flood":
        if cloud_cover is not None and cloud_cover >= 40:
            return AOIPlan(True, "sentinel-1",
                           "flood with cloud cover: prefer S1 SAR (cloud-penetrating)",
                           priority, True)
        return AOIPlan(True, "sentinel-2",
                       "flood, low cloud: S2 water extent (S1 fallback if cloudy)",
                       priority, True)
    if hazard == "earthquake":
        return AOIPlan(True, "sentinel-2",
                       "earthquake: S2 for large-scale change/damage context",
                       priority, True)
    if hazard in ("armed_conflict", "conflict"):
        supported, reason = capability_check("urban_damage_area", "sentinel-2")
        return AOIPlan(True, "sentinel-2",
                       "conflict: S2 for AGGREGATE urban-damage context only; "
                       "individual vehicle/tank detection is UNSUPPORTED at 10 m/px "
                       "-> CV Replay/benchmark. " + reason,
                       priority, supported)
    return AOIPlan(False, None, f"no EO recipe for hazard {hazard!r}", "none", True)
