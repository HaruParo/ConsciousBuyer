#!/usr/bin/env python3
"""Test store split logic for various recipes"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.ingredient_agent import IngredientAgent
from src.orchestrator.store_split import split_ingredients_by_store
from src.orchestrator.ingredient_classifier import classify_ingredient_store_type
from src.planner.product_index import ProductIndex

def test_store_split():
    """Test store split for various recipes"""

    # Initialize components
    agent = IngredientAgent(use_llm=True)
    product_index = ProductIndex(use_synthetic=False)  # Use source_listings.csv

    test_cases = [
        "fried rice with gochujang for 2",
        "chicken biryani for 4",
        "mushroom stir fry for 2",
    ]

    for meal_plan in test_cases:
        print(f"\n{'=' * 100}")
        print(f"MEAL PLAN: {meal_plan}")
        print(f"{'=' * 100}\n")

        # Extract ingredients
        result = agent.extract(meal_plan)

        if result.is_error:
            print(f"❌ ERROR: {result.error_message}")
            continue

        ingredients = result.facts.get("ingredients", [])
        ingredient_names = [ing.get("name") for ing in ingredients]

        print(f"📦 Extracted {len(ingredients)} ingredients:")
        for i, name in enumerate(ingredient_names, 1):
            print(f"  {i:2}. {name}")

        # Classify each ingredient
        print(f"\n🏷️  Ingredient classification:")
        for name in ingredient_names:
            classification = classify_ingredient_store_type(name)
            print(f"  {name:25} → {classification}")

        # Get product candidates
        candidates_by_ingredient = {}
        for name in ingredient_names:
            candidates = product_index.retrieve(name, max_candidates=6)
            candidates_by_ingredient[name] = [
                {
                    "title": c.title,
                    "price": c.price,
                    "brand": c.brand,
                    "store": c.available_stores[0] if c.available_stores else "Unknown",
                    "in_stock": True
                }
                for c in candidates
            ]

            if candidates:
                print(f"  ✓ {name}: {len(candidates)} products found")
            else:
                print(f"  ❌ {name}: No products found")

        # Run store split logic
        print(f"\n🏪 Store split analysis:")
        print(f"-" * 100)

        store_split = split_ingredients_by_store(
            ingredients=ingredient_names,
            candidates_by_ingredient=candidates_by_ingredient,
            meal_plan_text=meal_plan
        )

        print(f"\nStores needed: {store_split.total_stores_needed}")
        print(f"Efficiency rule applied: {store_split.applied_1_item_rule}")
        print(f"\nReasoning:")
        for line in store_split.reasoning:
            print(f"  {line}")

        print(f"\n📋 Store assignments:")
        for store_group in store_split.stores:
            print(f"\n  {store_group.store} ({store_group.delivery_estimate}):")
            print(f"    Type: {store_group.store_type}")
            print(f"    Primary: {store_group.is_primary}")
            print(f"    Count: {store_group.count} items")
            print(f"    Items: {', '.join(store_group.ingredients)}")

        if store_split.unavailable:
            print(f"\n  ❌ Unavailable ({len(store_split.unavailable)}):")
            for item in store_split.unavailable:
                print(f"    - {item}")

if __name__ == '__main__':
    test_store_split()
