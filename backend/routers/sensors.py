"""
routers/sensors.py — FastAPI router for IoT sensor data endpoints.

Routes:
  GET /sensors                       Latest reading per sensor
  GET /sensors/{sensor_id}/history   Last 20 readings for a sensor
  GET /sensors/predictions           Water-level predictions for all zones
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.incident import SensorReading
from services.prediction import predict_water_level
from services.simulator import WATER_SENSORS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sensors", tags=["Sensors"])


# ---------------------------------------------------------------------------
# Helper: fetch latest N readings for a sensor
# ---------------------------------------------------------------------------

def _latest_readings(db: Session, sensor_id: str, limit: int = 20) -> list[SensorReading]:
    return (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )


def _all_sensor_ids(db: Session) -> list[str]:
    """Return distinct sensor IDs present in the database."""
    rows = db.query(SensorReading.sensor_id).distinct().all()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
def list_sensors(
    sensor_type: Optional[str] = Query(None, description="Filter by type: WaterLevel, Rainfall, Temperature, AirQuality"),
    db: Session = Depends(get_db),
):
    """
    Return the single latest reading for every sensor.
    Optionally filter by sensor_type.
    """
    sensor_ids = _all_sensor_ids(db)
    if not sensor_ids:
        return []

    result = []
    for sid in sensor_ids:
        query = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == sid)
        )
        if sensor_type:
            query = query.filter(SensorReading.sensor_type == sensor_type)
        latest = query.order_by(SensorReading.timestamp.desc()).first()
        if latest:
            result.append(latest.to_dict())

    return result


@router.get("/predictions")
def get_predictions(db: Session = Depends(get_db)):
    """
    Compute 30-minute water-level predictions for all Zone water-level sensors.
    Returns a list of prediction dicts, one per water sensor.
    """
    predictions = []
    for sensor_meta in WATER_SENSORS:
        sid = sensor_meta["sensor_id"]
        zone = sensor_meta["zone"]

        readings_objs = _latest_readings(db, sid, limit=20)
        # Readings are newest-first; reverse for chronological order
        values = [r.value for r in reversed(readings_objs)]

        pred = predict_water_level(values)
        pred["sensor_id"] = sid
        pred["zone"] = zone
        pred["lat"] = sensor_meta["lat"]
        pred["lng"] = sensor_meta["lng"]
        predictions.append(pred)

    return predictions


@router.get("/{sensor_id}/history")
def sensor_history(sensor_id: str, db: Session = Depends(get_db)):
    """Return the last 20 readings for the specified sensor (newest first)."""
    readings = _latest_readings(db, sensor_id, limit=20)
    if not readings:
        raise HTTPException(
            status_code=404,
            detail=f"No readings found for sensor '{sensor_id}'.",
        )
    return [r.to_dict() for r in readings]
