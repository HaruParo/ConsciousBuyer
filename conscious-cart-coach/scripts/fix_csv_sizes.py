#!/usr/bin/env python3
"""
Fix missing size_value in inventory CSVs.
Chicken products are sold per lb - populate typical package weights.
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FRESHDIRECT_CSV = PROJECT_ROOT / "data/inventories_trusted/freshdirect_inventory.csv"
WHOLEFOODS_CSV = PROJECT_ROOT / "data/inventories_trusted/wholefoods_inventory.csv"


def fix_freshdirect():
    """Fix FreshDirect CSV with realistic sizes"""
    rows = []

    with open(FRESHDIRECT_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Chicken products - sold per lb
            if row['category'] == 'protein_poultry' and row['ingredient_key'] == 'chicken':
                if not row['size_value'] or float(row['size_value']) == 0:
                    title_lower = row['title'].lower()

                    # Whole chicken: 3.5 lb
                    if 'whole chicken' in title_lower or row['ingredient_form'] == 'whole':
                        row['size_value'] = '3.5'
                        row['size_unit'] = 'lb'
                        # Convert $/lb to $/oz (1 lb = 16 oz)
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Boneless breast/thighs: 1.5 lb packages
                    elif 'boneless' in title_lower and ('breast' in title_lower or 'thigh' in title_lower):
                        row['size_value'] = '1.5'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Bone-in thighs, legs: 2 lb packages
                    elif 'bone in' in title_lower or 'thigh' in title_lower or 'leg' in title_lower:
                        row['size_value'] = '2.0'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Drumsticks: 2 lb packages
                    elif 'drumstick' in title_lower:
                        row['size_value'] = '2.0'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Ground chicken: 1 lb packages
                    elif 'ground' in title_lower or row['ingredient_form'] == 'ground':
                        row['size_value'] = '1.0'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Default for other chicken: 1.5 lb
                    else:
                        row['size_value'] = '1.5'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

            # Garlic - sold per head or package
            elif row['ingredient_key'] == 'garlic':
                if not row['size_value'] or float(row['size_value']) == 0:
                    # Default: 3 heads = ~3 oz
                    row['size_value'] = '3.0'
                    row['size_unit'] = 'oz'
                    # Recalculate unit price
                    price = float(row['price'])
                    size_oz = 3.0
                    row['unit_price'] = str(round(price / size_oz, 4))
                    row['unit_price_unit'] = 'oz'

            # Ginger - sold per piece
            elif row['ingredient_key'] == 'ginger':
                if not row['size_value'] or float(row['size_value']) == 0:
                    # Default: 1 piece = ~6 oz
                    row['size_value'] = '6.0'
                    row['size_unit'] = 'oz'
                    price = float(row['price'])
                    size_oz = 6.0
                    row['unit_price'] = str(round(price / size_oz, 4))
                    row['unit_price_unit'] = 'oz'

            # Mint/Cilantro bunches - sold per bunch
            elif row['ingredient_key'] in ('mint', 'cilantro'):
                if not row['size_value'] or float(row['size_value']) == 0:
                    # Default: 1 bunch = ~2 oz
                    row['size_value'] = '2.0'
                    row['size_unit'] = 'oz'
                    price = float(row['price'])
                    size_oz = 2.0
                    row['unit_price'] = str(round(price / size_oz, 4))
                    row['unit_price_unit'] = 'oz'

            rows.append(row)

    # Write back
    with open(FRESHDIRECT_CSV, 'w', newline='') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Fixed FreshDirect CSV: {len(rows)} rows")


def fix_wholefoods():
    """Fix Whole Foods CSV with realistic sizes"""
    rows = []

    with open(WHOLEFOODS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Chicken products - sold per lb
            if row['category'] == 'protein_poultry' and row['ingredient_key'] == 'chicken':
                if not row['size_value'] or float(row['size_value']) == 0:
                    title_lower = row['title'].lower()

                    # Whole chicken: 3.5 lb
                    if 'whole chicken' in title_lower or row['ingredient_form'] == 'whole':
                        row['size_value'] = '3.5'
                        row['size_unit'] = 'lb'
                        # Convert $/lb to $/oz (1 lb = 16 oz)
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Boneless breast/thighs: 1.5 lb packages
                    elif 'boneless' in title_lower and ('breast' in title_lower or 'thigh' in title_lower):
                        row['size_value'] = '1.5'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Bone-in thighs: 2 lb packages
                    elif 'bone in' in title_lower or 'thigh' in title_lower:
                        row['size_value'] = '2.0'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Drumsticks: 2 lb packages
                    elif 'drumstick' in title_lower:
                        row['size_value'] = '2.0'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Ground chicken: 1 lb packages
                    elif 'ground' in title_lower or row['ingredient_form'] == 'powder':
                        row['size_value'] = '1.0'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Rotisserie chicken: 2.5 lb
                    elif 'rotisserie' in title_lower:
                        row['size_value'] = '2.5'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

                    # Default: 1.5 lb
                    else:
                        row['size_value'] = '1.5'
                        row['size_unit'] = 'lb'
                        row['unit_price'] = str(round(float(row['price']) / 16, 4))
                        row['unit_price_unit'] = 'oz'

            rows.append(row)

    # Write back
    with open(WHOLEFOODS_CSV, 'w', newline='') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Fixed Whole Foods CSV: {len(rows)} rows")


if __name__ == '__main__':
    print("Fixing inventory CSVs with missing size information...")
    fix_freshdirect()
    fix_wholefoods()
    print("\n✅ All CSVs fixed!")
