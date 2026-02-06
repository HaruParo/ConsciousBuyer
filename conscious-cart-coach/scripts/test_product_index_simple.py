#!/usr/bin/env python3
"""Simple test of ProductIndex loading"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 100)
print("TEST 1: Create ProductIndex with use_synthetic=False")
print("=" * 100)

from src.planner.product_index import ProductIndex

# Create index WITHOUT importing product_agent first
index1 = ProductIndex(use_synthetic=False)

print(f"\nAfter creation:")
print(f"  inventory keys: {len(index1.inventory)}")
print(f"  all_products: {len(index1.all_products)}")

if index1.inventory:
    print(f"\nFirst 5 categories:")
    for i, (cat, prods) in enumerate(sorted(index1.inventory.items())[:5]):
        print(f"  {cat:30} → {len(prods):3} products")
else:
    print("\n❌ inventory is EMPTY!")

print("\n" + "=" * 100)
print("TEST 2: Import product_agent (triggers global LOADED_INVENTORY)")
print("=" * 100)

from src.agents.product_agent import LOADED_INVENTORY, SIMULATED_INVENTORY

print(f"\nLOADED_INVENTORY keys: {len(LOADED_INVENTORY)}")
print(f"SIMULATED_INVENTORY keys: {len(SIMULATED_INVENTORY)}")

if LOADED_INVENTORY:
    print(f"\nFirst 5 LOADED_INVENTORY categories:")
    for i, (cat, prods) in enumerate(sorted(LOADED_INVENTORY.items())[:5]):
        print(f"  {cat:30} → {len(prods):3} products")
