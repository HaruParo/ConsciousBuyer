"""
Component-based scoring system for Conscious Cart.

Replaces "organic always wins" with EWG-aware, context-sensitive scoring.
Each component contributes to final score (0-100, higher is better).
"""

from typing import Dict, Optional, Tuple
from src.data.ewg_categories import get_ewg_category
from src.data.ingredient_categories import get_ingredient_category, detect_product_form, get_form_compatibility_score


def compute_ewg_component(
    ingredient_name: str,
    ingredient_category: str,
    is_organic: bool
) -> int:
    """
    EWG-aware organic scoring.

    Returns:
        Dirty Dozen produce: organic +18, conventional -12
        Clean Fifteen: organic +2, conventional 0
        Middle category: organic +8, conventional 0
        Non-produce: organic +2, conventional 0
    """
    if ingredient_category != "produce":
        # Non-produce: organic is minor benefit
        return 2 if is_organic else 0

    ewg_cat = get_ewg_category(ingredient_name)

    if ewg_cat == "dirty_dozen":
        return 18 if is_organic else -12  # Strong preference for organic

    if ewg_cat == "clean_fifteen":
        return 2 if is_organic else 0  # Organic optional

    if ewg_cat == "middle":
        return 8 if is_organic else 0  # Wash/peel recommended

    # Default non-produce
    return 2 if is_organic else 0


def compute_form_fit_component(
    required_form: Optional[str],
    product_title: str,
    ingredient_category: str
) -> int:
    """
    Form compatibility scoring.

    Returns:
        0-14 points based on form match quality
        Incompatible forms should be filtered before scoring
    """
    product_form = detect_product_form(product_title, ingredient_category)
    compat_score = get_form_compatibility_score(required_form, product_form)

    if compat_score >= 999:
        # Incompatible - should have been filtered
        return 0

    if compat_score == 0:
        return 14  # Perfect match

    if compat_score <= 2:
        return 10  # Acceptable

    if compat_score <= 5:
        return 6  # Neutral

    # Minor mismatch
    return 2


def compute_packaging_component(product_title: str, packaging_data: str = "") -> int:
    """
    Packaging scoring using structured data (preferred) or title fallback.

    Returns:
        Loose/paper: +6
        Glass jar: +4
        Plastic bag: +2
        Metal can: +1
        Plastic clamshell: -4
        Unknown: 0
    """
    # Prefer structured packaging data if available
    if packaging_data:
        packaging_lower = packaging_data.lower()

        # Best: Loose, bulk, or paper
        if any(kw in packaging_lower for kw in ["loose", "bulk", "paper bag", "paper"]):
            return 6

        # Good: Glass (sustainable, recyclable)
        if any(kw in packaging_lower for kw in ["glass jar", "glass"]):
            return 4

        # Acceptable: Plastic bags, cartons
        if any(kw in packaging_lower for kw in ["bag", "pouch", "carton", "gable-top"]):
            return 2

        # Neutral: Metal cans
        if any(kw in packaging_lower for kw in ["can", "aluminum", "metal"]):
            return 1

        # Bad: Plastic clamshells, foam trays
        if any(kw in packaging_lower for kw in ["clamshell", "plastic container", "tray", "foam"]):
            return -4

        # If we have packaging data but no match, neutral
        return 0

    # Fallback: Parse from title (legacy)
    title_lower = product_title.lower()

    if any(kw in title_lower for kw in ["loose", "bulk", "paper bag", "paper"]):
        return 6

    if any(kw in title_lower for kw in ["glass jar", "glass", "jar"]):
        return 4

    if any(kw in title_lower for kw in ["can", "canned", "tinned"]):
        return 1

    if any(kw in title_lower for kw in ["clamshell", "plastic container", "tray"]):
        return -4

    if any(kw in title_lower for kw in ["bag", "pouch"]):
        return 2

    # Unknown packaging
    return 0


def compute_delivery_component(
    delivery_estimate: str,
    prompt: str
) -> int:
    """
    Delivery timing scoring based on user intent.

    Determines intent from prompt:
        - "tonight/tomorrow/this week" → cook_soon
        - "pantry restock/bulk/stock up" → pantry
        - Default: cook_soon

    Returns:
        Long delivery (1-2 weeks) + cook_soon intent: -10
        Otherwise: 0
    """
    prompt_lower = prompt.lower()

    # Determine intent
    cook_soon_keywords = ["tonight", "tomorrow", "this week", "for dinner", "quick meal"]
    pantry_keywords = ["pantry", "restock", "bulk", "stock up"]

    is_cook_soon = any(kw in prompt_lower for kw in cook_soon_keywords)
    is_pantry = any(kw in prompt_lower for kw in pantry_keywords)

    # Default to cook_soon if ambiguous
    if not is_pantry:
        is_cook_soon = True

    # Check delivery estimate
    estimate_lower = delivery_estimate.lower()
    is_long_delivery = any(kw in estimate_lower for kw in ["1-2 weeks", "2 weeks", "7-14 days", "specialty"])

    if is_long_delivery and is_cook_soon:
        return -10  # Penalty for slow delivery when cooking soon

    return 0


def compute_unit_value_component(
    unit_price: float,
    all_unit_prices: list[float]
) -> int:
    """
    Relative unit value scoring.

    Compares unit price among candidates for the same ingredient.

    Returns:
        Best value per unit (lowest $/oz): +8
        Median value: +4
        Higher $/oz: 0
    """
    if not all_unit_prices or len(all_unit_prices) < 2:
        return 4  # Neutral if no comparison

    sorted_prices = sorted(all_unit_prices)
    q1 = sorted_prices[len(sorted_prices) // 4]
    median = sorted_prices[len(sorted_prices) // 2]

    if unit_price <= q1:
        return 8  # Best value

    if unit_price <= median:
        return 4  # Median value

    return 0  # Expensive


def compute_total_score(
    ingredient_name: str,
    ingredient_category: str,
    required_form: Optional[str],
    product_title: str,
    is_organic: bool,
    unit_price: float,
    all_unit_prices: list[float],
    delivery_estimate: str,
    prompt: str,
    price_outlier_penalty: int = 0,
    packaging_data: str = ""
) -> Tuple[int, Dict[str, int]]:
    """
    Compute total score with component breakdown.

    Returns:
        (total_score, component_breakdown)

    Component breakdown:
        - ewg: 0-18 points (EWG Dirty Dozen/Clean Fifteen guidance)
        - form_fit: 0-14 points (fresh vs powder vs seeds match quality)
        - packaging: -4 to +6 points (loose/glass vs plastic)
        - delivery: -10 to 0 points (fast delivery bonus for cook_soon prompts)
        - unit_value: 0-8 points (best value per unit among options)
        - outlier_penalty: -20 points (prevents premium-only selections)

    Base score: 50
    Total range: ~20-100
    """
    base_score = 50

    ewg = compute_ewg_component(ingredient_name, ingredient_category, is_organic)
    form_fit = compute_form_fit_component(required_form, product_title, ingredient_category)
    packaging = compute_packaging_component(product_title, packaging_data)
    delivery = compute_delivery_component(delivery_estimate, prompt)
    unit_value = compute_unit_value_component(unit_price, all_unit_prices)

    # Outlier penalty
    outlier = -20 if price_outlier_penalty > 0 else 0

    total = base_score + ewg + form_fit + packaging + delivery + unit_value + outlier

    # Clamp to 0-100
    total = max(0, min(100, total))

    breakdown = {
        "base": base_score,
        "ewg": ewg,
        "form_fit": form_fit,
        "packaging": packaging,
        "delivery": delivery,
        "unit_value": unit_value,
        "outlier_penalty": outlier
    }

    return total, breakdown


def compute_score_drivers(
    winner_breakdown: Dict[str, int],
    runner_up_breakdown: Dict[str, int]
) -> list[Dict[str, any]]:
    """
    Compute top 2 drivers explaining why winner won.

    Returns list of drivers sorted by delta descending.
    Each driver: {"rule": str, "delta": int}
    """
    drivers = []

    # Component labels
    labels = {
        "ewg": "EWG guidance",
        "form_fit": "Better form match",
        "packaging": "Lower plastic packaging",
        "delivery": "Faster delivery",
        "unit_value": "Better value per unit",
        "outlier_penalty": "Price sanity"
    }

    for key, label in labels.items():
        winner_val = winner_breakdown.get(key, 0)
        runner_up_val = runner_up_breakdown.get(key, 0)
        delta = winner_val - runner_up_val

        if delta > 0:
            drivers.append({"rule": label, "delta": delta})

    # Sort by delta descending, take top 2
    drivers.sort(key=lambda d: d["delta"], reverse=True)
    return drivers[:2]
