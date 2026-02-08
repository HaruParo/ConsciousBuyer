"""
Ingredient Agent - Extracts ingredients from user prompts.

This is the FIRST agent in the gated flow. It parses user requests
(recipes, meal plans, shopping lists) into structured ingredients.

Supports both LLM-powered extraction (Anthropic, Ollama, Gemini, etc.) and template-based fallback.

Returns AgentResult contract for all outputs.

Usage:
    from src.agents.ingredient_agent import IngredientAgent

    # With LLM (supports Anthropic, Ollama, Gemini, etc.)
    agent = IngredientAgent(use_llm=True)
    result = agent.extract("I want to make chicken biryani for 4 people")

    # Template-only (no API calls)
    agent = IngredientAgent(use_llm=False)
    result = agent.extract("biryani for 4")
"""

import logging
from datetime import datetime
from typing import Any, Optional

from ..core.types import AgentResult, Evidence, make_result, make_error

logger = logging.getLogger(__name__)


# Common recipe templates for quick extraction
# (In production, this would be LLM-powered)
RECIPE_TEMPLATES = {
    "biryani": {
        "base_ingredients": [
            {"name": "basmati rice", "canonical": "rice", "qty": 2, "unit": "cups", "optional": False},
            {"name": "onions", "canonical": "onion", "qty": 2, "unit": "large", "optional": False},
            {"name": "tomatoes", "canonical": "tomatoes", "qty": 2, "unit": "medium", "optional": False},
            {"name": "yogurt", "canonical": "yogurt", "qty": 1, "unit": "cup", "optional": False},
            {"name": "ginger", "canonical": "ginger", "qty": 2, "unit": "inch", "optional": False},
            {"name": "garlic", "canonical": "garlic", "qty": 10, "unit": "cloves", "optional": False},
            {"name": "green chilies", "canonical": "hot_peppers", "qty": 3, "unit": "whole", "optional": False},
            {"name": "mint leaves", "canonical": "mint", "qty": 0.5, "unit": "cup", "optional": False},
            {"name": "cilantro", "canonical": "cilantro", "qty": 0.5, "unit": "cup", "optional": False},
            {"name": "ghee", "canonical": "ghee", "qty": 4, "unit": "tbsp", "optional": False},
            {"name": "cumin", "canonical": "cumin", "qty": 2, "unit": "tsp", "optional": False},
            {"name": "coriander", "canonical": "coriander", "qty": 2, "unit": "tsp", "optional": False},
            {"name": "cardamom", "canonical": "cardamom", "qty": 6, "unit": "pods", "optional": False},
            {"name": "cinnamon", "canonical": "cinnamon", "qty": 2, "unit": "sticks", "optional": False},
            {"name": "cloves", "canonical": "cloves", "qty": 6, "unit": "whole", "optional": False},
            {"name": "black pepper", "canonical": "black_pepper", "qty": 1, "unit": "tsp", "optional": False},
            {"name": "turmeric", "canonical": "turmeric", "qty": 1, "unit": "tsp", "optional": False},
            {"name": "bay leaves", "canonical": "bay_leaves", "qty": 2, "unit": "leaves", "optional": False},
            {"name": "saffron", "canonical": "saffron", "qty": 1, "unit": "pinch", "optional": True},
            {"name": "salt", "canonical": "salt", "qty": 1, "unit": "tsp", "optional": False},
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

    def __init__(self, use_llm: bool = False, llm_client = None):
        """
        Initialize IngredientAgent.

        Args:
            use_llm: Whether to use LLM for extraction
            llm_client: Optional pre-initialized LLM client (supports Anthropic, Ollama, Gemini, etc.)
        """
        self.recipe_templates = RECIPE_TEMPLATES
        self.common_produce = COMMON_PRODUCE
        self.use_llm = use_llm
        self.llm_client = llm_client

        # Lazy import LLM module (only if needed)
        self._llm_extractor = None
        if self.use_llm:
            try:
                print("[IngredientAgent] Initializing LLM support...")
                from ..utils.llm_client import get_llm_client
                from ..llm.ingredient_extractor import extract_ingredients_with_llm
                self._llm_extractor = extract_ingredients_with_llm
                if not self.llm_client:
                    self.llm_client = get_llm_client()
                print(f"[IngredientAgent] LLM client: {type(self.llm_client).__name__}")
                logger.info(f"IngredientAgent initialized with LLM support (provider: {type(self.llm_client).__name__})")
            except Exception as e:
                print(f"[IngredientAgent] ERROR initializing LLM: {type(e).__name__}: {e}")
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
            print(f"[IngredientAgent] extract() called - use_llm={self.use_llm}, has_client={self.llm_client is not None}, has_extractor={self._llm_extractor is not None}")
            if self.use_llm and self.llm_client and self._llm_extractor:
                print(f"[IngredientAgent] Attempting LLM extraction for: '{user_prompt}'")
                logger.info(f"Attempting LLM extraction for: '{user_prompt}'")
                llm_result = self._extract_with_llm(user_prompt, servings)
                if llm_result:
                    print("[IngredientAgent] LLM extraction successful")
                    logger.info("LLM extraction successful")
                    return llm_result
                else:
                    print("[IngredientAgent] LLM extraction failed, falling back to templates")
                    logger.warning("LLM extraction failed, falling back to templates")
            else:
                print(f"[IngredientAgent] Skipping LLM (disabled or not available)")

            # Fall back to template-based extraction
            print(f"[IngredientAgent] Using template-based extraction")
            logger.info(f"Using template-based extraction for: '{user_prompt}'")
            return self._extract_with_templates(user_prompt, servings)

        except Exception as e:
            logger.error(f"Ingredient extraction failed: {e}")
            return make_error(self.AGENT_NAME, str(e))

    def _extract_with_llm(self, user_prompt: str, servings: int | None = None) -> Optional[AgentResult]:
        """Extract ingredients using LLM (Anthropic, Ollama, Gemini, etc.)."""
        if not self._llm_extractor or not self.llm_client:
            print("[IngredientAgent._extract_with_llm] Missing extractor or client")
            return None

        try:
            target_servings = servings or self._extract_servings(user_prompt.lower()) or 4
            print(f"[IngredientAgent._extract_with_llm] Calling LLM extractor with servings={target_servings}")

            llm_ingredients = self._llm_extractor(
                client=self.llm_client,
                prompt=user_prompt,
                servings=target_servings,
            )

            print(f"[IngredientAgent._extract_with_llm] LLM returned: {len(llm_ingredients) if llm_ingredients else 0} ingredients")

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
                    # Apply cooking-aware scaling: spices don't scale linearly
                    ingredient_scale = self._get_ingredient_scale_factor(ing["name"], scale)

                    ingredients.append({
                        "name": ing["name"],
                        "canonical": ing["canonical"],
                        "qty": round(ing["qty"] * ingredient_scale, 1) if ing["qty"] else None,
                        "unit": ing["unit"],
                        "optional": ing["optional"],
                        "confidence": 0.9,  # High confidence for known recipes
                    })

                # Check for protein specification
                if "protein_options" in template:
                    protein = self._extract_protein(prompt_lower, template["protein_options"])
                    if protein:
                        protein_scale = self._get_ingredient_scale_factor(protein, scale)
                        ingredients.insert(0, {
                            "name": protein,
                            "canonical": protein.replace(" ", "_"),
                            "qty": round(1 * protein_scale, 1),
                            "unit": "lb",
                            "optional": False,
                            "confidence": 0.85,
                        })
                    else:
                        assumptions.append(f"No protein specified, assuming chicken")
                        chicken_scale = self._get_ingredient_scale_factor("chicken", scale)
                        ingredients.insert(0, {
                            "name": "chicken",
                            "canonical": "chicken",
                            "qty": round(1 * chicken_scale, 1),
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

    def _get_ingredient_scale_factor(self, ingredient_name: str, base_scale: float) -> float:
        """
        Get cooking-aware scale factor for an ingredient.

        In real cooking, different ingredients scale differently:
        - Main ingredients (meat, rice, vegetables): scale fully (1.0x)
        - Cooking fats (ghee, oil, butter): scale moderately (0.5x)
        - Aromatics (onion, garlic, ginger): scale moderately (0.6x)
        - Spices and herbs: scale minimally (0.3x) - you don't need 2x spices for 2x servings

        Args:
            ingredient_name: Name of the ingredient
            base_scale: The base scaling factor (servings_target / servings_base)

        Returns:
            Adjusted scale factor to apply to this ingredient's quantity
        """
        ingredient_lower = ingredient_name.lower()

        # Spices, seasonings, and herbs - minimal scaling
        spice_keywords = [
            "masala", "powder", "turmeric", "cumin", "coriander", "cardamom",
            "cinnamon", "clove", "bay", "bay leaf", "bay leaves", "pepper",
            "chili", "paprika", "saffron", "nutmeg", "ginger powder",
            "garlic powder", "cayenne", "curry", "fenugreek", "fennel",
            "star anise", "dried", "herb", "thyme", "rosemary", "oregano",
            "basil", "mint", "cilantro", "parsley", "sage"
        ]
        if any(spice in ingredient_lower for spice in spice_keywords):
            # Scale spices by only 30% of the base scale, with a minimum of 1.0
            # Example: 2x servings → 1.3x spices (not 2x)
            return max(1.0, 1.0 + (base_scale - 1.0) * 0.3)

        # Cooking fats and oils - moderate scaling
        fat_keywords = [
            "ghee", "oil", "butter", "olive oil", "vegetable oil",
            "coconut oil", "sesame oil", "canola oil"
        ]
        if any(fat in ingredient_lower for fat in fat_keywords):
            # Scale fats by 50% of the base scale
            # Example: 2x servings → 1.5x oil
            return max(1.0, 1.0 + (base_scale - 1.0) * 0.5)

        # Aromatics - moderate scaling
        aromatic_keywords = [
            "onion", "garlic", "ginger", "shallot", "scallion",
            "green onion", "leek", "chile", "chilli", "fresh ginger",
            "fresh garlic", "green chile", "green chili"
        ]
        if any(aromatic in ingredient_lower for aromatic in aromatic_keywords):
            # Scale aromatics by 60% of the base scale
            # Example: 2x servings → 1.6x aromatics
            return max(1.0, 1.0 + (base_scale - 1.0) * 0.6)

        # Main ingredients (default) - full scaling
        return base_scale

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
