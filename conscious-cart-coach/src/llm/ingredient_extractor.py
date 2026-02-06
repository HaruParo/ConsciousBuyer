"""LLM-powered ingredient extraction from natural language prompts."""

import json
import logging
import re
from typing import Optional

# Type hints only - actual client is passed in
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from .client import call_claude_with_retry

logger = logging.getLogger(__name__)

# Controlled vocabulary for ingredient forms
VALID_FORMS = {
    "fresh", "leaves", "whole", "chopped", "paste", "powder",
    "seeds", "whole_spice",
    "thighs", "breast", "drumsticks", "whole_chicken", "bone_in", "boneless", "ground",
    "basmati", "jasmine", "long_grain", "short_grain", "whole_grain",
    "unspecified"
}

OVERRIDE_MODE_PROMPT = """You are in STRICT OVERRIDE MODE. Return EXACTLY the ingredients listed, no additions, no removals.

USER'S MEAL PLAN:
{prompt}

DETECTED INGREDIENT_LIST: {ingredient_list}
SERVINGS: {servings}

STRICT OVERRIDE RULES:
1. Return EXACTLY these ingredients: {ingredient_list}
2. DO NOT add any ingredients not in this list
3. DO NOT remove any ingredients from this list
4. DO NOT infer missing ingredients based on meal type
5. Parse embedded forms from ingredient phrases:
   - "fresh ginger" → name="ginger", form="fresh"
   - "coriander powder" → name="coriander", form="powder"
   - "cumin seeds" → name="cumin", form="seeds"
   - "mint leaves" → name="mint", form="leaves"
   - "chicken thighs" → name="chicken", form="thighs"
6. Use defaults: quantity=1, unit="unit"

VALID FORMS: fresh, leaves, whole, chopped, paste, powder, seeds, whole_spice, thighs, breast, drumsticks, whole_chicken, bone_in, boneless, ground, basmati, jasmine, long_grain, short_grain, whole_grain, unspecified

OUTPUT SCHEMA:
{{
  "servings": {servings},
  "ingredients": [
    {{"name": string, "form": string, "quantity": 1, "unit": "unit"}}
  ]
}}

Example:
Input list: "fresh ginger | coriander powder | cumin seeds"
Output:
{{
  "servings": {servings},
  "ingredients": [
    {{"name": "ginger", "form": "fresh", "quantity": 1, "unit": "unit"}},
    {{"name": "coriander", "form": "powder", "quantity": 1, "unit": "unit"}},
    {{"name": "cumin", "form": "seeds", "quantity": 1, "unit": "unit"}}
  ]
}}

NOW EXTRACT THE INGREDIENT_LIST ABOVE WITH STRICT COMPLIANCE.
Output ONLY valid JSON, no explanation.

JSON OUTPUT:"""

INGREDIENT_EXTRACTION_PROMPT = """You are an ingredient extraction specialist. Extract structured ingredient data from meal prompts.

STRICT BOUNDARIES - YOU MUST NOT:
❌ Suggest stores, availability, pricing, shipping estimates
❌ Make safety/recall/health claims
❌ Make brand recommendations or trust judgments
❌ Make ethical or sustainability judgments
✅ ONLY extract: ingredient names, forms, quantities, units

USER'S MEAL PLAN:
{prompt}

SERVINGS: {servings}

OUTPUT SCHEMA (REQUIRED - MUST BE VALID JSON):
{{
  "servings": number,
  "ingredients": [
    {{
      "name": string,
      "form": string (REQUIRED - from controlled vocabulary below),
      "quantity": number OR null (NEVER use the word "unspecified" - use null instead),
      "unit": string OR null,
      "notes": string (optional)
    }}
  ]
}}

⚠️  CRITICAL JSON RULES:
- quantity MUST be a number (e.g. 1, 2.5) or null - NEVER use strings like "unspecified"
- unit MUST be a string (e.g. "oz", "tbsp") or null - NEVER use "unspecified"
- If quantity/unit unknown, use null (not "unspecified", not "unknown")
- All strings MUST be in quotes: "fresh" not fresh, "mushrooms" not mushrooms
- No trailing commas in arrays or objects

CONTROLLED VOCABULARY FOR "form" (MUST use one of these):
Produce/Herbs: fresh, leaves, whole, chopped, paste, powder
Spices: powder, seeds, whole_spice
Meat: thighs, breast, drumsticks, whole_chicken, bone_in, boneless, ground
Rice/Grains: basmati, jasmine, long_grain, short_grain, whole_grain
Default: unspecified

EXTRACTION GUIDELINES:
✅ For recipe names (e.g., "fried rice", "biryani"), extract ALL typical ingredients for that dish
✅ Include: main ingredients, vegetables, sauces, seasonings, cooking oils, aromatics (garlic, ginger, onions)
✅ Be COMPREHENSIVE - include all ingredients a typical recipe would use
✅ Match the cuisine/dish type - extract ingredients authentic to that recipe
❌ Do NOT mix ingredients from different cuisines (no cumin in Chinese stir fry, no soy sauce in Italian pasta)

FORBIDDEN SUBSTITUTIONS:
❌ cumin → kalonji/black seed/nigella (these are DIFFERENT spices!)
❌ bay leaves → spice blends/garam masala/chaat masala
❌ coriander powder → cilantro leaves/coriander seeds (different forms!)
❌ fresh ginger → ginger powder (different forms!)

EXAMPLES:

Example 1 (Stir fry - Asian vegetables and sauce):
Input: "mushroom stir fry for 2"
Output:
{{
  "servings": 2,
  "ingredients": [
    {{"name": "mushrooms", "form": "whole", "quantity": 8, "unit": "oz"}},
    {{"name": "bell peppers", "form": "whole", "quantity": 2, "unit": "medium"}},
    {{"name": "snap peas", "form": "whole", "quantity": 1, "unit": "cup"}},
    {{"name": "soy sauce", "form": "unspecified", "quantity": 3, "unit": "tbsp"}},
    {{"name": "ginger", "form": "fresh", "quantity": 1, "unit": "inch"}},
    {{"name": "garlic", "form": "fresh", "quantity": 3, "unit": "cloves"}},
    {{"name": "oil", "form": "unspecified", "quantity": 2, "unit": "tbsp"}},
    {{"name": "rice", "form": "unspecified", "quantity": 1, "unit": "cup"}}
  ]
}}

Example 2 (Pantry restocking - staple ingredients):
Input: "restock korean pantry"
Output:
{{
  "servings": 4,
  "ingredients": [
    {{"name": "gochugaru", "form": "powder", "quantity": 1, "unit": "jar"}},
    {{"name": "doenjang", "form": "paste", "quantity": 1, "unit": "jar"}},
    {{"name": "gochujang", "form": "paste", "quantity": 1, "unit": "jar"}},
    {{"name": "sesame oil", "form": "unspecified", "quantity": 1, "unit": "bottle"}},
    {{"name": "soy sauce", "form": "unspecified", "quantity": 1, "unit": "bottle"}},
    {{"name": "rice vinegar", "form": "unspecified", "quantity": 1, "unit": "bottle"}},
    {{"name": "sesame seeds", "form": "seeds", "quantity": 1, "unit": "jar"}}
  ]
}}

Example 3 (Fried rice - comprehensive Asian ingredients):
Input: "fried rice for 2"
Output:
{{
  "servings": 2,
  "ingredients": [
    {{"name": "rice", "form": "long_grain", "quantity": 2, "unit": "cup"}},
    {{"name": "eggs", "form": "unspecified", "quantity": 2, "unit": "each"}},
    {{"name": "soy sauce", "form": "unspecified", "quantity": 3, "unit": "tbsp"}},
    {{"name": "sesame oil", "form": "unspecified", "quantity": 1, "unit": "tsp"}},
    {{"name": "garlic", "form": "fresh", "quantity": 3, "unit": "cloves"}},
    {{"name": "ginger", "form": "fresh", "quantity": 1, "unit": "inch"}},
    {{"name": "green onions", "form": "whole", "quantity": 3, "unit": "stalks"}},
    {{"name": "carrots", "form": "chopped", "quantity": 1, "unit": "medium"}},
    {{"name": "peas", "form": "whole", "quantity": 0.5, "unit": "cup"}},
    {{"name": "oil", "form": "unspecified", "quantity": 2, "unit": "tbsp"}}
  ]
}}

Example 4 (Specific ingredient list):
Input: "fresh ginger, coriander powder, and cumin seeds"
Output:
{{
  "servings": 2,
  "ingredients": [
    {{"name": "ginger", "form": "fresh", "quantity": 1, "unit": "unit"}},
    {{"name": "coriander", "form": "powder", "quantity": 1, "unit": "unit"}},
    {{"name": "cumin", "form": "seeds", "quantity": 1, "unit": "unit"}}
  ]
}}

Example 5 (Indian biryani - spices and aromatics):
Input: "chicken biryani for 4"
Output:
{{
  "servings": 4,
  "ingredients": [
    {{"name": "chicken", "form": "thighs", "quantity": 1.5, "unit": "lb"}},
    {{"name": "basmati rice", "form": "basmati", "quantity": 2, "unit": "cups"}},
    {{"name": "onions", "form": "whole", "quantity": 2, "unit": "medium"}},
    {{"name": "yogurt", "form": "unspecified", "quantity": 1, "unit": "cup"}},
    {{"name": "ginger", "form": "fresh", "quantity": 2, "unit": "inches"}},
    {{"name": "garlic", "form": "fresh", "quantity": 8, "unit": "cloves"}},
    {{"name": "ghee", "form": "unspecified", "quantity": 3, "unit": "tbsp"}},
    {{"name": "garam masala", "form": "powder", "quantity": 2, "unit": "tsp"}},
    {{"name": "turmeric", "form": "powder", "quantity": 1, "unit": "tsp"}},
    {{"name": "coriander", "form": "seeds", "quantity": 1, "unit": "tbsp"}},
    {{"name": "cumin", "form": "seeds", "quantity": 1, "unit": "tsp"}},
    {{"name": "cardamom", "form": "whole_spice", "quantity": 4, "unit": "pods"}},
    {{"name": "mint", "form": "leaves", "quantity": 0.25, "unit": "cup"}},
    {{"name": "cilantro", "form": "leaves", "quantity": 0.25, "unit": "cup"}}
  ]
}}

NOW EXTRACT INGREDIENTS FROM THE USER'S MEAL PLAN ABOVE.

CRITICAL REQUIREMENTS:
- Every ingredient MUST have a "form" field from controlled vocabulary
- Extract ONLY ingredients appropriate for the requested recipe/dish type
- For recipe names (stir fry, biryani, pasta): infer typical ingredients for that dish
- For pantry restocking: suggest common staples for that cuisine
- Never substitute cumin→kalonji, bay leaves→blends, fresh→powder
- Output ONLY valid JSON (no markdown, no explanation text)
- No duplicate ingredients
- Use canonical names (e.g., "coriander" not "coriander powder" in name field; form="powder" instead)
- Match the cuisine/recipe type - don't mix Indian spices into Chinese stir fry, etc.

JSON OUTPUT:"""


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
    if not text:
        return None

    # Preprocess: Fix common LLM mistakes in JSON
    # Replace unquoted "unspecified" or "unknown" with null
    text = re.sub(r':\s*unspecified\s*([,}])', r': null\1', text)
    text = re.sub(r':\s*unknown\s*([,}])', r': null\1', text)

    # Try direct JSON parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object with "ingredients" key
    json_match = re.search(r'\{[^{}]*"ingredients"[\s\S]*?\}(?=\s*$)', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # More aggressive extraction
    brace_start = text.find('{')
    brace_end = text.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _validate_ingredients(data: dict) -> bool:
    """Validate that response has required structure."""
    if not isinstance(data, dict):
        return False

    if "ingredients" not in data:
        return False

    ingredients = data["ingredients"]
    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return False

    # Check each ingredient has required fields
    for ing in ingredients:
        if not isinstance(ing, dict):
            return False
        if "name" not in ing or not isinstance(ing["name"], str):
            return False
        # Form field is now required (can be added with default if missing)
        if "form" not in ing:
            logger.warning(f"Ingredient missing 'form' field: {ing.get('name')}, adding default")
            ing["form"] = "unspecified"

    return True


def _detect_override_mode(prompt: str) -> tuple[bool, Optional[str]]:
    """Detect if prompt contains INGREDIENT_LIST for override mode."""
    if "INGREDIENT_LIST:" in prompt:
        # Extract the ingredient list
        match = re.search(r'INGREDIENT_LIST:\s*([^\n]+)', prompt, re.IGNORECASE)
        if match:
            ingredient_list = match.group(1).strip()
            return True, ingredient_list
    return False, None


def _parse_ingredient_with_form(ingredient_text: str) -> tuple[str, str]:
    """
    Parse ingredient text to extract name and form.

    Examples:
        "fresh ginger" → ("ginger", "fresh")
        "coriander powder" → ("coriander", "powder")
        "cumin seeds" → ("cumin", "seeds")
        "mint leaves" → ("mint", "leaves")
        "chicken thighs" → ("chicken", "thighs")
        "basmati rice" → ("basmati rice", "basmati")
    """
    text_lower = ingredient_text.lower().strip()

    # Check for form keywords at start
    if text_lower.startswith("fresh "):
        return text_lower.replace("fresh ", ""), "fresh"
    if text_lower.startswith("whole "):
        return text_lower.replace("whole ", ""), "whole"
    if text_lower.startswith("chopped "):
        return text_lower.replace("chopped ", ""), "chopped"
    if text_lower.startswith("ground "):
        return text_lower.replace("ground ", ""), "ground"

    # Check for form keywords at end
    if text_lower.endswith(" powder"):
        return text_lower.replace(" powder", ""), "powder"
    if text_lower.endswith(" seeds"):
        return text_lower.replace(" seeds", ""), "seeds"
    if text_lower.endswith(" leaves"):
        return text_lower.replace(" leaves", ""), "leaves"
    if text_lower.endswith(" paste"):
        return text_lower.replace(" paste", ""), "paste"
    if text_lower.endswith(" thighs"):
        return text_lower.replace(" thighs", ""), "thighs"
    if text_lower.endswith(" breast"):
        return text_lower.replace(" breast", ""), "breast"
    if text_lower.endswith(" drumsticks"):
        return text_lower.replace(" drumsticks", ""), "drumsticks"

    # Special cases
    if "basmati" in text_lower and "rice" in text_lower:
        return text_lower, "basmati"
    if "jasmine" in text_lower and "rice" in text_lower:
        return text_lower, "jasmine"

    # Default
    return text_lower, "unspecified"


def extract_ingredients_with_llm(
    client,  # BaseLLMClient (Anthropic, Ollama, Gemini, etc.)
    prompt: str,
    servings: int = 4,
) -> Optional[list[dict]]:
    """
    Extract ingredients from user prompt using LLM (Claude, Ollama, etc.).

    Args:
        client: LLM client instance (BaseLLMClient - Anthropic, Ollama, Gemini, etc.)
        prompt: User's natural language request
        servings: Number of servings

    Returns:
        List of ingredient dicts, or None if extraction failed.
        Each dict has: name, form, quantity, unit, notes (optional)
    """
    if not client:
        logger.warning("No LLM client provided")
        return None

    # Check for override mode
    is_override, ingredient_list = _detect_override_mode(prompt)

    if is_override and ingredient_list:
        logger.info(f"Override mode detected: {ingredient_list}")
        # Try LLM first for override mode
        formatted_prompt = OVERRIDE_MODE_PROMPT.format(
            prompt=prompt,
            ingredient_list=ingredient_list,
            servings=servings,
        )
    else:
        # Normal extraction mode
        formatted_prompt = INGREDIENT_EXTRACTION_PROMPT.format(
            prompt=prompt,
            servings=servings,
        )

    # Call LLM (works with Anthropic, Ollama, Gemini, etc.)
    try:
        response = client.generate_sync(
            prompt=formatted_prompt,
            system=None,  # System prompt is embedded in formatted_prompt
            max_tokens=3000,  # Increased for longer ingredient lists
            temperature=0.3,  # Moderate temperature for comprehensive extraction while maintaining structure
        )
        response_text = response.text if response else None
    except Exception as e:
        logger.error(f"LLM API call failed for ingredient extraction: {e}")
        response_text = None

    if not response_text:
        logger.warning("LLM API call failed for ingredient extraction")
        return None

    # Parse JSON
    parsed = _parse_json_response(response_text)
    if not parsed:
        logger.warning(f"Failed to parse JSON from response: {response_text[:200]}")

        # If override mode and LLM failed, use deterministic fallback
        if is_override and ingredient_list:
            logger.info("LLM failed in override mode, using deterministic fallback")
            return _deterministic_override_parse(ingredient_list, servings)

        return None

    # Validate structure
    if not _validate_ingredients(parsed):
        logger.warning(f"Invalid ingredient structure: {parsed}")

        # If override mode and validation failed, use deterministic fallback
        if is_override and ingredient_list:
            logger.info("Validation failed in override mode, using deterministic fallback")
            return _deterministic_override_parse(ingredient_list, servings)

        return None

    ingredients = parsed["ingredients"]
    logger.info(f"LLM extracted {len(ingredients)} ingredients from: '{prompt}'")

    return ingredients


def _deterministic_override_parse(ingredient_list: str, servings: int) -> list[dict]:
    """
    Deterministic parsing of INGREDIENT_LIST without LLM.

    Args:
        ingredient_list: Pipe-separated ingredient list
        servings: Number of servings

    Returns:
        List of ingredient dicts with name, form, quantity, unit
    """
    ingredients = []
    items = [item.strip() for item in ingredient_list.split("|")]

    for item in items:
        if not item:
            continue

        # Parse name and form
        name, form = _parse_ingredient_with_form(item)

        ingredients.append({
            "name": name,
            "form": form,
            "quantity": 1,
            "unit": "unit"
        })

    logger.info(f"Deterministically parsed {len(ingredients)} ingredients from override list")
    return ingredients
