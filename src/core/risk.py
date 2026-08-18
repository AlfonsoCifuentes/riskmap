"""Risk Engine v2 — risk is NOT confidence (spec §4.7 / §60 / §96, addendum B11).

The legacy score was a keyword sum presented as a probability. This engine keeps
the concepts the audit insists are different, and versions itself so historical
scores stay comparable:

    severity        how bad the incident itself is            (hazard intensity)
    exposure        how many people/assets are in harm's way
    vulnerability   how poorly the area can absorb it
    risk_score      f(severity, exposure, vulnerability)       -> 0..100
    confidence      how much we trust the evidence             -> 0..100
                    (independent sources, official corroboration, geo quality,
                     recency, model agreement)

`explain()` returns STRUCTURED factors ("why this risk") — never the LLM's
chain-of-thought (spec §60). Every assessment records `risk_engine_version`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

RISK_ENGINE_VERSION = "2.0.0"

# Risk bands (0..100).
_BANDS = [
    (80, "critical"),
    (60, "high"),
    (35, "medium"),
    (0, "low"),
]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def risk_level(score_0_100: float) -> str:
    for threshold, label in _BANDS:
        if score_0_100 >= threshold:
            return label
    return "low"


@dataclass
class RiskAssessment:
    risk_score: float           # 0..100
    risk_level: str
    confidence: float           # 0..100
    severity: float             # 0..1 (component)
    exposure: float             # 0..1
    vulnerability: float        # 0..1
    risk_engine_version: str = RISK_ENGINE_VERSION
    factors: list = field(default_factory=list)  # structured "why this risk"

    def as_dict(self) -> dict:
        return asdict(self)


def assess(
    *,
    severity: float,
    exposure: float = 0.5,
    vulnerability: float = 0.5,
    independent_source_count: int = 1,
    has_official_source: bool = False,
    geo_confidence: float = 0.5,
    recency_hours: float = 0.0,
    model_agreement: float = 0.5,
) -> RiskAssessment:
    """Compute a risk assessment with separated risk and confidence.

    Inputs are 0..1 components (severity/exposure/vulnerability) plus evidence
    signals that drive *confidence only*. Risk and confidence never mix.
    """
    sev = _clamp01(severity)
    exp = _clamp01(exposure)
    vul = _clamp01(vulnerability)

    # Risk: severity dominates; exposure & vulnerability modulate it.
    # Weighted so a severe-but-unexposed hazard is still notable, and exposure
    # can amplify a moderate hazard.
    risk_unit = 0.6 * sev + 0.25 * (sev * exp) + 0.15 * (sev * vul)
    # Also give exposure/vulnerability a small standalone contribution so a
    # highly exposed area registers even at moderate severity.
    risk_unit += 0.10 * exp + 0.05 * vul
    risk_unit = _clamp01(risk_unit)
    risk_score = round(risk_unit * 100, 1)

    # Confidence: purely about evidence quality.
    conf = 0.0
    factors: list[dict] = []

    if independent_source_count >= 5:
        conf += 0.30
        factors.append(_f("independent_sources", +30, f"{independent_source_count} independent sources"))
    elif independent_source_count >= 2:
        conf += 0.18
        factors.append(_f("independent_sources", +18, f"{independent_source_count} independent sources"))
    else:
        conf += 0.05
        factors.append(_f("independent_sources", +5, "single source (uncorroborated)"))

    if has_official_source:
        conf += 0.22
        factors.append(_f("official_corroboration", +22, "official source agrees"))

    conf += 0.18 * _clamp01(geo_confidence)
    factors.append(_f("geolocation_quality", round(18 * _clamp01(geo_confidence)),
                      f"geo confidence {geo_confidence:.2f}"))

    conf += 0.15 * _clamp01(model_agreement)

    # Recency decay: older evidence lowers confidence (half-life ~48h).
    if recency_hours > 0:
        decay = 0.5 ** (recency_hours / 48.0)
        conf *= (0.6 + 0.4 * decay)  # never zero it out entirely
        if recency_hours > 72:
            factors.append(_f("recency", -10, f"evidence {int(recency_hours)}h old"))

    confidence = round(_clamp01(conf) * 100, 1)

    # Structured "why this risk" for the risk side.
    risk_factors = [
        _f("severity", round(sev * 100), f"hazard severity {sev:.2f}"),
        _f("exposure", round(exp * 30), f"population/asset exposure {exp:.2f}"),
        _f("vulnerability", round(vul * 15), f"area vulnerability {vul:.2f}"),
    ]

    return RiskAssessment(
        risk_score=risk_score,
        risk_level=risk_level(risk_score),
        confidence=confidence,
        severity=round(sev, 3),
        exposure=round(exp, 3),
        vulnerability=round(vul, 3),
        factors=risk_factors + factors,
    )


def _f(name: str, contribution: int, detail: str) -> dict:
    return {"factor": name, "contribution": contribution, "detail": detail}
