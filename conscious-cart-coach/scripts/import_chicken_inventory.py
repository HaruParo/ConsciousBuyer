#!/usr/bin/env python3
"""
Import FreshDirect chicken inventory from TSV to source_listings.csv format.

This TSV has a different format with "Price per lb" instead of total price.
"""

import csv
import re
from pathlib import Path


def parse_price(price_str):
    """Parse price string and return float."""
    if not price_str or price_str.strip() == '':
        return None
    price_clean = price_str.replace('$', '').replace(',', '').strip()
    try:
        return float(price_clean)
    except ValueError:
        return None


def detect_certifications(product_name, brand):
    """Detect certifications from product name and brand."""
    certs = []
    name_lower = product_name.lower()
    brand_lower = brand.lower() if brand else ''

    if 'organic' in name_lower or 'organic' in brand_lower:
        certs.append('USDA Organic')

    if 'pasture-raised' in name_lower:
        certs.append('Pasture-Raised')
    elif 'air-chilled' in name_lower:
        certs.append('Air-Chilled')

    if 'raised w/o antibiotics' in name_lower or 'raised without antibiotics' in name_lower:
        certs.append('No Antibiotics')

    if not certs:
        return 'None (conventional)'

    return '; '.join(certs)


def determine_cut_type(product_name):
    """Determine chicken cut type from product name."""
    name_lower = product_name.lower()

    if 'breast' in name_lower:
        return 'breast'
    elif 'thigh' in name_lower:
        return 'thigh'
    elif 'drumstick' in name_lower:
        return 'drumstick'
    elif 'wing' in name_lower:
        return 'wing'
    elif 'leg' in name_lower and 'whole' in name_lower:
        return 'leg'
    elif 'tender' in name_lower:
        return 'tender'
    elif 'whole' in name_lower or 'spatchcock' in name_lower or 'broiler' in name_lower:
        return 'whole'
    elif 'cut-up' in name_lower:
        return 'cut_up'
    else:
        return 'mixed'


def determine_tier(price_per_lb, organic):
    """Determine selected_tier based on price and characteristics."""
    if organic:
        return 'Conscious'
    elif price_per_lb and price_per_lb < 5.0:
        return 'Cheaper'
    else:
        return 'Balanced'


def process_chicken_tsv(tsv_path):
    """Process chicken TSV file and return list of CSV rows."""
    rows = []

    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            brand = (row.get('Brand') or '').strip() or 'FreshDirect'
            product = (row.get('Product') or '').strip()
            price_per_lb_str = (row.get('Price per lb') or '').strip()
            count = (row.get('Count') or '').strip()
            notes = (row.get('Notes') or '').strip()

            # Skip if no product name or marked as sold out
            if not product or 'sold out' in notes.lower():
                continue

            # Parse price per lb
            price_per_lb = parse_price(price_per_lb_str)
            if price_per_lb is None or price_per_lb == 0:
                continue

            # Assume 1.5 lb per package (standard)
            package_weight = 1.5
            total_price = price_per_lb * package_weight
            size = f"{package_weight} lb"

            # Detect certifications and cut type
            certifications = detect_certifications(product, brand)
            cut_type = determine_cut_type(product)

            # Determine organic status and tier
            organic = 'Organic' in certifications
            tier = determine_tier(price_per_lb, organic)

            # Map to protein_poultry category
            csv_category = 'protein_poultry'

            # Determine item_type
            if 'frozen' in product.lower() or 'frozen' in notes.lower():
                item_type = 'convenience'
            elif 'breaded' in product.lower() or 'marinated' in product.lower() or 'stuffed' in product.lower():
                item_type = 'convenience'
            else:
                item_type = 'staple'

            # Build notes
            notes_parts = []
            if count:
                notes_parts.append(f"Count: {count}")
            if notes and 'sale' in notes.lower():
                notes_parts.append(notes)
            notes_str = ' | '.join(notes_parts) if notes_parts else ''

            # Generate selection reason
            if organic and cut_type in ['breast', 'thigh']:
                reason = f"Organic {cut_type}s"
            elif 'pasture' in certifications.lower():
                reason = "Pasture-raised chicken"
            elif tier == 'Cheaper':
                reason = f"Budget-friendly {cut_type}"
            else:
                reason = f"Quality {cut_type}"

            rows.append([
                csv_category,
                product,
                brand,
                f"{total_price:.2f}",
                'lb',
                size,
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

    # Input TSV file
    tsv_path = project_dir / 'Fresh_Direct_All_Chicken.tsv'

    if not tsv_path.exists():
        print(f"⚠️  Error: {tsv_path} not found")
        return

    output_file = project_dir / 'data' / 'alternatives' / 'source_listings.csv'

    # Process TSV
    rows = process_chicken_tsv(tsv_path)
    print(f"✓ Processed {len(rows)} chicken products from {tsv_path.name}")

    # Append to existing CSV
    with open(output_file, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"✓ Added {len(rows)} chicken products to {output_file}")


if __name__ == '__main__':
    main()
