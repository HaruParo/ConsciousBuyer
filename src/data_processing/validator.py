"""
LLM output validator module.
Validates decision outputs from LLM against facts_pack data to detect hallucinations.
"""

import re
from typing import Optional

from src.data_processing.seasonal_regional import filter_recalls_by_region


VALID_TIERS = {"cheaper", "balanced", "conscious"}

# EWG Dirty Dozen 2025 - these items should be organic, especially at cheaper tier
# High pesticide residue items where organic matters most
DIRTY_DOZEN = {
    "strawberries", "strawberry",
    "spinach",
    "kale", "collard greens", "collards", "mustard greens",
    "grapes", "grape",
    "peaches", "peach",
    "pears", "pear",
    "nectarines", "nectarine",
    "apples", "apple",
    "bell peppers", "bell pepper", "hot peppers", "hot pepper", "peppers", "pepper",
    "cherries", "cherry",
    "blueberries", "blueberry",
    "green beans", "green bean",
}

# EWG Clean Fifteen 2025 - conventional is acceptable
CLEAN_FIFTEEN = {
    "avocados", "avocado",
    "sweet corn", "corn",
    "pineapple", "pineapples",
    "onions", "onion",
    "papaya", "papayas",
    "sweet peas", "peas",
    "asparagus",
    "honeydew melon", "honeydew",
    "kiwi", "kiwis",
    "cabbage",
    "watermelon",
    "mushrooms", "mushroom",
    "mangoes", "mango",
    "sweet potatoes", "sweet potato",
    "carrots", "carrot",
}


def extract_prices_from_text(text: str) -> list[float]:
    """
    Extract all dollar amounts from text.

    Args:
        text: Text to search for prices

    Returns:
        List of float prices found
    """
    pattern = r'\$(\d+(?:\.\d{1,2})?)'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches]


def extract_brands_from_facts_pack(facts_pack: dict) -> set[str]:
    """
    Extract all brand names from facts_pack.

    Args:
        facts_pack: The facts pack dictionary

    Returns:
        Set of brand names (lowercase for comparison)
    """
    brands = set()

    for item in facts_pack.get("items", []):
        # Get brands from alternatives
        alternatives = item.get("alternatives") or {}
        for tier_data in alternatives.values():
            if isinstance(tier_data, dict):
                brand = tier_data.get("brand", "")
                if brand:
                    brands.add(brand.lower())

        # Get brand from baseline if present
        baseline = item.get("baseline") or {}
        if baseline:
            brand = baseline.get("brand", "")
            if brand:
                brands.add(brand.lower())

    return brands


def extract_prices_from_facts_pack(facts_pack: dict) -> list[float]:
    """
    Extract all prices from facts_pack.

    Args:
        facts_pack: The facts pack dictionary

    Returns:
        List of prices found
    """
    prices = []

    for item in facts_pack.get("items", []):
        # Get prices from alternatives
        alternatives = item.get("alternatives") or {}
        for tier_data in alternatives.values():
            if isinstance(tier_data, dict):
                price = tier_data.get("est_price")
                if price is not None:
                    prices.append(float(price))

        # Get price from baseline if present
        baseline = item.get("baseline") or {}
        if baseline:
            price = baseline.get("price")
            if price is not None:
                prices.append(float(price))

    return prices


def extract_packaging_from_facts_pack(facts_pack: dict) -> set[str]:
    """
    Extract all packaging types from facts_pack.

    Args:
        facts_pack: The facts pack dictionary

    Returns:
        Set of packaging types (lowercase for comparison)
    """
    packaging_types = set()

    for item in facts_pack.get("items", []):
        alternatives = item.get("alternatives") or {}
        for tier_data in alternatives.values():
            if isinstance(tier_data, dict):
                packaging = tier_data.get("packaging", "")
                if packaging:
                    packaging_types.add(packaging.lower())

        baseline = item.get("baseline") or {}
        if baseline:
            packaging = baseline.get("packaging", "")
            if packaging:
                packaging_types.add(packaging.lower())

    return packaging_types


def extract_certifications_from_facts_pack(facts_pack: dict) -> set[str]:
    """
    Extract all certifications from facts_pack.

    Args:
        facts_pack: The facts pack dictionary

    Returns:
        Set of certifications (lowercase for comparison)
    """
    certifications = set()

    for item in facts_pack.get("items", []):
        alternatives = item.get("alternatives") or {}
        for tier_data in alternatives.values():
            if isinstance(tier_data, dict):
                certs = tier_data.get("certifications", [])
                for cert in certs:
                    if cert:
                        certifications.add(cert.lower())

    return certifications


def is_dirty_dozen_item(category: str) -> bool:
    """
    Check if a category is a Dirty Dozen item.

    Args:
        category: Category name to check

    Returns:
        True if the category matches a Dirty Dozen item
    """
    category_lower = category.lower().replace("_", " ")
    for item in DIRTY_DOZEN:
        if item in category_lower or category_lower in item:
            return True
    return False


def is_clean_fifteen_item(category: str) -> bool:
    """
    Check if a category is a Clean Fifteen item.

    Args:
        category: Category name to check

    Returns:
        True if the category matches a Clean Fifteen item
    """
    category_lower = category.lower().replace("_", " ")
    for item in CLEAN_FIFTEEN:
        if item in category_lower or category_lower in item:
            return True
    return False


def check_tier_has_organic(tier_data: dict) -> bool:
    """
    Check if a tier option has organic certification.

    Args:
        tier_data: Tier data dictionary with certifications

    Returns:
        True if tier has organic certification
    """
    certifications = tier_data.get("certifications", [])
    for cert in certifications:
        if "organic" in cert.lower():
            return True

    # Also check product name and brand for organic
    product_name = tier_data.get("product_name", "").lower()
    brand = tier_data.get("brand", "").lower()
    if "organic" in product_name or "organic" in brand:
        return True

    return False


def get_categories_from_facts_pack(facts_pack: dict) -> list[str]:
    """
    Extract all categories from facts_pack.

    Args:
        facts_pack: The facts pack dictionary

    Returns:
        List of category names
    """
    categories = []
    for item in facts_pack.get("items", []):
        category = item.get("category", "")
        if category:
            categories.append(category)
    return categories


def check_dirty_dozen_tier_compliance(
    recommended_tier: str,
    facts_pack: dict
) -> list[str]:
    """
    Check if Dirty Dozen items at cheaper tier are organic.

    For EWG Dirty Dozen items, recommending the "cheaper" tier
    is problematic if that tier is not organic.

    Args:
        recommended_tier: The recommended tier
        facts_pack: Facts pack with items and alternatives

    Returns:
        List of error messages for non-compliant recommendations
    """
    errors = []

    if recommended_tier != "cheaper":
        return errors

    for item in facts_pack.get("items", []):
        category = item.get("category", "")

        if not is_dirty_dozen_item(category):
            continue

        alternatives = item.get("alternatives") or {}
        cheaper_tier = alternatives.get("cheaper") or {}

        if not cheaper_tier:
            continue

        if not check_tier_has_organic(cheaper_tier):
            errors.append(
                f"EWG Dirty Dozen item '{category}' recommended at 'cheaper' tier "
                f"without organic certification - consider 'balanced' or 'conscious' tier"
            )

    return errors


def check_recall_compliance(
    recommended_tier: str,
    facts_pack: dict
) -> list[str]:
    """
    Check if recommended tier has active recalls in user's region.

    Args:
        recommended_tier: The recommended tier
        facts_pack: Facts pack with items, alternatives, flags, and user_context

    Returns:
        List of error messages for recalled products
    """
    errors = []

    # Get user location for regional filtering
    user_context = facts_pack.get("user_context", {})
    location = user_context.get("location", "")

    for item in facts_pack.get("items", []):
        category = item.get("category", "")
        flags = item.get("flags", [])

        # Filter to only recall flags
        recall_flags = [f for f in flags if "recall" in f.get("type", "").lower()]

        # Filter recalls by user's region if location is provided
        if location and recall_flags:
            recall_flags = filter_recalls_by_region(recall_flags, location)

        # Check if any remaining recall affects the recommended tier
        for flag in recall_flags:
            affected_tiers = flag.get("affected_tiers", [])
            affected_regions = flag.get("affected_regions", [])
            region_note = f" ({', '.join(affected_regions)})" if affected_regions else ""

            if affected_tiers and recommended_tier in affected_tiers:
                errors.append(
                    f"RECALL WARNING: '{category}' at '{recommended_tier}' tier "
                    f"has active recall{region_note} - {flag.get('description', 'see flags for details')}"
                )
            elif not affected_tiers:
                # If no specific tiers listed, it's a general category recall
                errors.append(
                    f"RECALL WARNING: '{category}' category has active recall{region_note} - "
                    f"{flag.get('description', 'verify product safety')}"
                )

    return errors


def price_matches_facts_pack(price: float, facts_pack_prices: list[float], tolerance: float = 0.50) -> bool:
    """
    Check if a price matches any price in facts_pack within tolerance.

    Args:
        price: Price to check
        facts_pack_prices: List of valid prices from facts_pack
        tolerance: Allowed difference (default $0.50)

    Returns:
        True if price matches within tolerance
    """
    for fp_price in facts_pack_prices:
        if abs(price - fp_price) <= tolerance:
            return True
    return False


def validate_decision(decision: dict, facts_pack: dict) -> tuple[bool, list[str]]:
    """
    Validate LLM decision output against facts_pack data.

    Checks:
    1. recommended_tier is valid ("cheaper", "balanced", or "conscious")
    2. reasoning references actual facts:
       - Price mentions must match facts_pack prices (±$0.50)
       - Brand mentions must be in facts_pack
       - Packaging mentions must match facts_pack
    3. No invented data:
       - No prices not in facts_pack
       - No brands not in facts_pack
       - No certifications not in facts_pack
    4. Reasoning is substantive (>20 characters)
    5. key_trade_off is present

    Args:
        decision: LLM decision dictionary with recommended_tier, reasoning, key_trade_off
        facts_pack: Facts pack dictionary with items containing alternatives and baseline

    Returns:
        Tuple of (is_valid, list of error messages)
        - (True, []) if valid
        - (False, ["error1", "error2"]) if invalid
    """
    errors = []

    # Check 1: Validate recommended_tier
    recommended_tier = decision.get("recommended_tier")
    if not recommended_tier:
        errors.append("missing recommended_tier")
    elif recommended_tier not in VALID_TIERS:
        errors.append(f"invalid recommended_tier '{recommended_tier}': must be one of {VALID_TIERS}")

    # Get reasoning for subsequent checks
    reasoning = decision.get("reasoning", "")

    # Check 4: Reasoning is substantive (>20 characters)
    if not reasoning:
        errors.append("missing reasoning")
    elif len(reasoning) <= 20:
        errors.append(f"reasoning too short ({len(reasoning)} chars): must be >20 characters")

    # Check 5: key_trade_off is present
    key_trade_off = decision.get("key_trade_off")
    if not key_trade_off:
        errors.append("missing key_trade_off")

    # Extract reference data from facts_pack
    facts_pack_prices = extract_prices_from_facts_pack(facts_pack)
    facts_pack_brands = extract_brands_from_facts_pack(facts_pack)
    facts_pack_packaging = extract_packaging_from_facts_pack(facts_pack)
    facts_pack_certifications = extract_certifications_from_facts_pack(facts_pack)

    # Check 2 & 3: Validate reasoning references actual facts
    if reasoning:
        # Check prices in reasoning
        mentioned_prices = extract_prices_from_text(reasoning)
        for price in mentioned_prices:
            if not price_matches_facts_pack(price, facts_pack_prices):
                errors.append(f"hallucinated price ${price:.2f}: not found in facts_pack (±$0.50 tolerance)")

        # Check brands in reasoning (look for brand mentions)
        reasoning_lower = reasoning.lower()

        # Extract potential brand mentions using word boundaries
        words_in_reasoning = set(re.findall(r'\b[a-zA-Z][a-zA-Z\s\-\'\.]+\b', reasoning_lower))

        # Check for certification mentions not in facts_pack
        common_certifications = {
            "usda organic", "organic", "fair trade", "non-gmo", "certified b corp",
            "rainforest alliance", "certified humane", "grass-fed", "pasture-raised",
            "cage-free", "free-range", "wild-caught", "msc certified"
        }
        for cert in common_certifications:
            if cert in reasoning_lower and cert not in facts_pack_certifications:
                # Check if any facts_pack cert is a partial match
                if not any(cert in fc or fc in cert for fc in facts_pack_certifications):
                    errors.append(f"hallucinated certification '{cert}': not found in facts_pack")

    # Check 6: EWG Dirty Dozen compliance
    if recommended_tier:
        dirty_dozen_errors = check_dirty_dozen_tier_compliance(recommended_tier, facts_pack)
        errors.extend(dirty_dozen_errors)

    # Check 7: Recall compliance
    if recommended_tier:
        recall_errors = check_recall_compliance(recommended_tier, facts_pack)
        errors.extend(recall_errors)

    return len(errors) == 0, errors
