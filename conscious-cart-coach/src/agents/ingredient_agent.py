"""
Ingredient Agent - Extracts ingredients from user prompts.

This is the FIRST agent in the gated flow. It parses user requests
(recipes, meal plans, shopping lists) into structured ingredients.

Supports both LLM-powered extraction (Claude) and template-based fallback.

Returns AgentResult contract for all outputs.

Usage:
    from src.agents.ingredient_agent import IngredientAgent

    # With LLM (if available)
    agent = IngredientAgent(use_llm=True)
    result = agent.extract("I want to make chicken biryani for 4 people")

    # Template-only (no API calls)
    agent = IngredientAgent(use_llm=False)
    result = agent.extract("biryani for 4")
"""

import logging
from datetime import datetime
from typing import Any, Optional

from anthropic import Anthropic

from ..core.types import AgentResult, Evidence, make_result, make_error

logger = logging.getLogger(__name__)


# Common recipe templates for quick extraction
# (In production, this would be LLM-powered)
RECIPE_TEMPLATES = {
    "biryani": {
        "base_ingredients": [
            {"name": "basmati rice", "canonical": "rice_basmati", "qty": 2, "unit": "cups", "optional": False},
            {"name": "onions", "canonical": "onion", "qty": 2, "unit": "large", "optional": False},
            {"name": "tomatoes", "canonical": "tomato", "qty": 2, "unit": "medium", "optional": False},
            {"name": "yogurt", "canonical": "yogurt_plain", "qty": 1, "unit": "cup", "optional": False},
            {"name": "ginger", "canonical": "ginger_fresh", "qty": 2, "unit": "inch", "optional": False},
            {"name": "garlic", "canonical": "garlic", "qty": 6, "unit": "cloves", "optional": False},
            {"name": "green chilies", "canonical": "chili_green", "qty": 3, "unit": "pieces", "optional": True},
            {"name": "mint leaves", "canonical": "mint_fresh", "qty": 0.5, "unit": "cup", "optional": False},
            {"name": "cilantro", "canonical": "cilantro_fresh", "qty": 0.5, "unit": "cup", "optional": False},
            {"name": "ghee", "canonical": "ghee", "qty": 4, "unit": "tbsp", "optional": False},
            {"name": "biryani masala", "canonical": "spice_biryani", "qty": 2, "unit": "tbsp", "optional": False},
            {"name": "saffron", "canonical": "saffron", "qty": 1, "unit": "pinch", "optional": True},
        ],
        "protein_options": ["chicken", "lamb", "goat", "vegetable"],
        "servings": 4,
    },
    "chicken_tikka": {
        "base_ingredients": [
            {"name": "chicken breast", "canonical": "chicken_breast", "qty": 1, "unit": "lb", "optional": False},
            {"name": "yogurt", "canonical": "yogurt_plain", "qty": 1, "unit": "cup", "optional": False},
            {"name": "lemon", "canonical": "lemon", "qty": 1, "unit": "piece", "optional": False},
            {"name": "ginger", "canonical": "ginger_fresh", "qty": 1, "unit": "inch", "optional": False},
            {"name": "garlic", "canonical": "garlic", "qty": 4, "unit": "cloves", "optional": False},
            {"name": "tikka masala", "canonical": "spice_tikka", "qty": 2, "unit": "tbsp", "optional": False},
            {"name": "kashmiri chili", "canonical": "chili_kashmiri", "qty": 1, "unit": "tsp", "optional": True},
        ],
        "servings": 4,
    },
    "salad": {
        "base_ingredients": [
            {"name": "mixed greens", "canonical": "greens_mixed", "qty": 6, "unit": "cups", "optional": False},
            {"name": "tomatoes", "canonical": "tomato", "qty": 2, "unit": "medium", "optional": False},
            {"name": "cucumber", "canonical": "cucumber", "qty": 1, "unit": "medium", "optional": False},
            {"name": "olive oil", "canonical": "oil_olive", "qty": 3, "unit": "tbsp", "optional": False},
            {"name": "lemon", "canonical": "lemon", "qty": 1, "unit": "piece", "optional": False},
        ],
        "servings": 4,
    },
    "stir_fry": {
        "base_ingredients": [
            {"name": "bell peppers", "canonical": "pepper_bell", "qty": 2, "unit": "medium", "optional": False},
            {"name": "broccoli", "canonical": "broccoli", "qty": 2, "unit": "cups", "optional": False},
            {"name": "carrots", "canonical": "carrot", "qty": 2, "unit": "medium", "optional": False},
            {"name": "soy sauce", "canonical": "soy_sauce", "qty": 3, "unit": "tbsp", "optional": False},
            {"name": "sesame oil", "canonical": "oil_sesame", "qty": 1, "unit": "tbsp", "optional": False},
            {"name": "garlic", "canonical": "garlic", "qty": 3, "unit": "cloves", "optional": False},
            {"name": "ginger", "canonical": "ginger_fresh", "qty": 1, "unit": "inch", "optional": False},
        ],
        "protein_options": ["chicken", "beef", "tofu", "shrimp"],
        "servings": 4,
    },
}

# Common produce items for direct extraction
COMMON_PRODUCE = {
    "spinach", "kale", "lettuce", "arugula", "cabbage",
    "tomato", "tomatoes", "onion", "onions", "garlic",
    "carrot", "carrots", "broccoli", "cauliflower",
    "potato", "potatoes", "sweet potato", "sweet potatoes",
    "apple", "apples", "banana", "bananas", "orange", "oranges",
    "strawberry", "strawberries", "blueberry", "blueberries",
    "grape", "grapes", "peach", "peaches", "pear", "pears",
    "avocado", "avocados", "cucumber", "cucumbers",
    "bell pepper", "bell peppers", "zucchini", "eggplant",
    "mushroom", "mushrooms", "corn", "peas", "green beans",
    "lemon", "lemons", "lime", "limes", "ginger", "cilantro", "mint",
}


class IngredientAgent:
    """
    Agent that extracts ingredients from user prompts.

    Supports:
    - LLM-powered extraction (Claude) for natural language prompts
    - Template-based fallback for known recipes
    - Direct ingredient lists
    - Meal descriptions

    Never throws hard errors - returns best-guess with low confidence if unsure.
    """

    AGENT_NAME = "ingredient"

    def __init__(self, use_llm: bool = False, anthropic_client: Optional[Anthropic] = None):
        """
        Initialize IngredientAgent.

        Args:
            use_llm: Whether to use LLM for extraction (requires API key)
            anthropic_client: Optional pre-initialized Anthropic client
        """
        self.recipe_templates = RECIPE_TEMPLATES
        self.common_produce = COMMON_PRODUCE
        self.use_llm = use_llm
        self.anthropic_client = anthropic_client

        # Lazy import LLM module (only if needed)
        self._llm_extractor = None
        if self.use_llm:
            try:
                from ..llm.client import get_anthropic_client
                from ..llm.ingredient_extractor import extract_ingredients_with_llm
                self._llm_extractor = extract_ingredients_with_llm
                if not self.anthropic_client:
                    self.anthropic_client = get_anthropic_client()
                logger.info("IngredientAgent initialized with LLM support")
            except ImportError as e:
                logger.warning(f"LLM module not available: {e}. Falling back to templates.")
                self.use_llm = False

    def extract(self, user_prompt: str, servings: int | None = None) -> AgentResult:
        """
        Extract ingredients from a user prompt.

        Uses LLM if available, falls back to template matching.

        Args:
            user_prompt: User's request (recipe name, ingredients, etc.)
            servings: Optional serving size override

        Returns:
            AgentResult with ingredients list
        """
        try:
            # Try LLM extraction first (if enabled)
            if self.use_llm and self.anthropic_client and self._llm_extractor:
                logger.info(f"Attempting LLM extraction for: '{user_prompt}'")
                llm_result = self._extract_with_llm(user_prompt, servings)
                if llm_result:
                    logger.info("LLM extraction successful")
                    return llm_result
                else:
                    logger.warning("LLM extraction failed, falling back to templates")

            # Fall back to template-based extraction
            logger.info(f"Using template-based extraction for: '{user_prompt}'")
            return self._extract_with_templates(user_prompt, servings)

        except Exception as e:
            logger.error(f"Ingredient extraction failed: {e}")
            return make_error(self.AGENT_NAME, str(e))

    def _extract_with_llm(self, user_prompt: str, servings: int | None = None) -> Optional[AgentResult]:
        """Extract ingredients using LLM (Claude)."""
        if not self._llm_extractor or not self.anthropic_client:
            return None

        try:
            target_servings = servings or self._extract_servings(user_prompt.lower()) or 4

            llm_ingredients = self._llm_extractor(
                client=self.anthropic_client,
                prompt=user_prompt,
                servings=target_servings,
            )

            if not llm_ingredients:
                return None

            # Convert LLM format to our IngredientSpec format
            ingredients = []
            for ing in llm_ingredients:
                ingredients.append({
                    "name": ing.get("name", ""),
                    "canonical": ing.get("category", ing.get("name", "").replace(" ", "_")),
                    "qty": ing.get("quantity"),
                    "unit": ing.get("unit"),
                    "optional": ing.get("optional", False),
                    "confidence": 0.95,  # High confidence from LLM
                })

            explain = [
                f"LLM extracted {len(ingredients)} ingredient(s)",
                f"Servings: {target_servings}",
            ]

            evidence = [Evidence(
                source="Claude LLM",
                key="ingredient_extraction",
                value=f"{len(ingredients)} ingredients",
            )]

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "ingredients": ingredients,
                    "assumptions": ["Used LLM for natural language extraction"],
                    "confidence": 0.95,
                    "matched_recipe": None,
                    "servings": target_servings,
                    "extraction_method": "llm",
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return None

    def _extract_with_templates(self, user_prompt: str, servings: int | None = None) -> AgentResult:
        """Extract ingredients using template matching (original logic)."""
        try:
            prompt_lower = user_prompt.lower()
            ingredients = []
            assumptions = []
            confidence = 1.0  # Start high, reduce based on uncertainty

            # Try to match a known recipe template
            matched_recipe = None
            for recipe_name, template in self.recipe_templates.items():
                if recipe_name.replace("_", " ") in prompt_lower or recipe_name in prompt_lower:
                    matched_recipe = recipe_name
                    break

            if matched_recipe:
                # Use recipe template
                template = self.recipe_templates[matched_recipe]
                base_servings = template.get("servings", 4)
                target_servings = servings or self._extract_servings(prompt_lower) or base_servings
                scale = target_servings / base_servings

                for ing in template["base_ingredients"]:
                    ingredients.append({
                        "name": ing["name"],
                        "canonical": ing["canonical"],
                        "qty": round(ing["qty"] * scale, 1) if ing["qty"] else None,
                        "unit": ing["unit"],
                        "optional": ing["optional"],
                        "confidence": 0.9,  # High confidence for known recipes
                    })

                # Check for protein specification
                if "protein_options" in template:
                    protein = self._extract_protein(prompt_lower, template["protein_options"])
                    if protein:
                        ingredients.insert(0, {
                            "name": protein,
                            "canonical": protein.replace(" ", "_"),
                            "qty": round(1 * scale, 1),
                            "unit": "lb",
                            "optional": False,
                            "confidence": 0.85,
                        })
                    else:
                        assumptions.append(f"No protein specified, assuming chicken")
                        ingredients.insert(0, {
                            "name": "chicken",
                            "canonical": "chicken",
                            "qty": round(1 * scale, 1),
                            "unit": "lb",
                            "optional": False,
                            "confidence": 0.5,  # Lower confidence for assumption
                        })
                        confidence = 0.7

                assumptions.append(f"Using {matched_recipe} recipe template")
                if target_servings != base_servings:
                    assumptions.append(f"Scaled from {base_servings} to {target_servings} servings")

            else:
                # Try to extract direct produce items
                found_items = self._extract_produce(prompt_lower)

                if found_items:
                    for item in found_items:
                        ingredients.append({
                            "name": item,
                            "canonical": item.replace(" ", "_"),
                            "qty": None,
                            "unit": None,
                            "optional": False,
                            "confidence": 0.8,
                        })
                    assumptions.append("Extracted individual produce items")
                else:
                    # Unknown request - provide generic response
                    assumptions.append("Unknown recipe/request - please specify ingredients")
                    confidence = 0.3

                    # Suggest common items based on keywords
                    if "healthy" in prompt_lower or "salad" in prompt_lower:
                        ingredients = [
                            {"name": "mixed greens", "canonical": "greens_mixed", "confidence": 0.4},
                            {"name": "tomatoes", "canonical": "tomato", "confidence": 0.4},
                            {"name": "cucumber", "canonical": "cucumber", "confidence": 0.4},
                        ]
                        assumptions.append("Suggesting salad ingredients based on 'healthy' keyword")

            # Build explain bullets
            explain = []
            if matched_recipe:
                explain.append(f"Recognized recipe: {matched_recipe.replace('_', ' ').title()}")
            explain.append(f"Found {len(ingredients)} ingredient(s)")
            if assumptions:
                explain.append(f"Assumptions: {assumptions[0]}")

            # Build evidence
            evidence = []
            if matched_recipe:
                evidence.append(Evidence(
                    source="Recipe Templates",
                    key=matched_recipe,
                    value=f"{len(ingredients)} ingredients",
                ))

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "ingredients": ingredients,
                    "assumptions": assumptions,
                    "confidence": confidence,
                    "matched_recipe": matched_recipe,
                    "servings": servings or self._extract_servings(prompt_lower) or 4,
                    "extraction_method": "template",
                },
                explain=explain,
                evidence=evidence,
            )

        except Exception as e:
            logger.error(f"Template extraction error: {e}")
            return make_error(self.AGENT_NAME, str(e))

    def _extract_servings(self, text: str) -> int | None:
        """Extract serving size from text."""
        import re

        # Look for patterns like "for 4 people", "serves 6", "4 servings"
        patterns = [
            r"for (\d+) people",
            r"serves (\d+)",
            r"(\d+) servings",
            r"(\d+) portions",
            r"feed (\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        return None

    def _extract_protein(self, text: str, options: list[str]) -> str | None:
        """Extract protein choice from text."""
        for protein in options:
            if protein in text:
                return protein
        return None

    def _extract_produce(self, text: str) -> list[str]:
        """Extract produce items from text."""
        found = []
        for item in self.common_produce:
            if item in text:
                # Normalize to singular
                normalized = item.rstrip("es").rstrip("s") if item.endswith("s") else item
                if normalized not in found and item not in found:
                    found.append(item)
        return found

    def validate_ingredients(self, ingredients: list[dict]) -> AgentResult:
        """
        Validate a list of ingredients (check for obvious issues).

        Args:
            ingredients: List of ingredient dicts

        Returns:
            AgentResult with validation status
        """
        try:
            issues = []
            warnings = []

            for ing in ingredients:
                name = ing.get("name", "")
                confidence = ing.get("confidence", 1.0)

                if confidence < 0.5:
                    warnings.append(f"Low confidence for '{name}' - please confirm")

                if not name:
                    issues.append("Empty ingredient name found")

            explain = []
            if issues:
                explain.append(f"{len(issues)} issue(s) found")
            if warnings:
                explain.append(f"{len(warnings)} warning(s)")
            if not issues and not warnings:
                explain.append("All ingredients validated")

            return make_result(
                agent_name=self.AGENT_NAME,
                facts={
                    "valid": len(issues) == 0,
                    "issues": issues,
                    "warnings": warnings,
                    "ingredient_count": len(ingredients),
                },
                explain=explain,
                evidence=[],
            )

        except Exception as e:
            return make_error(self.AGENT_NAME, str(e))


# Convenience function
def get_ingredient_agent() -> IngredientAgent:
    """Get default ingredient agent instance."""
    return IngredientAgent()
