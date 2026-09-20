"""
models/incident.py — SQLAlchemy ORM models for CrisisMesh.

Models:
  - Incident       : A disaster event tracked by the platform.
  - SensorReading  : A timestamped reading from an IoT sensor.
  - ResponseTeam   : An emergency response unit.
  - CitizenReport  : A text report submitted by a citizen.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------------
# Helper – UTC-aware "now"
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------

class Incident(Base):
    """Represents a disaster incident being managed by CrisisMesh."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    # Human-readable identifier, e.g. "#1042"
    incident_number = Column(String(20), unique=True, nullable=False)

    # Location information
    location = Column(String(255), nullable=False)
    zone = Column(String(50), nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # Classification
    type = Column(String(50), nullable=False)          # Flood / Fire / Industrial / Infrastructure
    severity = Column(String(20), nullable=False)      # Critical / Warning / Normal

    # Environmental metrics
    water_level = Column(Float, nullable=True)         # metres
    rainfall = Column(Float, nullable=True)            # mm/hr
    road_blocked = Column(Boolean, default=False)
    people_affected = Column(Integer, nullable=True)

    # Nearest medical facility
    nearby_hospital = Column(String(255), nullable=True)
    hospital_distance = Column(Float, nullable=True)   # km

    # AI-generated content (stored as plain text / JSON strings)
    ai_assessment = Column(Text, nullable=True)
    _recommended_actions = Column("recommended_actions", Text, nullable=True)

    # Lifecycle
    status = Column(String(50), default="Active")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="incident", cascade="all, delete-orphan")
    citizen_reports = relationship("CitizenReport", back_populates="incident", cascade="all, delete-orphan")
    response_teams = relationship("ResponseTeam", back_populates="current_incident")

    # ------------------------------------------------------------------
    # recommended_actions – transparently serialise / deserialise JSON
    # ------------------------------------------------------------------

    @property
    def recommended_actions(self):
        if self._recommended_actions is None:
            return []
        try:
            return json.loads(self._recommended_actions)
        except (json.JSONDecodeError, TypeError):
            return []

    @recommended_actions.setter
    def recommended_actions(self, value):
        if value is None:
            self._recommended_actions = None
        else:
            self._recommended_actions = json.dumps(value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_number": self.incident_number,
            "location": self.location,
            "zone": self.zone,
            "lat": self.lat,
            "lng": self.lng,
            "type": self.type,
            "severity": self.severity,
            "water_level": self.water_level,
            "rainfall": self.rainfall,
            "road_blocked": self.road_blocked,
            "people_affected": self.people_affected,
            "nearby_hospital": self.nearby_hospital,
            "hospital_distance": self.hospital_distance,
            "ai_assessment": self.ai_assessment,
            "recommended_actions": self.recommended_actions,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# SensorReading
# ---------------------------------------------------------------------------

class SensorReading(Base):
    """A single timestamped reading from an IoT sensor node."""

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    sensor_type = Column(String(50), nullable=False)   # WaterLevel / Rainfall / Temperature / AirQuality
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)

    # Optional FK linking reading to an active incident
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    incident = relationship("Incident", back_populates="sensor_readings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "lat": self.lat,
            "lng": self.lng,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "incident_id": self.incident_id,
        }


# ---------------------------------------------------------------------------
# ResponseTeam
# ---------------------------------------------------------------------------

class ResponseTeam(Base):
    """An emergency response unit (Rescue / Medical / Authority)."""

    __tablename__ = "response_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)    # Rescue / Medical / Authority
    status = Column(String(30), default="Available")  # Available / Deployed / OnScene

    # Currently assigned incident (nullable when Available)
    current_incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    current_incident = relationship("Incident", back_populates="response_teams")

    # Last-known GPS coordinates
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "current_incident_id": self.current_incident_id,
            "lat": self.lat,
            "lng": self.lng,
        }


# ---------------------------------------------------------------------------
# CitizenReport
# ---------------------------------------------------------------------------

class CitizenReport(Base):
    """
    A free-text report submitted by a member of the public via the app.
    The NLP parser extracts structured fields from the raw message.
    """

    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Raw input
    message = Column(Text, nullable=False)

    # NLP-extracted fields
    extracted_location = Column(String(255), nullable=True)
    extracted_type = Column(String(50), nullable=True)
    extracted_severity = Column(String(20), nullable=True)
    people_mentioned = Column(Integer, nullable=True)

    # Processing state
    status = Column(String(30), default="Pending")   # Pending / Processed / Linked

    # FK to incident created / updated from this report
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    incident = relationship("Incident", back_populates="citizen_reports")

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message": self.message,
            "extracted_location": self.extracted_location,
            "extracted_type": self.extracted_type,
            "extracted_severity": self.extracted_severity,
            "people_mentioned": self.people_mentioned,
            "status": self.status,
            "incident_id": self.incident_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
