"""
routers/teams.py — FastAPI router for response-team management endpoints.

Routes:
  GET  /teams              List all response teams with current status
  POST /teams/{id}/deploy  Deploy a team to an incident
  POST /teams/{id}/recall  Recall a team back to available status
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.incident import Incident, ResponseTeam

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teams", tags=["Teams"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class DeployRequest(BaseModel):
    incident_id: int
    status: Optional[str] = "Deployed"  # Deployed | OnScene


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
def list_teams(db: Session = Depends(get_db)):
    """Return all response teams with their current status and assignment."""
    teams = db.query(ResponseTeam).order_by(ResponseTeam.type, ResponseTeam.name).all()
    result = []
    for team in teams:
        team_dict = team.to_dict()
        # Attach brief incident info if assigned
        if team.current_incident:
            team_dict["incident_info"] = {
                "incident_number": team.current_incident.incident_number,
                "location": team.current_incident.location,
                "severity": team.current_incident.severity,
                "type": team.current_incident.type,
            }
        else:
            team_dict["incident_info"] = None
        result.append(team_dict)
    return result


@router.post("/{team_id}/deploy")
def deploy_team(
    team_id: int,
    payload: DeployRequest,
    db: Session = Depends(get_db),
):
    """
    Assign a response team to an incident.
    Team status is set to 'Deployed' by default (or 'OnScene' if specified).
    """
    team = db.query(ResponseTeam).filter(ResponseTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found.")

    incident = db.query(Incident).filter(Incident.id == payload.incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=404, detail=f"Incident {payload.incident_id} not found."
        )

    allowed_statuses = {"Deployed", "OnScene"}
    deploy_status = payload.status if payload.status in allowed_statuses else "Deployed"

    team.current_incident_id = incident.id
    team.status = deploy_status
    # Snap team coordinates to incident location
    if incident.lat and incident.lng:
        team.lat = incident.lat
        team.lng = incident.lng

    db.commit()
    db.refresh(team)

    logger.info(
        "Team '%s' deployed to incident %s with status '%s'.",
        team.name,
        incident.incident_number,
        team.status,
    )
    return {
        "message": f"Team '{team.name}' successfully deployed to {incident.incident_number}.",
        "team": team.to_dict(),
    }


@router.post("/{team_id}/recall")
def recall_team(team_id: int, db: Session = Depends(get_db)):
    """
    Recall a response team from its current incident.
    Sets team status to 'Available' and clears the incident assignment.
    """
    team = db.query(ResponseTeam).filter(ResponseTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found.")

    if team.status == "Available":
        return {
            "message": f"Team '{team.name}' is already available.",
            "team": team.to_dict(),
        }

    previous_incident = team.current_incident_id
    team.current_incident_id = None
    team.status = "Available"

    db.commit()
    db.refresh(team)

    logger.info(
        "Team '%s' recalled from incident ID %s.",
        team.name,
        previous_incident,
    )
    return {
        "message": f"Team '{team.name}' recalled and is now available.",
        "team": team.to_dict(),
    }
