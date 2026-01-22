"""
EWG (Environmental Working Group) Full Produce Pesticide Rankings.

Single source of truth for pesticide-related produce classifications.
Used by decision_engine.py and csv_validator.py.

THREE categories (2025 list, 47 items total):
- Dirty Dozen (ranks 36-47): Organic REQUIRED
- Middle (ranks 16-35): Organic BENEFICIAL
- Clean Fifteen (ranks 1-15): Conventional OK

Data loaded from: data/flags/ewg_lists.csv
Source: https://www.ewg.org/foodnews/full-list.php
Refresh Schedule: Annual (March/April when EWG releases new list)
"""

import csv
from pathlib import Path

# Data file path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
EWG_CSV_PATH = DATA_DIR / "flags" / "ewg_lists.csv"

# Cache for loaded data
_ewg_data = None
_dirty_dozen_items = None
_clean_fifteen_items = None
_middle_items = None


def _load_ewg_data() -> list[dict]:
    """Load EWG data from CSV file."""
    global _ewg_data

    if _ewg_data is not None:
        return _ewg_data

    _ewg_data = []

    if not EWG_CSV_PATH.exists():
        # Fallback to hardcoded data if CSV doesn't exist
        return _get_fallback_data()

    with open(EWG_CSV_PATH, newline="", encoding="utf-8") as f:
        # Skip comment lines
        lines = [line for line in f if not line.startswith("#")]

    if not lines:
        return _get_fallback_data()

    reader = csv.DictReader(lines)
    for row in reader:
        _ewg_data.append({
            "rank": int(row.get("rank", 0)),
            "item": row.get("item", "").lower(),
            "list": row.get("list", ""),
            "pesticide_score": int(row.get("pesticide_residue_score", 50)),
            "organic_recommendation": row.get("organic_recommendation", ""),
            "notes": row.get("notes", ""),
            "source_url": row.get("source_url", ""),
        })

    return _ewg_data


def _get_fallback_data() -> list[dict]:
    """Fallback hardcoded EWG data if CSV not available."""
    return [
        {"rank": 1, "item": "strawberries", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 2, "item": "spinach", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 3, "item": "kale", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 4, "item": "grapes", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 5, "item": "peaches", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 6, "item": "pears", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 7, "item": "nectarines", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 8, "item": "apples", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 9, "item": "bell peppers", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 10, "item": "cherries", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 11, "item": "blueberries", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 12, "item": "green beans", "list": "dirty_dozen", "organic_recommendation": "required"},
        {"rank": 1, "item": "avocados", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 2, "item": "sweet corn", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 3, "item": "pineapple", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 4, "item": "onions", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 5, "item": "papaya", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 6, "item": "sweet peas (frozen)", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 7, "item": "asparagus", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 8, "item": "honeydew melon", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 9, "item": "kiwi", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 10, "item": "cabbage", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 11, "item": "watermelon", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 12, "item": "mushrooms", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 13, "item": "mangoes", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 14, "item": "sweet potatoes", "list": "clean_fifteen", "organic_recommendation": "optional"},
        {"rank": 15, "item": "carrots", "list": "clean_fifteen", "organic_recommendation": "optional"},
    ]


def _get_item_sets() -> tuple[set, set, set]:
    """Get sets of dirty dozen, clean fifteen, and middle items for quick lookup."""
    global _dirty_dozen_items, _clean_fifteen_items, _middle_items

    if _dirty_dozen_items is not None and _clean_fifteen_items is not None and _middle_items is not None:
        return _dirty_dozen_items, _clean_fifteen_items, _middle_items

    data = _load_ewg_data()
    _dirty_dozen_items = set()
    _clean_fifteen_items = set()
    _middle_items = set()

    for row in data:
        item = row["item"].lower()
        target_set = None

        if row["list"] == "dirty_dozen":
            target_set = _dirty_dozen_items
        elif row["list"] == "clean_fifteen":
            target_set = _clean_fifteen_items
        elif row["list"] == "middle":
            target_set = _middle_items

        if target_set is not None:
            target_set.add(item)
            # Add common variations
            if item.endswith("s"):
                target_set.add(item[:-1])  # singular
            else:
                target_set.add(item + "s")  # plural

    return _dirty_dozen_items, _clean_fifteen_items, _middle_items


# Build flat sets for backward compatibility
def _build_item_sets():
    dirty, clean, middle = _get_item_sets()
    return dirty, clean, middle


DIRTY_DOZEN_ITEMS, CLEAN_FIFTEEN_ITEMS, MIDDLE_ITEMS = _build_item_sets()


def is_dirty_dozen(product_name: str) -> bool:
    """
    Check if a product is on the EWG Dirty Dozen list.

    Args:
        product_name: Product name or category to check

    Returns:
        True if the product is on the Dirty Dozen list
    """
    dirty_items, _, _ = _get_item_sets()
    name_lower = product_name.lower()

    for item in dirty_items:
        if item in name_lower or name_lower in item:
            return True
    return False


def is_clean_fifteen(product_name: str) -> bool:
    """
    Check if a product is on the EWG Clean Fifteen list.

    Args:
        product_name: Product name or category to check

    Returns:
        True if the product is on the Clean Fifteen list
    """
    _, clean_items, _ = _get_item_sets()
    name_lower = product_name.lower()

    for item in clean_items:
        if item in name_lower or name_lower in item:
            return True
    return False


def is_middle(product_name: str) -> bool:
    """
    Check if a product is on the EWG Middle list (ranks 16-35).

    Args:
        product_name: Product name or category to check

    Returns:
        True if the product is on the Middle list
    """
    _, _, middle_items = _get_item_sets()
    name_lower = product_name.lower()

    for item in middle_items:
        if item in name_lower or name_lower in item:
            return True
    return False


def get_middle_rank(product_name: str) -> int | None:
    """
    Get the Middle list rank (16-35) for a product.

    Args:
        product_name: Product name or category to check

    Returns:
        Rank (16-35) if on Middle list, None otherwise
    """
    data = _load_ewg_data()
    name_lower = product_name.lower()

    for row in data:
        if row["list"] != "middle":
            continue
        item = row["item"].lower()
        if item in name_lower or name_lower in item:
            return row["rank"]
    return None


def get_dirty_dozen_rank(product_name: str) -> int | None:
    """
    Get the Dirty Dozen rank (1-12) for a product.

    Args:
        product_name: Product name or category to check

    Returns:
        Rank (1-12) if on Dirty Dozen, None otherwise
    """
    data = _load_ewg_data()
    name_lower = product_name.lower()

    for row in data:
        if row["list"] != "dirty_dozen":
            continue
        item = row["item"].lower()
        if item in name_lower or name_lower in item:
            return row["rank"]
    return None


def get_clean_fifteen_rank(product_name: str) -> int | None:
    """
    Get the Clean Fifteen rank (1-15) for a product.

    Args:
        product_name: Product name or category to check

    Returns:
        Rank (1-15) if on Clean Fifteen, None otherwise
    """
    data = _load_ewg_data()
    name_lower = product_name.lower()

    for row in data:
        if row["list"] != "clean_fifteen":
            continue
        item = row["item"].lower()
        if item in name_lower or name_lower in item:
            return row["rank"]
    return None


def get_ewg_classification(product_name: str) -> dict:
    """
    Get full EWG classification for a product.

    Args:
        product_name: Product name or category to check

    Returns:
        Dict with classification info:
        {
            "is_dirty_dozen": bool,
            "is_clean_fifteen": bool,
            "is_middle": bool,
            "rank": int or None,
            "list": "dirty_dozen" | "clean_fifteen" | "middle" | "unknown",
            "pesticide_score": int or None,
            "organic_required": bool,  # True if dirty dozen
            "organic_beneficial": bool, # True if middle
            "organic_optional": bool,  # True if clean fifteen
        }
    """
    data = _load_ewg_data()
    name_lower = product_name.lower().strip()

    # Priority matching: exact > word-boundary > substring
    # This prevents "apple" matching "pineapple" or "potato" matching "sweet potato"
    best_match = None
    best_priority = 999  # lower is better

    for row in data:
        item = row["item"].lower()

        # Priority 0: Exact match
        if name_lower == item or name_lower + "s" == item or name_lower == item + "s":
            best_match = row
            best_priority = 0
            break  # Can't do better than exact

        # Priority 1: Query is a word within the item (e.g., "kale" in "kale collard and mustard greens")
        item_words = item.replace(",", " ").replace(" and ", " ").split()
        name_words = name_lower.replace(",", " ").replace(" and ", " ").split()

        if any(nw in item_words for nw in name_words):
            if best_priority > 1:
                best_match = row
                best_priority = 1
            continue

        # Priority 2: Item is a word within the query (e.g., "organic spinach" contains "spinach")
        if any(iw in name_words for iw in item_words):
            if best_priority > 2:
                best_match = row
                best_priority = 2
            continue

        # Priority 3: Substring match (only if no ambiguity)
        if (name_lower in item or item in name_lower) and len(name_lower) > 3:
            if best_priority > 3:
                best_match = row
                best_priority = 3

    if best_match:
        list_type = best_match["list"]
        return {
            "is_dirty_dozen": list_type == "dirty_dozen",
            "is_clean_fifteen": list_type == "clean_fifteen",
            "is_middle": list_type == "middle",
            "rank": best_match["rank"],
            "list": list_type,
            "pesticide_score": best_match.get("pesticide_score"),
            "organic_required": list_type == "dirty_dozen",
            "organic_beneficial": list_type == "middle",
            "organic_optional": list_type == "clean_fifteen",
        }

    # Not found on any list
    return {
        "is_dirty_dozen": False,
        "is_clean_fifteen": False,
        "is_middle": False,
        "rank": None,
        "list": "unknown",
        "pesticide_score": None,
        "organic_required": False,
        "organic_beneficial": False,
        "organic_optional": False,
    }


def get_ewg_data_info() -> dict:
    """
    Get metadata about the EWG data source.

    Returns:
        Dict with source info for transparency
    """
    data = _load_ewg_data()
    dirty_count = sum(1 for r in data if r["list"] == "dirty_dozen")
    clean_count = sum(1 for r in data if r["list"] == "clean_fifteen")
    middle_count = sum(1 for r in data if r["list"] == "middle")

    return {
        "source": "Environmental Working Group (EWG)",
        "url": "https://www.ewg.org/foodnews/full-list.php",
        "data_file": str(EWG_CSV_PATH),
        "total_items": len(data),
        "dirty_dozen_count": dirty_count,
        "middle_count": middle_count,
        "clean_fifteen_count": clean_count,
        "version": "2025",
        "refresh_schedule": "Annual (March/April)",
        "trust_level": "Research Non-profit",
    }


def reload_ewg_data():
    """Force reload of EWG data from CSV (useful after updates)."""
    global _ewg_data, _dirty_dozen_items, _clean_fifteen_items, _middle_items
    _ewg_data = None
    _dirty_dozen_items = None
    _clean_fifteen_items = None
    _middle_items = None
    _load_ewg_data()
