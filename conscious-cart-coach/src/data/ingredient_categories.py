"""
Ingredient categorization for scoring system.

Maps ingredient names to categories and forms for context-aware scoring.
"""

from typing import Tuple, Optional


# Ingredient category mappings
PRODUCE_ITEMS = {
    "onions", "tomatoes", "garlic", "ginger", "lettuce", "spinach",
    "kale", "arugula", "peppers", "bell peppers", "cucumbers", "zucchini",
    "carrots", "potatoes", "sweet potatoes", "mushrooms", "broccoli",
    "cauliflower", "cabbage", "celery", "avocado", "strawberries",
    "blueberries", "apples", "pears", "grapes", "oranges", "lemons",
    "limes", "cilantro", "mint", "parsley", "basil", "thyme", "rosemary"
}

PROTEIN_ITEMS = {
    "chicken", "chicken thighs", "chicken breasts", "chicken legs",
    "chicken drumsticks", "chicken wings", "whole chicken",
    "beef", "pork", "lamb", "fish", "salmon", "tuna", "shrimp",
    "eggs", "tofu", "tempeh"
}

DAIRY_ITEMS = {
    "milk", "yogurt", "cheese", "butter", "ghee", "cream",
    "sour cream", "cottage cheese", "ricotta", "mozzarella", "cheddar"
}

SPICE_ITEMS = {
    "turmeric", "coriander", "cumin", "cardamom", "cinnamon",
    "cloves", "nutmeg", "paprika", "chili powder", "cayenne",
    "black pepper", "white pepper", "garam masala", "curry powder",
    "bay leaves", "bay leaf", "mustard seeds", "fennel seeds",
    "fenugreek", "saffron"
}

HERB_ITEMS = {
    "cilantro", "mint", "parsley", "basil", "thyme", "rosemary",
    "oregano", "dill", "sage", "tarragon", "chives"
}

PANTRY_ITEMS = {
    "rice", "basmati rice", "brown rice", "white rice",
    "flour", "sugar", "salt", "oil", "olive oil", "vegetable oil",
    "coconut oil", "vinegar", "soy sauce", "pasta", "beans",
    "lentils", "chickpeas", "quinoa", "oats"
}


def get_ingredient_category(ingredient_name: str) -> str:
    """
    Determine ingredient category for scoring.

    Returns:
        "produce", "protein", "dairy", "spice", "herb", "pantry", or "other"
    """
    name_lower = ingredient_name.lower().strip()

    # Check each category (order matters for overlaps)
    for item in HERB_ITEMS:
        if item in name_lower:
            return "herb"

    for item in SPICE_ITEMS:
        if item in name_lower:
            return "spice"

    for item in PROTEIN_ITEMS:
        if item in name_lower:
            return "protein"

    for item in DAIRY_ITEMS:
        if item in name_lower:
            return "dairy"

    for item in PANTRY_ITEMS:
        if item in name_lower:
            return "pantry"

    for item in PRODUCE_ITEMS:
        if item in name_lower:
            return "produce"

    return "other"


def detect_product_form(product_title: str, category: str) -> str:
    """
    Detect product form from title.

    Returns form classification:
        "fresh_root", "leaves", "whole_spice", "powder", "seeds",
        "paste", "dairy", "meat_cut", "whole", "unknown"
    """
    title_lower = product_title.lower()

    # Form-specific keywords
    if any(kw in title_lower for kw in ["powder", "ground", "powdered"]):
        return "powder"

    if any(kw in title_lower for kw in ["seed", "seeds", "whole cumin", "whole coriander"]):
        return "seeds"

    if any(kw in title_lower for kw in ["pod", "pods", "cardamom pods"]):
        return "seeds"  # Pods are similar to seeds for scoring

    if any(kw in title_lower for kw in ["paste", "minced", "crushed"]):
        return "paste"

    if any(kw in title_lower for kw in ["dried", "dry"]) and category == "herb":
        return "dried_leaf"

    if any(kw in title_lower for kw in ["fresh", "bunch", "leaves"]) and category in ["herb", "produce"]:
        if any(kw in title_lower for kw in ["ginger root", "ginger", "garlic cloves", "garlic"]):
            return "fresh_root"
        return "leaves"

    if category == "protein":
        if any(kw in title_lower for kw in ["thigh", "breast", "leg", "drumstick", "wing", "cut"]):
            return "meat_cut"
        if "whole" in title_lower:
            return "whole"

    if category == "dairy":
        return "dairy"

    # Default to whole for produce
    if category == "produce":
        return "whole"

    return "unknown"


def get_form_compatibility_score(required_form: Optional[str], product_form: str) -> int:
    """
    Score form compatibility (0 = perfect, higher = worse mismatch).

    Returns:
        0: Perfect match
        5: Acceptable alternative
        10: Minor mismatch
        999: Incompatible (should filter out)
    """
    if not required_form or product_form == "unknown":
        return 5  # Neutral when form is unknown

    required_lower = required_form.lower()
    product_lower = product_form.lower()

    # Exact match
    if required_lower == product_lower:
        return 0

    # Acceptable substitutions
    acceptable_subs = {
        ("fresh_root", "fresh"): 0,
        ("fresh", "fresh_root"): 0,
        ("leaves", "fresh"): 2,
        ("whole", "fresh"): 2,
        ("seeds", "whole_spice"): 2,
        ("powder", "ground"): 0,
    }

    for (req, prod), score in acceptable_subs.items():
        if req in required_lower and prod in product_lower:
            return score

    # Incompatible (should be filtered)
    incompatible = {
        ("fresh", "powder"): 999,
        ("fresh", "dried_leaf"): 999,
        ("powder", "seeds"): 999,
        ("seeds", "powder"): 999,
        ("leaves", "powder"): 999,
        ("powder", "paste"): 10,  # Paste vs powder is minor
    }

    for (req, prod), score in incompatible.items():
        if req in required_lower and prod in product_lower:
            return score

    # Default mismatch
    return 10
