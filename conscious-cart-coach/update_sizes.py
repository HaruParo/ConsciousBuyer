#!/usr/bin/env python3
"""Update source_listings.csv with corrected sizes from pure_indian_foods_products.csv"""

import csv
from pathlib import Path

# File paths
base_dir = Path(__file__).parent
source_file = base_dir / "data" / "alternatives" / "pure_indian_foods_products.csv"
target_file = base_dir / "data" / "alternatives" / "source_listings.csv"

# Read pure_indian_foods_products.csv to build a mapping of product_name -> size
size_map = {}
with open(source_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Key is product_name, value is size
        product_name = row['product_name'].strip()
        size = row['size'].strip()
        size_map[product_name] = size

print(f"Loaded {len(size_map)} products from pure_indian_foods_products.csv")

# Read source_listings.csv and update sizes
# First, read comment lines (lines starting with #)
comment_lines = []
with open(target_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('#'):
            comment_lines.append(line)
        else:
            break

# Now read the CSV data, skipping comment lines
rows = []
updated_count = 0
with open(target_file, 'r', encoding='utf-8') as f:
    # Skip comment lines
    for line in f:
        if not line.startswith('#'):
            break

    # Now read CSV from current position
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    for row in reader:
        brand = row.get('brand', '').strip()
        product_name = row.get('product_name', '').strip()
        current_size = row.get('size', '').strip()

        # Only update Pure Indian Foods products with "varies" size
        if brand == "Pure Indian Foods" and current_size == "varies":
            if product_name in size_map:
                new_size = size_map[product_name]
                row['size'] = new_size
                updated_count += 1
                print(f"Updated: {product_name}: varies -> {new_size}")
            else:
                print(f"WARNING: No size found for: {product_name}")

        rows.append(row)

# Write updated data back to source_listings.csv
with open(target_file, 'w', encoding='utf-8', newline='') as f:
    # Write comment lines first
    for comment in comment_lines:
        f.write(comment)

    # Write CSV data
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nUpdated {updated_count} products in source_listings.csv")
print("Done!")
