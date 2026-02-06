#!/usr/bin/env python3
"""Test LLM extraction with random/unique recipes"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.ingredient_agent import IngredientAgent

def test_random_recipes():
    """Test with random recipes that don't match any template"""

    agent = IngredientAgent(use_llm=True)

    print("=" * 100)
    print("TESTING RANDOM/UNIQUE RECIPES (No templates)")
    print("=" * 100)
    print(f"LLM Client: {type(agent.llm_client).__name__}")
    print()

    # Random recipes that definitely don't match templates
    test_cases = [
        "spicy tofu scramble with spinach",
        "thai basil eggplant",
        "moroccan lentil soup",
        "greek salad with feta",
        "honey garlic salmon",
    ]

    for prompt in test_cases:
        print(f"\n{'=' * 100}")
        print(f"PROMPT: {prompt}")
        print("-" * 100)

        result = agent.extract(prompt, servings=2)

        if result.is_error:
            print(f"❌ ERROR: {result.error_message}")
            continue

        ingredients = result.facts.get("ingredients", [])
        extraction_method = result.facts.get("extraction_method", "unknown")

        print(f"Method: {extraction_method}")
        print(f"Extracted {len(ingredients)} ingredients:")

        for i, ing in enumerate(ingredients, 1):
            name = ing.get("name", "unknown")
            qty = ing.get("qty", "?")
            unit = ing.get("unit") or ""
            print(f"  {i:2}. {name:20} - {qty} {unit}")

if __name__ == '__main__':
    test_random_recipes()
