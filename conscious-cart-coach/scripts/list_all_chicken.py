#!/usr/bin/env python3
"""List all chicken products across all cuts"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def list_all_chicken():
    """List all chicken products grouped by cut"""

    products = {'thighs': [], 'breasts': [], 'drumsticks': [], 'whole': [], 'other': []}

    # Read FreshDirect
    freshdirect_csv = PROJECT_ROOT / "data/inventories_trusted/freshdirect_inventory.csv"
    with open(freshdirect_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['category'] == 'protein_poultry' and row['ingredient_key'] == 'chicken':
                if not row['size_value'] or float(row['size_value']) == 0:
                    continue  # Skip products without size

                product = {
                    'store': 'FreshDirect',
                    'title': row['title'],
                    'brand': row['brand'],
                    'price': float(row['price']),
                    'size': f"{row['size_value']} {row['size_unit']}",
                    'unit_price': float(row['unit_price']) if row['unit_price'] else 0,
                    'organic': row['organic'] == 'True'
                }

                title_lower = row['title'].lower()
                if 'thigh' in title_lower:
                    products['thighs'].append(product)
                elif 'breast' in title_lower:
                    products['breasts'].append(product)
                elif 'drumstick' in title_lower:
                    products['drumsticks'].append(product)
                elif 'whole' in title_lower or row['ingredient_form'] == 'whole':
                    products['whole'].append(product)
                else:
                    products['other'].append(product)

    # Read Whole Foods
    wholefoods_csv = PROJECT_ROOT / "data/inventories_trusted/wholefoods_inventory.csv"
    with open(wholefoods_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['category'] == 'protein_poultry' and row['ingredient_key'] == 'chicken':
                if not row['size_value'] or float(row['size_value']) == 0:
                    continue

                product = {
                    'store': 'Whole Foods',
                    'title': row['title'],
                    'brand': row['brand'],
                    'price': float(row['price']),
                    'size': f"{row['size_value']} {row['size_unit']}",
                    'unit_price': float(row['unit_price']) if row['unit_price'] else 0,
                    'organic': row['organic'] == 'True'
                }

                title_lower = row['title'].lower()
                if 'thigh' in title_lower:
                    products['thighs'].append(product)
                elif 'breast' in title_lower:
                    products['breasts'].append(product)
                elif 'drumstick' in title_lower:
                    products['drumsticks'].append(product)
                elif 'whole' in title_lower or row['ingredient_form'] == 'whole':
                    products['whole'].append(product)
                else:
                    products['other'].append(product)

    # Print results
    print(f"\n{'='*100}")
    print("CHICKEN PRODUCTS BY CUT TYPE (sorted: Organic first, then unit price)")
    print(f"{'='*100}\n")

    for cut_type, items in products.items():
        if not items:
            continue

        items.sort(key=lambda p: (not p['organic'], p['unit_price']))

        print(f"\n🍗 {cut_type.upper()} ({len(items)} products)")
        print("-" * 100)

        for i, p in enumerate(items[:5], 1):  # Show top 5 per category
            organic_badge = "✓ ORG" if p['organic'] else "      "
            print(f"  {i}. {organic_badge} | ${p['price']:5.2f}/lb | ${p['unit_price']:.4f}/oz | {p['size']:8} | {p['brand'][:20]:20} | {p['title'][:40]}")

    print(f"\n{'='*100}")
    print("💡 KEY INSIGHT:")
    print("   For 'chicken biryani', ANY cut (thighs/breasts/drumsticks) should be valid")
    print("   System should score: form_match=0 for ANY chicken cut (not penalize)")
    print(f"{'='*100}\n")


if __name__ == '__main__':
    list_all_chicken()
