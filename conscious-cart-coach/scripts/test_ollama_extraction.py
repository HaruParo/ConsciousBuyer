#!/usr/bin/env python3
"""Test LLM extraction with Ollama for diverse recipes"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.ingredient_agent import IngredientAgent

def test_ollama_extraction():
    """Test ingredient extraction using Ollama LLM"""

    # Initialize with LLM enabled (should use Ollama by default)
    agent = IngredientAgent(use_llm=True)

    print("=" * 100)
    print("TESTING OLLAMA LLM EXTRACTION")
    print("=" * 100)
    print(f"\nLLM Client: {type(agent.llm_client).__name__}")
    print(f"Use LLM: {agent.use_llm}")
    print(f"Has extractor: {agent._llm_extractor is not None}")
    print()

    # Test cases
    test_cases = [
        ("mushroom stir fry for 2", "Should extract mushrooms + stir fry vegetables"),
        ("restock korean pantry", "Should extract Korean pantry staples"),
        ("chicken biryani for 4", "Should extract biryani ingredients"),
    ]

    for user_prompt, expected in test_cases:
        print(f"\n{'=' * 100}")
        print(f"TEST: {user_prompt}")
        print(f"Expected: {expected}")
        print("-" * 100)

        result = agent.extract(user_prompt)

        if result.is_error:
            print(f"❌ ERROR: {result.error_message}")
            continue

        ingredients = result.facts.get("ingredients", [])

        print(f"\n✅ Extracted {len(ingredients)} ingredients:")
        for i, ing in enumerate(ingredients, 1):
            name = ing.get("name", "unknown")
            qty = ing.get("qty", "?")
            unit = ing.get("unit") or ""
            optional = "🔹 (optional)" if ing.get("optional") else ""
            print(f"  {i:2}. {name:20} - {qty} {unit}")

        # Check for expected ingredients
        ingredient_names = [ing.get("name", "").lower() for ing in ingredients]

        if "mushroom" in user_prompt.lower():
            has_mushrooms = any("mushroom" in name for name in ingredient_names)
            if has_mushrooms:
                print(f"\n✅ Contains mushrooms as expected!")
            else:
                print(f"\n⚠️  WARNING: No mushrooms found in extraction!")
                print(f"   Ingredient names: {ingredient_names}")

if __name__ == '__main__':
    test_ollama_extraction()
