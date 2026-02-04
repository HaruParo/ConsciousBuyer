#!/usr/bin/env python3
"""Test synthetic inventory loading"""

from src.planner.product_index import ProductIndex

# Test loading synthetic inventories
print("Testing Synthetic Inventory Loading...")
index = ProductIndex(use_synthetic=True)

print(f'\nTotal products: {len(index.all_products)}')
print(f'Categories: {len(index.inventory)}')

# Test retrieval for biryani ingredients
print('\n=== Testing Biryani Ingredient Retrieval ===')
for ingredient in ['chicken', 'rice', 'garam masala', 'ghee']:
    candidates = index.retrieve(ingredient, max_candidates=6)
    print(f'\n{ingredient}: {len(candidates)} candidates')
    for c in candidates[:3]:
        print(f'  - {c.title} [{c.source_store_id}] ${c.price:.2f}')

# Check store exclusivity
print('\n=== Checking Store Exclusivity ===')
violations = []
for product in index.all_products:
    # Check 365 brand
    if '365' in product.brand and product.source_store_id != 'wholefoods':
        violations.append(f"365 product in {product.source_store_id}: {product.title}")

    # Check Pure Indian Foods
    if 'Pure Indian Foods' in product.brand and product.source_store_id != 'pure_indian_foods':
        violations.append(f"Pure Indian Foods product in {product.source_store_id}: {product.title}")

if violations:
    print("❌ Violations found:")
    for v in violations:
        print(f"  - {v}")
else:
    print("✅ No store exclusivity violations")

print("\n✅ Test complete!")
