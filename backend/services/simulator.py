"""
services/simulator.py — IoT sensor data simulator for CrisisMesh.

Generates realistic, slowly-evolving sensor readings for:
  - 8 water-level sensors (Zones 1–8)
  - 4 rainfall sensors
  - 6 temperature sensors (fire detection)
  - 3 smoke / air-quality sensors

Runs as an async background task, inserting new SensorReadings every 3 s
and updating Incident records when thresholds are crossed.

Also seeds 5 initial incidents and 18 response teams on first startup.
"""

import asyncio
import logging
import math
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database import SessionLocal
from models.incident import Incident, ResponseTeam, SensorReading
from services.alert_engine import score_incident
from services.llm_summary import generate_intelligence_card

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sensor definitions
# ---------------------------------------------------------------------------

WATER_SENSORS = [
    {"sensor_id": "WL-Z1", "zone": "Zone 1", "lat": 13.0827, "lng": 80.2707, "base": 0.3,  "target": 0.35},
    {"sensor_id": "WL-Z2", "zone": "Zone 2", "lat": 13.0900, "lng": 80.2800, "base": 0.7,  "target": 0.85},
    {"sensor_id": "WL-Z3", "zone": "Zone 3", "lat": 13.0450, "lng": 80.2600, "base": 0.4,  "target": 0.45},
    {"sensor_id": "WL-Z4", "zone": "Zone 4", "lat": 13.1000, "lng": 80.2500, "base": 0.9,  "target": 1.10},
    {"sensor_id": "WL-Z5", "zone": "Zone 5", "lat": 13.0600, "lng": 80.2900, "base": 1.2,  "target": 1.40},
    {"sensor_id": "WL-Z6", "zone": "Zone 6", "lat": 13.0750, "lng": 80.2650, "base": 0.5,  "target": 0.60},
    {"sensor_id": "WL-Z7", "zone": "Zone 7", "lat": 13.0550, "lng": 80.2750, "base": 1.82, "target": 2.10},
    {"sensor_id": "WL-Z8", "zone": "Zone 8", "lat": 13.1100, "lng": 80.2850, "base": 0.6,  "target": 0.70},
]

RAINFALL_SENSORS = [
    {"sensor_id": "RF-N1", "zone": "North",  "lat": 13.1200, "lng": 80.2700, "base": 45.0, "target": 55.0},
    {"sensor_id": "RF-N2", "zone": "South",  "lat": 13.0200, "lng": 80.2700, "base": 86.0, "target": 90.0},
    {"sensor_id": "RF-N3", "zone": "East",   "lat": 13.0827, "lng": 80.3200, "base": 30.0, "target": 35.0},
    {"sensor_id": "RF-N4", "zone": "West",   "lat": 13.0827, "lng": 80.2200, "base": 20.0, "target": 18.0},
]

TEMP_SENSORS = [
    {"sensor_id": "TMP-1", "zone": "Zone 3", "lat": 13.0450, "lng": 80.2600, "base": 85.0, "target": 90.0},
    {"sensor_id": "TMP-2", "zone": "Zone 3", "lat": 13.0460, "lng": 80.2610, "base": 40.0, "target": 38.0},
    {"sensor_id": "TMP-3", "zone": "Zone 6", "lat": 13.0750, "lng": 80.2650, "base": 32.0, "target": 33.0},
    {"sensor_id": "TMP-4", "zone": "Zone 9", "lat": 13.1300, "lng": 80.3000, "base": 55.0, "target": 60.0},
    {"sensor_id": "TMP-5", "zone": "Zone 1", "lat": 13.0827, "lng": 80.2707, "base": 31.0, "target": 31.5},
    {"sensor_id": "TMP-6", "zone": "Zone 2", "lat": 13.0900, "lng": 80.2800, "base": 33.0, "target": 34.0},
]

SMOKE_SENSORS = [
    {"sensor_id": "AQ-1", "zone": "Zone 3", "lat": 13.0450, "lng": 80.2600, "base": 320.0, "target": 450.0},
    {"sensor_id": "AQ-2", "zone": "Zone 9", "lat": 13.1300, "lng": 80.3000, "base": 280.0, "target": 350.0},
    {"sensor_id": "AQ-3", "zone": "Zone 1", "lat": 13.0827, "lng": 80.2707, "base": 80.0,  "target": 75.0},
]

# In-memory current values – start at base values
_current_values: dict[str, float] = {}


def _init_current_values() -> None:
    for s in WATER_SENSORS + RAINFALL_SENSORS + TEMP_SENSORS + SMOKE_SENSORS:
        _current_values[s["sensor_id"]] = s["base"]


def _step_value(sensor_id: str, target: float, noise_scale: float = 0.03) -> float:
    """
    Nudge current value slightly toward target with added Gaussian noise.
    This simulates a realistic slowly-drifting sensor reading.
    """
    current = _current_values.get(sensor_id, target)
    # Move 5% of the gap toward target each tick
    step = (target - current) * 0.05
    noise = random.gauss(0, noise_scale)
    new_val = current + step + noise
    # Clamp to avoid physically impossible values
    new_val = max(0.0, new_val)
    _current_values[sensor_id] = new_val
    return round(new_val, 3)


# ---------------------------------------------------------------------------
# Pre-seeded incident data
# ---------------------------------------------------------------------------

SEED_INCIDENTS = [
    {
        "incident_number": "#1042",
        "location": "Anna Nagar, Zone 7",
        "zone": "Zone 7",
        "lat": 13.0550,
        "lng": 80.2750,
        "type": "Flood",
        "severity": "Critical",
        "water_level": 1.82,
        "rainfall": 86.0,
        "road_blocked": True,
        "people_affected": 37,
        "nearby_hospital": "City General Hospital",
        "hospital_distance": 1.8,
        "status": "Active",
    },
    {
        "incident_number": "#1038",
        "location": "Industrial Estate, Zone 3",
        "zone": "Zone 3",
        "lat": 13.0450,
        "lng": 80.2600,
        "type": "Fire",
        "severity": "Warning",
        "water_level": None,
        "rainfall": None,
        "road_blocked": False,
        "people_affected": 12,
        "nearby_hospital": "St. Mary's Hospital",
        "hospital_distance": 3.2,
        "status": "Active",
    },
    {
        "incident_number": "#1035",
        "location": "Tambaram, Zone 5",
        "zone": "Zone 5",
        "lat": 13.0600,
        "lng": 80.2900,
        "type": "Flood",
        "severity": "Warning",
        "water_level": 1.2,
        "rainfall": 52.0,
        "road_blocked": False,
        "people_affected": 15,
        "nearby_hospital": "Rainbow Medical Centre",
        "hospital_distance": 2.5,
        "status": "Active",
    },
    {
        "incident_number": "#1031",
        "location": "Adyar, Zone 1",
        "zone": "Zone 1",
        "lat": 13.0827,
        "lng": 80.2707,
        "type": "Infrastructure",
        "severity": "Normal",
        "water_level": 0.3,
        "rainfall": 10.0,
        "road_blocked": False,
        "people_affected": 0,
        "nearby_hospital": "Apollo Hospital",
        "hospital_distance": 4.0,
        "status": "Resolved",
    },
    {
        "incident_number": "#1044",
        "location": "Manali Industrial Zone, Zone 9",
        "zone": "Zone 9",
        "lat": 13.1300,
        "lng": 80.3000,
        "type": "Industrial",
        "severity": "Warning",
        "water_level": None,
        "rainfall": None,
        "road_blocked": True,
        "people_affected": 5,
        "nearby_hospital": "MIOT International",
        "hospital_distance": 6.1,
        "status": "Active",
    },
]

# ---------------------------------------------------------------------------
# Pre-seeded team data
# ---------------------------------------------------------------------------

SEED_TEAMS = [
    # Rescue teams (6)
    {"name": "Rescue Alpha",   "type": "Rescue",    "status": "Deployed",   "lat": 13.0550, "lng": 80.2750},
    {"name": "Rescue Bravo",   "type": "Rescue",    "status": "OnScene",    "lat": 13.0560, "lng": 80.2760},
    {"name": "Rescue Charlie", "type": "Rescue",    "status": "Available",  "lat": 13.0700, "lng": 80.2600},
    {"name": "Rescue Delta",   "type": "Rescue",    "status": "Deployed",   "lat": 13.0600, "lng": 80.2900},
    {"name": "Rescue Echo",    "type": "Rescue",    "status": "Available",  "lat": 13.1000, "lng": 80.2800},
    {"name": "Rescue Foxtrot", "type": "Rescue",    "status": "Available",  "lat": 13.0827, "lng": 80.2707},
    # Medical teams (6)
    {"name": "Medical Alpha",  "type": "Medical",   "status": "OnScene",    "lat": 13.0450, "lng": 80.2600},
    {"name": "Medical Bravo",  "type": "Medical",   "status": "Available",  "lat": 13.0900, "lng": 80.2800},
    {"name": "Medical Charlie","type": "Medical",   "status": "Deployed",   "lat": 13.0550, "lng": 80.2750},
    {"name": "Medical Delta",  "type": "Medical",   "status": "Available",  "lat": 13.1100, "lng": 80.2850},
    {"name": "Medical Echo",   "type": "Medical",   "status": "Available",  "lat": 13.0600, "lng": 80.2650},
    {"name": "Medical Foxtrot","type": "Medical",   "status": "Deployed",   "lat": 13.0750, "lng": 80.2700},
    # Authority teams (6)
    {"name": "Authority Alpha","type": "Authority", "status": "Deployed",   "lat": 13.1300, "lng": 80.3000},
    {"name": "Authority Bravo","type": "Authority", "status": "Available",  "lat": 13.0827, "lng": 80.2800},
    {"name": "Authority Charlie","type":"Authority","status": "Available",  "lat": 13.0827, "lng": 80.2600},
    {"name": "Authority Delta","type": "Authority", "status": "OnScene",    "lat": 13.0550, "lng": 80.2750},
    {"name": "Authority Echo", "type": "Authority", "status": "Available",  "lat": 13.0600, "lng": 80.2900},
    {"name": "Authority Foxtrot","type":"Authority","status": "Available",  "lat": 13.1000, "lng": 80.2500},
]


# ---------------------------------------------------------------------------
# Database seeding helpers
# ---------------------------------------------------------------------------

def seed_incidents(db: Session) -> None:
    """Insert seed incidents if the table is empty."""
    if db.query(Incident).count() > 0:
        return
    for data in SEED_INCIDENTS:
        card = generate_intelligence_card(data)
        incident = Incident(
            incident_number=data["incident_number"],
            location=data["location"],
            zone=data["zone"],
            lat=data["lat"],
            lng=data["lng"],
            type=data["type"],
            severity=data["severity"],
            water_level=data["water_level"],
            rainfall=data["rainfall"],
            road_blocked=data["road_blocked"],
            people_affected=data["people_affected"],
            nearby_hospital=data["nearby_hospital"],
            hospital_distance=data["hospital_distance"],
            ai_assessment=card["ai_assessment"],
            status=data["status"],
        )
        incident.recommended_actions = card["recommended_actions"]
        db.add(incident)
    db.commit()
    logger.info("Seeded %d incidents.", len(SEED_INCIDENTS))


def seed_teams(db: Session) -> None:
    """Insert seed response teams if the table is empty."""
    if db.query(ResponseTeam).count() > 0:
        return
    for data in SEED_TEAMS:
        team = ResponseTeam(
            name=data["name"],
            type=data["type"],
            status=data["status"],
            lat=data["lat"],
            lng=data["lng"],
        )
        db.add(team)
    db.commit()
    logger.info("Seeded %d response teams.", len(SEED_TEAMS))


def link_deployed_teams(db: Session) -> None:
    """
    Assign deployed/on-scene teams to incidents so the FK relationship is
    populated correctly after initial seeding.
    """
    # Get the Zone 7 Critical flood incident
    z7 = db.query(Incident).filter(Incident.zone == "Zone 7").first()
    z3 = db.query(Incident).filter(Incident.zone == "Zone 3").first()
    z5 = db.query(Incident).filter(Incident.zone == "Zone 5").first()
    z9 = db.query(Incident).filter(Incident.zone == "Zone 9").first()

    mappings = {
        "Rescue Alpha": z7,
        "Rescue Bravo": z7,
        "Rescue Delta": z5,
        "Medical Alpha": z3,
        "Medical Charlie": z7,
        "Medical Foxtrot": z5,
        "Authority Alpha": z9,
        "Authority Delta": z7,
    }

    for team_name, incident in mappings.items():
        if incident is None:
            continue
        team = db.query(ResponseTeam).filter(ResponseTeam.name == team_name).first()
        if team and team.current_incident_id is None:
            team.current_incident_id = incident.id

    db.commit()


# ---------------------------------------------------------------------------
# Simulator loop
# ---------------------------------------------------------------------------

async def run_simulator() -> None:
    """
    Async background task: generates sensor readings every 3 seconds.
    Inserts SensorReading rows and updates Incident water_level / severity
    when thresholds are crossed.
    """
    _init_current_values()
    logger.info("IoT Simulator started.")

    while True:
        try:
            await _simulate_tick()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Simulator error: %s", exc)
        await asyncio.sleep(3)


async def _simulate_tick() -> None:
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # --- Water level sensors ---
        for s in WATER_SENSORS:
            val = _step_value(s["sensor_id"], s["target"], noise_scale=0.04)
            reading = SensorReading(
                sensor_id=s["sensor_id"],
                sensor_type="WaterLevel",
                value=val,
                unit="m",
                lat=s["lat"],
                lng=s["lng"],
                timestamp=now,
            )
            db.add(reading)

            # Update matching incident water level
            incident = db.query(Incident).filter(
                Incident.zone == s["zone"],
                Incident.type == "Flood",
                Incident.status == "Active",
            ).first()
            if incident:
                incident.water_level = val
                # Recompute severity
                result = score_incident(
                    incident_type=incident.type,
                    water_level=val,
                    people_affected=incident.people_affected,
                    road_blocked=incident.road_blocked or False,
                    rainfall=incident.rainfall,
                    zone=incident.zone,
                    nearby_hospital=incident.nearby_hospital,
                )
                new_severity = result["severity_label"]
                if incident.severity != new_severity:
                    incident.severity = new_severity
                    logger.debug(
                        "Incident %s severity updated to %s",
                        incident.incident_number,
                        new_severity,
                    )

        # --- Rainfall sensors ---
        for s in RAINFALL_SENSORS:
            val = _step_value(s["sensor_id"], s["target"], noise_scale=2.0)
            reading = SensorReading(
                sensor_id=s["sensor_id"],
                sensor_type="Rainfall",
                value=val,
                unit="mm/hr",
                lat=s["lat"],
                lng=s["lng"],
                timestamp=now,
            )
            db.add(reading)

        # --- Temperature sensors ---
        for s in TEMP_SENSORS:
            val = _step_value(s["sensor_id"], s["target"], noise_scale=0.5)
            reading = SensorReading(
                sensor_id=s["sensor_id"],
                sensor_type="Temperature",
                value=val,
                unit="°C",
                lat=s["lat"],
                lng=s["lng"],
                timestamp=now,
            )
            db.add(reading)

        # --- Smoke / Air quality sensors ---
        for s in SMOKE_SENSORS:
            val = _step_value(s["sensor_id"], s["target"], noise_scale=5.0)
            reading = SensorReading(
                sensor_id=s["sensor_id"],
                sensor_type="AirQuality",
                value=val,
                unit="AQI",
                lat=s["lat"],
                lng=s["lng"],
                timestamp=now,
            )
            db.add(reading)

        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
