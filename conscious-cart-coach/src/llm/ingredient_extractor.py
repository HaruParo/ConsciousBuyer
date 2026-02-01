"""LLM-powered ingredient extraction from natural language prompts."""

import json
import logging
import re
from typing import Optional

from anthropic import Anthropic

from .client import call_claude_with_retry

logger = logging.getLogger(__name__)

INGREDIENT_EXTRACTION_PROMPT = """Extract ingredients from this user request for grocery shopping.

USER REQUEST: {prompt}
SERVINGS: {servings}

Extract a structured list of ingredients with:
- name: ingredient name (e.g., "spinach", "chicken breast", "basmati rice")
- quantity: amount needed (e.g., "2 bunches", "1 lb", "2 cups")
- unit: normalized unit (e.g., "bunch", "lb", "cup", "oz")
- category: broad category (e.g., "produce_greens", "protein_poultry", "grain", "spice")
- optional: true if ingredient is optional/garnish, false otherwise

RULES:
1. Use common ingredient names (not brand names)
2. Normalize quantities for the specified servings using COOKING-AWARE SCALING:
   - Main ingredients (meat, rice, vegetables, beans): scale fully with servings (2x servings = 2x quantity)
   - Cooking fats (ghee, oil, butter): scale moderately (2x servings = 1.5x quantity, not 2x)
   - Aromatics (onion, garlic, ginger, chilies): scale moderately (2x servings = 1.6x quantity, not 2x)
   - Spices and herbs: scale minimally (2x servings = 1.3x quantity, not 2x) - you don't need double the spices for double servings!
   - Salt: scale moderately (2x servings = 1.5x quantity)
3. Include cooking essentials (oil, salt) if recipe requires them
4. Mark garnishes/optional items as optional: true
5. Use canonical categories: produce_*, protein_*, grain, dairy, spice, condiment, oil
6. If the request is vague ("something healthy"), suggest 5-8 common ingredients
7. Be conservative with spice quantities - it's easier to add more than remove

OUTPUT FORMAT (JSON only, no markdown):
{{
  "ingredients": [
    {{
      "name": "ingredient name",
      "quantity": "amount",
      "unit": "unit",
      "category": "category",
      "optional": false
    }}
  ]
}}"""


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
    if not text:
        return None

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

    return True


def extract_ingredients_with_llm(
    client: Anthropic,
    prompt: str,
    servings: int = 4,
) -> Optional[list[dict]]:
    """
    Extract ingredients from user prompt using Claude LLM.

    Args:
        client: Anthropic client instance
        prompt: User's natural language request
        servings: Number of servings

    Returns:
        List of ingredient dicts, or None if extraction failed.
        Each dict has: name, quantity, unit, category, optional
    """
    if not client:
        logger.warning("No Anthropic client provided")
        return None

    # Format prompt
    formatted_prompt = INGREDIENT_EXTRACTION_PROMPT.format(
        prompt=prompt,
        servings=servings,
    )

    # Call Claude with Opik tracing
    response_text = call_claude_with_retry(
        client=client,
        prompt=formatted_prompt,
        max_tokens=2048,
        temperature=0.0,  # Deterministic
        trace_name="ingredient_extraction",
        metadata={
            "user_prompt": prompt,
            "servings": servings,
            "operation": "extract_ingredients"
        }
    )

    if not response_text:
        logger.warning("Claude API call failed for ingredient extraction")
        return None

    # Parse JSON
    parsed = _parse_json_response(response_text)
    if not parsed:
        logger.warning(f"Failed to parse JSON from response: {response_text[:200]}")
        return None

    # Validate structure
    if not _validate_ingredients(parsed):
        logger.warning(f"Invalid ingredient structure: {parsed}")
        return None

    ingredients = parsed["ingredients"]
    logger.info(f"LLM extracted {len(ingredients)} ingredients from: '{prompt}'")

    return ingredients
