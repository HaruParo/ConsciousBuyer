"""
Ingredient Form Canonicalization

Maps base ingredient names to specific forms for better product matching.
Example: "coriander" → ("coriander", "powder") for biryani context
"""

from typing import Dict, Tuple, Optional


# ============================================================================
# Form Mappings by Cuisine/Recipe Type
# ============================================================================

BIRYANI_INGREDIENT_FORMS: Dict[str, Tuple[str, str]] = {
    # Rice - specify basmati
    "rice": ("basmati rice", "whole"),
    "basmati rice": ("basmati rice", "whole"),

    # Spices - specify powder vs seeds vs pods
    "coriander": ("coriander seeds", "seeds"),  # Changed to seeds (powder not in inventory)
    "cumin": ("cumin seeds", "seeds"),
    "cardamom": ("green cardamom pods", "pods"),
    "green cardamom": ("green cardamom pods", "pods"),
    "black cardamom": ("black cardamom pods", "pods"),
    "turmeric": ("turmeric powder", "powder"),
    "garam masala": ("garam masala", "powder"),

    # Herbs - specify fresh leaves
    "mint": ("fresh mint leaves", "leaves"),
    "cilantro": ("fresh cilantro leaves", "leaves"),
    "bay leaves": ("bay leaves", "whole"),

    # Fresh ingredients - emphasize fresh
    "ginger": ("fresh ginger root", "fresh"),
    "garlic": ("fresh garlic cloves", "fresh"),

    # Protein - specify cut (default to thighs for biryani)
    "chicken": ("chicken thighs", "cut"),
    "chicken thighs": ("chicken thighs", "cut"),
    "chicken legs": ("chicken legs", "cut"),
    "chicken drumsticks": ("chicken drumsticks", "cut"),
    "chicken breasts": ("chicken breasts", "cut"),
    "chicken wings": ("chicken wings", "cut"),
    "whole chicken": ("whole chicken", "whole"),

    # Vegetables - whole
    "onions": ("whole onions", "whole"),
    "tomatoes": ("whole tomatoes", "whole"),

    # Dairy
    "yogurt": ("plain yogurt", "other"),
    "ghee": ("ghee", "other"),
}


def canonicalize_ingredient(
    ingredient: str,
    recipe_type: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Canonicalize ingredient name and determine form

    Args:
        ingredient: Base ingredient name (e.g., "coriander")
        recipe_type: Optional recipe context (e.g., "biryani")

    Returns:
        Tuple of (canonical_name, form)
        Example: ("coriander", "powder") for biryani
        Example: ("coriander", None) if no context
    """
    ingredient_lower = ingredient.lower().strip()

    # Apply recipe-specific forms
    if recipe_type == "biryani":
        if ingredient_lower in BIRYANI_INGREDIENT_FORMS:
            return BIRYANI_INGREDIENT_FORMS[ingredient_lower]

    # Default: no form specified
    return (ingredient_lower, None)


def format_ingredient_label(canonical_name: str, form: Optional[str]) -> str:
    """
    Format ingredient label for display (combines name + form in natural language)

    Args:
        canonical_name: Base ingredient name
        form: Optional form (powder, seeds, pods, leaves, fresh, etc.)

    Returns:
        User-friendly label for display
        Examples:
            - ("ginger", "fresh") → "fresh ginger root"
            - ("coriander", "powder") → "coriander powder"
            - ("cumin", "seeds") → "cumin seeds"
            - ("chicken", "cut") → "chicken thighs"
    """
    if not form or form == "other" or form == "unknown":
        return canonical_name

    # Check if form is already in the canonical name (avoid duplication)
    if form in canonical_name:
        return canonical_name

    # Special cases where form is prefix
    if form in ["fresh", "whole", "plain"]:
        # Check if canonical_name already starts with this form
        if canonical_name.startswith(f"{form} "):
            return canonical_name
        return f"{form} {canonical_name}"

    # Default: form as suffix
    return f"{canonical_name} {form}"


def get_ingredient_key(ingredient: str, form: Optional[str] = None) -> str:
    """
    Generate unique ingredient key including form

    Args:
        ingredient: Canonical ingredient name
        form: Optional form (powder, seeds, pods, etc.)

    Returns:
        Ingredient key for matching
        Example: "coriander_powder", "cumin_seeds", "cardamom_pods"
    """
    if form and form != "other":
        return f"{ingredient}_{form}"
    return ingredient


# ============================================================================
# Form Validation
# ============================================================================

VALID_FORMS = {
    "powder", "seeds", "pods", "leaves", "whole", "paste", "chopped", "other"
}


def validate_form(form: Optional[str]) -> bool:
    """Check if form is valid"""
    if form is None:
        return True
    return form.lower() in VALID_FORMS
