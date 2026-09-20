"""
services/nlp_parser.py — Lightweight NLP parser for citizen disaster reports.

Uses regex patterns and curated keyword dictionaries to extract:
  - location       : area name or landmark
  - incident_type  : Flood / Fire / Accident / Infrastructure / Industrial
  - severity       : High / Medium / Low
  - people_count   : integer count of people mentioned
  - confidence     : float 0.0 – 1.0

No external NLP libraries are required.
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Keyword dictionaries
# ---------------------------------------------------------------------------

FLOOD_KEYWORDS = [
    "flood", "flooding", "flooded", "inundated", "inundation",
    "water level", "water entered", "water has entered", "submerged",
    "overflowing", "overflow", "waterlogged", "water logged",
    "rising water", "heavy rain", "rain water", "drainage blocked",
    "sewage overflow", "stagnant water", "knee deep", "waist deep",
    "chest deep", "flash flood",
]

FIRE_KEYWORDS = [
    "fire", "blaze", "burning", "flames", "smoke", "on fire",
    "caught fire", "fire broke", "inferno", "combustion",
    "explosion", "blast", "burn", "burnt", "ablaze",
]

ACCIDENT_KEYWORDS = [
    "accident", "collision", "crash", "hit", "vehicle accident",
    "car accident", "road accident", "injured", "casualties",
    "ambulance needed", "person hit", "people injured",
]

INFRASTRUCTURE_KEYWORDS = [
    "road blocked", "road closed", "bridge collapsed", "building collapsed",
    "wall collapsed", "power cut", "power outage", "electricity gone",
    "transformer exploded", "wire snapped", "fallen tree",
    "landslide", "sinkhole", "pothole", "debris",
]

INDUSTRIAL_KEYWORDS = [
    "chemical", "gas leak", "lpg", "toxic", "hazmat",
    "factory", "industrial", "pipeline", "oil spill",
    "fumes", "vapour", "vapor", "leakage",
]

HIGH_SEVERITY_WORDS = [
    "critical", "emergency", "urgent", "immediately", "sos", "help",
    "trapped", "dying", "dead", "killed", "deaths", "severe",
    "dangerous", "life threatening", "evacuate", "rescue needed",
    "no exit", "surrounded", "completely", "many people",
]

MEDIUM_SEVERITY_WORDS = [
    "warning", "alert", "concern", "worried", "increasing", "rising",
    "getting worse", "spreading", "escalating",
    "some people", "few people", "several",
]

# Common location patterns and well-known area keywords
LOCATION_PATTERNS = [
    # "near <Location>" / "at <Location>" / "in <Location>"
    r"\b(?:near|at|in|around|beside|by|opposite|behind|front\s+of)\s+([A-Z][a-zA-Z\s]{2,30}?)(?:\s+(?:road|street|avenue|lane|nagar|colony|area|block|sector|zone|district|town|city|bus\s+stand|metro|station|signal|junction|crossing|hospital|school|college|temple|mosque|church|park|lake|bridge|flyover|market|mall))",
    # "<Location> area / zone / sector"
    r"\b([A-Z][a-zA-Z\s]{2,25}?)\s+(?:area|zone|sector|block|colony|nagar|district|town)",
    # "Zone <number>"
    r"\b(Zone\s+\d+)\b",
    # "<Location> road / street"
    r"\b([A-Z][a-zA-Z\s]{2,25}?)\s+(?:road|street|avenue|lane)\b",
    # Standalone title-cased two-word proper nouns (fallback)
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b",
]

# Numbers adjacent to "people", "persons", "residents", "families", etc.
PEOPLE_PATTERNS = [
    r"(\d+)\s*(?:people|persons?|individuals?|residents?|families|households?|victims?|civilians?|trapped)",
    r"(?:about|around|nearly|over|more than|at least)\s+(\d+)\s*(?:people|persons?|residents?|families)",
    r"(?:people|persons?|residents?)\s*(?:are|is|were|have)?\s*(?:about|around|nearly)?\s*(\d+)",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lower-case and collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _count_keyword_hits(text_lower: str, keywords: list[str]) -> int:
    """Return how many keywords from the list appear in the text."""
    return sum(1 for kw in keywords if kw in text_lower)


def _detect_type(text_lower: str) -> tuple[str, float]:
    """
    Returns (incident_type, type_confidence) by scoring keyword hits
    across all category dictionaries.
    """
    scores = {
        "Flood": _count_keyword_hits(text_lower, FLOOD_KEYWORDS),
        "Fire": _count_keyword_hits(text_lower, FIRE_KEYWORDS),
        "Accident": _count_keyword_hits(text_lower, ACCIDENT_KEYWORDS),
        "Infrastructure": _count_keyword_hits(text_lower, INFRASTRUCTURE_KEYWORDS),
        "Industrial": _count_keyword_hits(text_lower, INDUSTRIAL_KEYWORDS),
    }
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return "Unknown", 0.0

    # Normalise confidence: 1 hit → 0.5, 2 hits → 0.75, 3+ hits → 0.9+
    confidence = min(0.5 + (best_score - 1) * 0.2, 0.95)
    return best_type, round(confidence, 2)


def _detect_severity(text_lower: str) -> tuple[str, float]:
    """
    Returns (severity_label, severity_confidence).
    High / Medium / Low based on urgency keywords.
    """
    high_hits = _count_keyword_hits(text_lower, HIGH_SEVERITY_WORDS)
    medium_hits = _count_keyword_hits(text_lower, MEDIUM_SEVERITY_WORDS)

    if high_hits >= 1:
        conf = min(0.6 + high_hits * 0.15, 0.95)
        return "High", round(conf, 2)
    if medium_hits >= 1:
        conf = min(0.5 + medium_hits * 0.15, 0.85)
        return "Medium", round(conf, 2)
    return "Low", 0.5


def _extract_location(text: str) -> Optional[str]:
    """
    Try each location regex pattern in priority order; return the first
    non-trivial match or None.
    """
    # Common stop-words that are never valid location names
    STOP_WORDS = {
        "water", "fire", "flood", "people", "road", "area", "zone",
        "help", "the", "and", "this", "that", "they", "there",
        "some", "with", "from", "have", "been", "were", "has",
    }

    for pattern in LOCATION_PATTERNS:
        for match in re.finditer(pattern, text):
            candidate = match.group(1).strip()
            # Filter: must be ≥ 3 chars, not a stop-word, not purely numeric
            words = candidate.lower().split()
            if (
                len(candidate) >= 3
                and not any(w in STOP_WORDS for w in words)
                and not candidate.isdigit()
            ):
                return candidate

    return None


def _extract_people_count(text_lower: str) -> Optional[int]:
    """Return the first plausible people count extracted from the text."""
    for pattern in PEOPLE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            try:
                count = int(match.group(1))
                if 1 <= count <= 10_000:   # sanity bounds
                    return count
            except (ValueError, IndexError):
                continue
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_citizen_report(message: str) -> dict:
    """
    Parse a free-text citizen report and return a structured dictionary.

    Parameters
    ----------
    message : str
        Raw text from the citizen (e.g. WhatsApp message).

    Returns
    -------
    dict with keys:
        location        : str | None
        incident_type   : str          (Flood / Fire / Accident / Infrastructure / Industrial / Unknown)
        severity        : str          (High / Medium / Low)
        people_count    : int | None
        confidence      : float        (0.0 – 1.0)
        raw_message     : str
    """
    if not message or not message.strip():
        return {
            "location": None,
            "incident_type": "Unknown",
            "severity": "Low",
            "people_count": None,
            "confidence": 0.0,
            "raw_message": message,
        }

    text_lower = _normalise(message)

    incident_type, type_conf = _detect_type(text_lower)
    severity, sev_conf = _detect_severity(text_lower)
    location = _extract_location(message)          # use original case for proper nouns
    people_count = _extract_people_count(text_lower)

    # Overall confidence: weighted average of type and severity confidences,
    # boosted slightly if a location was found.
    base_confidence = round((type_conf * 0.6 + sev_conf * 0.4), 2)
    if location:
        base_confidence = min(base_confidence + 0.1, 1.0)
    if people_count is not None:
        base_confidence = min(base_confidence + 0.05, 1.0)

    return {
        "location": location,
        "incident_type": incident_type,
        "severity": severity,
        "people_count": people_count,
        "confidence": round(base_confidence, 2),
        "raw_message": message,
    }
