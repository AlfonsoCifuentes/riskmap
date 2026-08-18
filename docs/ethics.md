# Ethical use

RiskMap is a situational-awareness and portfolio project. It is **not an
emergency authority** and does not issue official instructions.

## Hard boundaries (never implemented)

- No face recognition or identity matching.
- No person tracking or re-identification.
- No licence-plate recognition.
- No biometric or sensitive-trait inference (ethnicity, health, political
  affiliation, "suspicious person").
- No inference of "mass migration" from crowd density.

These apply everywhere, especially the experimental **Visual Intelligence**
camera module, which is limited to **environmental** phenomena (smoke, fire,
flooding, obstruction, low visibility) and boundary-locked by tests
(`tests/unit/test_cameras.py`).

## Principles

- **Provenance:** every datum links to a source; every inference records model +
  version.
- **Uncertainty visible:** geolocation precision and confidence are shown; risk
  is separated from confidence.
- **Honest labels:** LIVE / REPLAY / BENCHMARK / EXPERIMENTAL / DEGRADED are used
  literally; synthetic/replay data is never presented as live.
- **Safety:** official guidance is kept separate from RiskMap-generated context;
  evacuation/shelter/medical instructions are never invented (`safety_brief.py`).
- **Copyright:** extracts + links + attribution, not full-article republication.
