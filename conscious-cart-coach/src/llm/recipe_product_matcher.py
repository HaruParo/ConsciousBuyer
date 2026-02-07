"""LLM-powered recipe-aware product matching considering ALL attributes."""

import logging
from typing import Optional, List, Dict

from .client import call_claude_with_retry

logger = logging.getLogger(__name__)

PRODUCT_MATCHING_PROMPT = """You are a culinary expert selecting grocery products for authentic recipes.

RECIPE: {recipe_context}
INGREDIENT: {ingredient_name}

PRODUCTS:
{products_list}

EVALUATE each product on ALL attributes:

1. **FORM** - Fresh vs dried, powder vs whole, chopped vs whole, etc.
   - Aromatics (ginger, garlic, onions) → FRESH only for cooking
   - Herbs (cilantro, mint, basil) → FRESH bunches
   - Ground spices → POWDER form (not granules/root)
   - Whole spices → SEEDS/PODS for tempering

2. **QUALITY MARKERS**
   - Organic certification (USDA Organic)
   - Grass-fed, free-range, pasture-raised (for meat/dairy)
   - Wild-caught vs farm-raised (fish)
   - Artisan vs commercial production

3. **VARIETY/STRAIN**
   - Tomatoes: Roma/Plum (for curry) vs Cherry (for salad)
   - Rice: Aged Basmati (for biryani) vs Jasmine (for Thai)
   - Onions: Yellow (for cooking) vs Red (for raw)

4. **ORIGIN/SOURCE**
   - Local sourcing (fresher, supports local)
   - Import authenticity (Indian spices from India)
   - Regional specialties (Himalayan Basmati)

5. **PROCESSING LEVEL**
   - Raw vs roasted (nuts, spices)
   - Aged vs fresh (rice, cheese)
   - Fermented vs regular (pickles, condiments)

6. **BRAND REPUTATION**
   - Specialty brands (Pure Indian Foods for spices)
   - Store brands (365 by Whole Foods)
   - Commercial brands

7. **VALUE**
   - Price per unit ($/oz)
   - Quality-to-price ratio
   - Organic premium justification

SELECT the BEST product considering recipe authenticity + quality + value.

OUTPUT (JSON):
{{
  "selected_product_number": <1-based number>,
  "reason": "<Explain which attributes make this best for the recipe>"
}}

EXAMPLES:

Example 1:
Recipe: Chicken Biryani
Ingredient: ginger
Products:
1. Fresh Organic Ginger Root - $3.99/lb (FreshDirect)
2. Ginger Root Coarse Granules - $6.99/2.5oz (Pure Indian Foods, Organic)
3. Ginger Minced Dried - $5.99/2oz (Generic brand)

Output:
{{
  "selected_product_number": 1,
  "reason": "FORM: Fresh ginger essential for authentic biryani (dried lacks oils). QUALITY: Organic. ORIGIN: Local. VALUE: Best $/oz."
}}

Example 2:
Recipe: Chicken Biryani
Ingredient: basmati rice
Products:
1. Generic White Basmati Rice - $4.99/2lb
2. Aged Himalayan Basmati Rice - $8.99/2lb (Pure Indian Foods, Organic)
3. Jasmine Rice - $3.99/2lb

Output:
{{
  "selected_product_number": 2,
  "reason": "VARIETY: Aged Himalayan Basmati (authentic for biryani, jasmine wrong type). PROCESSING: Aged (better texture). QUALITY: Organic. Worth premium."
}}

Example 3:
Recipe: Chicken Biryani
Ingredient: turmeric
Products:
1. Turmeric Root Ground (High Curcumin 4-5%) - $6.99/3oz (Pure Indian Foods, Organic)
2. Turmeric Root Coarse Granules - $6.99/2.5oz (Pure Indian Foods, Organic)
3. Generic Turmeric Powder - $2.99/2oz

Output:
{{
  "selected_product_number": 1,
  "reason": "FORM: Powder blends smoothly (granules don't dissolve). QUALITY: High curcumin content. BRAND: Specialty Indian spices. ORIGIN: Authentic sourcing."
}}

NOW SELECT THE BEST PRODUCT FOR THE RECIPE ABOVE.
OUTPUT (JSON only):"""


def select_best_product_for_recipe(
    client,
    recipe_context: str,
    ingredient_name: str,
    products: List[Dict],
) -> Optional[int]:
    """
    Use LLM to select the best product considering ALL attributes for a recipe.

    Evaluates: form, quality, variety, origin, processing, brand, value

    Args:
        client: LLM client (OllamaClient or AnthropicClient)
        recipe_context: Recipe name/description (e.g., "chicken biryani")
        ingredient_name: Ingredient to match (e.g., "ginger")
        products: List of product dicts with {title, price, brand, size}

    Returns:
        Index of best product (0-based), or None if LLM fails
    """
    if not client or not products:
        return None

    # Format products list
    products_text = ""
    for i, p in enumerate(products[:5], 1):  # Limit to top 5 to save tokens
        products_text += f"{i}. {p['title']} - ${p['price']}/{p.get('size', 'ea')}\n"

    # Build prompt
    formatted_prompt = PRODUCT_MATCHING_PROMPT.format(
        recipe_context=recipe_context,
        ingredient_name=ingredient_name,
        products_list=products_text.strip(),
    )

    # Call LLM
    try:
        response = call_claude_with_retry(
            client=client,
            prompt=formatted_prompt,
            max_tokens=200,
            temperature=0.0,  # Deterministic
            trace_name="ingredient_form_matching",
            metadata={
                "recipe": recipe_context,
                "ingredient": ingredient_name,
                "num_products": len(products),
            }
        )

        if not response:
            logger.warning(f"LLM returned no response for {ingredient_name}")
            return None

        # Parse JSON response
        import json
        import re

        # Extract JSON
        json_match = re.search(r'\{[^{}]*"selected_product_number"[^{}]*\}', response, re.DOTALL)
        if not json_match:
            logger.warning(f"No JSON found in LLM response: {response[:100]}")
            return None

        data = json.loads(json_match.group(0))
        selected = data.get("selected_product_number")

        if selected and 1 <= selected <= len(products):
            logger.info(f"LLM selected product {selected} for {ingredient_name}: {data.get('reason', '')[:80]}")
            return selected - 1  # Convert to 0-based index
        else:
            logger.warning(f"Invalid product number: {selected}")
            return None

    except Exception as e:
        logger.error(f"LLM form matching failed for {ingredient_name}: {e}")
        return None


def rerank_products_by_recipe_fit(
    client,
    recipe_context: str,
    ingredient_name: str,
    products: List[Dict],
) -> List[Dict]:
    """
    Rerank products using LLM to prioritize recipe-appropriate forms.

    Args:
        client: LLM client
        recipe_context: Recipe name (e.g., "chicken biryani")
        ingredient_name: Ingredient name (e.g., "ginger")
        products: List of product candidates

    Returns:
        Reranked products list (best first)
    """
    if not client or not products or len(products) <= 1:
        return products

    # Use LLM to select best product
    best_idx = select_best_product_for_recipe(
        client, recipe_context, ingredient_name, products
    )

    if best_idx is not None and 0 <= best_idx < len(products):
        # Move best product to front
        best = products.pop(best_idx)
        return [best] + products
    else:
        # LLM failed, return original order
        return products
