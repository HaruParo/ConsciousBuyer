#!/usr/bin/env python3
"""
Update chicken products with accurate data from user-provided table.
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FRESHDIRECT_CSV = PROJECT_ROOT / "data/inventories_trusted/freshdirect_inventory.csv"

# Chicken products from user's table with accurate pricing
CHICKEN_PRODUCTS = {
    # Chicken Breasts
    "Organic Boneless Skinless Chicken Breast": {
        "brand": "Farmer Focus",
        "price": 9.19,
        "size_value": 1.5,  # 2-3ct ≈ 1.5 lb
        "size_unit": "lb",
        "organic": True,
        "form": "unknown"
    },
    "Boneless Skinless Chicken Breasts, Raised w/o Antibiotics": {
        "brand": "Springer Mountain Farms",
        "price": 6.49,
        "size_value": 1.5,
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Boneless Skinless Chicken Breast, Value Pack, Air-Chilled, Raised w/o Antibiotics": {
        "brand": "Katie's Best",
        "price": 7.49,
        "size_value": 2.5,  # 6ct ≈ 2.5 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Organic Boneless Skinless Breasts, Air-Chilled": {
        "brand": "Smart Chicken",
        "price": 13.49,
        "size_value": 1.0,  # 2ct ≈ 1 lb
        "size_unit": "lb",
        "organic": True,
        "form": "unknown"
    },
    "Boneless Skinless Chicken Breasts Value Pack, Raised w/o Antibiotics": {
        "brand": "Springer Mountain Farms",
        "price": 5.49,
        "size_value": 2.0,  # 5-7ct ≈ 2 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Boneless Skinless Chicken Breasts, Air-Chilled, Raised w/o Antibiotics": {
        "brand": "Katie's Best",
        "price": 7.99,
        "size_value": 1.5,  # 3ct ≈ 1.5 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },

    # Chicken Thighs
    "Organic Boneless Skinless Chicken Thighs": {
        "brand": "Farmer Focus",
        "price": 8.29,
        "size_value": 1.5,  # 4-5ct ≈ 1.5 lb
        "size_unit": "lb",
        "organic": True,
        "form": "unknown"
    },
    "Boneless Skinless Chicken Thighs, Raised w/o Antibiotics": {
        "brand": "Springer Mountain Farms",
        "price": 5.59,
        "size_value": 1.75,  # 5-6ct ≈ 1.75 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Bone-In Chicken Thighs, Air-Chilled, Raised w/o Antibiotics": {
        "brand": "Katie's Best",
        "price": 5.49,
        "size_value": 2.0,  # 4ct ≈ 2 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Bone-In Chicken Thighs, Raised w/o Antibiotics": {
        "brand": "Springer Mountain Farms",
        "price": 3.99,
        "size_value": 2.0,  # 4ct ≈ 2 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Boneless Skinless Chicken Thighs, Air-Chilled, Raised w/o Antibiotics": {
        "brand": "Katie's Best",
        "price": 6.99,
        "size_value": 1.5,  # 4-5ct ≈ 1.5 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Organic Boneless Skinless Thighs, Air-Chilled": {
        "brand": "Smart Chicken",
        "price": 9.99,
        "size_value": 1.5,  # 4ct ≈ 1.5 lb
        "size_unit": "lb",
        "organic": True,
        "form": "unknown"
    },

    # Whole Chicken
    "Organic Whole Chicken": {
        "brand": "Farmer Focus",
        "price": 4.99,
        "size_value": 3.5,
        "size_unit": "lb",
        "organic": True,
        "form": "whole"
    },
    "Whole Chicken, Air-Chilled, Raised w/o Antibiotics": {
        "brand": "Katie's Best",
        "price": 4.49,
        "size_value": 3.5,
        "size_unit": "lb",
        "organic": False,
        "form": "whole"
    },
    "Whole Chicken, Raised w/o Antibiotics": {
        "brand": "Springer Mountain Farms",
        "price": 3.49,
        "size_value": 3.5,
        "size_unit": "lb",
        "organic": False,
        "form": "whole"
    },
    "Organic Whole Chicken, Air-Chilled": {
        "brand": "Smart Chicken",
        "price": 6.49,
        "size_value": 3.5,
        "size_unit": "lb",
        "organic": True,
        "form": "whole"
    },

    # Drumsticks
    "Chicken Drumsticks, Raised w/o Antibiotics": {
        "brand": "Springer Mountain Farms",
        "price": 3.49,
        "size_value": 1.75,  # 4-5ct ≈ 1.75 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
    "Chicken Drumsticks, Air-Chilled, Raised w/o Antibiotics": {
        "brand": "Katie's Best",
        "price": 4.49,
        "size_value": 1.75,  # 4-6ct ≈ 1.75 lb
        "size_unit": "lb",
        "organic": False,
        "form": "unknown"
    },
}


def update_freshdirect():
    """Update FreshDirect CSV with accurate chicken data"""
    rows = []
    updated_count = 0

    with open(FRESHDIRECT_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check if this is a chicken product we have accurate data for
            if row['category'] == 'protein_poultry' and row['ingredient_key'] == 'chicken':
                title = row['title']

                if title in CHICKEN_PRODUCTS:
                    product_data = CHICKEN_PRODUCTS[title]

                    # Update with accurate data
                    row['brand'] = product_data['brand']
                    row['price'] = str(product_data['price'])
                    row['size_value'] = str(product_data['size_value'])
                    row['size_unit'] = product_data['size_unit']
                    row['organic'] = str(product_data['organic'])
                    row['ingredient_form'] = product_data['form']

                    # Calculate unit price: $/lb → $/oz (divide by 16)
                    unit_price = round(product_data['price'] / 16, 4)
                    row['unit_price'] = str(unit_price)
                    row['unit_price_unit'] = 'oz'

                    updated_count += 1
                    print(f"  ✓ Updated: {title} @ ${product_data['price']}/lb")

            rows.append(row)

    # Write back
    with open(FRESHDIRECT_CSV, 'w', newline='') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Updated {updated_count} chicken products in FreshDirect CSV")


if __name__ == '__main__':
    print("Updating FreshDirect chicken products with accurate data...")
    update_freshdirect()
