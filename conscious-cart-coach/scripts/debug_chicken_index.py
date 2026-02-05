#!/usr/bin/env python3
"""Debug script to check chicken products in the product index"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.planner.product_index import ProductIndex

def main():
    print("=" * 80)
    print("Chicken Products Debug")
    print("=" * 80)

    # Load index
    index = ProductIndex()

    # Check what's in protein_poultry category
    print("\n1. Checking protein_poultry category:")
    if "protein_poultry" in index.inventory:
        chicken_products = index.inventory["protein_poultry"]
        print(f"   Found {len(chicken_products)} products in protein_poultry")

        # Filter for Bell & Evans
        bell_evans = [p for p in chicken_products if "bell" in p.brand.lower()]
        print(f"   Found {len(bell_evans)} Bell & Evans products:")
        for p in bell_evans:
            print(f"     - {p.title} ({p.brand}) - {p.source_store_id}")
    else:
        print("   ⚠️  No protein_poultry category found!")

    # Try retrieving chicken products
    print("\n2. Testing retrieve() for 'chicken legs':")
    candidates = index.retrieve("chicken legs", max_candidates=10)
    print(f"   Found {len(candidates)} candidates:")
    for c in candidates[:5]:
        print(f"     - {c.title} ({c.brand}) - {c.source_store_id}")

    print("\n3. Testing retrieve() for 'chicken drumsticks':")
    candidates = index.retrieve("chicken drumsticks", max_candidates=10)
    print(f"   Found {len(candidates)} candidates:")
    for c in candidates[:5]:
        print(f"     - {c.title} ({c.brand}) - {c.source_store_id}")

    print("\n4. Testing retrieve() for 'chicken thighs':")
    candidates = index.retrieve("chicken thighs", max_candidates=10)
    print(f"   Found {len(candidates)} candidates:")
    for c in candidates[:5]:
        print(f"     - {c.title} ({c.brand}) - {c.source_store_id}")

    # Check all_products
    print(f"\n5. Total products loaded: {len(index.all_products)}")
    print(f"   Categories: {list(index.inventory.keys())}")

if __name__ == "__main__":
    main()
