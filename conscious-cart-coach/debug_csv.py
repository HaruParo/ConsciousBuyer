#!/usr/bin/env python3
"""Debug CSV reading"""

import csv
from pathlib import Path

# Read first 10 lines
target_file = Path("data/alternatives/source_listings.csv")

print("=== First 10 raw lines ===")
with open(target_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 10:
            break
        print(f"{i}: {repr(line)}")

print("\n=== CSV DictReader test ===")
with open(target_file, 'r', encoding='utf-8') as f:
    # Skip comment lines
    for line in f:
        if not line.startswith('#'):
            # This is the header line
            print(f"Header line: {repr(line)}")
            # Reset to start of this line
            f.seek(f.tell() - len(line.encode('utf-8')))
            break

    reader = csv.DictReader(f)
    print(f"Fieldnames: {reader.fieldnames}")

    # Read first 3 data rows
    for i, row in enumerate(reader):
        if i >= 3:
            break
        brand = row.get('brand', 'N/A')
        product_name = row.get('product_name', 'N/A')
        size = row.get('size', 'N/A')
        print(f"Row {i}: brand={brand}, product={product_name}, size={size}")

print("\n=== Check Pure Indian Foods entries ===")
with open(target_file, 'r', encoding='utf-8') as f:
    # Skip comment lines
    for line in f:
        if not line.startswith('#'):
            f.seek(f.tell() - len(line.encode('utf-8')))
            break

    reader = csv.DictReader(f)
    pif_count = 0
    pif_varies = 0

    for row in reader:
        brand = row.get('brand', '').strip()
        if brand == "Pure Indian Foods":
            pif_count += 1
            size = row.get('size', '').strip()
            if size == "varies":
                pif_varies += 1
                if pif_varies <= 3:
                    print(f"  - {row.get('product_name', 'N/A')}: size={size}")

    print(f"\nTotal Pure Indian Foods: {pif_count}")
    print(f"With 'varies' size: {pif_varies}")
