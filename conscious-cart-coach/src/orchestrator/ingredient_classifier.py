"""
Ingredient Classification for Store Routing

Dynamically classifies ingredients to determine which store types can carry them.
Handles new/unknown ingredients without manual intervention.

Classification:
- "primary": Fresh items, common groceries → FreshDirect, Whole Foods, ShopRite
- "specialty": Ethnic spices, specialty items → Pure Indian Foods, Patel Brothers
- "both": Common shelf-stable → Available at both store types
"""

from typing import Optional
import re


# Fresh/perishable ingredients (MUST go to primary stores - specialty can't ship fresh)
FRESH_CATEGORIES = {
    # Produce
    "spinach", "kale", "lettuce", "romaine", "arugula", "chard",
    "tomato", "tomatoes", "cherry_tomatoes", "grape_tomatoes", "plum_tomatoes", "roma_tomatoes", "roma_tomato",
    "onion", "onions", "red_onion", "red_onions", "yellow_onion", "yellow_onions", "white_onion",
    "garlic", "ginger", "shallot",
    "bell_pepper", "bell_peppers", "hot_peppers", "jalapeno", "serrano",
    "cucumber", "cucumbers", "carrot", "carrots", "celery",
    "broccoli", "cauliflower", "cabbage", "brussels_sprouts",
    "potato", "potatoes", "sweet_potato", "yam",
    "avocado", "avocados", "lemon", "lemons", "lime", "limes",
    "strawberries", "blueberries", "raspberries", "blackberries",
    "apple", "apples", "banana", "bananas", "orange", "oranges",
    "mushroom", "mushrooms", "zucchini", "squash", "eggplant",
    # Herbs (fresh)
    "cilantro", "coriander_leaves", "parsley", "basil", "mint", "mint_leaves",
    "thyme", "rosemary", "oregano", "dill", "chives", "sage", "tarragon",
    # Proteins (fresh)
    "chicken", "beef", "pork", "lamb", "turkey", "duck",
    "ground_beef", "ground_turkey", "ground_chicken",
    "salmon", "fish", "shrimp", "tuna", "cod", "tilapia",
    "sausage", "bacon", "ham",
    # Dairy (fresh)
    "milk", "yogurt", "cheese", "butter", "cream", "sour_cream",
    "cottage_cheese", "ricotta", "mozzarella", "cheddar",
    "eggs", "egg",
}

# Alternative ingredient names (for handling different names for the same ingredient)
INGREDIENT_ALIASES = {
    "coriander_leaves": "cilantro",
    "coriander leaves": "cilantro",
    "chinese_parsley": "cilantro",
    "mint_leaves": "mint",
    "mint leaves": "mint",
    "fresh_mint": "mint",
    "fresh_cilantro": "cilantro",
    "fresh_coriander": "cilantro",
    "fresh_basil": "basil",
    "fresh_parsley": "parsley",
}

# Ethnic specialty ingredients (better quality/matching at specialty stores)
# Strategy: ALL ethnic ingredients go to specialty stores for better quality
ETHNIC_SPECIALTY = {
    # Indian spices (ALL spices, including common ones)
    "turmeric", "cumin", "coriander", "cardamom", "cinnamon",
    "clove", "cloves", "bay_leaf", "bay_leaves", "curry_leaves",
    "garam_masala", "curry_powder", "chaat_masala", "tandoori_masala",
    "mustard_seed", "mustard_seeds", "fenugreek", "kasuri_methi",
    "asafoetida", "hing", "fennel_seed", "fennel_seeds",
    "black_pepper", "white_pepper", "red_chili", "kashmiri_chili",
    "paprika", "cayenne", "red_pepper_flakes", "chili_powder",
    # Indian specialty & staples
    "ghee", "paneer", "dal", "lentils", "urad_dal", "chana_dal", "toor_dal",
    "basmati_rice", "jasmine_rice", "sona_masoori", "rice",  # ALL rice types
    "tamarind", "jaggery", "coconut_milk", "coconut_cream",
    "saffron", "rose_water", "kewra_water",
    # Middle Eastern
    "sumac", "za'atar", "tahini", "pomegranate_molasses", "harissa",
    "preserved_lemon", "orange_blossom_water",
    # Asian
    "miso", "miso_paste", "kimchi", "gochugaru", "gochujang",
    "sesame_oil", "rice_vinegar", "black_vinegar", "shaoxing_wine",
    "fish_sauce", "oyster_sauce", "hoisin_sauce",
    "soy_sauce", "tamari", "shoyu", "mirin",
    "tofu", "tempeh", "nori", "wakame", "kombu",
    "dashi", "bonito_flakes", "furikake",
    # Latin American
    "adobo", "chipotle", "ancho_chili", "guajillo_chili",
    "epazote", "mexican_oregano", "annatto", "achiote",
}

# Common shelf-stable (truly basic items available everywhere)
# Note: Rice, lentils, and most spices moved to specialty for better quality
COMMON_SHELF_STABLE = {
    "olive_oil", "vegetable_oil", "canola_oil", "avocado_oil",
    "salt", "sea_salt", "kosher_salt", "table_salt",
    "sugar", "brown_sugar", "powdered_sugar", "honey", "maple_syrup",
    "flour", "all_purpose_flour", "bread_flour", "whole_wheat_flour",
    "pasta", "spaghetti", "penne", "linguine", "noodles",
    "quinoa", "couscous", "bulgur", "farro",
    "beans", "black_beans", "kidney_beans", "chickpeas",  # Removed lentils - goes to specialty
    "canned_tomatoes", "crushed_tomatoes", "diced_tomatoes", "tomato_paste",
    "broth", "stock", "chicken_broth", "vegetable_broth",
    "vinegar", "balsamic_vinegar", "red_wine_vinegar", "white_vinegar",
}


def normalize_ingredient_name(ingredient_name: str) -> str:
    """
    Normalize ingredient name by handling aliases and standardizing format.

    Examples:
        normalize_ingredient_name("coriander leaves") → "cilantro"
        normalize_ingredient_name("mint leaves") → "mint"
    """
    ingredient_lower = ingredient_name.lower().strip().replace(" ", "_")

    # Check for aliases
    if ingredient_lower in INGREDIENT_ALIASES:
        return INGREDIENT_ALIASES[ingredient_lower]

    return ingredient_lower


def classify_ingredient_store_type(
    ingredient_name: str,
    product_data: Optional[dict] = None,
    use_llm_fallback: bool = False
) -> str:
    """
    Dynamically classify ingredient to determine which store types can carry it.

    Args:
        ingredient_name: The ingredient to classify
        product_data: Optional product attributes (organic, brand, etc.)
        use_llm_fallback: Use LLM for unknown ingredients (not implemented yet)

    Returns:
        "primary" | "specialty" | "both"

    Examples:
        classify_ingredient_store_type("spinach") → "primary" (fresh)
        classify_ingredient_store_type("coriander leaves") → "primary" (fresh, alias for cilantro)
        classify_ingredient_store_type("turmeric") → "specialty" (ethnic spice)
        classify_ingredient_store_type("olive_oil") → "both" (common)
        classify_ingredient_store_type("saffron") → "specialty" (exotic spice)
    """
    ingredient_lower = normalize_ingredient_name(ingredient_name)

    # Rule 1: Fresh/perishable items MUST go to primary stores
    # (Specialty stores can't ship fresh produce)
    if is_fresh_ingredient(ingredient_lower):
        return "primary"

    # Rule 2: Ethnic specialty items go to specialty stores
    # (Better quality, organic options, transparency)
    if is_ethnic_specialty(ingredient_lower):
        return "specialty"

    # Rule 3: Common shelf-stable items available at both
    if is_common_shelf_stable(ingredient_lower):
        return "both"

    # Rule 4: Check product attributes if available
    if product_data:
        # Organic spices → prefer specialty stores
        if product_data.get("organic") and is_spice_like(ingredient_lower):
            return "specialty"

        # Specialty brands → specialty stores
        if is_specialty_brand(product_data.get("brand", "")):
            return "specialty"

    # Default: Available at both
    return "both"


def is_fresh_ingredient(ingredient: str) -> bool:
    """
    Check if ingredient is fresh/perishable.

    Uses:
    - Known fresh categories (produce, meat, dairy)
    - Keyword patterns ("fresh", "bunch", "leaves")
    - Normalization to handle aliases
    """
    # Normalize the ingredient name first
    normalized = normalize_ingredient_name(ingredient)

    # Direct category match
    if normalized in FRESH_CATEGORIES:
        return True

    # Partial match (e.g., "baby_spinach" matches "spinach")
    for fresh_item in FRESH_CATEGORIES:
        if fresh_item in normalized or normalized in fresh_item:
            return True

    # Keyword patterns indicating fresh items
    fresh_keywords = ["fresh", "bunch", "leaf", "leaves", "head", "stalk"]
    if any(kw in normalized for kw in fresh_keywords):
        return True

    return False


def is_ethnic_specialty(ingredient: str) -> bool:
    """
    Check if ingredient is ethnic specialty with better options at specialty stores.

    Ethnic specialty = spices, condiments, staples with better quality/transparency
    at specialty stores (Pure Indian Foods, Patel Brothers, etc.)
    """
    # Direct category match
    if ingredient in ETHNIC_SPECIALTY:
        return True

    # Partial match
    for specialty_item in ETHNIC_SPECIALTY:
        if specialty_item in ingredient or ingredient in specialty_item:
            return True

    # Pattern matching for spice-like ingredients
    spice_suffixes = ["_powder", "_seed", "_seeds", "_spice", "_masala", "_paste"]
    if any(ingredient.endswith(suffix) for suffix in spice_suffixes):
        # If it's a spice and not in common list, likely specialty
        if ingredient not in COMMON_SHELF_STABLE:
            return True

    return False


def is_common_shelf_stable(ingredient: str) -> bool:
    """Check if ingredient is common shelf-stable (available everywhere)."""
    # Direct match
    if ingredient in COMMON_SHELF_STABLE:
        return True

    # Partial match
    for common_item in COMMON_SHELF_STABLE:
        if common_item in ingredient or ingredient in common_item:
            return True

    return False


def is_spice_like(ingredient: str) -> bool:
    """Check if ingredient appears to be a spice/seasoning."""
    spice_patterns = [
        "powder", "seed", "seeds", "spice", "masala", "seasoning",
        "pepper", "chili", "curry"
    ]
    return any(pattern in ingredient for pattern in spice_patterns)


def is_specialty_brand(brand: str) -> bool:
    """Check if brand is a specialty/ethnic brand."""
    specialty_brands = {
        "pure_indian_foods", "patel_brothers", "deep", "laxmi",
        "swad", "shan", "mtd", "everest", "mdh",
        "simply_organic", "frontier_co-op", "burlap_&_barrel",
    }
    brand_lower = brand.lower().replace(" ", "_").replace("-", "_")
    return brand_lower in specialty_brands


def get_ingredient_classification_reason(ingredient_name: str) -> str:
    """
    Get human-readable reason for classification.

    Useful for debugging and user explanations.
    """
    ingredient_lower = ingredient_name.lower().strip().replace(" ", "_")

    if is_fresh_ingredient(ingredient_lower):
        return "Fresh/perishable item (specialty stores can't ship fresh)"

    if is_ethnic_specialty(ingredient_lower):
        return "Ethnic specialty (better quality/transparency at specialty stores)"

    if is_common_shelf_stable(ingredient_lower):
        return "Common shelf-stable item (available at both store types)"

    return "General grocery item (available at both store types)"


# Expose main function
__all__ = ["classify_ingredient_store_type", "get_ingredient_classification_reason"]
