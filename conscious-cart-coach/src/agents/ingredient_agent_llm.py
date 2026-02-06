"""
Enhanced Ingredient Agent with LLM Support (Ollama/Anthropic)

This is an example of how to update agents to use the unified LLM client.
It supports both rule-based extraction and LLM-enhanced extraction.
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.utils.llm_client import get_llm_client, LLMResponse


@dataclass
class Ingredient:
    """Ingredient data structure"""

    name: str
    amount: float
    unit: str
    category: Optional[str] = None
    notes: Optional[str] = None


class IngredientAgentLLM:
    """
    Ingredient extraction agent with LLM support

    Supports two modes:
    1. Rule-based: Fast, deterministic, predefined recipes
    2. LLM-enhanced: Flexible, understands natural language, adapts to context
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize ingredient agent

        Args:
            use_llm: If True, use LLM for extraction. If False, use rules.
        """
        self.use_llm = use_llm
        self.llm_client = get_llm_client() if use_llm else None

    def extract_ingredients(self, meal_plan: str) -> List[Ingredient]:
        """
        Extract ingredients from meal plan description

        Args:
            meal_plan: User's meal plan (e.g., "chicken biryani for 4")

        Returns:
            List of Ingredient objects
        """
        if self.use_llm:
            try:
                return self._extract_with_llm(meal_plan)
            except Exception as e:
                print(f"LLM extraction failed: {e}, falling back to rules")
                return self._extract_with_rules(meal_plan)
        else:
            return self._extract_with_rules(meal_plan)

    def _extract_with_llm(self, meal_plan: str) -> List[Ingredient]:
        """Extract ingredients using LLM (Ollama or Anthropic)"""

        prompt = f"""Extract ingredients from this meal plan: {meal_plan}

Return as a JSON array with this exact format:
[
  {{"name": "chicken", "amount": 1.5, "unit": "lb", "category": "protein"}},
  {{"name": "basmati rice", "amount": 2, "unit": "cup", "category": "grains"}},
  {{"name": "onion", "amount": 2, "unit": "medium", "category": "produce"}},
  {{"name": "cumin", "amount": 2, "unit": "tsp", "category": "spices"}}
]

Categories: protein, grains, produce, spices, dairy, pantry

Only return the JSON array, nothing else."""

        system_prompt = """You are a grocery shopping assistant that extracts ingredients from meal descriptions.
Be specific about quantities and units.
Consider standard recipe proportions for the given serving size.
Always return valid JSON."""

        response = self.llm_client.generate_sync(
            prompt=prompt, system=system_prompt, temperature=0.5, max_tokens=800
        )

        # Parse JSON response
        return self._parse_llm_response(response.text)

    def _parse_llm_response(self, response_text: str) -> List[Ingredient]:
        """Parse LLM response into Ingredient objects"""

        # Extract JSON from response (LLM might add extra text)
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON array found in LLM response")

        json_str = json_match.group(0)
        ingredients_data = json.loads(json_str)

        ingredients = []
        for item in ingredients_data:
            ingredients.append(
                Ingredient(
                    name=item.get("name", ""),
                    amount=float(item.get("amount", 1)),
                    unit=item.get("unit", ""),
                    category=item.get("category"),
                    notes=item.get("notes"),
                )
            )

        return ingredients

    def _extract_with_rules(self, meal_plan: str) -> List[Ingredient]:
        """Extract ingredients using predefined rules (fallback)"""

        meal_plan_lower = meal_plan.lower()

        # Extract serving size
        servings = 4  # default
        servings_match = re.search(r'for (\d+)', meal_plan_lower)
        if servings_match:
            servings = int(servings_match.group(1))

        # Detect dish type and return ingredients
        if "biryani" in meal_plan_lower:
            return self._get_biryani_ingredients(servings)
        elif "curry" in meal_plan_lower:
            return self._get_curry_ingredients(servings)
        elif "salad" in meal_plan_lower:
            return self._get_salad_ingredients(servings)
        else:
            # Generic fallback
            return self._get_generic_ingredients(meal_plan_lower, servings)

    def _get_biryani_ingredients(self, servings: int) -> List[Ingredient]:
        """Predefined biryani ingredients"""

        base_recipe = [
            Ingredient("chicken", 1.5, "lb", "protein"),
            Ingredient("basmati rice", 2, "cup", "grains"),
            Ingredient("onion", 2, "medium", "produce"),
            Ingredient("tomato", 2, "medium", "produce"),
            Ingredient("ginger", 2, "tbsp", "produce"),
            Ingredient("garlic", 4, "cloves", "produce"),
            Ingredient("yogurt", 1, "cup", "dairy"),
            Ingredient("cumin", 2, "tsp", "spices"),
            Ingredient("coriander", 1, "tbsp", "spices"),
            Ingredient("cardamom", 6, "pods", "spices"),
            Ingredient("cinnamon", 1, "stick", "spices"),
            Ingredient("bay leaves", 2, "leaves", "spices"),
        ]

        # Scale by servings (assuming base is for 4)
        scale_factor = servings / 4

        return [
            Ingredient(
                name=ing.name,
                amount=ing.amount * scale_factor,
                unit=ing.unit,
                category=ing.category,
            )
            for ing in base_recipe
        ]

    def _get_curry_ingredients(self, servings: int) -> List[Ingredient]:
        """Predefined curry ingredients"""

        base_recipe = [
            Ingredient("chicken", 1.5, "lb", "protein"),
            Ingredient("onion", 2, "medium", "produce"),
            Ingredient("tomato", 2, "medium", "produce"),
            Ingredient("garlic", 4, "cloves", "produce"),
            Ingredient("ginger", 1, "tbsp", "produce"),
            Ingredient("coconut milk", 1, "can", "pantry"),
            Ingredient("curry powder", 2, "tbsp", "spices"),
        ]

        scale_factor = servings / 4
        return [
            Ingredient(
                name=ing.name,
                amount=ing.amount * scale_factor,
                unit=ing.unit,
                category=ing.category,
            )
            for ing in base_recipe
        ]

    def _get_salad_ingredients(self, servings: int) -> List[Ingredient]:
        """Predefined salad ingredients"""

        base_recipe = [
            Ingredient("mixed greens", 8, "oz", "produce"),
            Ingredient("tomato", 2, "medium", "produce"),
            Ingredient("cucumber", 1, "medium", "produce"),
            Ingredient("olive oil", 2, "tbsp", "pantry"),
            Ingredient("lemon", 1, "whole", "produce"),
        ]

        scale_factor = servings / 4
        return [
            Ingredient(
                name=ing.name,
                amount=ing.amount * scale_factor,
                unit=ing.unit,
                category=ing.category,
            )
            for ing in base_recipe
        ]

    def _get_generic_ingredients(self, meal_plan: str, servings: int) -> List[Ingredient]:
        """Generic fallback for unknown dishes"""

        # Very basic extraction - real implementation would be more sophisticated
        return [
            Ingredient("ingredients needed", 1, "set", "unknown", notes=f"Could not parse: {meal_plan}")
        ]


# Example usage and testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing Ingredient Agent with LLM\n")
    print("=" * 60)

    # Test with LLM
    print("\n1. Testing with LLM (Ollama):")
    print("-" * 60)

    try:
        agent_llm = IngredientAgentLLM(use_llm=True)
        ingredients = agent_llm.extract_ingredients("chicken biryani for 4 people")

        print(f"Extracted {len(ingredients)} ingredients:")
        for ing in ingredients:
            print(f"  - {ing.amount} {ing.unit} {ing.name} ({ing.category})")

    except Exception as e:
        print(f"Error: {e}")

    # Test with rules
    print("\n2. Testing with Rules (fallback):")
    print("-" * 60)

    agent_rules = IngredientAgentLLM(use_llm=False)
    ingredients = agent_rules.extract_ingredients("chicken biryani for 6 people")

    print(f"Extracted {len(ingredients)} ingredients:")
    for ing in ingredients:
        print(f"  - {ing.amount} {ing.unit} {ing.name} ({ing.category})")

    print("\n" + "=" * 60)
