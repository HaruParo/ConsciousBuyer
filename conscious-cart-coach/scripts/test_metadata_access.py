#!/usr/bin/env python3
"""Test that metadata (packaging, nutrition, labels) is accessible"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.planner.product_index import ProductIndex

def test_metadata_access():
    """Test if packaging, nutrition, and labels are loaded and accessible"""

    product_index = ProductIndex(use_synthetic=False)

    print(f"✓ Loaded {len(product_index.all_products)} total products\n")

    # Test 1: Check grass-fed milk for labels
    print("=" * 80)
    print("TEST 1: Grass-Fed Milk (should have 'Grass-Fed' label)")
    print("=" * 80)

    milk_candidates = product_index.retrieve("milk", max_candidates=10)
    grassfed_found = False

    for product in milk_candidates:
        if "grassmilk" in product.title.lower() or "grass-fed" in product.title.lower():
            print(f"\n✓ Found: {product.title}")
            print(f"  Packaging: {product.packaging or '(empty)'}")
            print(f"  Nutrition: {product.nutrition or '(empty)'}")
            print(f"  Labels: {product.labels or '(empty)'}")
            if product.labels and "Grass-Fed" in product.labels:
                print(f"  ✅ Has 'Grass-Fed' label!")
                grassfed_found = True
            break

    if not grassfed_found:
        print("\n  ⚠️  No grass-fed milk found with label")

    # Test 2: Check spinach for packaging and labels
    print("\n" + "=" * 80)
    print("TEST 2: Organic Spinach (should have packaging + vegan label)")
    print("=" * 80)

    spinach_candidates = product_index.retrieve("spinach", max_candidates=5)

    for product in spinach_candidates[:3]:
        print(f"\n✓ {product.title}")
        print(f"  Packaging: {product.packaging or '(empty)'}")
        print(f"  Labels: {product.labels or '(empty)'}")

        if product.packaging:
            print(f"  ✅ Has packaging info!")
        if product.labels and ("Vegan" in product.labels or "Gluten-Free" in product.labels):
            print(f"  ✅ Has dietary labels!")

    # Test 3: Check basmati rice
    print("\n" + "=" * 80)
    print("TEST 3: Basmati Rice (should have packaging)")
    print("=" * 80)

    rice_candidates = product_index.retrieve("basmati rice", max_candidates=3)

    for product in rice_candidates[:3]:
        print(f"\n✓ {product.title}")
        print(f"  Price: ${product.price}")
        print(f"  Packaging: {product.packaging or '(empty)'}")
        print(f"  Labels: {product.labels or '(empty)'}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Check how many products have each field populated
    products_with_packaging = sum(1 for p in product_index.all_products if p.packaging)
    products_with_nutrition = sum(1 for p in product_index.all_products if p.nutrition)
    products_with_labels = sum(1 for p in product_index.all_products if p.labels)

    print(f"\nTotal products: {len(product_index.all_products)}")
    print(f"  With packaging: {products_with_packaging} ({100*products_with_packaging/len(product_index.all_products):.1f}%)")
    print(f"  With nutrition: {products_with_nutrition} ({100*products_with_nutrition/len(product_index.all_products):.1f}%)")
    print(f"  With labels: {products_with_labels} ({100*products_with_labels/len(product_index.all_products):.1f}%)")

    print("\n✅ Metadata fields are accessible in ProductCandidate!")


if __name__ == '__main__':
    test_metadata_access()
