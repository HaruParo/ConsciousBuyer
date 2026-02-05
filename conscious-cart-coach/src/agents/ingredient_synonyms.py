"""
Ingredient Synonym Detection and Deduplication

Maps ingredient variations to canonical forms to prevent duplicate cart items.
Example: "cilantro", "coriander leaves", "cilantros" → "cilantro"
"""

from typing import Dict, Set, List, Tuple
import re


# ============================================================================
# Synonym Groups (lowercase canonical form → all variations)
# ============================================================================

INGREDIENT_SYNONYMS: Dict[str, Set[str]] = {
    # Herbs
    "cilantro": {"cilantro", "cilantros", "coriander leaves", "coriander leaf", "fresh coriander", "chinese parsley"},
    "scallions": {"scallions", "scallion", "green onions", "green onion", "spring onions", "spring onion"},
    "parsley": {"parsley", "italian parsley", "flat-leaf parsley", "curly parsley"},

    # Legumes
    "chickpeas": {"chickpeas", "chickpea", "garbanzo beans", "garbanzo bean", "garbanzos", "chana"},

    # Produce
    "eggplant": {"eggplant", "eggplants", "aubergine", "aubergines", "brinjal"},
    "zucchini": {"zucchini", "zucchinis", "courgette", "courgettes"},
    "bell pepper": {"bell pepper", "bell peppers", "sweet pepper", "sweet peppers", "capsicum"},

    # Proteins
    "chicken thighs": {"chicken thighs", "chicken thigh", "thighs", "bone-in thighs", "boneless thighs"},
    "chicken breasts": {"chicken breasts", "chicken breast", "breasts", "bone-in breasts", "boneless breasts"},
    "chicken legs": {"chicken legs", "chicken leg", "drumsticks", "drumstick", "legs"},
    "ground beef": {"ground beef", "minced beef", "beef mince", "hamburger meat"},

    # Grains
    "basmati rice": {"basmati rice", "basmati", "long grain rice"},

    # Dairy
    "greek yogurt": {"greek yogurt", "greek yoghurt", "strained yogurt", "greek-style yogurt"},

    # Spices (different forms are NOT synonyms - handle separately)
    # "cumin seeds" and "cumin powder" should remain distinct
}


# ============================================================================
# Reverse Lookup: variation → canonical
# ============================================================================

def _build_reverse_map() -> Dict[str, str]:
    """Build reverse lookup: variation → canonical form"""
    reverse = {}
    for canonical, variations in INGREDIENT_SYNONYMS.items():
        for variation in variations:
            reverse[variation.lower()] = canonical
    return reverse


VARIATION_TO_CANONICAL = _build_reverse_map()


# ============================================================================
# Normalization Functions
# ============================================================================

def normalize_ingredient(ingredient: str) -> str:
    """
    Normalize ingredient to canonical form

    Args:
        ingredient: Raw ingredient name (e.g., "cilantros", "coriander leaves")

    Returns:
        Canonical form (e.g., "cilantro")
    """
    ingredient_lower = ingredient.lower().strip()

    # Direct lookup
    if ingredient_lower in VARIATION_TO_CANONICAL:
        return VARIATION_TO_CANONICAL[ingredient_lower]

    # Check for partial matches (e.g., "fresh cilantro" → "cilantro")
    for variation, canonical in VARIATION_TO_CANONICAL.items():
        if variation in ingredient_lower or ingredient_lower in variation:
            # Check it's not a false positive (e.g., "chicken" shouldn't match "whole chicken")
            if len(variation) >= 4:  # Minimum length to avoid false matches
                return canonical

    # Default: return as-is (lowercase)
    return ingredient_lower


def deduplicate_ingredients(ingredients: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Deduplicate ingredient list using synonym detection

    Args:
        ingredients: Raw ingredient list (may contain duplicates/synonyms)

    Returns:
        Tuple of (deduplicated_list, duplicates_removed)
        - deduplicated_list: Unique ingredients (first occurrence kept)
        - duplicates_removed: Dict mapping kept_ingredient → [removed_variations]

    Example:
        Input: ["cilantro", "chicken", "coriander leaves", "cilantros"]
        Output: (["cilantro", "chicken"], {"cilantro": ["coriander leaves", "cilantros"]})
    """
    seen_canonical = {}  # canonical_form → first_original
    duplicates_removed = {}

    for ingredient in ingredients:
        canonical = normalize_ingredient(ingredient)

        if canonical not in seen_canonical:
            # First occurrence - keep it
            seen_canonical[canonical] = ingredient
        else:
            # Duplicate detected
            kept_ingredient = seen_canonical[canonical]
            if kept_ingredient not in duplicates_removed:
                duplicates_removed[kept_ingredient] = []
            duplicates_removed[kept_ingredient].append(ingredient)

    # Return deduplicated list (preserving order)
    deduplicated = [seen_canonical[normalize_ingredient(ing)] for ing in ingredients
                    if normalize_ingredient(ing) in seen_canonical.values() or
                    seen_canonical[normalize_ingredient(ing)] == ing]

    # Simpler approach: just preserve first occurrence
    deduplicated = []
    seen_canonical_set = set()
    for ingredient in ingredients:
        canonical = normalize_ingredient(ingredient)
        if canonical not in seen_canonical_set:
            deduplicated.append(ingredient)
            seen_canonical_set.add(canonical)
        else:
            # Track duplicate
            kept = next(ing for ing in deduplicated if normalize_ingredient(ing) == canonical)
            if kept not in duplicates_removed:
                duplicates_removed[kept] = []
            duplicates_removed[kept].append(ingredient)

    return deduplicated, duplicates_removed


# ============================================================================
# Validation
# ============================================================================

def check_for_duplicates(ingredients: List[str]) -> List[Tuple[str, str]]:
    """
    Check if ingredient list contains duplicates/synonyms

    Returns:
        List of (ingredient1, ingredient2) pairs that are duplicates
    """
    duplicates = []
    canonical_map = {}

    for ingredient in ingredients:
        canonical = normalize_ingredient(ingredient)
        if canonical in canonical_map:
            duplicates.append((canonical_map[canonical], ingredient))
        else:
            canonical_map[canonical] = ingredient

    return duplicates


# ============================================================================
# Reporting
# ============================================================================

def get_synonym_info(ingredient: str) -> Dict[str, any]:
    """
    Get synonym information for an ingredient

    Returns:
        Dict with canonical form and known variations
    """
    canonical = normalize_ingredient(ingredient)
    variations = INGREDIENT_SYNONYMS.get(canonical, {canonical})

    return {
        "input": ingredient,
        "canonical": canonical,
        "is_synonym": ingredient.lower() != canonical,
        "known_variations": sorted(list(variations))
    }
