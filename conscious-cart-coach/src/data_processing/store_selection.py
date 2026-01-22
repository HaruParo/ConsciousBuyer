"""
Store selection module.
Selects the best store based on inventory matching user request categories.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Store inventory data: which categories each store carries
# This represents the available inventory at each store
STORE_INVENTORY = {
    "FreshDirect": {
        "name": "FreshDirect",
        "location": "Serving Woodbridge Township, NJ",
        "categories": {
            # Produce
            "produce_greens", "produce_onions", "produce_roots", "produce_tomatoes",
            "produce_peppers", "produce_squash", "produce_beans", "produce_cucumbers",
            "produce_mushrooms", "produce_aromatics",
            # Fruits
            "fruit_tropical", "fruit_berries", "fruit_citrus", "fruit_other",
            # Dairy
            "milk", "yogurt", "cheese", "eggs", "butter_ghee", "ice_cream",
            # Proteins
            "chicken", "meat_other", "tofu",
            # Japanese/Asian specialty
            "miso_paste", "seaweed", "dashi",
            # Pantry
            "grains", "bread", "oils_olive", "oils_coconut", "oils_other",
            "vinegar", "spices", "canned_coconut", "canned_beans",
            "nuts_almonds", "nuts_cashews", "nuts_peanuts", "nuts_other",
            "hummus_dips", "chocolate", "cookies_crackers", "chips", "tea",
        },
        "priority": 1,  # Primary store
    },
    "Whole Foods": {
        "name": "Whole Foods Market",
        "location": "Edison, NJ (5.2 mi)",
        "categories": {
            # Strong in organics and specialty
            "produce_greens", "produce_onions", "produce_tomatoes", "produce_peppers",
            "produce_squash", "produce_beans", "produce_aromatics",
            "fruit_tropical", "fruit_berries", "fruit_citrus",
            "milk", "yogurt", "cheese", "eggs", "butter_ghee",
            "tofu", "grains", "bread", "oils_olive",
            # Japanese/Asian specialty (Whole Foods has good selection)
            "miso_paste", "seaweed", "dashi",
            "hummus_dips", "nuts_almonds", "nuts_cashews",
        },
        "priority": 2,
    },
    "Trader Joes": {
        "name": "Trader Joe's",
        "location": "Woodbridge, NJ (2.1 mi)",
        "categories": {
            # Good variety, limited organics
            "produce_greens", "produce_onions", "produce_tomatoes",
            "fruit_tropical", "fruit_berries",
            "milk", "yogurt", "cheese", "eggs", "butter_ghee",
            "miso_paste", "tofu",  # Has miso and tofu
            "grains", "bread", "oils_olive", "spices",
            "hummus_dips", "chocolate", "chips", "nuts_almonds",
            # Limited Asian specialty
            "seaweed",  # Has some seaweed snacks
        },
        "priority": 3,
    },
    "ShopRite": {
        "name": "ShopRite",
        "location": "Iselin, NJ (1.3 mi)",
        "categories": {
            # Broad but conventional focus
            "produce_greens", "produce_onions", "produce_roots", "produce_tomatoes",
            "produce_peppers", "produce_squash", "produce_beans",
            "fruit_tropical", "fruit_berries", "fruit_citrus", "fruit_other",
            "milk", "yogurt", "cheese", "eggs", "butter_ghee",
            "chicken", "meat_other", "tofu",  # Basic tofu
            "grains", "bread", "oils_olive", "oils_other", "vinegar", "spices",
            "canned_coconut", "canned_beans", "chips",
            # Limited Asian - may have basic miso
            "miso_paste",
        },
        "priority": 4,
    },
    "H Mart": {
        "name": "H Mart",
        "location": "Edison, NJ (4.8 mi)",
        "categories": {
            # Asian specialty supermarket - best for miso soup ingredients
            "produce_greens", "produce_onions", "produce_aromatics", "produce_mushrooms",
            "fruit_tropical", "fruit_citrus",
            "eggs",
            # Excellent Asian specialty selection
            "miso_paste", "tofu", "seaweed", "dashi",
            "grains", "oils_other", "vinegar", "spices",
            # Asian pantry
            "canned_coconut", "tea",
        },
        "priority": 5,  # Specialty store
    },
}


def count_matching_categories(store_categories: set, requested_categories: list) -> int:
    """
    Count how many requested categories the store has.

    Args:
        store_categories: Set of categories the store carries
        requested_categories: List of categories from user request

    Returns:
        Number of matching categories
    """
    return len(set(requested_categories) & store_categories)


def select_best_store(
    requested_categories: list[str],
    available_stores: dict = None,
) -> tuple[str, dict]:
    """
    Select the store with the most matching inventory for the request.

    Args:
        requested_categories: List of category names from user request
        available_stores: Optional dict of stores to consider (defaults to STORE_INVENTORY)

    Returns:
        Tuple of (store_key, store_info_dict)
    """
    if available_stores is None:
        available_stores = STORE_INVENTORY

    if not requested_categories:
        # Default to primary store if no categories
        logger.warning("No categories provided, defaulting to FreshDirect")
        return "FreshDirect", available_stores.get("FreshDirect", {})

    # Score each store by matching categories
    store_scores = []
    for store_key, store_info in available_stores.items():
        store_categories = store_info.get("categories", set())
        match_count = count_matching_categories(store_categories, requested_categories)
        match_percentage = (match_count / len(requested_categories)) * 100 if requested_categories else 0
        priority = store_info.get("priority", 99)

        store_scores.append({
            "key": store_key,
            "info": store_info,
            "match_count": match_count,
            "match_percentage": match_percentage,
            "priority": priority,
        })

        logger.debug(
            f"Store '{store_key}': {match_count}/{len(requested_categories)} categories "
            f"({match_percentage:.0f}% match)"
        )

    # Sort by match_count (descending), then by priority (ascending) for ties
    store_scores.sort(key=lambda x: (-x["match_count"], x["priority"]))

    best_store = store_scores[0]
    logger.info(
        f"Selected store: {best_store['info']['name']} with "
        f"{best_store['match_count']}/{len(requested_categories)} matching categories "
        f"({best_store['match_percentage']:.0f}% match)"
    )

    return best_store["key"], best_store["info"]


def get_store_selection_summary(
    store_info: dict,
    requested_categories: list[str],
) -> dict:
    """
    Generate a summary of the store selection for display.

    Args:
        store_info: Selected store info dict
        requested_categories: List of requested categories

    Returns:
        Summary dict with display information
    """
    store_categories = store_info.get("categories", set())
    match_count = count_matching_categories(store_categories, requested_categories)
    total_requested = len(requested_categories)
    match_percentage = (match_count / total_requested) * 100 if total_requested else 0

    # Find missing categories
    missing = set(requested_categories) - store_categories
    available = set(requested_categories) & store_categories

    return {
        "store_name": store_info.get("name", "Unknown"),
        "location": store_info.get("location", ""),
        "match_count": match_count,
        "total_requested": total_requested,
        "match_percentage": match_percentage,
        "available_categories": list(available),
        "missing_categories": list(missing),
        "has_full_inventory": match_count == total_requested,
    }


def get_all_stores_comparison(
    requested_categories: list[str],
    available_stores: dict = None,
) -> list[dict]:
    """
    Get comparison of all stores for the requested categories.

    Args:
        requested_categories: List of category names from user request
        available_stores: Optional dict of stores to consider (defaults to STORE_INVENTORY)

    Returns:
        List of store summaries sorted by match count (descending)
    """
    if available_stores is None:
        available_stores = STORE_INVENTORY

    if not requested_categories:
        return []

    store_summaries = []
    for store_key, store_info in available_stores.items():
        summary = get_store_selection_summary(store_info, requested_categories)
        summary["store_key"] = store_key
        store_summaries.append(summary)

    # Sort by match_count descending, then by priority
    store_summaries.sort(
        key=lambda x: (-x["match_count"], available_stores.get(x["store_key"], {}).get("priority", 99))
    )

    return store_summaries
