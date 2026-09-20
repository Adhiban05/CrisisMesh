"""
services/alert_engine.py — Severity scoring and recommended action generation.

Produces:
  - severity_score  : int 0–100
  - severity_label  : Critical / Warning / Normal
  - actions         : list[str]  — prioritised response actions

No external dependencies.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

# Water level (metres) → contribution score
def _water_level_score(water_level: Optional[float]) -> int:
    if water_level is None:
        return 0
    if water_level >= 2.0:
        return 40
    if water_level >= 1.5:
        return 30
    if water_level >= 1.0:
        return 20
    if water_level >= 0.5:
        return 10
    return 5


# People affected → contribution score
def _people_score(people_affected: Optional[int]) -> int:
    if people_affected is None:
        return 0
    if people_affected >= 100:
        return 25
    if people_affected >= 50:
        return 18
    if people_affected >= 20:
        return 12
    if people_affected >= 5:
        return 6
    return 2


# Rainfall (mm/hr) → contribution score
def _rainfall_score(rainfall: Optional[float]) -> int:
    if rainfall is None:
        return 0
    if rainfall >= 80:
        return 20
    if rainfall >= 50:
        return 14
    if rainfall >= 30:
        return 8
    if rainfall >= 10:
        return 4
    return 0


# Road blocked → fixed contribution
def _road_blocked_score(road_blocked: bool) -> int:
    return 15 if road_blocked else 0


def _label_from_score(score: int) -> str:
    if score >= 70:
        return "Critical"
    if score >= 40:
        return "Warning"
    return "Normal"


# ---------------------------------------------------------------------------
# Action templates
# ---------------------------------------------------------------------------

def _flood_actions(
    severity_label: str,
    zone: str,
    road_blocked: bool,
    hospital: Optional[str],
    people_affected: Optional[int],
) -> list[str]:
    actions: list[str] = []

    if severity_label == "Critical":
        actions.append(f"Dispatch Rescue Team immediately to {zone}")
        if people_affected and people_affected > 0:
            actions.append(f"Evacuate {people_affected} affected residents from {zone}")
        if road_blocked:
            actions.append(f"Close flooded roads in {zone} – deploy traffic wardens")
        actions.append(f"Alert all residents in {zone} via emergency broadcast")
        if hospital:
            actions.append(f"Prepare {hospital} for incoming flood casualties")
        actions.append("Activate Emergency Operations Centre (EOC)")
        actions.append("Request National Disaster Response Force (NDRF) support")
    elif severity_label == "Warning":
        actions.append(f"Pre-position Rescue Team at {zone} perimeter")
        actions.append(f"Issue flood advisory for {zone} residents")
        if road_blocked:
            actions.append(f"Monitor road conditions in {zone} – prepare diversions")
        if hospital:
            actions.append(f"Notify {hospital} to stand by for possible casualties")
        actions.append("Increase sensor monitoring frequency in affected area")
    else:
        actions.append(f"Continue routine monitoring of water levels in {zone}")
        actions.append("No immediate action required — situation under observation")

    return actions


def _fire_actions(severity_label: str, zone: str, hospital: Optional[str]) -> list[str]:
    actions: list[str] = []
    if severity_label in ("Critical", "Warning"):
        actions.append(f"Deploy Fire Brigade units to {zone} immediately")
        actions.append(f"Evacuate building / area in {zone}")
        actions.append("Dispatch Medical Response Team for burn casualties")
        if hospital:
            actions.append(f"Alert {hospital} emergency department — fire casualties expected")
        actions.append("Establish 200 m safety perimeter")
        actions.append("Notify utility providers to cut power / gas supply")
    else:
        actions.append(f"Fire Safety Team to investigate smoke report in {zone}")
        actions.append("Verify source before escalation")
    return actions


def _industrial_actions(severity_label: str, zone: str, hospital: Optional[str]) -> list[str]:
    actions: list[str] = []
    actions.append(f"Isolate {zone} — restrict public access immediately")
    actions.append("Dispatch HazMat (Hazardous Materials) Response Team")
    actions.append("Notify Pollution Control Board and relevant authorities")
    if hospital:
        actions.append(f"Alert {hospital} for potential chemical exposure casualties")
    if severity_label == "Critical":
        actions.append("Evacuate 500 m radius from incident site")
        actions.append("Request Environmental Agency rapid assessment team")
    actions.append("Document and photograph site for regulatory reporting")
    return actions


def _infrastructure_actions(severity_label: str, zone: str) -> list[str]:
    actions: list[str] = []
    actions.append(f"Dispatch Civil Engineering Assessment Team to {zone}")
    actions.append("Cordon off damaged infrastructure — prevent public access")
    if severity_label == "Critical":
        actions.append("Emergency structural assessment required within 2 hours")
        actions.append("Coordinate with utility companies for emergency shut-offs")
    actions.append("Issue public advisory regarding route/utility disruption")
    return actions


def _default_actions(severity_label: str, zone: str) -> list[str]:
    if severity_label == "Critical":
        return [
            f"Dispatch emergency response team to {zone}",
            "Activate Emergency Operations Centre",
            "Issue public alert for affected area",
        ]
    if severity_label == "Warning":
        return [
            f"Monitor situation in {zone} closely",
            "Pre-position response resources nearby",
        ]
    return [f"Continue observation in {zone} — no immediate action required"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_incident(
    incident_type: str,
    water_level: Optional[float] = None,
    people_affected: Optional[int] = None,
    road_blocked: bool = False,
    rainfall: Optional[float] = None,
    zone: str = "the affected area",
    nearby_hospital: Optional[str] = None,
) -> dict:
    """
    Score an incident and generate prioritised recommended actions.

    Parameters
    ----------
    incident_type   : str    Flood / Fire / Industrial / Infrastructure / other
    water_level     : float  Current water level in metres (Flood incidents)
    people_affected : int    Number of people impacted
    road_blocked    : bool   Whether access roads are blocked
    rainfall        : float  Rainfall in mm/hr
    zone            : str    Zone / area name for action text
    nearby_hospital : str    Name of the nearest hospital

    Returns
    -------
    dict with keys:
        severity_score  : int    0–100
        severity_label  : str    Critical / Warning / Normal
        actions         : list[str]
    """
    score = 0
    score += _water_level_score(water_level)
    score += _people_score(people_affected)
    score += _rainfall_score(rainfall)
    score += _road_blocked_score(road_blocked)

    # Type-specific bonus
    TYPE_BONUS = {
        "Flood": 0,
        "Fire": 10,
        "Industrial": 15,
        "Infrastructure": 5,
    }
    score += TYPE_BONUS.get(incident_type, 0)
    score = min(score, 100)  # cap at 100

    label = _label_from_score(score)

    # Generate actions based on type
    inc_type = incident_type.strip().title()
    if inc_type == "Flood":
        actions = _flood_actions(label, zone, road_blocked, nearby_hospital, people_affected)
    elif inc_type == "Fire":
        actions = _fire_actions(label, zone, nearby_hospital)
    elif inc_type == "Industrial":
        actions = _industrial_actions(label, zone, nearby_hospital)
    elif inc_type == "Infrastructure":
        actions = _infrastructure_actions(label, zone)
    else:
        actions = _default_actions(label, zone)

    return {
        "severity_score": score,
        "severity_label": label,
        "actions": actions,
    }
