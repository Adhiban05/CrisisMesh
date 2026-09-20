"""
routers/incidents.py — FastAPI router for incident management endpoints.

Routes:
  GET  /incidents          List all incidents (filter by severity)
  GET  /incidents/stats    Count incidents grouped by severity
  GET  /incidents/{id}     Single incident with full AI intelligence card
  POST /incidents          Manually create a new incident
  PUT  /incidents/{id}/status   Update incident status
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.incident import Incident
from services.alert_engine import score_incident
from services.llm_summary import generate_intelligence_card

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/incidents", tags=["Incidents"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class IncidentCreate(BaseModel):
    location: str
    zone: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    type: str = Field(..., pattern="^(Flood|Fire|Industrial|Infrastructure)$")
    severity: Optional[str] = None
    water_level: Optional[float] = None
    rainfall: Optional[float] = None
    road_blocked: bool = False
    people_affected: Optional[int] = None
    nearby_hospital: Optional[str] = None
    hospital_distance: Optional[float] = None
    status: str = "Active"


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(Active|Monitoring|Resolved|Closed)$")


# ---------------------------------------------------------------------------
# Helper: generate unique incident number
# ---------------------------------------------------------------------------

def _next_incident_number(db: Session) -> str:
    latest = db.query(Incident).order_by(Incident.id.desc()).first()
    if latest and latest.incident_number:
        try:
            num = int(latest.incident_number.lstrip("#")) + 1
            return f"#{num}"
        except ValueError:
            pass
    return "#1000"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
def list_incidents(
    severity: Optional[str] = Query(None, description="Filter by severity: Critical, Warning, Normal"),
    status: Optional[str] = Query(None, description="Filter by status: Active, Monitoring, Resolved, Closed"),
    db: Session = Depends(get_db),
):
    """Return all incidents, optionally filtered by severity and/or status."""
    query = db.query(Incident)
    if severity:
        query = query.filter(Incident.severity == severity)
    if status:
        query = query.filter(Incident.status == status)
    incidents = query.order_by(Incident.created_at.desc()).all()
    return [inc.to_dict() for inc in incidents]


@router.get("/stats")
def incident_stats(db: Session = Depends(get_db)):
    """Return incident counts grouped by severity and overall totals."""
    all_incidents = db.query(Incident).all()
    stats = {
        "total": len(all_incidents),
        "critical": sum(1 for i in all_incidents if i.severity == "Critical"),
        "warning": sum(1 for i in all_incidents if i.severity == "Warning"),
        "normal": sum(1 for i in all_incidents if i.severity == "Normal"),
        "active": sum(1 for i in all_incidents if i.status == "Active"),
        "resolved": sum(1 for i in all_incidents if i.status == "Resolved"),
        "people_affected_total": sum(
            (i.people_affected or 0) for i in all_incidents
        ),
    }
    return stats


@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Return a single incident enriched with a fresh AI intelligence card."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    data = incident.to_dict()
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
    data["intelligence_card"] = card
    return data


@router.post("", status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Manually create a new incident; AI assessment is generated automatically."""
    incident_number = _next_incident_number(db)

    # Run alert engine to compute severity if not provided
    engine = score_incident(
        incident_type=payload.type,
        water_level=payload.water_level,
        people_affected=payload.people_affected,
        road_blocked=payload.road_blocked,
        rainfall=payload.rainfall,
        zone=payload.zone,
        nearby_hospital=payload.nearby_hospital,
    )
    severity = payload.severity or engine["severity_label"]

    # Generate AI card
    card = generate_intelligence_card({
        "incident_number": incident_number,
        "location": payload.location,
        "zone": payload.zone,
        "type": payload.type,
        "severity": severity,
        "water_level": payload.water_level,
        "rainfall": payload.rainfall,
        "road_blocked": payload.road_blocked,
        "people_affected": payload.people_affected,
        "nearby_hospital": payload.nearby_hospital,
        "hospital_distance": payload.hospital_distance,
    })

    incident = Incident(
        incident_number=incident_number,
        location=payload.location,
        zone=payload.zone,
        lat=payload.lat,
        lng=payload.lng,
        type=payload.type,
        severity=severity,
        water_level=payload.water_level,
        rainfall=payload.rainfall,
        road_blocked=payload.road_blocked,
        people_affected=payload.people_affected,
        nearby_hospital=payload.nearby_hospital,
        hospital_distance=payload.hospital_distance,
        ai_assessment=card["ai_assessment"],
        status=payload.status,
    )
    incident.recommended_actions = card["recommended_actions"]

    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info("Created incident %s (%s)", incident.incident_number, incident.type)
    return incident.to_dict()


@router.put("/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the lifecycle status of an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    incident.status = payload.status
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    return {"id": incident.id, "status": incident.status, "updated_at": incident.updated_at.isoformat()}
