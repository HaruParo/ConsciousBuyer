#!/usr/bin/env python3
"""Debug product retrieval issue"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.planner.product_index import ProductIndex

def debug_product_retrieval():
    """Debug why product retrieval is failing"""

    product_index = ProductIndex(use_synthetic=False)  # Use source_listings.csv

    print(f"Loaded inventory has {len(product_index.inventory)} categories:\n")
    for category, products in sorted(product_index.inventory.items()):
        print(f"  {category:30} → {len(products):3} products")

    print(f"\n{'=' * 100}\n")
    print("Testing ingredient normalization and retrieval:\n")

    # Test ingredients from our failed cases
    test_ingredients = [
        "rice",
        "eggs",
        "soy sauce",
        "sesame oil",
        "gochujang",
        "garlic",
        "ginger",
        "green onions",
        "carrots",
        "chicken",
        "mushrooms",
        "onions",
        "turmeric",
        "cumin",
        "ghee",
    ]

    for ingredient in test_ingredients:
        # Try to normalize
        normalized = product_index._normalize_ingredient(ingredient)

        # Try to retrieve
        candidates = product_index.retrieve(ingredient, max_candidates=3)

        # Check if category exists in inventory
        has_category = normalized in product_index.inventory
        category_count = len(product_index.inventory.get(normalized, []))

        status = "✅" if candidates else "❌"
        print(f"{status} {ingredient:20} → normalized: '{normalized:30}' → in_inventory: {has_category:5} ({category_count:3} products) → retrieved: {len(candidates)}")

        if candidates:
            for c in candidates[:2]:
                print(f"     - {c.title} (${c.price})")

if __name__ == '__main__':
    debug_product_retrieval()
