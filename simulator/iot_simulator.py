"""
CrisisMesh AI - IoT Data Simulator
Simulates ESP8266 sensors sending data via MQTT/HTTP to the backend.
Can run standalone or be imported as a module.

Usage:
    python iot_simulator.py --backend http://localhost:8000 --interval 3
"""

import asyncio
import random
import json
import time
import argparse
import math
from datetime import datetime
from typing import Optional
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    print("httpx not installed. Install with: pip install httpx")

# ─── Sensor Definitions ──────────────────────────────────────────────────────

WATER_SENSORS = [
    {"id": "WL-001", "zone": "Zone 1", "lat": 13.0827, "lng": 80.2707, "base_level": 0.3},
    {"id": "WL-002", "zone": "Zone 2", "lat": 13.0900, "lng": 80.2650, "base_level": 0.5},
    {"id": "WL-003", "zone": "Zone 3", "lat": 13.0750, "lng": 80.2800, "base_level": 0.8},
    {"id": "WL-004", "zone": "Zone 4", "lat": 13.0680, "lng": 80.2720, "base_level": 0.4},
    {"id": "WL-005", "zone": "Zone 5", "lat": 13.0950, "lng": 80.2580, "base_level": 1.2},
    {"id": "WL-006", "zone": "Zone 6", "lat": 13.1020, "lng": 80.2620, "base_level": 0.6},
    {"id": "WL-007", "zone": "Zone 7", "lat": 13.0600, "lng": 80.2900, "base_level": 1.8},  # Critical zone
    {"id": "WL-008", "zone": "Zone 8", "lat": 13.1100, "lng": 80.2700, "base_level": 0.2},
]

RAINFALL_SENSORS = [
    {"id": "RF-001", "zone": "Zone 1", "lat": 13.0830, "lng": 80.2710, "base_value": 15},
    {"id": "RF-002", "zone": "Zone 5", "lat": 13.0955, "lng": 80.2585, "base_value": 45},
    {"id": "RF-003", "zone": "Zone 7", "lat": 13.0605, "lng": 80.2905, "base_value": 86},  # Heavy rain
    {"id": "RF-004", "zone": "Zone 8", "lat": 13.1105, "lng": 80.2705, "base_value": 8},
]

TEMPERATURE_SENSORS = [
    {"id": "TMP-001", "zone": "Zone 2", "lat": 13.0905, "lng": 80.2655, "base_value": 32},
    {"id": "TMP-002", "zone": "Zone 3", "lat": 13.0755, "lng": 80.2805, "base_value": 85},  # Fire zone
    {"id": "TMP-003", "zone": "Zone 4", "lat": 13.0685, "lng": 80.2725, "base_value": 28},
    {"id": "TMP-004", "zone": "Zone 6", "lat": 13.1025, "lng": 80.2625, "base_value": 35},
    {"id": "TMP-005", "zone": "Zone 9", "lat": 13.1200, "lng": 80.2800, "base_value": 72},  # Industrial
    {"id": "TMP-006", "zone": "Zone 10", "lat": 13.0500, "lng": 80.2600, "base_value": 30},
]

SMOKE_SENSORS = [
    {"id": "SMK-001", "zone": "Zone 3", "lat": 13.0758, "lng": 80.2808, "base_value": 450},  # Fire
    {"id": "SMK-002", "zone": "Zone 9", "lat": 13.1205, "lng": 80.2805, "base_value": 280},  # Industrial
    {"id": "SMK-003", "zone": "Zone 1", "lat": 13.0832, "lng": 80.2712, "base_value": 35},  # Normal
]

# ─── Simulation State ─────────────────────────────────────────────────────────

class SensorState:
    def __init__(self):
        self.water_levels = {s["id"]: s["base_level"] for s in WATER_SENSORS}
        self.rainfall = {s["id"]: s["base_value"] for s in RAINFALL_SENSORS}
        self.temperature = {s["id"]: s["base_value"] for s in TEMPERATURE_SENSORS}
        self.smoke = {s["id"]: s["base_value"] for s in SMOKE_SENSORS}
        self.tick = 0

    def update(self):
        """Update all sensor values with realistic simulation."""
        self.tick += 1
        t = self.tick

        # Water levels: slow sine wave + random walk + rising trend for Zone 7
        for sensor in WATER_SENSORS:
            sid = sensor["id"]
            base = sensor["base_level"]
            if sid == "WL-007":  # Zone 7 is critical and rising
                trend = 0.005 * t  # slowly rising
                noise = random.gauss(0, 0.02)
                self.water_levels[sid] = min(3.0, base + trend + noise + 0.1 * math.sin(t * 0.1))
            elif sid == "WL-005":  # Zone 5 is warning
                noise = random.gauss(0, 0.03)
                self.water_levels[sid] = max(0.1, base + noise + 0.05 * math.sin(t * 0.15))
            else:
                noise = random.gauss(0, 0.01)
                self.water_levels[sid] = max(0.05, base + noise + 0.02 * math.sin(t * 0.08))

        # Rainfall: fluctuate with gradual changes
        for sensor in RAINFALL_SENSORS:
            sid = sensor["id"]
            base = sensor["base_value"]
            noise = random.gauss(0, base * 0.05)
            self.rainfall[sid] = max(0, base + noise + 5 * math.sin(t * 0.05))

        # Temperature: fire zones stay high, others normal
        for sensor in TEMPERATURE_SENSORS:
            sid = sensor["id"]
            base = sensor["base_value"]
            noise = random.gauss(0, 1.5)
            self.temperature[sid] = max(20, base + noise + 2 * math.sin(t * 0.1))

        # Smoke: high in fire/industrial zones
        for sensor in SMOKE_SENSORS:
            sid = sensor["id"]
            base = sensor["base_value"]
            noise = random.gauss(0, base * 0.08)
            self.smoke[sid] = max(0, base + noise)

    def get_readings(self):
        """Get all current sensor readings as a list of dicts."""
        readings = []
        for sensor in WATER_SENSORS:
            readings.append({
                "sensor_id": sensor["id"],
                "sensor_type": "water_level",
                "value": round(self.water_levels[sensor["id"]], 3),
                "unit": "m",
                "zone": sensor["zone"],
                "lat": sensor["lat"],
                "lng": sensor["lng"],
                "timestamp": datetime.utcnow().isoformat()
            })
        for sensor in RAINFALL_SENSORS:
            readings.append({
                "sensor_id": sensor["id"],
                "sensor_type": "rainfall",
                "value": round(self.rainfall[sensor["id"]], 1),
                "unit": "mm/hr",
                "zone": sensor["zone"],
                "lat": sensor["lat"],
                "lng": sensor["lng"],
                "timestamp": datetime.utcnow().isoformat()
            })
        for sensor in TEMPERATURE_SENSORS:
            readings.append({
                "sensor_id": sensor["id"],
                "sensor_type": "temperature",
                "value": round(self.temperature[sensor["id"]], 1),
                "unit": "°C",
                "zone": sensor["zone"],
                "lat": sensor["lat"],
                "lng": sensor["lng"],
                "timestamp": datetime.utcnow().isoformat()
            })
        for sensor in SMOKE_SENSORS:
            readings.append({
                "sensor_id": sensor["id"],
                "sensor_type": "smoke_aqi",
                "value": round(self.smoke[sensor["id"]], 0),
                "unit": "ppm",
                "zone": sensor["zone"],
                "lat": sensor["lat"],
                "lng": sensor["lng"],
                "timestamp": datetime.utcnow().isoformat()
            })
        return readings


# ─── Simulator Runner ─────────────────────────────────────────────────────────

state = SensorState()


async def push_to_backend(backend_url: str, readings: list):
    """Push sensor readings to the backend API."""
    if not HAS_HTTPX:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{backend_url}/api/sensors/batch", json={"readings": readings})
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Backend push failed: {e}")


def print_summary(readings: list):
    """Print a human-readable summary of current sensor state."""
    water = [r for r in readings if r["sensor_type"] == "water_level"]
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === Sensor Update ===")
    for r in water:
        level = r["value"]
        bar = "█" * int(level * 5)
        status = "🔴 CRITICAL" if level > 1.5 else ("🟠 WARNING" if level > 0.8 else "🟢 NORMAL")
        print(f"  {r['sensor_id']} ({r['zone']}): {level:.2f}m {bar} {status}")

    high_temp = [r for r in readings if r["sensor_type"] == "temperature" and r["value"] > 60]
    if high_temp:
        for r in high_temp:
            print(f"  🔥 {r['sensor_id']} ({r['zone']}): {r['value']:.1f}°C - HIGH TEMPERATURE")


async def run_simulator(backend_url: str = "http://localhost:8000", interval: float = 3.0, verbose: bool = True):
    """Main simulator loop."""
    print(f"""
╔═══════════════════════════════════════════╗
║     CrisisMesh IoT Simulator              ║
║     Pushing to: {backend_url:<25}║
║     Interval: {interval}s                        ║
╚═══════════════════════════════════════════╝
""")
    tick = 0
    while True:
        state.update()
        readings = state.get_readings()

        if verbose:
            print_summary(readings)

        await push_to_backend(backend_url, readings)

        tick += 1
        await asyncio.sleep(interval)


def get_current_readings() -> list:
    """Get current readings (used when imported as module)."""
    state.update()
    return state.get_readings()


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CrisisMesh IoT Simulator")
    parser.add_argument("--backend", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--interval", type=float, default=3.0, help="Update interval in seconds")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    args = parser.parse_args()

    try:
        asyncio.run(run_simulator(
            backend_url=args.backend,
            interval=args.interval,
            verbose=not args.quiet
        ))
    except KeyboardInterrupt:
        print("\n[Simulator stopped]")
