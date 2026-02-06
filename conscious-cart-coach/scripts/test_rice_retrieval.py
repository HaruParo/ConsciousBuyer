#!/usr/bin/env python3
"""Test basmati rice retrieval"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.planner.product_index import ProductIndex

def test_rice_retrieval():
    """Test if basmati rice can be retrieved"""

    product_index = ProductIndex(use_synthetic=False)

    print(f"Loaded {len(product_index.all_products)} total products")
    print(f"Categories: {len(product_index.inventory)}")

    # Check if grain_rice_dry category exists
    if "grain_rice_dry" in product_index.inventory:
        rice_count = len(product_index.inventory["grain_rice_dry"])
        print(f"\n✓ Found grain_rice_dry category with {rice_count} products")
        print("\nFirst 5 rice products:")
        for i, product in enumerate(product_index.inventory["grain_rice_dry"][:5]):
            print(f"  {i+1}. {product.title} - ${product.price}")
    else:
        print("\n❌ grain_rice_dry category NOT found!")

    # Test retrieval
    print("\n" + "=" * 80)
    print("Testing retrieval for 'basmati rice':")
    print("=" * 80)

    candidates = product_index.retrieve("basmati rice", max_candidates=5)

    if candidates:
        print(f"\n✓ Found {len(candidates)} candidates:")
        for i, product in enumerate(candidates):
            print(f"  {i+1}. {product.title} (${product.price}) - {product.store_type}")
    else:
        print("\n❌ No candidates found!")

    # Test yogurt too
    print("\n" + "=" * 80)
    print("Testing retrieval for 'yogurt':")
    print("=" * 80)

    yogurt_candidates = product_index.retrieve("yogurt", max_candidates=5)

    if yogurt_candidates:
        print(f"\n✓ Found {len(yogurt_candidates)} candidates:")
        for i, product in enumerate(yogurt_candidates):
            print(f"  {i+1}. {product.title} (${product.price}) - {product.store_type}")
    else:
        print("\n❌ No yogurt candidates found!")


if __name__ == '__main__':
    test_rice_retrieval()
