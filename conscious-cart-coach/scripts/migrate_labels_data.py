#!/usr/bin/env python3
"""
Migrate packaging, nutrition, and labels data from source_listings.csv
to inventories_trusted/*.csv files.

This will:
1. Read packaging/nutrition/labels from source_listings.csv
2. Add these columns to inventories_trusted/*.csv files
3. Match products by title+brand and populate the data
"""

import csv
from pathlib import Path
from typing import Dict, Tuple
import shutil

def load_source_data() -> Dict[Tuple[str, str], Dict[str, str]]:
    """
    Load packaging/nutrition/labels from source_listings.csv

    Returns:
        Dict mapping (title_lower, brand_lower) -> {packaging, nutrition, labels}
    """
    source_file = Path("data/alternatives/source_listings.csv")
    data = {}

    with open(source_file, 'r') as f:
        # Skip comment lines
        lines = [line for line in f if not line.strip().startswith('"#')]

    reader = csv.DictReader(lines)

    for row in reader:
        title = row.get('product_name', '').strip()
        brand = row.get('brand', '').strip()

        if not title or not brand:
            continue

        # Create lookup key (case-insensitive)
        key = (title.lower(), brand.lower())

        data[key] = {
            'packaging': row.get('packaging', '').strip(),
            'nutrition': row.get('nutrition', '').strip(),
            'labels': row.get('labels', '').strip()
        }

    print(f"✓ Loaded {len(data)} products from source_listings.csv")
    return data


def migrate_inventory_file(inventory_file: Path, source_data: Dict[Tuple[str, str], Dict[str, str]]) -> Tuple[int, int]:
    """
    Add packaging/nutrition/labels columns to an inventory file and populate them.

    Returns:
        (total_products, matched_products)
    """
    # Create backup
    backup_file = inventory_file.with_suffix('.csv.backup')
    shutil.copy(inventory_file, backup_file)
    print(f"  ✓ Created backup: {backup_file.name}")

    # Read existing inventory
    with open(inventory_file, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    # Check if columns already exist
    new_columns = []
    if 'nutrition' not in fieldnames:
        new_columns.append('nutrition')
    if 'labels' not in fieldnames:
        new_columns.append('labels')

    # packaging already exists in the trusted inventories, just need to populate it

    if new_columns:
        fieldnames.extend(new_columns)
        print(f"  ✓ Adding columns: {', '.join(new_columns)}")

    # Match and populate data
    matched = 0
    total = len(rows)

    for row in rows:
        title = row.get('title', '').strip()
        brand = row.get('brand', '').strip()

        if not title or not brand:
            # Set empty values
            row['packaging'] = row.get('packaging', '')
            if 'nutrition' in fieldnames:
                row['nutrition'] = ''
            if 'labels' in fieldnames:
                row['labels'] = ''
            continue

        # Look up in source data
        key = (title.lower(), brand.lower())
        if key in source_data:
            source_row = source_data[key]
            row['packaging'] = source_row['packaging']
            if 'nutrition' in fieldnames:
                row['nutrition'] = source_row['nutrition']
            if 'labels' in fieldnames:
                row['labels'] = source_row['labels']
            matched += 1
        else:
            # No match found, set empty
            row['packaging'] = row.get('packaging', '')
            if 'nutrition' in fieldnames:
                row['nutrition'] = ''
            if 'labels' in fieldnames:
                row['labels'] = ''

    # Write updated file
    with open(inventory_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ Updated {inventory_file.name}: {matched}/{total} products matched")
    return total, matched


def main():
    print("=" * 70)
    print("MIGRATE LABELS DATA")
    print("=" * 70)
    print()

    # Change to project root
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)

    # Load source data
    print("Step 1: Loading source data...")
    source_data = load_source_data()
    print()

    # Get all inventory files
    inventories_dir = Path("data/inventories_trusted")
    inventory_files = list(inventories_dir.glob("*_inventory.csv"))

    if not inventory_files:
        print("❌ No inventory files found in data/inventories_trusted/")
        return

    print(f"Step 2: Migrating {len(inventory_files)} inventory files...")
    print()

    total_products = 0
    total_matched = 0

    for inventory_file in sorted(inventory_files):
        print(f"Processing {inventory_file.name}:")
        products, matched = migrate_inventory_file(inventory_file, source_data)
        total_products += products
        total_matched += matched
        print()

    # Summary
    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Total products processed: {total_products}")
    print(f"Total products matched: {total_matched} ({total_matched*100//total_products if total_products else 0}%)")
    print(f"Unmatched: {total_products - total_matched}")
    print()
    print("Backup files created with .backup extension")
    print("To restore: mv file.csv.backup file.csv")
    print()
    print("Next steps:")
    print("  1. Restart the backend: lsof -ti :8000 | xargs kill -9 && python -m uvicorn api.main:app --reload")
    print("  2. Test a cart plan to see the labels data")


if __name__ == "__main__":
    main()
