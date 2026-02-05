#!/usr/bin/env python3
"""List all chicken thigh products with scores"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def list_chicken_thighs():
    """List all chicken thigh products"""

    products = []

    # Read FreshDirect
    freshdirect_csv = PROJECT_ROOT / "data/inventories_trusted/freshdirect_inventory.csv"
    with open(freshdirect_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'thigh' in row['title'].lower() and row['category'] == 'protein_poultry':
                products.append({
                    'store': 'FreshDirect',
                    'title': row['title'],
                    'brand': row['brand'],
                    'price': float(row['price']),
                    'size': f"{row['size_value']} {row['size_unit']}" if row['size_value'] else "N/A",
                    'unit_price': float(row['unit_price']) if row['unit_price'] else 0,
                    'organic': row['organic'] == 'True'
                })

    # Read Whole Foods
    wholefoods_csv = PROJECT_ROOT / "data/inventories_trusted/wholefoods_inventory.csv"
    with open(wholefoods_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'thigh' in row['title'].lower() and row['category'] == 'protein_poultry':
                products.append({
                    'store': 'Whole Foods',
                    'title': row['title'],
                    'brand': row['brand'],
                    'price': float(row['price']),
                    'size': f"{row['size_value']} {row['size_unit']}" if row['size_value'] else "N/A",
                    'unit_price': float(row['unit_price']) if row['unit_price'] else 0,
                    'organic': row['organic'] == 'True'
                })

    # Sort by: organic first, then by unit price (lower is better)
    products.sort(key=lambda p: (not p['organic'], p['unit_price']))

    print(f"\n{'='*120}")
    print(f"CHICKEN THIGHS PRODUCTS (sorted by: Organic first, then unit price)")
    print(f"{'='*120}\n")

    for i, p in enumerate(products, 1):
        organic_badge = "✓ ORGANIC" if p['organic'] else "         "
        print(f"{i:2}. {organic_badge} | ${p['price']:5.2f}/lb | ${p['unit_price']:.4f}/oz | {p['size']:8} | {p['brand']:20} | {p['title'][:50]}")

    print(f"\n{'='*120}")
    print(f"Scoring Logic:")
    print(f"  1. Form match score (boneless thighs = best)")
    print(f"  2. Organic preference (organic = 0, non-organic = 1)")
    print(f"  3. Price (lower unit price = better)")
    print(f"{'='*120}\n")


if __name__ == '__main__':
    list_chicken_thighs()
