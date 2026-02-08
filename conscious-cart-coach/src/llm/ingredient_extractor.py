"""LLM-powered ingredient extraction from natural language prompts."""

import json
import logging
import os
import re
from typing import Optional

# Type hints only - actual client is passed in
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Opik tracking (optional)
try:
    import opik
    # Configure Opik on import if API key available
    opik_api_key = os.environ.get("OPIK_API_KEY")
    if opik_api_key:
        opik.configure(
            api_key=opik_api_key,
            workspace=os.environ.get("OPIK_WORKSPACE", "default"),
        )
    OPIK_AVAILABLE = True
except ImportError:
    opik = None
    OPIK_AVAILABLE = False
except Exception:
    opik = None
    OPIK_AVAILABLE = False

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

# System prompt - concise instructions (reusable context)
INGREDIENT_SYSTEM_PROMPT = """You extract ingredients from meal requests as JSON. Rules:
- Output ONLY valid JSON, no markdown/explanation
- quantity: number or null (never strings like "unspecified")
- form: fresh|leaves|whole|chopped|paste|powder|seeds|whole_spice|thighs|breast|ground|basmati|unspecified
- Match cuisine (no cumin in Chinese, no soy sauce in Italian)
- Be comprehensive for recipe names (include aromatics, oils, seasonings)"""

# Minimal user prompt with 1 example
INGREDIENT_EXTRACTION_PROMPT = """Extract ingredients from: {prompt}
Servings: {servings}

Schema: {{"servings": N, "ingredients": [{{"name": str, "form": str, "quantity": num|null, "unit": str|null}}]}}

Example - "stir fry for 2":
{{"servings": 2, "ingredients": [
  {{"name": "mushrooms", "form": "whole", "quantity": 8, "unit": "oz"}},
  {{"name": "soy sauce", "form": "unspecified", "quantity": 3, "unit": "tbsp"}},
  {{"name": "ginger", "form": "fresh", "quantity": 1, "unit": "inch"}},
  {{"name": "garlic", "form": "fresh", "quantity": 3, "unit": "cloves"}},
  {{"name": "oil", "form": "unspecified", "quantity": 2, "unit": "tbsp"}}
]}}

JSON:"""


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

    # Start Opik trace
    trace = None
    if OPIK_AVAILABLE and opik:
        try:
            trace = opik.trace(
                name="ingredient_extraction",
                input={
                    "prompt": prompt,
                    "servings": servings,
                },
                project_name=os.environ.get("OPIK_PROJECT_NAME", "consciousbuyer"),
            )
        except Exception as e:
            logger.debug(f"Opik trace failed to start: {e}")

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
            system=INGREDIENT_SYSTEM_PROMPT,  # Concise system prompt
            max_tokens=2000,
            temperature=0.2,
        )
        response_text = response.text if response else None
    except Exception as e:
        logger.error(f"LLM API call failed for ingredient extraction: {e}")
        if trace:
            trace.end(output={"error": str(e)})
        response_text = None

    if not response_text:
        logger.warning("LLM API call failed for ingredient extraction")
        if trace:
            trace.end(output={"error": "Empty response"})
        return None

    # Parse JSON
    parsed = _parse_json_response(response_text)
    if not parsed:
        logger.warning(f"Failed to parse JSON from response: {response_text[:200]}")

        # If override mode and LLM failed, use deterministic fallback
        if is_override and ingredient_list:
            logger.info("LLM failed in override mode, using deterministic fallback")
            ingredients = _deterministic_override_parse(ingredient_list, servings)
            if trace:
                trace.end(output={"ingredients": ingredients, "method": "fallback"})
            return ingredients

        if trace:
            trace.end(output={"error": "JSON parse failed"})
        return None

    # Validate structure
    if not _validate_ingredients(parsed):
        logger.warning(f"Invalid ingredient structure: {parsed}")

        # If override mode and validation failed, use deterministic fallback
        if is_override and ingredient_list:
            logger.info("Validation failed in override mode, using deterministic fallback")
            ingredients = _deterministic_override_parse(ingredient_list, servings)
            if trace:
                trace.end(output={"ingredients": ingredients, "method": "fallback"})
            return ingredients

        if trace:
            trace.end(output={"error": "Validation failed"})
        return None

    ingredients = parsed["ingredients"]
    logger.info(f"LLM extracted {len(ingredients)} ingredients from: '{prompt}'")

    # End trace with success
    if trace:
        trace.end(output={
            "ingredients": [i.get("name") for i in ingredients],
            "count": len(ingredients),
        })

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
