"""
Rules module for tier selection logic.
Applies user priorities to select recommended product tiers.

This module is fully deterministic - same input always produces same output.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Packaging material scores (higher = better for environment)
PACKAGING_SCORES = {
    # Excellent - reusable/recyclable
    "glass": 10,
    "metal": 10,
    "aluminum": 10,
    # Good - recyclable/biodegradable
    "paper": 8,
    "cardboard": 8,
    "carton": 7,
    # Moderate - some recyclability
    "minimal plastic": 6,
    "recyclable plastic": 5,
    "bioplastic": 5,
    # Poor - difficult to recycle
    "plastic": 3,
    "mixed materials": 3,
    "polystyrene": 1,
    "styrofoam": 1,
}

# Default score for unknown packaging
DEFAULT_PACKAGING_SCORE = 4

# Price threshold for "cheap" baseline (below this, no need to go cheaper)
CHEAP_THRESHOLD = 3.00


def score_packaging(packaging_str: str) -> int:
    """
    Score packaging based on material sustainability.

    Args:
        packaging_str: Packaging description string (e.g., "glass jar", "plastic bag")

    Returns:
        Integer score (1-10, higher = more sustainable)
    """
    if not packaging_str:
        return DEFAULT_PACKAGING_SCORE

    packaging_lower = packaging_str.lower()

    # Check for each material keyword, collect all matches
    matched_scores = []
    for material, score in PACKAGING_SCORES.items():
        if material in packaging_lower:
            matched_scores.append(score)

    if not matched_scores:
        return DEFAULT_PACKAGING_SCORE

    # If we have mixed materials, return the best score
    # (assumption: if glass + plastic, the main container is glass)
    return max(matched_scores)


def score_tier_packaging(tier_data: dict) -> int:
    """
    Score a tier's packaging from its data.

    Checks both simple packaging string and detailed packaging_details.

    Args:
        tier_data: Tier data dict with packaging info

    Returns:
        Integer score (1-10)
    """
    if not tier_data:
        return DEFAULT_PACKAGING_SCORE

    # Try detailed packaging first (from Open Food Facts)
    packaging_details = tier_data.get("packaging_details", {})
    if packaging_details:
        rating = packaging_details.get("packaging_rating")
        if rating == "good":
            return 10
        elif rating == "mixed":
            return 6
        elif rating == "poor":
            return 3

        # Check materials list
        materials = packaging_details.get("materials", [])
        if materials:
            scores = [PACKAGING_SCORES.get(m.lower(), DEFAULT_PACKAGING_SCORE) for m in materials]
            return max(scores) if scores else DEFAULT_PACKAGING_SCORE

    # Fall back to packaging string
    return score_packaging(tier_data.get("packaging", ""))


def has_certifications(tier_data: dict) -> bool:
    """
    Check if a tier has health/quality certifications.

    Args:
        tier_data: Tier data dict

    Returns:
        True if tier has relevant certifications
    """
    if not tier_data:
        return False

    certifications = tier_data.get("certifications", [])
    if isinstance(certifications, str):
        certifications = [c.strip() for c in certifications.split(",") if c.strip()]

    # Check for health-related certifications
    health_keywords = ["organic", "non-gmo", "usda", "fair trade", "certified", "natural"]
    for cert in certifications:
        cert_lower = cert.lower()
        if any(keyword in cert_lower for keyword in health_keywords):
            return True

    return False


def get_tier_price(tier_data: dict) -> Optional[float]:
    """
    Extract price from tier data.

    Args:
        tier_data: Tier data dict

    Returns:
        Price as float or None if not available
    """
    if not tier_data:
        return None

    price = tier_data.get("est_price")
    if price is not None:
        return float(price)

    return None


def select_tier_for_item(
    item: dict,
    user_context: dict,
) -> dict:
    """
    Select the recommended tier for a single item based on user priorities.

    Decision logic (in priority order):
    1. If budget_priority == "high": prefer cheaper (unless baseline already cheap)
    2. If packaging_priority == "high": prefer tier with best packaging score
    3. If health_priority == "high": prefer conscious (for certifications)
    4. Default: balanced tier

    Args:
        item: Item dict with category, baseline, alternatives, flags
        user_context: User priorities dict

    Returns:
        Result dict with recommended_tier, reasoning_points, all_tiers
    """
    category = item.get("category", "unknown")
    baseline = item.get("baseline") or {}
    alternatives = item.get("alternatives") or {}

    # Extract priorities (default to "medium")
    budget_priority = user_context.get("budget_priority", "medium")
    packaging_priority = user_context.get("packaging_priority", "medium")
    health_priority = user_context.get("health_priority", "medium")

    # Get available tiers
    cheaper = alternatives.get("cheaper")
    balanced = alternatives.get("balanced")
    conscious = alternatives.get("conscious")

    # Default to balanced
    recommended_tier = "balanced"
    reasoning_points = []

    # Get baseline price for reference
    baseline_price = baseline.get("price")

    # Rule 1: High budget priority -> cheaper tier
    if budget_priority == "high":
        if baseline_price is not None and baseline_price <= CHEAP_THRESHOLD:
            # Baseline is already cheap, stay balanced
            recommended_tier = "balanced"
            reasoning_points.append(f"Your usual is already budget-friendly (${baseline_price:.2f})")
        elif cheaper:
            recommended_tier = "cheaper"
            cheaper_price = get_tier_price(cheaper)
            if cheaper_price:
                reasoning_points.append(f"Budget priority: cheaper option at ${cheaper_price:.2f}")
            else:
                reasoning_points.append("Budget priority: selecting cheaper option")

    # Rule 2: High packaging priority -> best packaging tier
    elif packaging_priority == "high":
        tier_scores = {}
        if cheaper:
            tier_scores["cheaper"] = score_tier_packaging(cheaper)
        if balanced:
            tier_scores["balanced"] = score_tier_packaging(balanced)
        if conscious:
            tier_scores["conscious"] = score_tier_packaging(conscious)

        if tier_scores:
            # Select tier with highest packaging score
            # In case of tie, prefer in order: conscious > balanced > cheaper
            best_tier = max(
                tier_scores.keys(),
                key=lambda t: (tier_scores[t], {"conscious": 3, "balanced": 2, "cheaper": 1}.get(t, 0))
            )
            recommended_tier = best_tier
            best_score = tier_scores[best_tier]

            # Get packaging description for reasoning
            tier_data = alternatives.get(best_tier, {})
            packaging = tier_data.get("packaging", "")
            if packaging:
                reasoning_points.append(f"Best packaging: {packaging} (score {best_score}/10)")
            else:
                reasoning_points.append(f"Best packaging score: {best_score}/10")

    # Rule 3: High health priority -> conscious tier (for certifications)
    elif health_priority == "high":
        if conscious and has_certifications(conscious):
            recommended_tier = "conscious"
            certs = conscious.get("certifications", [])
            if isinstance(certs, list) and certs:
                reasoning_points.append(f"Health priority: {', '.join(certs[:2])}")
            else:
                reasoning_points.append("Health priority: certified/organic option")
        elif conscious:
            # Conscious exists but no certifications, still prefer it
            recommended_tier = "conscious"
            reasoning_points.append("Health priority: premium quality option")
        else:
            # No conscious tier, stay balanced
            recommended_tier = "balanced"
            reasoning_points.append("Health priority noted, balanced tier recommended")

    # Rule 4: Default (all medium) -> balanced tier
    else:
        recommended_tier = "balanced"
        reasoning_points.append("Your usual choice")

    # Add additional reasoning based on selected tier
    selected_tier_data = alternatives.get(recommended_tier, {})

    # Add packaging info if relevant
    if packaging_priority in ("medium", "high"):
        packaging = selected_tier_data.get("packaging", "")
        if packaging and "packaging" not in str(reasoning_points).lower():
            score = score_tier_packaging(selected_tier_data)
            reasoning_points.append(f"Packaging: {packaging}")

    # Add price info if relevant
    if budget_priority in ("medium", "high"):
        price = get_tier_price(selected_tier_data)
        if price and "price" not in str(reasoning_points).lower() and "$" not in str(reasoning_points):
            reasoning_points.append(f"Price: ${price:.2f}")

    # Add baseline comparison
    if baseline.get("your_usual") and baseline.get("brand"):
        if recommended_tier == "balanced":
            reasoning_points.append(f"Similar to your usual: {baseline.get('brand')}")

    return {
        "category": category,
        "recommended_tier": recommended_tier,
        "reasoning_points": reasoning_points,
        "all_tiers": {
            "cheaper": cheaper,
            "balanced": balanced,
            "conscious": conscious,
        },
    }


def apply_rules(facts_pack: dict) -> dict:
    """
    Apply tier selection rules to a facts pack.

    This function is fully deterministic - same input always gives same output.

    Args:
        facts_pack: Facts pack from generate_facts_pack()

    Returns:
        Dict with recommendations for each item:
        {
            "request": "original request",
            "recommendations": [
                {
                    "category": "miso_paste",
                    "recommended_tier": "balanced",
                    "reasoning_points": [...],
                    "all_tiers": {...}
                },
                ...
            ],
            "user_context": {...}
        }
    """
    user_context = facts_pack.get("user_context", {})
    items = facts_pack.get("items", [])

    recommendations = []
    for item in items:
        recommendation = select_tier_for_item(item, user_context)
        recommendations.append(recommendation)

    return {
        "request": facts_pack.get("request", ""),
        "recommendations": recommendations,
        "user_context": user_context,
    }
