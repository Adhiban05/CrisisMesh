"""
services/prediction.py — Time-series water-level prediction service.

Uses NumPy-based ordinary least-squares linear regression on recent sensor
readings to forecast the water level 30 minutes ahead and classify risk.

No scikit-learn required.
"""

from typing import Optional
import numpy as np


# ---------------------------------------------------------------------------
# Risk classification thresholds (in metres)
# ---------------------------------------------------------------------------

RISK_THRESHOLDS = {
    "Low": (None, 0.5),       # value < 0.5 m
    "Medium": (0.5, 1.5),     # 0.5 ≤ value < 1.5 m
    "High": (1.5, 2.0),       # 1.5 ≤ value < 2.0 m
    "Critical": (2.0, None),  # value ≥ 2.0 m
}

TREND_STABLE_THRESHOLD = 0.02   # m / interval — slope below this → "stable"


def _classify_risk(value_m: float) -> str:
    """Map a water-level value (metres) to a risk label."""
    if value_m < 0.5:
        return "Low"
    if value_m < 1.5:
        return "Medium"
    if value_m < 2.0:
        return "High"
    return "Critical"


def _classify_trend(slope: float) -> str:
    """Map OLS slope to a human-readable trend label."""
    if slope > TREND_STABLE_THRESHOLD:
        return "rising"
    if slope < -TREND_STABLE_THRESHOLD:
        return "falling"
    return "stable"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_water_level(
    readings: list[float],
    interval_seconds: int = 60,
    predict_minutes: int = 30,
) -> dict:
    """
    Predict future water level using linear regression on recent readings.

    Parameters
    ----------
    readings : list[float]
        Chronologically ordered water-level values (metres).
        At least 2 readings are required; more gives a better fit.
    interval_seconds : int
        Time interval between consecutive readings in seconds.
        Default: 60 s (one reading per minute).
    predict_minutes : int
        How many minutes ahead to predict. Default: 30.

    Returns
    -------
    dict with keys:
        predicted_value      : float  (metres, rounded to 3 d.p.)
        predicted_in_minutes : int
        risk_level           : str    (Low / Medium / High / Critical)
        trend                : str    (rising / falling / stable)
        slope_per_minute     : float  (m / min)
        current_value        : float  (latest reading)
        confidence           : float  (R² of the linear fit, 0–1)
    """
    if not readings:
        return {
            "predicted_value": 0.0,
            "predicted_in_minutes": predict_minutes,
            "risk_level": "Low",
            "trend": "stable",
            "slope_per_minute": 0.0,
            "current_value": 0.0,
            "confidence": 0.0,
        }

    if len(readings) == 1:
        val = float(readings[0])
        return {
            "predicted_value": round(val, 3),
            "predicted_in_minutes": predict_minutes,
            "risk_level": _classify_risk(val),
            "trend": "stable",
            "slope_per_minute": 0.0,
            "current_value": round(val, 3),
            "confidence": 0.5,
        }

    # Build time axis in minutes
    n = len(readings)
    interval_minutes = interval_seconds / 60.0
    t = np.arange(n, dtype=float) * interval_minutes   # shape (n,)
    y = np.array(readings, dtype=float)                 # shape (n,)

    # OLS: [slope, intercept] via numpy least-squares
    A = np.vstack([t, np.ones(n)]).T          # shape (n, 2)
    result = np.linalg.lstsq(A, y, rcond=None)
    coeffs = result[0]                         # [slope, intercept]
    slope = float(coeffs[0])                   # m / minute
    intercept = float(coeffs[1])

    # Predict at t = last_t + predict_minutes
    t_future = t[-1] + predict_minutes
    predicted = slope * t_future + intercept
    predicted = max(predicted, 0.0)            # water level can't go negative

    # Compute R² as confidence measure
    y_hat = slope * t + intercept
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-10 else 1.0
    r_squared = max(0.0, min(1.0, r_squared))

    current_value = float(y[-1])
    trend = _classify_trend(slope)
    risk_level = _classify_risk(predicted)

    return {
        "predicted_value": round(predicted, 3),
        "predicted_in_minutes": predict_minutes,
        "risk_level": risk_level,
        "trend": trend,
        "slope_per_minute": round(slope, 5),
        "current_value": round(current_value, 3),
        "confidence": round(r_squared, 3),
    }


def predict_all_zones(zone_readings: dict[str, list[float]]) -> dict[str, dict]:
    """
    Run predictions for multiple zones at once.

    Parameters
    ----------
    zone_readings : dict
        Mapping of zone_id → list of recent water-level readings.

    Returns
    -------
    dict mapping zone_id → prediction result dict.
    """
    return {
        zone_id: predict_water_level(readings)
        for zone_id, readings in zone_readings.items()
    }
