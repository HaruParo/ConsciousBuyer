#!/usr/bin/env python3
"""Debug chicken retrieval issue"""

from src.planner.product_index import ProductIndex

# Create fresh index
index = ProductIndex(use_synthetic=True)

# Check what's in inventory["chicken"]
chicken_list = index.inventory["chicken"]
print(f'inventory["chicken"] has {len(chicken_list)} items')
print(f'Type: {type(chicken_list)}')
print(f'ID: {id(chicken_list)}')

# Manually iterate and count
count = 0
for product in chicken_list:
    count += 1
    if count <= 5:
        print(f'  Item {count}: {product.product_id} [{product.source_store_id}] {product.title}')

print(f'\\nTotal items iterated: {count}')

# Try direct indexing
print(f'\\nDirect indexing:')
for i in range(min(5, len(chicken_list))):
    p = chicken_list[i]
    print(f'  [{i}]: {p.product_id} [{p.source_store_id}] {p.title}')

# Call retrieve()
print(f'\\nCalling retrieve():')
candidates = index.retrieve('chicken', max_candidates=10)
print(f'Retrieved {len(candidates)} candidates')
for c in candidates[:5]:
    print(f'  - [{c.source_store_id}] {c.title}')
