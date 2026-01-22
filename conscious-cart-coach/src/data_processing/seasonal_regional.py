"""
Seasonal and Regional Produce Calendar for NJ/Mid-Atlantic region.

Dynamically computes seasonality based on current date and user location.
Default: Middlesex County, NJ (FreshDirect delivery area)

Data loaded from CSV files:
- data/seasonal/nj_crop_calendar.csv
- data/seasonal/trusted_regional_sources.csv

=== DATA SOURCES (All Government/Academic - High Trust) ===

Primary Sources:
1. Jersey Fresh Program (NJ Dept of Agriculture)
   URL: https://jerseyfresh.nj.gov/
   Trust: OFFICIAL - State government program since 1984

2. Rutgers Cooperative Extension - NJ Agricultural Experiment Station
   URL: https://njaes.rutgers.edu/
   Trust: ACADEMIC - Land-grant university research
   Publications: FS1218 "NJ Vegetable Planting Calendar"

3. USDA National Agricultural Statistics Service
   URL: https://www.nass.usda.gov/
   Trust: OFFICIAL - Federal government

4. NJ Department of Agriculture
   URL: https://www.nj.gov/agriculture/
   Trust: OFFICIAL - State government
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

# Data file paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CROP_CALENDAR_CSV = DATA_DIR / "seasonal" / "nj_crop_calendar.csv"
REGIONAL_SOURCES_CSV = DATA_DIR / "seasonal" / "trusted_regional_sources.csv"

# Cache for loaded data
_crop_calendar = None
_regional_sources = None


# User location configuration
@dataclass
class UserLocation:
    """User location for regional produce matching."""
    state: str = "NJ"
    county: str = "Middlesex"
    latitude: float = 40.4862  # New Brunswick, NJ
    longitude: float = -74.4518

    # Maximum distance (miles) to consider "local"
    local_radius: int = 100


DEFAULT_LOCATION = UserLocation()


# Month names for output
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_ABBREV = ["", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _load_crop_calendar() -> dict:
    """Load crop calendar from CSV file."""
    global _crop_calendar

    if _crop_calendar is not None:
        return _crop_calendar

    _crop_calendar = {}

    if not CROP_CALENDAR_CSV.exists():
        return _get_fallback_calendar()

    with open(CROP_CALENDAR_CSV, newline="", encoding="utf-8") as f:
        lines = [line for line in f if not line.startswith("#")]

    if not lines:
        return _get_fallback_calendar()

    reader = csv.DictReader(lines)
    for row in reader:
        crop = row.get("crop", "").lower()
        if not crop:
            continue

        # Parse month columns to build season list
        seasons = []
        for month_num in range(1, 13):
            month_col = MONTH_ABBREV[month_num]
            status = row.get(month_col, "").lower().strip()
            if status in ("peak", "available", "storage"):
                seasons.append((month_num, status))

        # Group consecutive months into ranges
        season_ranges = _group_seasons(seasons)

        _crop_calendar[crop] = {
            "seasons": season_ranges,
            "category": row.get("category", ""),
            "nj_rank": row.get("nj_rank", ""),
            "notes": row.get("notes", ""),
            "source": row.get("source", ""),
        }

    return _crop_calendar


def _group_seasons(month_statuses: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    """Group consecutive months with same status into ranges."""
    if not month_statuses:
        return []

    ranges = []
    start_month = month_statuses[0][0]
    current_status = month_statuses[0][1]
    prev_month = start_month

    for month, status in month_statuses[1:]:
        # Check if consecutive and same status
        is_consecutive = (month == prev_month + 1) or (prev_month == 12 and month == 1)
        if is_consecutive and status == current_status:
            prev_month = month
        else:
            # Close current range
            ranges.append((start_month, prev_month, current_status))
            start_month = month
            current_status = status
            prev_month = month

    # Close final range
    ranges.append((start_month, prev_month, current_status))

    return ranges


def _get_fallback_calendar() -> dict:
    """Fallback hardcoded calendar if CSV not available."""
    return {
        "spinach": {"seasons": [(3, 5, "peak"), (9, 11, "peak")], "source": "Jersey Fresh"},
        "kale": {"seasons": [(3, 5, "peak"), (9, 12, "peak")], "source": "Jersey Fresh"},
        "tomato": {"seasons": [(7, 9, "peak")], "source": "Jersey Fresh"},
        "blueberry": {"seasons": [(6, 8, "peak")], "source": "USDA NASS"},
        "apple": {"seasons": [(8, 10, "peak"), (11, 3, "storage")], "source": "Jersey Fresh"},
        "potato": {"seasons": [(7, 10, "peak"), (11, 5, "storage")], "source": "Jersey Fresh"},
    }


def _load_regional_sources() -> dict:
    """Load trusted regional sources from CSV file."""
    global _regional_sources

    if _regional_sources is not None:
        return _regional_sources

    _regional_sources = {}

    if not REGIONAL_SOURCES_CSV.exists():
        return _get_fallback_sources()

    with open(REGIONAL_SOURCES_CSV, newline="", encoding="utf-8") as f:
        lines = [line for line in f if not line.startswith("#")]

    if not lines:
        return _get_fallback_sources()

    reader = csv.DictReader(lines)
    for row in reader:
        source_name = row.get("source_name", "").lower()
        keywords = row.get("source_keywords", source_name).lower()

        # Store both the source name and any keywords
        for keyword in keywords.split(";"):
            keyword = keyword.strip()
            if keyword:
                _regional_sources[keyword] = {
                    "source_name": row.get("source_name", ""),
                    "state": row.get("state", ""),
                    "distance_miles": int(row.get("distance_miles", 100) or 100),
                    "priority": int(row.get("priority", 3) or 3),
                    "trust_level": row.get("trust_level", "generic"),
                    "certification_type": row.get("certification_type", ""),
                    "verification": row.get("verification", ""),
                    "year_established": row.get("year_established", ""),
                    "url": row.get("url", ""),
                    "notes": row.get("notes", ""),
                }

    return _regional_sources


def _get_fallback_sources() -> dict:
    """Fallback hardcoded sources if CSV not available."""
    return {
        "jersey fresh": {"source_name": "Jersey Fresh", "state": "NJ", "distance_miles": 0, "priority": 1, "trust_level": "official"},
        "lancaster": {"source_name": "Lancaster", "state": "PA", "distance_miles": 80, "priority": 2, "trust_level": "verified"},
        "local": {"source_name": "Local", "state": None, "distance_miles": 50, "priority": 1, "trust_level": "generic"},
    }


# Backward compatibility - load on first access
def _get_trusted_sources():
    return _load_regional_sources()


# For imports that expect TRUSTED_REGIONAL_SOURCES as a dict
TRUSTED_REGIONAL_SOURCES = property(lambda self: _load_regional_sources())


@dataclass
class SeasonalStatus:
    """Seasonal status for a product."""
    is_in_season: bool
    quality: Literal["peak", "available", "storage", "off_season"]
    local_available: bool
    season_months: list[tuple[int, int]]  # (start, end) pairs
    recommendation: str
    environmental_bonus: int  # Points to add to environmental score
    source: str = ""  # Data source for this info

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_in_season": self.is_in_season,
            "quality": self.quality,
            "local_available": self.local_available,
            "season_months": self.season_months,
            "recommendation": self.recommendation,
            "environmental_bonus": self.environmental_bonus,
            "source": self.source,
        }


def get_current_month() -> int:
    """Get current month (1-12)."""
    return datetime.now().month


def is_month_in_range(month: int, start: int, end: int) -> bool:
    """Check if month is within range, handling year wraparound."""
    if start <= end:
        return start <= month <= end
    else:
        # Wraparound (e.g., Nov-Mar = 11-3)
        return month >= start or month <= end


def get_seasonal_status(
    product_name: str,
    category: str = "",
    current_month: int | None = None,
    location: UserLocation | None = None,
) -> SeasonalStatus:
    """
    Get seasonal status for a product based on current date and location.

    Args:
        product_name: Name of the product
        category: Product category for additional context
        current_month: Override current month (for testing)
        location: User location (defaults to NJ Middlesex)

    Returns:
        SeasonalStatus with season info and recommendations
    """
    if current_month is None:
        current_month = get_current_month()

    if location is None:
        location = DEFAULT_LOCATION

    calendar = _load_crop_calendar()

    # Normalize product name for lookup
    name_lower = product_name.lower()
    category_lower = category.lower() if category else ""

    # Find matching crop in calendar
    matched_crop = None
    matched_data = None
    for crop, data in calendar.items():
        if crop in name_lower or crop in category_lower:
            matched_crop = crop
            matched_data = data
            break

    # Default for items not in calendar (year-round/imported)
    if matched_crop is None:
        return SeasonalStatus(
            is_in_season=False,
            quality="off_season",
            local_available=False,
            season_months=[],
            recommendation="Not locally grown - imported or greenhouse",
            environmental_bonus=0,
            source="",
        )

    # Check current season status
    seasons = matched_data.get("seasons", [])
    current_quality = "off_season"
    is_in_season = False
    season_months = [(s[0], s[1]) for s in seasons]
    source = matched_data.get("source", "")

    for start, end, quality in seasons:
        if is_month_in_range(current_month, start, end):
            is_in_season = True
            current_quality = quality
            break

    # Generate recommendation
    if current_quality == "peak":
        recommendation = f"Peak season for local {matched_crop}! Best quality and price from NJ farms."
        environmental_bonus = 40  # Highest bonus for peak local
        local_available = True
    elif current_quality == "storage":
        recommendation = f"Local {matched_crop} available from regional storage. Good quality."
        environmental_bonus = 25  # Good bonus for stored local
        local_available = True
    elif current_quality == "available":
        recommendation = f"Local {matched_crop} in season. Support NJ farms!"
        environmental_bonus = 35
        local_available = True
    else:
        # Find next season
        next_season_start = None
        for start, end, _ in seasons:
            if start > current_month:
                next_season_start = start
                break
        if next_season_start is None and seasons:
            next_season_start = seasons[0][0]

        if next_season_start:
            recommendation = f"Local {matched_crop} returns in {MONTH_NAMES[next_season_start]}. Currently imported."
        else:
            recommendation = f"Local {matched_crop} not currently available. Consider alternatives."
        environmental_bonus = 0
        local_available = False

    return SeasonalStatus(
        is_in_season=is_in_season,
        quality=current_quality,
        local_available=local_available,
        season_months=season_months,
        recommendation=recommendation,
        environmental_bonus=environmental_bonus,
        source=source,
    )


def is_regional_source(brand: str, notes: str = "", certifications: str = "") -> dict:
    """
    Check if a product is from a trusted regional source.

    Args:
        brand: Product brand name
        notes: Product notes/description
        certifications: Product certifications

    Returns:
        Dict with regional info if matched, empty dict if not.
        Includes trust_level: "official" (government certified),
        "verified" (known cooperative), or "generic" (self-declared)
    """
    sources = _load_regional_sources()
    text = f"{brand} {notes} {certifications}".lower()

    for keyword, info in sources.items():
        if keyword in text:
            return {
                "source": info.get("source_name", keyword),
                "state": info.get("state"),
                "distance_miles": info.get("distance_miles", 100),
                "priority": info.get("priority", 3),
                "is_local": info.get("distance_miles", 100) <= DEFAULT_LOCATION.local_radius,
                "trust_level": info.get("trust_level", "generic"),
                "verification": info.get("verification", ""),
                "url": info.get("url"),
            }

    return {}


def get_seasonal_recommendations(
    month: int | None = None,
    location: UserLocation | None = None,
) -> dict[str, list[str]]:
    """
    Get what's in season for a given month.

    Args:
        month: Month number (1-12), defaults to current
        location: User location

    Returns:
        Dict with 'peak', 'available', 'storage' lists of crops
    """
    if month is None:
        month = get_current_month()

    calendar = _load_crop_calendar()

    results = {
        "peak": [],
        "available": [],
        "storage": [],
        "month": month,
        "month_name": MONTH_NAMES[month],
    }

    for crop, data in calendar.items():
        for start, end, quality in data.get("seasons", []):
            if is_month_in_range(month, start, end):
                if quality in results:
                    results[quality].append(crop)
                break

    return results


def get_trusted_sources_summary() -> list[dict]:
    """
    Get summary of all trusted regional sources with verification info.

    Returns:
        List of dicts with source details, sorted by trust level
    """
    sources = _load_regional_sources()
    seen = set()
    result = []

    for keyword, info in sources.items():
        source_name = info.get("source_name", keyword)
        if source_name in seen:
            continue
        seen.add(source_name)

        result.append({
            "name": source_name,
            "state": info.get("state"),
            "distance_miles": info.get("distance_miles"),
            "trust_level": info.get("trust_level", "generic"),
            "verification": info.get("verification", ""),
            "url": info.get("url"),
        })

    # Sort by trust level (official > verified > generic)
    trust_order = {"official": 0, "verified": 1, "generic": 2}
    result.sort(key=lambda x: (trust_order.get(x["trust_level"], 3), x.get("distance_miles", 100)))

    return result


def get_calendar_source_info() -> dict:
    """
    Get information about the crop calendar data sources.

    Returns:
        Dict with source citations and last update info
    """
    return {
        "primary_sources": [
            {
                "name": "Jersey Fresh Availability Guide",
                "authority": "NJ Department of Agriculture",
                "url": "https://jerseyfresh.nj.gov/",
                "type": "official_government",
            },
            {
                "name": "NJ Vegetable Planting Calendar (FS1218)",
                "authority": "Rutgers Cooperative Extension",
                "url": "https://njaes.rutgers.edu/fs1218/",
                "type": "academic_research",
            },
        ],
        "cross_references": [
            {
                "name": "USDA NASS Crop Production Reports",
                "authority": "US Department of Agriculture",
                "url": "https://www.nass.usda.gov/Statistics_by_State/New_Jersey/",
                "type": "official_government",
            },
        ],
        "data_files": {
            "crop_calendar": str(CROP_CALENDAR_CSV),
            "regional_sources": str(REGIONAL_SOURCES_CSV),
        },
        "nj_agriculture_facts": {
            "blueberry_rank": "#3 nationally",
            "cranberry_rank": "#4 nationally",
            "peach_rank": "#4 nationally",
            "tomato_note": "Jersey Tomato is a protected marketing term",
            "source": "USDA NASS 2023",
        },
    }


def get_data_sources() -> dict:
    """
    Get metadata about data sources used for seasonal/regional info.

    Returns:
        Dict with source information for transparency/citation
    """
    return {
        "jersey_fresh": {
            "name": "Jersey Fresh Program",
            "url": "https://jerseyfresh.nj.gov/",
            "authority": "NJ Department of Agriculture",
            "trust_level": "official_government",
        },
        "rutgers_extension": {
            "name": "Rutgers Cooperative Extension",
            "url": "https://njaes.rutgers.edu/",
            "authority": "Rutgers University (Land Grant)",
            "trust_level": "academic_research",
        },
        "usda_nass": {
            "name": "USDA National Agricultural Statistics",
            "url": "https://www.nass.usda.gov/",
            "authority": "US Department of Agriculture",
            "trust_level": "official_government",
        },
    }


# Quick access functions
def is_peak_season(product_name: str, category: str = "") -> bool:
    """Check if product is at peak season right now."""
    status = get_seasonal_status(product_name, category)
    return status.quality == "peak"


def is_local_available(product_name: str, category: str = "") -> bool:
    """Check if local version is currently available."""
    status = get_seasonal_status(product_name, category)
    return status.local_available


def get_environmental_bonus(product_name: str, category: str = "") -> int:
    """Get environmental score bonus for seasonal/local product."""
    status = get_seasonal_status(product_name, category)
    return status.environmental_bonus


def reload_seasonal_data():
    """Force reload of seasonal data from CSV (useful after updates)."""
    global _crop_calendar, _regional_sources
    _crop_calendar = None
    _regional_sources = None
    _load_crop_calendar()
    _load_regional_sources()
