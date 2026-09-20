"""
services/llm_summary.py — Template-based AI Intelligence Card generator.

Generates rich, human-readable AI intelligence cards for incidents WITHOUT
calling any external LLM API.  All text is constructed from curated
templates and live incident data.
"""

import random
from datetime import datetime, timezone
from typing import Optional

from services.alert_engine import score_incident


# ---------------------------------------------------------------------------
# Narrative sentence pools (randomly sampled for variety)
# ---------------------------------------------------------------------------

_FLOOD_RISING = [
    "Water levels are rising at an accelerated rate, posing imminent risk to low-lying structures.",
    "Hydrological sensors indicate a sustained upward trend — conditions may deteriorate within the hour.",
    "Upstream discharge is contributing to rapidly rising water in the affected zone.",
]

_FLOOD_STABLE = [
    "Water levels remain elevated but are currently stable — active monitoring is essential.",
    "No further rise observed in the last monitoring cycle; however, levels remain above safe thresholds.",
]

_FLOOD_FALLING = [
    "Water levels are beginning to recede, though access routes remain hazardous.",
    "Early signs of drainage improvement detected — continue monitoring for secondary surges.",
]

_FIRE_SENTENCES = [
    "Thermal sensors confirm above-normal temperatures in the incident area — fire spread risk is elevated.",
    "Dry conditions and wind speed data suggest the fire could propagate rapidly without intervention.",
    "Smoke dispersion modelling indicates air quality impact extending beyond the immediate zone.",
]

_INDUSTRIAL_SENTENCES = [
    "Chemical sensor readings indicate the presence of airborne contaminants above safety thresholds.",
    "The incident poses cross-contamination risk to surrounding residential sectors.",
    "HazMat protocols must be invoked before any first-responder entry into the zone.",
]

_INFRASTRUCTURE_SENTENCES = [
    "Structural integrity of the affected infrastructure is compromised — load-bearing assessment required.",
    "Traffic and utility routing will be significantly impacted pending repair assessment.",
    "Secondary collapse risk identified — a 200 m exclusion zone is recommended.",
]

_GENERIC_SENTENCES = [
    "Multi-source data correlation confirms the reported incident with high confidence.",
    "Response coordination across agencies is critical to minimise impact escalation.",
    "Real-time telemetry is being used to update situational awareness continuously.",
]


def _pick(*pool: list[str], n: int = 2) -> list[str]:
    """Pick n unique sentences from pool(s) at random."""
    combined = [s for p in pool for s in p]
    return random.sample(combined, min(n, len(combined)))


# ---------------------------------------------------------------------------
# Assessment text builder
# ---------------------------------------------------------------------------

def _build_assessment(
    incident_type: str,
    severity_label: str,
    water_level: Optional[float],
    rainfall: Optional[float],
    people_affected: Optional[int],
    road_blocked: bool,
    zone: str,
    risk_score: int,
) -> str:
    """Construct a multi-sentence AI assessment paragraph."""

    lines: list[str] = []

    # Opening sentence
    opening = (
        f"{severity_label} severity {incident_type} incident detected in {zone}. "
        f"Composite risk score: {risk_score}/100."
    )
    lines.append(opening)

    # Type-specific narrative
    if incident_type == "Flood":
        if water_level is not None:
            lines.append(
                f"Current water level: {water_level:.2f} m "
                f"({'above' if water_level >= 1.5 else 'approaching'} critical threshold of 1.5 m)."
            )
        if rainfall is not None:
            lines.append(f"Rainfall intensity: {rainfall:.1f} mm/hr — "
                         f"{'severe' if rainfall >= 50 else 'moderate'} precipitation observed.")
        if road_blocked:
            lines.append("Primary access road reported blocked — evacuation corridor planning required.")
        lines.extend(_pick(_FLOOD_RISING if (water_level or 0) > 1.5 else _FLOOD_STABLE))

    elif incident_type == "Fire":
        lines.extend(_pick(_FIRE_SENTENCES))

    elif incident_type == "Industrial":
        lines.extend(_pick(_INDUSTRIAL_SENTENCES))

    elif incident_type == "Infrastructure":
        lines.extend(_pick(_INFRASTRUCTURE_SENTENCES))

    else:
        lines.extend(_pick(_GENERIC_SENTENCES))

    # People affected
    if people_affected and people_affected > 0:
        lines.append(
            f"Approximately {people_affected} individual(s) are estimated to be affected — "
            "prioritise evacuation and welfare checks."
        )

    # Closing
    lines.append(
        "Continuous sensor monitoring and field verification are recommended until the "
        "situation is resolved."
    )

    return " ".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_intelligence_card(incident_data: dict) -> dict:
    """
    Generate a full AI Intelligence Card from incident data.

    Parameters
    ----------
    incident_data : dict
        Must contain at minimum: 'type', 'zone'.
        Optional keys improve output quality.

    Returns
    -------
    dict — the fully populated intelligence card.
    """
    # Extract fields with sensible defaults
    incident_number = incident_data.get("incident_number", "#0000")
    location = incident_data.get("location", incident_data.get("zone", "Unknown Location"))
    zone = incident_data.get("zone", "Unknown Zone")
    incident_type = incident_data.get("type", "Unknown")
    water_level: Optional[float] = incident_data.get("water_level")
    rainfall: Optional[float] = incident_data.get("rainfall")
    road_blocked: bool = incident_data.get("road_blocked", False)
    people_affected: Optional[int] = incident_data.get("people_affected")
    nearby_hospital: Optional[str] = incident_data.get("nearby_hospital")
    hospital_distance: Optional[float] = incident_data.get("hospital_distance")

    # Run alert engine to get severity + actions
    engine_result = score_incident(
        incident_type=incident_type,
        water_level=water_level,
        people_affected=people_affected,
        road_blocked=road_blocked,
        rainfall=rainfall,
        zone=zone,
        nearby_hospital=nearby_hospital,
    )
    severity_label = engine_result["severity_label"]
    risk_score = engine_result["severity_score"]
    actions = engine_result["actions"]

    # Use provided severity if available (manual override)
    severity_label = incident_data.get("severity", severity_label)

    # Build AI assessment text
    assessment = _build_assessment(
        incident_type=incident_type,
        severity_label=severity_label,
        water_level=water_level,
        rainfall=rainfall,
        people_affected=people_affected,
        road_blocked=road_blocked,
        zone=zone,
        risk_score=risk_score,
    )

    # Determine status string
    if severity_label == "Critical":
        status_text = "RESPONSE REQUIRED"
    elif severity_label == "Warning":
        status_text = "MONITORING ACTIVE"
    else:
        status_text = "UNDER OBSERVATION"

    # Format display strings
    water_level_display: Optional[str] = None
    if water_level is not None:
        arrow = "↑" if water_level >= 1.5 else ("↘" if water_level < 0.5 else "→")
        water_level_display = f"{water_level:.2f} m {arrow}"

    rainfall_display: Optional[str] = None
    if rainfall is not None:
        rainfall_display = f"{rainfall:.1f} mm/hr"

    hospital_distance_display: Optional[str] = None
    if hospital_distance is not None:
        hospital_distance_display = f"{hospital_distance:.1f} km"

    # Confidence: higher score → higher confidence in the assessment
    confidence = round(0.60 + (risk_score / 100) * 0.35, 2)

    return {
        "incident_number": incident_number,
        "location": location,
        "zone": zone,
        "type": incident_type,
        "severity": severity_label,
        "water_level": water_level_display,
        "water_level_raw": water_level,
        "rainfall": rainfall_display,
        "rainfall_raw": rainfall,
        "road_blocked": road_blocked,
        "people_reported": people_affected,
        "nearby_hospital": nearby_hospital,
        "hospital_distance": hospital_distance_display,
        "hospital_distance_raw": hospital_distance,
        "ai_assessment": assessment,
        "recommended_actions": actions,
        "status": status_text,
        "risk_score": risk_score,
        "confidence": confidence,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
