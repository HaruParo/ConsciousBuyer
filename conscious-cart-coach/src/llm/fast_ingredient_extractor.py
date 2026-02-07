"""
Fast Ingredient Extraction - Template matching with LLM fallback.

Performance:
- Template match: <50ms (instant)
- LLM fallback: ~4-5s (only for unknown dishes)

Usage:
    from src.llm.fast_ingredient_extractor import extract_ingredients_fast

    # Fast path - matches template
    result = extract_ingredients_fast("chicken biryani for 4")  # <50ms

    # Slow path - calls LLM
    result = extract_ingredients_fast("some obscure dish")  # ~4s
"""

import re
import time
from typing import Optional
from functools import lru_cache

# =============================================================================
# MEAL TEMPLATES - Common dishes with pre-defined ingredients
# =============================================================================

MEAL_TEMPLATES = {
    # Indian
    "biryani": {
        "keywords": ["biryani", "biriyani", "briyani"],
        "protein_variants": {
            "chicken": ["chicken"],
            "lamb": ["lamb"],
            "goat": ["goat"],
            "vegetable": ["mixed vegetables", "paneer"],
            "egg": ["eggs"],
        },
        "base_ingredients": [
            {"name": "basmati rice", "form": "basmati", "quantity": 2, "unit": "cups"},
            {"name": "onion", "form": "whole", "quantity": 3, "unit": "large"},
            {"name": "tomato", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "yogurt", "form": "unspecified", "quantity": 1, "unit": "cup"},
            {"name": "ginger", "form": "fresh", "quantity": 2, "unit": "inch"},
            {"name": "garlic", "form": "fresh", "quantity": 8, "unit": "cloves"},
            {"name": "green chili", "form": "fresh", "quantity": 4, "unit": "pieces"},
            {"name": "cilantro", "form": "fresh", "quantity": 1, "unit": "bunch"},
            {"name": "mint", "form": "leaves", "quantity": 1, "unit": "bunch"},
            {"name": "ghee", "form": "unspecified", "quantity": 4, "unit": "tbsp"},
            {"name": "oil", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
            {"name": "garam masala", "form": "powder", "quantity": 2, "unit": "tsp"},
            {"name": "turmeric", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "red chili powder", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "tsp"},
            {"name": "bay leaves", "form": "whole", "quantity": 3, "unit": "pieces"},
            {"name": "cardamom", "form": "whole_spice", "quantity": 6, "unit": "pods"},
            {"name": "cinnamon", "form": "whole_spice", "quantity": 2, "unit": "sticks"},
            {"name": "cloves", "form": "whole_spice", "quantity": 6, "unit": "pieces"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },
    "butter_chicken": {
        "keywords": ["butter chicken", "murgh makhani"],
        "base_ingredients": [
            {"name": "chicken", "form": "boneless", "quantity": 2, "unit": "lb"},
            {"name": "butter", "form": "unspecified", "quantity": 4, "unit": "tbsp"},
            {"name": "heavy cream", "form": "unspecified", "quantity": 1, "unit": "cup"},
            {"name": "tomato puree", "form": "unspecified", "quantity": 2, "unit": "cups"},
            {"name": "onion", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "ginger", "form": "fresh", "quantity": 2, "unit": "inch"},
            {"name": "garlic", "form": "fresh", "quantity": 6, "unit": "cloves"},
            {"name": "garam masala", "form": "powder", "quantity": 2, "unit": "tsp"},
            {"name": "turmeric", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "kashmiri red chili", "form": "powder", "quantity": 2, "unit": "tsp"},
            {"name": "cumin", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "coriander", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "kasuri methi", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
            {"name": "sugar", "form": "unspecified", "quantity": 1, "unit": "tsp"},
        ],
    },
    "dal": {
        "keywords": ["dal", "daal", "dhal", "lentils", "dal tadka", "dal fry"],
        "base_ingredients": [
            {"name": "toor dal", "form": "unspecified", "quantity": 1, "unit": "cup"},
            {"name": "onion", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "tomato", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "ginger", "form": "fresh", "quantity": 1, "unit": "inch"},
            {"name": "garlic", "form": "fresh", "quantity": 4, "unit": "cloves"},
            {"name": "green chili", "form": "fresh", "quantity": 2, "unit": "pieces"},
            {"name": "cilantro", "form": "fresh", "quantity": 0.5, "unit": "bunch"},
            {"name": "ghee", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "cumin", "form": "seeds", "quantity": 1, "unit": "tsp"},
            {"name": "mustard seeds", "form": "seeds", "quantity": 0.5, "unit": "tsp"},
            {"name": "turmeric", "form": "powder", "quantity": 0.5, "unit": "tsp"},
            {"name": "red chili powder", "form": "powder", "quantity": 0.5, "unit": "tsp"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },

    # Italian
    "pasta": {
        "keywords": ["pasta", "spaghetti", "penne", "fettuccine", "linguine"],
        "sauce_variants": {
            "marinara": ["tomatoes", "tomato sauce"],
            "alfredo": ["heavy cream", "parmesan"],
            "pesto": ["basil", "pine nuts", "parmesan"],
            "bolognese": ["ground beef", "tomatoes"],
        },
        "base_ingredients": [
            {"name": "pasta", "form": "unspecified", "quantity": 1, "unit": "lb"},
            {"name": "garlic", "form": "fresh", "quantity": 4, "unit": "cloves"},
            {"name": "olive oil", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
            {"name": "parmesan", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
            {"name": "black pepper", "form": "unspecified", "quantity": None, "unit": "to taste"},
            {"name": "basil", "form": "fresh", "quantity": 0.5, "unit": "cup"},
        ],
    },
    "pizza": {
        "keywords": ["pizza"],
        "base_ingredients": [
            {"name": "pizza dough", "form": "unspecified", "quantity": 1, "unit": "lb"},
            {"name": "tomato sauce", "form": "unspecified", "quantity": 1, "unit": "cup"},
            {"name": "mozzarella", "form": "unspecified", "quantity": 2, "unit": "cups"},
            {"name": "olive oil", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "garlic", "form": "fresh", "quantity": 2, "unit": "cloves"},
            {"name": "basil", "form": "fresh", "quantity": 0.25, "unit": "cup"},
            {"name": "oregano", "form": "unspecified", "quantity": 1, "unit": "tsp"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },

    # Mexican
    "tacos": {
        "keywords": ["tacos", "taco"],
        "protein_variants": {
            "chicken": ["chicken"],
            "beef": ["ground beef"],
            "carnitas": ["pork"],
            "fish": ["fish", "tilapia"],
            "shrimp": ["shrimp"],
        },
        "base_ingredients": [
            {"name": "taco shells", "form": "unspecified", "quantity": 12, "unit": "pieces"},
            {"name": "onion", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "tomato", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "lettuce", "form": "fresh", "quantity": 0.5, "unit": "head"},
            {"name": "cilantro", "form": "fresh", "quantity": 0.5, "unit": "bunch"},
            {"name": "lime", "form": "fresh", "quantity": 2, "unit": "pieces"},
            {"name": "sour cream", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
            {"name": "cheddar cheese", "form": "unspecified", "quantity": 1, "unit": "cup"},
            {"name": "cumin", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "chili powder", "form": "powder", "quantity": 1, "unit": "tbsp"},
            {"name": "garlic powder", "form": "powder", "quantity": 0.5, "unit": "tsp"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },
    "burrito": {
        "keywords": ["burrito", "burritos"],
        "base_ingredients": [
            {"name": "flour tortillas", "form": "unspecified", "quantity": 6, "unit": "large"},
            {"name": "rice", "form": "unspecified", "quantity": 2, "unit": "cups"},
            {"name": "black beans", "form": "unspecified", "quantity": 1, "unit": "can"},
            {"name": "chicken", "form": "boneless", "quantity": 1, "unit": "lb"},
            {"name": "onion", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "bell pepper", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "cilantro", "form": "fresh", "quantity": 0.5, "unit": "bunch"},
            {"name": "lime", "form": "fresh", "quantity": 2, "unit": "pieces"},
            {"name": "sour cream", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
            {"name": "cheddar cheese", "form": "unspecified", "quantity": 1, "unit": "cup"},
            {"name": "cumin", "form": "powder", "quantity": 1, "unit": "tsp"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },

    # Asian
    "stir_fry": {
        "keywords": ["stir fry", "stirfry", "stir-fry"],
        "base_ingredients": [
            {"name": "chicken", "form": "boneless", "quantity": 1, "unit": "lb"},
            {"name": "broccoli", "form": "fresh", "quantity": 2, "unit": "cups"},
            {"name": "bell pepper", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "carrot", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "mushrooms", "form": "whole", "quantity": 8, "unit": "oz"},
            {"name": "ginger", "form": "fresh", "quantity": 1, "unit": "inch"},
            {"name": "garlic", "form": "fresh", "quantity": 4, "unit": "cloves"},
            {"name": "soy sauce", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
            {"name": "sesame oil", "form": "unspecified", "quantity": 1, "unit": "tbsp"},
            {"name": "vegetable oil", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "cornstarch", "form": "unspecified", "quantity": 1, "unit": "tbsp"},
            {"name": "rice", "form": "unspecified", "quantity": 2, "unit": "cups"},
        ],
    },
    "fried_rice": {
        "keywords": ["fried rice"],
        "base_ingredients": [
            {"name": "rice", "form": "unspecified", "quantity": 3, "unit": "cups"},
            {"name": "eggs", "form": "unspecified", "quantity": 3, "unit": "pieces"},
            {"name": "green onion", "form": "fresh", "quantity": 4, "unit": "stalks"},
            {"name": "carrots", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "peas", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
            {"name": "garlic", "form": "fresh", "quantity": 3, "unit": "cloves"},
            {"name": "soy sauce", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
            {"name": "sesame oil", "form": "unspecified", "quantity": 1, "unit": "tsp"},
            {"name": "vegetable oil", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
        ],
    },

    # American
    "burger": {
        "keywords": ["burger", "hamburger", "cheeseburger"],
        "base_ingredients": [
            {"name": "ground beef", "form": "ground", "quantity": 1.5, "unit": "lb"},
            {"name": "burger buns", "form": "unspecified", "quantity": 6, "unit": "pieces"},
            {"name": "cheddar cheese", "form": "unspecified", "quantity": 6, "unit": "slices"},
            {"name": "lettuce", "form": "fresh", "quantity": 0.5, "unit": "head"},
            {"name": "tomato", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "onion", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "pickles", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
            {"name": "ketchup", "form": "unspecified", "quantity": 0.25, "unit": "cup"},
            {"name": "mustard", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
            {"name": "black pepper", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },
    "salad": {
        "keywords": ["salad", "greek salad", "caesar salad"],
        "base_ingredients": [
            {"name": "lettuce", "form": "fresh", "quantity": 1, "unit": "head"},
            {"name": "tomato", "form": "whole", "quantity": 2, "unit": "medium"},
            {"name": "cucumber", "form": "whole", "quantity": 1, "unit": "medium"},
            {"name": "red onion", "form": "whole", "quantity": 0.5, "unit": "medium"},
            {"name": "olive oil", "form": "unspecified", "quantity": 3, "unit": "tbsp"},
            {"name": "lemon", "form": "fresh", "quantity": 1, "unit": "piece"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
            {"name": "black pepper", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },

    # Breakfast
    "pancakes": {
        "keywords": ["pancakes", "pancake"],
        "base_ingredients": [
            {"name": "flour", "form": "unspecified", "quantity": 2, "unit": "cups"},
            {"name": "eggs", "form": "unspecified", "quantity": 2, "unit": "pieces"},
            {"name": "milk", "form": "unspecified", "quantity": 1.5, "unit": "cups"},
            {"name": "butter", "form": "unspecified", "quantity": 4, "unit": "tbsp"},
            {"name": "sugar", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "baking powder", "form": "unspecified", "quantity": 2, "unit": "tsp"},
            {"name": "salt", "form": "unspecified", "quantity": 0.5, "unit": "tsp"},
            {"name": "maple syrup", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
        ],
    },
    "omelette": {
        "keywords": ["omelette", "omelet"],
        "base_ingredients": [
            {"name": "eggs", "form": "unspecified", "quantity": 6, "unit": "pieces"},
            {"name": "butter", "form": "unspecified", "quantity": 2, "unit": "tbsp"},
            {"name": "cheese", "form": "unspecified", "quantity": 0.5, "unit": "cup"},
            {"name": "bell pepper", "form": "whole", "quantity": 0.5, "unit": "medium"},
            {"name": "onion", "form": "whole", "quantity": 0.25, "unit": "medium"},
            {"name": "mushrooms", "form": "whole", "quantity": 0.5, "unit": "cup"},
            {"name": "salt", "form": "unspecified", "quantity": None, "unit": "to taste"},
            {"name": "black pepper", "form": "unspecified", "quantity": None, "unit": "to taste"},
        ],
    },
}


# =============================================================================
# FAST MATCHING LOGIC
# =============================================================================

def _normalize_text(text: str) -> str:
    """Normalize text for matching."""
    return re.sub(r'[^a-z\s]', '', text.lower().strip())


def _extract_servings(prompt: str) -> int:
    """Extract serving count from prompt."""
    patterns = [
        r'for\s+(\d+)\s*(?:people|person|ppl)?',
        r'serves?\s+(\d+)',
        r'(\d+)\s+servings?',
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return int(match.group(1))
    return 4  # default


def _detect_protein(prompt: str) -> Optional[str]:
    """Detect protein type from prompt."""
    prompt_lower = prompt.lower()
    proteins = {
        "chicken": ["chicken"],
        "beef": ["beef", "steak"],
        "lamb": ["lamb", "mutton"],
        "goat": ["goat"],
        "pork": ["pork", "carnitas"],
        "fish": ["fish", "salmon", "tilapia", "cod"],
        "shrimp": ["shrimp", "prawn"],
        "vegetable": ["veg", "vegetarian", "veggie"],
        "egg": ["egg"],
    }
    for protein, keywords in proteins.items():
        for kw in keywords:
            if kw in prompt_lower:
                return protein
    return "chicken"  # default


@lru_cache(maxsize=100)
def _match_template(prompt_normalized: str) -> Optional[str]:
    """Match prompt to a template. Cached for performance."""
    for template_name, template in MEAL_TEMPLATES.items():
        for keyword in template["keywords"]:
            if keyword in prompt_normalized:
                return template_name
    return None


def _scale_ingredients(ingredients: list[dict], servings: int, base_servings: int = 4) -> list[dict]:
    """Scale ingredient quantities based on servings."""
    if servings == base_servings:
        return ingredients

    scale_factor = servings / base_servings
    scaled = []
    for ing in ingredients:
        scaled_ing = ing.copy()
        if scaled_ing.get("quantity") is not None:
            scaled_ing["quantity"] = round(scaled_ing["quantity"] * scale_factor, 2)
        scaled.append(scaled_ing)
    return scaled


def extract_ingredients_fast(
    prompt: str,
    servings: Optional[int] = None,
    llm_client=None,
) -> tuple[list[dict], dict]:
    """
    Fast ingredient extraction with template matching.

    Args:
        prompt: User's meal request
        servings: Number of servings (extracted from prompt if not provided)
        llm_client: Optional LLM client for fallback

    Returns:
        Tuple of (ingredients list, metadata dict)
        Metadata includes: method, latency_ms, template_name
    """
    start_time = time.time()

    # Extract servings if not provided
    if servings is None:
        servings = _extract_servings(prompt)

    # Normalize and match
    prompt_normalized = _normalize_text(prompt)
    template_name = _match_template(prompt_normalized)

    if template_name:
        # FAST PATH: Use template
        template = MEAL_TEMPLATES[template_name]
        ingredients = list(template["base_ingredients"])  # Copy

        # Add protein variant if applicable
        if "protein_variants" in template:
            protein = _detect_protein(prompt)
            if protein in template["protein_variants"]:
                for protein_name in template["protein_variants"][protein]:
                    # Find form based on protein type
                    form = "boneless" if protein in ["chicken", "fish"] else "ground" if protein == "beef" else "unspecified"
                    ingredients.insert(0, {
                        "name": protein_name,
                        "form": form,
                        "quantity": 1.5 if protein == "beef" else 2,
                        "unit": "lb"
                    })

        # Scale for servings
        ingredients = _scale_ingredients(ingredients, servings)

        latency_ms = (time.time() - start_time) * 1000

        return ingredients, {
            "method": "template",
            "template_name": template_name,
            "latency_ms": round(latency_ms, 2),
            "servings": servings,
        }

    # SLOW PATH: Fall back to LLM
    if llm_client:
        from .ingredient_extractor import extract_ingredients_with_llm

        ingredients = extract_ingredients_with_llm(
            client=llm_client,
            prompt=prompt,
            servings=servings,
        )

        latency_ms = (time.time() - start_time) * 1000

        return ingredients or [], {
            "method": "llm",
            "template_name": None,
            "latency_ms": round(latency_ms, 2),
            "servings": servings,
        }

    # No LLM client and no template match
    latency_ms = (time.time() - start_time) * 1000
    return [], {
        "method": "none",
        "template_name": None,
        "latency_ms": round(latency_ms, 2),
        "servings": servings,
        "error": "No template match and no LLM client provided",
    }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_available_templates() -> list[str]:
    """Get list of available meal templates."""
    return list(MEAL_TEMPLATES.keys())


def get_template_keywords() -> dict[str, list[str]]:
    """Get keywords for all templates."""
    return {name: template["keywords"] for name, template in MEAL_TEMPLATES.items()}
