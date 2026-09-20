"""
main.py — CrisisMesh AI Disaster Response Platform — FastAPI entry point.

Features:
  - CORS enabled for all origins (hackathon mode)
  - All routers mounted under /api prefix
  - WebSocket at /ws for real-time dashboard updates (2 s broadcast cycle)
  - Startup: DB table creation → incident + team seeding → IoT simulator launch
  - GET / health-check endpoint
"""

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models.incident import Incident, ResponseTeam, SensorReading  # noqa: F401 – registers ORM models
from routers import ai, incidents, sensors, teams
from services.prediction import predict_water_level
from services.simulator import (
    WATER_SENSORS,
    link_deployed_teams,
    run_simulator,
    seed_incidents,
    seed_teams,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("crisismesh")


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages a pool of active WebSocket connections."""

    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        logger.info("WebSocket client connected. Total: %d", len(self.active))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)
        logger.info("WebSocket client disconnected. Total: %d", len(self.active))

    async def broadcast(self, data: dict) -> None:
        """Send JSON payload to all connected clients, pruning dead connections."""
        payload = json.dumps(data, default=str)
        dead: list[WebSocket] = []
        for ws in list(self.active):
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Broadcast payload builder
# ---------------------------------------------------------------------------

def _build_broadcast_payload(db: Session) -> dict:
    """Assemble the real-time update payload from current DB state."""
    # Incidents
    all_incidents = (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .limit(20)
        .all()
    )
    incidents_data = [inc.to_dict() for inc in all_incidents]

    # Teams
    all_teams = db.query(ResponseTeam).order_by(ResponseTeam.type, ResponseTeam.name).all()
    teams_data = [t.to_dict() for t in all_teams]

    # Latest sensor readings (one per sensor)
    sensor_ids: list[str] = [
        r[0]
        for r in db.query(SensorReading.sensor_id).distinct().all()
    ]
    sensors_data: list[dict] = []
    for sid in sensor_ids:
        latest = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == sid)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        if latest:
            sensors_data.append(latest.to_dict())

    # Water-level predictions
    predictions: list[dict] = []
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

    # Quick stats
    stats = {
        "total_incidents": len(all_incidents),
        "critical": sum(1 for i in all_incidents if i.severity == "Critical"),
        "warning": sum(1 for i in all_incidents if i.severity == "Warning"),
        "normal": sum(1 for i in all_incidents if i.severity == "Normal"),
        "active_incidents": sum(1 for i in all_incidents if i.status == "Active"),
        "teams_available": sum(1 for t in all_teams if t.status == "Available"),
        "teams_deployed": sum(1 for t in all_teams if t.status in ("Deployed", "OnScene")),
        "people_affected": sum((i.people_affected or 0) for i in all_incidents),
    }

    return {
        "type": "update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "incidents": incidents_data,
        "sensors": sensors_data,
        "teams": teams_data,
        "predictions": predictions,
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# WebSocket broadcast loop (background task)
# ---------------------------------------------------------------------------

async def _broadcast_loop() -> None:
    """Emit real-time updates to all connected WebSocket clients every 2 seconds."""
    logger.info("WebSocket broadcast loop started.")
    while True:
        await asyncio.sleep(2)
        if not manager.active:
            continue
        try:
            db: Session = SessionLocal()
            try:
                payload = _build_broadcast_payload(db)
            finally:
                db.close()
            await manager.broadcast(payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Broadcast error: %s", exc)


# ---------------------------------------------------------------------------
# Application lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup sequence:
      1. Create all DB tables.
      2. Seed incidents and response teams.
      3. Link deployed teams to incidents.
      4. Launch IoT simulator as background task.
      5. Launch WebSocket broadcast loop.
    """
    logger.info("=== CrisisMesh AI — Starting Up ===")

    # 1. Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")

    # 2 & 3. Seed data
    db: Session = SessionLocal()
    try:
        seed_incidents(db)
        seed_teams(db)
        link_deployed_teams(db)
    finally:
        db.close()

    # 4. Start IoT simulator
    asyncio.create_task(run_simulator(), name="iot_simulator")
    logger.info("IoT Simulator task scheduled.")

    # 5. Start WebSocket broadcast loop
    asyncio.create_task(_broadcast_loop(), name="ws_broadcast")
    logger.info("WebSocket broadcast task scheduled.")

    logger.info("=== CrisisMesh AI — Ready ===")
    yield
    logger.info("=== CrisisMesh AI — Shutting Down ===")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CrisisMesh AI",
    description=(
        "Real-time AI-powered disaster response coordination platform. "
        "Aggregates IoT sensor data, citizen reports, and AI assessments "
        "to coordinate emergency response."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- CORS (open for hackathon / local frontend dev) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(incidents.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """Platform health check — confirms API is live."""
    return {
        "status": "ok",
        "platform": "CrisisMesh AI",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "docs": "/docs",
        "websocket": "/ws",
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Real-time WebSocket feed.
    Sends an initial full snapshot immediately on connect,
    then the broadcast loop delivers updates every 2 seconds.
    """
    await manager.connect(ws)
    try:
        # Send immediate snapshot so dashboard populates instantly
        db: Session = SessionLocal()
        try:
            initial_payload = _build_broadcast_payload(db)
        finally:
            db.close()
        await ws.send_text(json.dumps(initial_payload, default=str))

        # Keep connection alive — wait for client messages or disconnect
        while True:
            try:
                # Await any client message (ping / pong / commands)
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                # Echo back an acknowledgement
                await ws.send_text(json.dumps({"type": "ack", "received": msg}))
            except asyncio.TimeoutError:
                # No message in 30 s — send a heartbeat ping
                await ws.send_text(json.dumps({"type": "ping", "timestamp": datetime.now(timezone.utc).isoformat()}))
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as exc:  # noqa: BLE001
        logger.warning("WebSocket error: %s", exc)
        manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Development entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
