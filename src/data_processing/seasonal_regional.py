"""
Seasonal and regional data for conscious buying recommendations.

Provides:
- Seasonal produce availability by region and month
- Region-specific recall filtering
- Local sourcing recommendations
"""

from datetime import datetime
from typing import Optional

# US regions for seasonal produce
US_REGIONS = {
    "northeast": ["CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
    "southeast": ["AL", "FL", "GA", "KY", "MS", "NC", "SC", "TN", "VA", "WV"],
    "midwest": ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"],
    "southwest": ["AZ", "NM", "OK", "TX"],
    "west": ["CA", "CO", "NV", "UT"],
    "pacific_northwest": ["OR", "WA", "ID", "MT", "WY"],
}

# Reverse lookup: state -> region
STATE_TO_REGION = {}
for region, states in US_REGIONS.items():
    for state in states:
        STATE_TO_REGION[state] = region


# Seasonal produce by month and region
# Format: {month: {region: [produce_categories]}}
SEASONAL_PRODUCE = {
    1: {  # January
        "northeast": ["produce_root_veg", "produce_greens", "produce_squash"],
        "southeast": ["produce_greens", "produce_citrus", "produce_root_veg"],
        "midwest": ["produce_root_veg", "produce_squash"],
        "southwest": ["produce_greens", "produce_citrus", "produce_root_veg"],
        "west": ["produce_greens", "produce_citrus", "produce_avocado"],
        "pacific_northwest": ["produce_root_veg", "produce_squash"],
    },
    2: {  # February
        "northeast": ["produce_root_veg", "produce_greens"],
        "southeast": ["produce_greens", "produce_citrus", "produce_strawberries"],
        "midwest": ["produce_root_veg"],
        "southwest": ["produce_greens", "produce_citrus"],
        "west": ["produce_greens", "produce_citrus", "produce_avocado"],
        "pacific_northwest": ["produce_root_veg"],
    },
    3: {  # March
        "northeast": ["produce_greens", "produce_root_veg"],
        "southeast": ["produce_greens", "produce_strawberries", "produce_asparagus"],
        "midwest": ["produce_greens"],
        "southwest": ["produce_greens", "produce_asparagus"],
        "west": ["produce_greens", "produce_asparagus", "produce_strawberries"],
        "pacific_northwest": ["produce_greens"],
    },
    4: {  # April
        "northeast": ["produce_greens", "produce_asparagus"],
        "southeast": ["produce_strawberries", "produce_asparagus", "produce_greens"],
        "midwest": ["produce_greens", "produce_asparagus"],
        "southwest": ["produce_tomatoes", "produce_peppers", "produce_greens"],
        "west": ["produce_strawberries", "produce_asparagus", "produce_greens"],
        "pacific_northwest": ["produce_greens", "produce_asparagus"],
    },
    5: {  # May
        "northeast": ["produce_greens", "produce_asparagus", "produce_strawberries"],
        "southeast": ["produce_berries", "produce_tomatoes", "produce_peppers"],
        "midwest": ["produce_greens", "produce_asparagus"],
        "southwest": ["produce_tomatoes", "produce_peppers", "produce_melons"],
        "west": ["produce_strawberries", "produce_cherries", "produce_greens"],
        "pacific_northwest": ["produce_greens", "produce_asparagus", "produce_berries"],
    },
    6: {  # June
        "northeast": ["produce_berries", "produce_greens", "produce_beans"],
        "southeast": ["produce_berries", "produce_tomatoes", "produce_peaches"],
        "midwest": ["produce_berries", "produce_greens"],
        "southwest": ["produce_tomatoes", "produce_peppers", "produce_melons"],
        "west": ["produce_cherries", "produce_berries", "produce_tomatoes"],
        "pacific_northwest": ["produce_berries", "produce_cherries"],
    },
    7: {  # July
        "northeast": ["produce_berries", "produce_tomatoes", "produce_corn"],
        "southeast": ["produce_tomatoes", "produce_peaches", "produce_melons"],
        "midwest": ["produce_berries", "produce_tomatoes", "produce_corn"],
        "southwest": ["produce_melons", "produce_peppers"],
        "west": ["produce_tomatoes", "produce_berries", "produce_peaches"],
        "pacific_northwest": ["produce_berries", "produce_cherries", "produce_tomatoes"],
    },
    8: {  # August
        "northeast": ["produce_tomatoes", "produce_corn", "produce_peppers", "produce_berries"],
        "southeast": ["produce_tomatoes", "produce_peppers", "produce_melons"],
        "midwest": ["produce_tomatoes", "produce_corn", "produce_peppers"],
        "southwest": ["produce_peppers", "produce_melons"],
        "west": ["produce_tomatoes", "produce_peppers", "produce_grapes"],
        "pacific_northwest": ["produce_tomatoes", "produce_berries", "produce_peppers"],
    },
    9: {  # September
        "northeast": ["produce_apples", "produce_tomatoes", "produce_squash"],
        "southeast": ["produce_tomatoes", "produce_peppers", "produce_greens"],
        "midwest": ["produce_apples", "produce_squash", "produce_tomatoes"],
        "southwest": ["produce_peppers", "produce_greens"],
        "west": ["produce_grapes", "produce_tomatoes", "produce_apples"],
        "pacific_northwest": ["produce_apples", "produce_pears", "produce_tomatoes"],
    },
    10: {  # October
        "northeast": ["produce_apples", "produce_squash", "produce_root_veg"],
        "southeast": ["produce_greens", "produce_root_veg"],
        "midwest": ["produce_apples", "produce_squash", "produce_root_veg"],
        "southwest": ["produce_greens", "produce_peppers"],
        "west": ["produce_apples", "produce_grapes", "produce_squash"],
        "pacific_northwest": ["produce_apples", "produce_pears", "produce_squash"],
    },
    11: {  # November
        "northeast": ["produce_squash", "produce_root_veg", "produce_greens"],
        "southeast": ["produce_greens", "produce_citrus", "produce_root_veg"],
        "midwest": ["produce_squash", "produce_root_veg"],
        "southwest": ["produce_greens", "produce_citrus"],
        "west": ["produce_citrus", "produce_squash", "produce_greens"],
        "pacific_northwest": ["produce_squash", "produce_root_veg"],
    },
    12: {  # December
        "northeast": ["produce_squash", "produce_root_veg"],
        "southeast": ["produce_greens", "produce_citrus"],
        "midwest": ["produce_squash", "produce_root_veg"],
        "southwest": ["produce_citrus", "produce_greens"],
        "west": ["produce_citrus", "produce_avocado", "produce_greens"],
        "pacific_northwest": ["produce_root_veg", "produce_squash"],
    },
}

# Map generic produce categories to seasonal categories
PRODUCE_TO_SEASONAL = {
    "produce_greens": "produce_greens",
    "produce_spinach": "produce_greens",
    "produce_kale": "produce_greens",
    "produce_lettuce": "produce_greens",
    "produce_tomatoes": "produce_tomatoes",
    "produce_peppers": "produce_peppers",
    "produce_berries": "produce_berries",
    "fruit_berries": "produce_berries",
    "produce_strawberries": "produce_berries",
    "produce_root_veg": "produce_root_veg",
    "produce_squash": "produce_squash",
    "produce_corn": "produce_corn",
    "produce_beans": "produce_beans",
    "fruit_citrus": "produce_citrus",
    "fruit_tropical": "produce_avocado",
    "produce_apples": "produce_apples",
    "fruit_other": "produce_apples",
}


def get_region_from_state(state: str) -> Optional[str]:
    """Get US region from state abbreviation."""
    return STATE_TO_REGION.get(state.upper())


def get_region_from_location(location: str) -> Optional[str]:
    """
    Determine region from location string.

    Accepts:
    - State abbreviation (e.g., "CA", "NY")
    - Region name (e.g., "west", "northeast")
    - City, State format (e.g., "San Francisco, CA")
    """
    location = location.strip()

    # Check if it's a region name directly
    if location.lower() in US_REGIONS:
        return location.lower()

    # Check if it's a state abbreviation
    if len(location) == 2:
        return get_region_from_state(location)

    # Try to extract state from "City, STATE" format
    if "," in location:
        parts = location.split(",")
        if len(parts) >= 2:
            state = parts[-1].strip()
            if len(state) == 2:
                return get_region_from_state(state)

    # Check if location contains a state abbreviation
    for state, region in STATE_TO_REGION.items():
        if f" {state}" in location.upper() or location.upper().endswith(state):
            return region

    return None


def is_in_season(category: str, location: str, month: Optional[int] = None) -> bool:
    """
    Check if a produce category is in season for the given location.

    Args:
        category: Product category (e.g., "produce_tomatoes")
        location: Location string (state, region, or city)
        month: Month number (1-12), defaults to current month

    Returns:
        True if in season, False otherwise
    """
    if month is None:
        month = datetime.now().month

    region = get_region_from_location(location)
    if not region:
        return True  # Unknown region, assume in season

    # Map category to seasonal category
    seasonal_cat = PRODUCE_TO_SEASONAL.get(category, category)

    # Get seasonal produce for this month and region
    month_data = SEASONAL_PRODUCE.get(month, {})
    regional_produce = month_data.get(region, [])

    return seasonal_cat in regional_produce


def get_seasonal_produce(location: str, month: Optional[int] = None) -> list[str]:
    """
    Get list of in-season produce categories for location.

    Args:
        location: Location string
        month: Month number (1-12), defaults to current month

    Returns:
        List of produce categories in season
    """
    if month is None:
        month = datetime.now().month

    region = get_region_from_location(location)
    if not region:
        return []

    month_data = SEASONAL_PRODUCE.get(month, {})
    return month_data.get(region, [])


def get_seasonal_note(category: str, location: str, month: Optional[int] = None) -> Optional[str]:
    """
    Get a note about seasonal availability for a category.

    Args:
        category: Product category
        location: Location string
        month: Month number (1-12)

    Returns:
        Seasonal note string or None
    """
    if month is None:
        month = datetime.now().month

    region = get_region_from_location(location)
    if not region:
        return None

    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    in_season = is_in_season(category, location, month)
    region_display = region.replace("_", " ").title()

    if in_season:
        return f"✓ In season in {region_display} ({month_names[month]})"
    else:
        # Find when it IS in season
        in_season_months = []
        for m in range(1, 13):
            if is_in_season(category, location, m):
                in_season_months.append(month_names[m])

        if in_season_months:
            return f"⚠️ Out of season in {region_display}. Best months: {', '.join(in_season_months[:3])}"
        return f"⚠️ Not typically grown locally in {region_display}"


def filter_recalls_by_region(
    recalls: list[dict],
    location: str
) -> list[dict]:
    """
    Filter recalls to only those affecting the user's region.

    Args:
        recalls: List of recall flag dictionaries
        location: User's location

    Returns:
        Filtered list of recalls relevant to the location
    """
    region = get_region_from_location(location)

    filtered = []
    for recall in recalls:
        affected_regions = recall.get("affected_regions", [])
        affected_states = recall.get("affected_states", [])

        # If no region specified, assume nationwide
        if not affected_regions and not affected_states:
            filtered.append(recall)
            continue

        # Check if user's region is affected
        if region and region in [r.lower() for r in affected_regions]:
            filtered.append(recall)
            continue

        # Check if user's state is affected
        if location.upper() in [s.upper() for s in affected_states]:
            filtered.append(recall)
            continue

        # Check region's states
        if region:
            region_states = US_REGIONS.get(region, [])
            if any(state in affected_states for state in region_states):
                filtered.append(recall)

    return filtered


def get_local_sourcing_note(category: str, location: str) -> Optional[str]:
    """
    Get a note about local sourcing options.

    Args:
        category: Product category
        location: Location string

    Returns:
        Local sourcing note or None
    """
    region = get_region_from_location(location)
    if not region:
        return None

    # Regional specialties
    regional_specialties = {
        "west": {
            "produce_avocado": "California is the top US avocado producer",
            "produce_citrus": "California citrus in season",
            "produce_greens": "Year-round local greens available",
        },
        "pacific_northwest": {
            "produce_apples": "Washington apples are world-renowned",
            "produce_berries": "Oregon/Washington berry country",
            "produce_cherries": "Peak cherry season June-July",
        },
        "southeast": {
            "produce_peaches": "Georgia peaches in summer",
            "produce_citrus": "Florida citrus in winter",
        },
        "northeast": {
            "produce_apples": "New York apple country",
            "produce_berries": "Local berry farms in summer",
        },
        "midwest": {
            "produce_corn": "Corn belt - freshest sweet corn",
            "grains": "Local grain options available",
        },
    }

    seasonal_cat = PRODUCE_TO_SEASONAL.get(category, category)
    region_notes = regional_specialties.get(region, {})

    return region_notes.get(seasonal_cat)
