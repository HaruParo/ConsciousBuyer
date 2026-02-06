"""
Hard form constraints for ingredient matching.

Prevents incorrect product matches:
- Fresh ginger should NOT match ginger powder
- Cumin seeds should NOT match kalonji (black seed)
- Bay leaves should NOT match spice blends
"""

from typing import Optional, List, Tuple


# Synonym/anti-synonym dictionary for specific ingredients
INGREDIENT_CONSTRAINTS = {
    "cumin seeds": {
        "include": ["cumin", "jeera", "whole cumin", "cumin seed"],
        "exclude": ["kalonji", "nigella", "black seed", "onion seed", "charnushka", "ground", "powder"]
    },
    "cumin": {
        "include": ["cumin", "jeera", "whole cumin", "cumin seed"],
        "exclude": ["kalonji", "nigella", "black seed", "onion seed", "ground", "powder"]
    },
    "bay leaves": {
        "include": ["bay leaf", "bay leaves", "tej patta", "indian bay"],
        "exclude": ["blend", "mix", "chaat", "DIY", "garam masala", "curry powder", "mixed spice"]
    },
    "bay leaf": {
        "include": ["bay leaf", "bay leaves", "tej patta"],
        "exclude": ["blend", "mix", "chaat", "DIY", "garam masala"]
    },
    "fresh ginger": {
        "include": ["ginger root", "fresh ginger", "organic ginger", "ginger", "whole ginger"],
        "exclude": ["powder", "paste", "dried", "minced ginger", "ground ginger", "ginger powder"]
    },
    "ginger": {
        "include": ["ginger root", "fresh ginger", "organic ginger", "ginger"],
        "exclude": ["powder", "paste", "dried", "minced", "ground ginger"]
    },
    "coriander powder": {
        "include": ["ground coriander", "coriander powder", "dhania powder"],
        "exclude": ["seeds", "whole coriander", "leaves", "cilantro", "coriander seed"]
    },
    "coriander": {
        "include": ["ground coriander", "coriander powder", "dhania"],
        "exclude": ["seeds", "whole coriander", "leaves", "cilantro"]
    },
    "coriander seeds": {
        "include": ["coriander seed", "whole coriander", "dhania seed"],
        "exclude": ["powder", "ground", "leaves", "cilantro"]
    },
    "fresh mint": {
        "include": ["mint", "fresh mint", "mint leaves", "mint bunch"],
        "exclude": ["dried mint", "mint powder", "peppermint extract", "mint tea"]
    },
    "fresh cilantro": {
        "include": ["cilantro", "fresh cilantro", "cilantro bunch", "coriander leaves"],
        "exclude": ["dried cilantro", "coriander seed", "coriander powder"]
    },
    "cardamom": {
        "include": ["green cardamom", "cardamom pods", "elaichi", "cardamom"],
        "exclude": ["black cardamom", "cardamom powder", "ground cardamom"]
    },
    "green cardamom": {
        "include": ["green cardamom", "cardamom pods", "elaichi"],
        "exclude": ["black cardamom", "cardamom powder"]
    },
    "turmeric": {
        "include": ["turmeric powder", "ground turmeric", "haldi"],
        "exclude": ["turmeric root", "fresh turmeric", "whole turmeric"]
    }
}


def get_form_constraint(ingredient_name: str, ingredient_form: Optional[str]) -> Optional[Tuple[List[str], List[str]]]:
    """
    Get include/exclude constraints for an ingredient.

    Args:
        ingredient_name: Canonical ingredient name
        ingredient_form: Expected form (fresh, powder, seeds, etc.)

    Returns:
        Tuple of (include_keywords, exclude_keywords) or None if no constraints
    """
    name_lower = ingredient_name.lower().strip()

    # Check for exact match in constraints
    if name_lower in INGREDIENT_CONSTRAINTS:
        constraints = INGREDIENT_CONSTRAINTS[name_lower]
        return (constraints["include"], constraints["exclude"])

    # Form-based generic constraints
    if ingredient_form:
        form_lower = ingredient_form.lower()

        # Fresh form: exclude powder, paste, dried
        if form_lower in ["fresh", "fresh_root", "leaves"]:
            return (
                [ingredient_name.lower()],
                ["powder", "paste", "dried", "ground", "minced"]
            )

        # Powder form: exclude seeds, whole, fresh
        if form_lower == "powder":
            return (
                [ingredient_name.lower(), "powder", "ground"],
                ["seed", "whole", "fresh", "root", "leaves"]
            )

        # Seeds form: exclude powder, ground
        if form_lower in ["seeds", "whole_spice", "pods"]:
            return (
                [ingredient_name.lower(), "seed", "whole", "pod"],
                ["powder", "ground", "paste"]
            )

    return None


def passes_form_constraints(
    product_title: str,
    ingredient_name: str,
    ingredient_form: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """
    Check if a product passes form constraints for an ingredient.

    Args:
        product_title: Product title to check
        ingredient_name: Canonical ingredient name
        ingredient_form: Expected form

    Returns:
        Tuple of (passes: bool, reason: Optional[str])
        If passes=False, reason explains why
    """
    constraints = get_form_constraint(ingredient_name, ingredient_form)

    if not constraints:
        return True, None  # No constraints, allow

    include_keywords, exclude_keywords = constraints
    title_lower = product_title.lower()

    # Check exclude keywords first (hard failures)
    for exclude_kw in exclude_keywords:
        if exclude_kw in title_lower:
            return False, f"FORM_MISMATCH: contains '{exclude_kw}' (incompatible with {ingredient_form or ingredient_name})"

    # Check include keywords (at least one must match)
    has_include_match = any(include_kw in title_lower for include_kw in include_keywords)
    if not has_include_match and len(include_keywords) > 0:
        # Relaxed: if no include match but also no exclude match, allow (may be synonym we don't know)
        return True, None

    return True, None
