#!/usr/bin/env python3
"""Update source_listings.csv with corrected sizes from pure_indian_foods_products.csv"""

import pandas as pd
from pathlib import Path

# File paths
base_dir = Path(__file__).parent
source_file = base_dir / "data" / "alternatives" / "pure_indian_foods_products.csv"
target_file = base_dir / "data" / "alternatives" / "source_listings.csv"

# Read pure_indian_foods_products.csv
print("Loading pure_indian_foods_products.csv...")
pure_df = pd.read_csv(source_file)
print(f"Loaded {len(pure_df)} products")

# Create mapping of product_name -> size
size_map = {}
for _, row in pure_df.iterrows():
    product_name = str(row['product_name']).strip()
    size = str(row['size']).strip()
    size_map[product_name] = size

print(f"Created size mapping for {len(size_map)} products")

# Read the comment lines from source_listings.csv
comment_lines = []
with open(target_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('#'):
            comment_lines.append(line)
        else:
            break

print(f"Found {len(comment_lines)} comment lines")

# Read source_listings.csv (skip comment lines)
print("\nLoading source_listings.csv...")
source_df = pd.read_csv(target_file, comment='#')
print(f"Loaded {len(source_df)} products")

# Update sizes for Pure Indian Foods products
updated_count = 0
for idx, row in source_df.iterrows():
    brand = str(row.get('brand', '')).strip()
    product_name = str(row.get('product_name', '')).strip()
    current_size = str(row.get('size', '')).strip()

    # Only update Pure Indian Foods products with "varies" size
    if brand == "Pure Indian Foods" and current_size == "varies":
        if product_name in size_map:
            new_size = size_map[product_name]
            source_df.at[idx, 'size'] = new_size
            updated_count += 1
            print(f"  Updated: {product_name}: varies -> {new_size}")
        else:
            print(f"  WARNING: No size found for: {product_name}")

print(f"\nUpdated {updated_count} products")

# Write back to file with comments preserved
print("\nWriting updated CSV...")
with open(target_file, 'w', encoding='utf-8', newline='') as f:
    # Write comment lines first
    for comment in comment_lines:
        f.write(comment)

    # Write CSV data (without index)
    source_df.to_csv(f, index=False)

print("Done!")
