"""Value normalizers for extracted order data.

Handles: dates (15+ formats), weights, phone numbers, address abbreviations.
"""

import re
from datetime import date, datetime, timedelta
from typing import Any


# --- Date Normalization ---

# Common date formats to try
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%d/%m/%y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d %Y",
    "%b %d %Y",
    "%d %B %Y",
    "%d %b %Y",
    "%Y%m%d",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%m.%d.%Y",
    "%d.%m.%Y",
]

# Relative date patterns
RELATIVE_PATTERNS: dict[str, int] = {
    "today": 0,
    "tomorrow": 1,
    "day after tomorrow": 2,
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def normalize_date(value: str | None, reference_date: date | None = None) -> date | None:
    """Normalize a date string to ISO 8601 (YYYY-MM-DD).

    Handles:
    - Standard formats: 2026-06-15, 06/15/2026, June 15 2026, etc.
    - Relative: 'today', 'tomorrow', 'next Monday', '3 weeks from today'
    - Returns None if unparseable.
    """
    if not value:
        return None

    value = value.strip()
    ref = reference_date or date.today()

    # Try relative patterns first
    lower = value.lower().strip()

    if lower in RELATIVE_PATTERNS:
        return ref + timedelta(days=RELATIVE_PATTERNS[lower])

    # "next Monday", "next Tuesday", etc.
    next_match = re.match(r"next\s+(\w+)", lower)
    if next_match:
        day_name = next_match.group(1).lower()
        if day_name in WEEKDAYS:
            target_weekday = WEEKDAYS.index(day_name)
            days_ahead = target_weekday - ref.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return ref + timedelta(days=days_ahead)

    # "N days/weeks from today"
    relative_match = re.match(r"(\d+)\s+(day|days|week|weeks)\s+from\s+today", lower)
    if relative_match:
        n = int(relative_match.group(1))
        unit = relative_match.group(2)
        if "week" in unit:
            n *= 7
        return ref + timedelta(days=n)

    # Try standard date formats
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt).date()
            return parsed
        except ValueError:
            continue

    return None


# --- Weight Normalization ---

WEIGHT_PATTERNS = [
    (r"([\d,]+\.?\d*)\s*(lbs?|pounds?)", "lbs"),
    (r"([\d,]+\.?\d*)\s*(kgs?|kilograms?|kilos?)", "kgs"),
    (r"([\d,]+\.?\d*)\s*(tons?|tonnes?|t)\b", "tons"),
    (r"([\d,]+\.?\d*)", None),  # bare number, unit unknown
]


def normalize_weight(value: str | None, default_unit: str = "lbs") -> tuple[float | None, str]:
    """Normalize a weight string to (numeric_value, unit).

    Returns (None, default_unit) if unparseable.
    """
    if not value:
        return None, default_unit

    value = value.strip().lower()

    for pattern, unit in WEIGHT_PATTERNS:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "")
            try:
                num = float(num_str)
                detected_unit = unit or default_unit
                # Convert tons to lbs if needed
                if detected_unit == "tons":
                    num *= 2000
                    detected_unit = "lbs"
                return num, detected_unit
            except ValueError:
                continue

    return None, default_unit


# --- Phone Normalization ---


def normalize_phone(value: str | None) -> str | None:
    """Normalize phone number toward E.164 format.

    For North American numbers, produces +1XXXXXXXXXX.
    Returns original if unable to normalize.
    """
    if not value:
        return None

    # Strip everything except digits and leading +
    digits = re.sub(r"[^\d+]", "", value)

    if digits.startswith("+"):
        return digits  # Already has country code

    # Remove leading 1 for North American numbers, then re-add
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) == 10:
        return f"+1{digits}"

    # Return original if we can't normalize
    return value


# --- Address Abbreviation Expansion ---

ADDRESS_ABBREVIATIONS = {
    "st": "Street",
    "st.": "Street",
    "ave": "Avenue",
    "ave.": "Avenue",
    "blvd": "Boulevard",
    "blvd.": "Boulevard",
    "dr": "Drive",
    "dr.": "Drive",
    "ln": "Lane",
    "ln.": "Lane",
    "rd": "Road",
    "rd.": "Road",
    "ct": "Court",
    "ct.": "Court",
    "pl": "Place",
    "pl.": "Place",
    "cir": "Circle",
    "cir.": "Circle",
    "hwy": "Highway",
    "hwy.": "Highway",
    "pkwy": "Parkway",
    "pkwy.": "Parkway",
    "n": "North",
    "n.": "North",
    "s": "South",
    "s.": "South",
    "e": "East",
    "e.": "East",
    "w": "West",
    "w.": "West",
    "ne": "Northeast",
    "nw": "Northwest",
    "se": "Southeast",
    "sw": "Southwest",
    "apt": "Apartment",
    "apt.": "Apartment",
    "ste": "Suite",
    "ste.": "Suite",
}


def expand_address_abbreviations(address: str | None) -> str | None:
    """Expand common address abbreviations to full words.

    E.g., '123 St James St' -> '123 St James Street'
    Only expands the LAST occurrence of directional/street type abbreviations
    to avoid false positives in street names like 'St James'.
    """
    if not address:
        return None

    words = address.split()
    if not words:
        return address

    # Only expand the last word if it's a known street type abbreviation
    last_word = words[-1].lower().rstrip(",.")
    if last_word in ADDRESS_ABBREVIATIONS and last_word in (
        "st", "st.", "ave", "ave.", "blvd", "blvd.", "dr", "dr.",
        "ln", "ln.", "rd", "rd.", "ct", "ct.", "pl", "pl.",
        "cir", "cir.", "hwy", "hwy.", "pkwy", "pkwy.",
    ):
        words[-1] = ADDRESS_ABBREVIATIONS[last_word]

    return " ".join(words)
