#!/usr/bin/env python3
"""
Import FreshDirect inventory from TSV files to source_listings.csv format.

Converts seafood, rice, and dairy TSV files to the standard CSV format.
"""

import csv
import re
from pathlib import Path


def parse_size(size_str):
    """Parse size string and return normalized format."""
    if not size_str or size_str == '':
        return '', 'ea'

    # Clean up
    size_str = size_str.strip()

    # Handle "approx. X oz" format
    if 'approx.' in size_str.lower():
        size_str = size_str.lower().replace('approx.', '').strip()

    # Extract number and unit
    # Examples: "8oz", "1 lb", "12 oz", "1/2 gallon", "32fl oz"
    match = re.search(r'([\d\.\/]+)\s*(oz|lb|pound|g|kg|gallon|quart|fl\s*oz|ct|ea)', size_str, re.IGNORECASE)

    if match:
        amount = match.group(1)
        unit = match.group(2).lower().replace(' ', '')

        # Handle fractions
        if '/' in amount:
            parts = amount.split('/')
            amount = str(float(parts[0]) / float(parts[1]))

        # Normalize units
        if 'fl' in unit or unit == 'floz':
            return f"{amount} fl oz", "ea"
        elif unit in ['oz', 'lb', 'g', 'kg', 'gallon', 'quart']:
            return f"{amount} {unit}", "ea"
        elif unit == 'ct':
            return f"{amount} ct", "ea"

    # Default fallback
    if 'lb' in size_str.lower():
        return size_str, "lb"
    elif 'ct' in size_str.lower():
        return size_str, "ea"
    else:
        return size_str if size_str else "", "ea"


def parse_price(price_str):
    """Parse price string and return float."""
    if not price_str or price_str.strip() == '':
        return None

    # Remove $ and commas
    price_clean = price_str.replace('$', '').replace(',', '').strip()

    try:
        return float(price_clean)
    except ValueError:
        return None


def detect_certifications(product_name, category):
    """Detect certifications from product name."""
    certs = []
    name_lower = product_name.lower()

    if 'organic' in name_lower or 'USDA' in product_name:
        certs.append('USDA Organic')

    if 'wild' in name_lower and 'seafood' in category:
        certs.append('Wild-Caught')

    if 'farm-raised' in name_lower and 'seafood' in category:
        certs.append('Farm-Raised')

    if 'grass-fed' in name_lower or 'grassfed' in name_lower:
        certs.append('Grass-Fed')

    if 'free-range' in name_lower or 'cage-free' in name_lower:
        certs.append('Free-Range')

    if 'pasture-raised' in name_lower:
        certs.append('Pasture-Raised')

    if not certs:
        return 'None (conventional)'

    return '; '.join(certs)


def map_category(tsv_category, product_name):
    """Map TSV category to source_listings.csv category."""
    cat_lower = tsv_category.lower()
    name_lower = product_name.lower()

    # Seafood categories
    if 'salmon' in cat_lower:
        return 'protein_seafood_salmon'
    elif 'shrimp' in cat_lower:
        return 'protein_seafood_shrimp'
    elif cat_lower in ['scallops', 'mussels & clams', 'oysters']:
        return 'protein_seafood_shellfish'
    elif 'fish' in cat_lower:
        return 'protein_seafood_fish'
    elif 'prepped seafood' in cat_lower:
        return 'protein_seafood_prepared'
    elif cat_lower == 'frozen' and 'seafood' in name_lower:
        return 'protein_seafood_frozen'

    # Rice categories
    elif 'dry rice' in cat_lower:
        return 'grain_rice_dry'
    elif 'prepared rice' in cat_lower:
        return 'grain_rice_prepared'
    elif 'ready rice' in cat_lower or 'rice mix' in cat_lower:
        return 'grain_rice_instant'
    elif 'frozen meals' in cat_lower and 'rice' in name_lower:
        return 'grain_rice_frozen'
    elif 'rice noodles' in cat_lower or 'rice' in name_lower and 'pasta' in cat_lower:
        return 'grain_rice_noodles'
    elif 'rice cakes' in cat_lower or 'rice crackers' in name_lower:
        return 'grain_rice_snacks'
    elif 'rice pudding' in cat_lower:
        return 'grain_rice_pudding'

    # Dairy categories
    elif cat_lower == 'eggs':
        return 'dairy_eggs'
    elif cat_lower == 'milk':
        return 'dairy_milk'
    elif cat_lower == 'yogurt':
        return 'dairy_yogurt'
    elif cat_lower == 'butter':
        return 'dairy_butter'
    elif 'cheese' in cat_lower:
        return 'dairy_cheese'
    elif cat_lower == 'sour cream':
        return 'dairy_sour_cream'
    elif 'dips' in cat_lower or 'spreads' in cat_lower:
        return 'dairy_dips'
    elif 'packaged meats' in cat_lower:
        return 'protein_deli'

    # Default fallback
    return 'other'


def determine_tier(price, organic, category):
    """Determine selected_tier based on price and characteristics."""
    if organic:
        return 'Conscious'
    elif price and price < 5.0:
        return 'Cheaper'
    else:
        return 'Balanced'


def process_tsv_file(tsv_path, category_hint):
    """Process a single TSV file and return list of CSV rows."""
    rows = []

    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            brand = (row.get('Brand') or '').strip() or 'FreshDirect'
            product = (row.get('Product') or '').strip()
            category = (row.get('Category') or category_hint).strip()
            price_str = (row.get('Price') or '').strip()
            size = (row.get('Size') or '').strip()

            if not product:
                continue

            price = parse_price(price_str)
            if price is None or price == 0:
                continue  # Skip items with no valid price

            size_normalized, unit = parse_size(size)
            certifications = detect_certifications(product, category)
            csv_category = map_category(category, product)

            organic = 'Organic' in certifications
            tier = determine_tier(price, organic, csv_category)

            # Determine item_type
            if 'frozen' in product.lower() or 'frozen' in category.lower():
                item_type = 'convenience'
            elif 'prepared' in category.lower() or 'ready' in product.lower():
                item_type = 'convenience'
            else:
                item_type = 'staple'

            # Build notes (handle None values)
            notes = []
            sale_promo = row.get('Sale/Promo') or ''
            quality = row.get('Quality') or ''
            notes_field = row.get('Notes') or ''

            if sale_promo.strip():
                notes.append(sale_promo.strip())
            if quality.strip():
                notes.append(f"Quality: {quality.strip()}")
            if notes_field.strip():
                notes.append(notes_field.strip())

            notes_str = ' | '.join(notes) if notes else ''

            # Generate selection reason
            if organic:
                reason = f"Organic {csv_category.split('_')[-1]}"
            elif 'wild' in certifications.lower():
                reason = "Wild-caught seafood"
            elif tier == 'Cheaper':
                reason = "Budget-friendly option"
            else:
                reason = f"Good quality {csv_category.split('_')[-1]}"

            rows.append([
                csv_category,
                product,
                brand,
                f"{price:.2f}",
                unit,
                size_normalized,
                certifications,
                notes_str,
                item_type,
                '',  # seasonality
                tier,
                reason
            ])

    return rows


def main():
    """Main conversion script."""
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    # Input TSV files
    tsv_files = [
        ('Fresh_Direct_seafood.tsv', 'Seafood'),
        ('Fresh_Direct_rice.tsv', 'Rice'),
        ('Fresh_Direct_dairy.tsv', 'Dairy'),
    ]

    output_file = project_dir / 'data' / 'alternatives' / 'source_listings.csv'

    all_rows = []
    total_added = 0

    for tsv_file, category_hint in tsv_files:
        tsv_path = script_dir.parent / tsv_file
        if not tsv_path.exists():
            print(f"⚠️  Warning: {tsv_file} not found at {tsv_path}")
            continue

        rows = process_tsv_file(tsv_path, category_hint)
        all_rows.extend(rows)
        print(f"✓ Processed {len(rows)} products from {tsv_file}")
        total_added += len(rows)

    # Append to existing CSV
    with open(output_file, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)

    print(f"\n✓ Added {total_added} products to {output_file}")
    print(f"  - Seafood products")
    print(f"  - Rice products")
    print(f"  - Dairy products")


if __name__ == '__main__':
    main()
