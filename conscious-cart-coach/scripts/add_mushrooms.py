#!/usr/bin/env python3
"""Add mushroom products from TSV to source_listings.csv"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TSV_PATH = Path("/Users/hash/Downloads/Fresh_Direct_Mushrooms.tsv")
CSV_PATH = PROJECT_ROOT / "data/alternatives/source_listings.csv"

# Fresh mushroom products to add (excluding prepared foods, sauces, supplements)
MUSHROOM_PRODUCTS = [
    # Line 2
    ("produce_mushrooms", "Organic Baby Bella Mushrooms, Packaged", "FreshDirect", 3.49, "ea", "8 oz", "USDA Organic", "Cremini mushrooms", "staple", "", "Balanced", "Organic baby bella"),
    # Line 3
    ("produce_mushrooms", "Organic Heirloom Sliced Shiitake Mushrooms", "Mushroom King", 5.99, "ea", "4 oz", "USDA Organic", "Pre-sliced", "staple", "", "Conscious", "Premium organic shiitake"),
    # Line 4
    ("produce_mushrooms", "Sliced Baby Bella Mushrooms, Packaged", "FreshDirect", 1.49, "ea", "8 oz", "None (conventional)", "Pre-sliced, cheapest", "staple", "", "Cheaper", "Budget-friendly sliced mushrooms"),
    # Line 5
    ("produce_mushrooms", "Organic Gourmet Mushroom Blend, Packaged", "FreshDirect", 3.99, "ea", "4 oz", "USDA Organic", "Mixed varieties", "specialty", "", "Balanced", "Organic blend"),
    # Line 6
    ("produce_mushrooms", "Organic Heirloom Mushroom Medley", "Mushroom King", 5.99, "ea", "4 oz", "USDA Organic", "Mixed varieties", "specialty", "", "Conscious", "Premium organic medley"),
    # Line 7
    ("produce_mushrooms", "Organic White Mushrooms, Packaged", "FreshDirect", 3.49, "ea", "8 oz", "USDA Organic", "Button mushrooms", "staple", "", "Balanced", "Organic white mushrooms"),
    # Line 8
    ("produce_mushrooms", "Sliced Organic Baby Bella Mushrooms, Packaged", "FreshDirect", 3.49, "ea", "8 oz", "USDA Organic", "Pre-sliced", "staple", "", "Balanced", "Organic sliced cremini"),
    # Line 9
    ("produce_mushrooms", "White Button Mushrooms, Packaged", "FreshDirect", 2.99, "ea", "8 oz", "None (conventional)", "Standard white", "staple", "", "Cheaper", "Budget-friendly white mushrooms"),
    # Line 10
    ("produce_mushrooms", "Baby Bella Mushrooms, Packaged", "FreshDirect", 2.99, "ea", "8 oz", "None (conventional)", "Cremini", "staple", "", "Cheaper", "Budget-friendly baby bella"),
    # Line 11
    ("produce_mushrooms", "Organic Shiitake Mushroom Caps", "Mushroom King", 6.99, "ea", "8 oz", "USDA Organic", "Caps only", "specialty", "", "Conscious", "Premium organic shiitake caps"),
    # Line 12
    ("produce_mushrooms", "Organic Maitake Mushrooms", "Mushroom King", 5.99, "ea", "3.5 oz", "USDA Organic", "Hen of the woods", "specialty", "", "Conscious", "Premium organic maitake"),
    # Line 13
    ("produce_mushrooms", "Organic Shiitake Mushrooms, Packaged", "FreshDirect", 4.49, "ea", "3.5 oz", "USDA Organic", "Whole shiitake", "specialty", "", "Balanced", "Organic shiitake"),
    # Line 14
    ("produce_mushrooms", "Oyster Mushrooms, Packaged", "FreshDirect", 2.99, "ea", "3.5 oz", "None (conventional)", "Oyster variety", "specialty", "", "Cheaper", "Budget oyster mushrooms"),
    # Line 15
    ("produce_mushrooms", "Organic Portabella Mushroom Caps, Packaged", "FreshDirect", 3.99, "ea", "6 oz", "USDA Organic", "Large caps", "staple", "", "Balanced", "Organic portabella caps"),
    # Line 16
    ("produce_mushrooms", "Organic Heirloom Asian Blend", "Mushroom King", 6.99, "ea", "8 oz", "USDA Organic", "Asian varieties", "specialty", "", "Conscious", "Premium Asian mushroom blend"),
    # Line 17
    ("produce_mushrooms", "Sliced White Mushroom", "FreshDirect", 2.99, "ea", "8 oz", "None (conventional)", "Pre-sliced white", "staple", "", "Cheaper", "Budget sliced white"),
    # Line 18
    ("produce_mushrooms", "Organic Heirloom Baby Shiitake Mushrooms", "Mushroom King", 5.99, "ea", "4 oz", "USDA Organic", "Small shiitake", "specialty", "", "Conscious", "Premium baby shiitake"),
    # Line 19
    ("produce_mushrooms", "Royal Trumpet Mushrooms, Packaged", "FreshDirect", 4.49, "ea", "4 oz", "None (conventional)", "King trumpet", "specialty", "", "Balanced", "King trumpet mushrooms"),
    # Line 20
    ("produce_mushrooms", "Organic Sliced King Trumpet Mushrooms", "Mushroom King", 5.99, "ea", "4 oz", "USDA Organic", "Pre-sliced", "specialty", "", "Conscious", "Organic sliced trumpet"),
    # Line 21
    ("produce_mushrooms", "Jumbo Maitake Mushroom", "Meadows and More", 14.49, "ea", "10 oz", "None (conventional)", "Large size", "specialty", "", "Premium Specialty", "Jumbo maitake"),
    # Line 22
    ("produce_mushrooms", "Yellowfoot Chanterelle Mushrooms", "FreshDirect", 7.99, "ea", "3.5 oz", "None (conventional)", "Wild variety", "specialty", "", "Premium Specialty", "Chanterelle mushrooms"),
    # Line 23
    ("produce_mushrooms", "Baby Petite White Mushrooms, Packaged", "FreshDirect", 2.99, "ea", "6 oz", "None (conventional)", "Small white", "staple", "", "Cheaper", "Petite white mushrooms"),
    # Line 24 - dried
    ("produce_mushrooms", "Dried Porcini Mushrooms", "Goodness Gardens", 7.49, "ea", "0.5 oz", "None (conventional)", "Dried", "specialty", "", "Premium Specialty", "Dried porcini"),
    # Line 25
    ("produce_mushrooms", "Steak Cut Mushrooms, Packaged", "FreshDirect", 2.99, "ea", "8 oz", "None (conventional)", "Thick sliced", "staple", "", "Cheaper", "Thick-cut mushrooms"),
    # Line 27
    ("produce_mushrooms", "Organic Lion's Mane Mushrooms", "Mushroom King", 6.99, "ea", "3.5 oz", "USDA Organic", "Lion's mane", "specialty", "", "Conscious", "Premium lion's mane"),
    # Line 31
    ("produce_mushrooms", "Hedgehog Mushrooms", "FreshDirect", 9.99, "ea", "3.5 oz", "None (conventional)", "Wild variety", "specialty", "", "Premium Specialty", "Hedgehog mushrooms"),
    # Line 32 - dried
    ("produce_mushrooms", "Dried Morel Mushrooms", "Goodness Gardens", 15.99, "ea", "0.5 oz", "None (conventional)", "Dried wild", "specialty", "", "Premium Specialty", "Dried morel"),
]

def add_mushrooms_to_csv():
    """Add mushroom products to source_listings.csv"""

    # Read existing CSV
    rows = []
    with open(CSV_PATH, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Find insertion point (after last produce entry or before protein_poultry)
    insert_index = len(rows)
    for i, row in enumerate(rows):
        if len(row) > 0 and row[0] == 'protein_poultry':
            insert_index = i
            break

    # Convert mushroom products to CSV format
    mushroom_rows = []
    for product in MUSHROOM_PRODUCTS:
        category, product_name, brand, price, unit, size, certifications, notes, item_type, seasonality, selected_tier, selection_reason = product
        mushroom_rows.append([
            category,
            product_name,
            brand,
            str(price),
            unit,
            size,
            certifications,
            notes,
            item_type,
            seasonality,
            selected_tier,
            selection_reason
        ])

    # Insert mushroom rows
    rows[insert_index:insert_index] = mushroom_rows

    # Write back
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"✅ Added {len(mushroom_rows)} mushroom products to source_listings.csv")
    print(f"   Inserted at line {insert_index}")

if __name__ == '__main__':
    add_mushrooms_to_csv()
