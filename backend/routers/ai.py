"""
routers/ai.py — FastAPI router for AI-driven endpoints.

Routes:
  POST /ai/parse-report          Run NLP parser on a citizen text message
  POST /ai/citizen-report        Full pipeline: parse → create / link incident
  GET  /ai/predictions           All current water-level predictions
  GET  /ai/intelligence/{id}     Full AI intelligence card for an incident
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.incident import CitizenReport, Incident
from services.alert_engine import score_incident
from services.llm_summary import generate_intelligence_card
from services.nlp_parser import parse_citizen_report
from services.prediction import predict_water_level
from services.simulator import WATER_SENSORS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    message: str


class CitizenReportRequest(BaseModel):
    message: str
    reporter_name: Optional[str] = None
    contact: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper: latest water readings from DB (reused across routes)
# ---------------------------------------------------------------------------

def _water_predictions(db: Session) -> list[dict]:
    from models.incident import SensorReading

    predictions = []
    for sensor_meta in WATER_SENSORS:
        sid = sensor_meta["sensor_id"]
        readings_objs = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == sid)
            .order_by(SensorReading.timestamp.desc())
            .limit(20)
            .all()
        )
        values = [r.value for r in reversed(readings_objs)]
        pred = predict_water_level(values)
        pred["sensor_id"] = sid
        pred["zone"] = sensor_meta["zone"]
        pred["lat"] = sensor_meta["lat"]
        pred["lng"] = sensor_meta["lng"]
        predictions.append(pred)
    return predictions


def _next_incident_number(db: Session) -> str:
    latest = db.query(Incident).order_by(Incident.id.desc()).first()
    if latest and latest.incident_number:
        try:
            num = int(latest.incident_number.lstrip("#")) + 1
            return f"#{num}"
        except ValueError:
            pass
    return "#2000"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/parse-report")
def parse_report(payload: ParseRequest):
    """
    Run the NLP parser on a raw citizen message.
    Returns extracted: location, incident_type, severity, people_count, confidence.
    """
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message must not be empty.")

    result = parse_citizen_report(payload.message)
    return {
        "parsed": result,
        "message": payload.message,
    }


@router.post("/citizen-report", status_code=201)
def citizen_report(payload: CitizenReportRequest, db: Session = Depends(get_db)):
    """
    Full citizen-report pipeline:
      1. Run NLP parser to extract structured fields.
      2. Save a CitizenReport record.
      3. If confidence ≥ 0.5 and type is known, auto-create an Incident.
      4. Return the parsed data + created/linked incident (if any).
    """
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message must not be empty.")

    # Step 1: Parse
    parsed = parse_citizen_report(payload.message)

    # Step 2: Save citizen report
    cr = CitizenReport(
        message=payload.message,
        extracted_location=parsed["location"],
        extracted_type=parsed["incident_type"],
        extracted_severity=parsed["severity"],
        people_mentioned=parsed["people_count"],
        status="Pending",
    )
    db.add(cr)
    db.flush()  # get ID without committing

    incident_dict: Optional[dict] = None

    # Step 3: Auto-create incident if confidence is sufficient
    if parsed["confidence"] >= 0.5 and parsed["incident_type"] not in ("Unknown",):
        location = parsed["location"] or "Unknown Location"
        zone = f"Zone (from citizen report)"
        incident_type = parsed["incident_type"]
        severity = parsed["severity"].title() if parsed["severity"] else "Normal"

        # Map High/Medium/Low → Critical/Warning/Normal
        severity_map = {"High": "Critical", "Medium": "Warning", "Low": "Normal"}
        severity = severity_map.get(severity, severity)

        engine = score_incident(
            incident_type=incident_type,
            people_affected=parsed["people_count"],
            zone=location,
        )
        severity = engine["severity_label"]

        incident_number = _next_incident_number(db)
        card = generate_intelligence_card({
            "incident_number": incident_number,
            "location": location,
            "zone": location,
            "type": incident_type,
            "severity": severity,
            "people_affected": parsed["people_count"],
        })

        incident = Incident(
            incident_number=incident_number,
            location=location,
            zone=location,
            type=incident_type,
            severity=severity,
            people_affected=parsed["people_count"],
            ai_assessment=card["ai_assessment"],
            status="Active",
        )
        incident.recommended_actions = card["recommended_actions"]
        db.add(incident)
        db.flush()

        # Link citizen report to incident
        cr.incident_id = incident.id
        cr.status = "Linked"

        incident_dict = incident.to_dict()

    else:
        cr.status = "Processed"

    db.commit()

    return {
        "citizen_report_id": cr.id,
        "parsed": parsed,
        "incident_created": incident_dict is not None,
        "incident": incident_dict,
    }


@router.get("/predictions")
def ai_predictions(db: Session = Depends(get_db)):
    """
    Return 30-minute water-level predictions for all zone sensors,
    derived from the most recent sensor readings in the database.
    """
    return _water_predictions(db)


@router.get("/intelligence/{incident_id}")
def intelligence_card(incident_id: int, db: Session = Depends(get_db)):
    """
    Generate and return a full AI Intelligence Card for the specified incident.
    The card is freshly computed from current sensor data and templates.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    card = generate_intelligence_card({
        "incident_number": incident.incident_number,
        "location": incident.location,
        "zone": incident.zone,
        "type": incident.type,
        "severity": incident.severity,
        "water_level": incident.water_level,
        "rainfall": incident.rainfall,
        "road_blocked": incident.road_blocked or False,
        "people_affected": incident.people_affected,
        "nearby_hospital": incident.nearby_hospital,
        "hospital_distance": incident.hospital_distance,
    })
    return card
