#!/usr/bin/env python3
"""Test CSV parsing directly"""

import csv
from pathlib import Path

csv_path = Path(__file__).parent.parent / "data/alternatives/source_listings.csv"

print(f"Testing CSV parsing: {csv_path}\n")

with open(csv_path, 'r', encoding='utf-8') as f:
    # Skip comment lines
    lines = [line for line in f if not line.strip().startswith('#')]

print(f"Total lines after filtering comments: {len(lines)}")
print(f"\nFirst 5 lines:")
for i, line in enumerate(lines[:5], 1):
    print(f"{i}. {line.strip()[:100]}")

# Try to parse with DictReader
print("\n" + "="*80)
print("Parsing with csv.DictReader...")
print("="*80)

reader = csv.DictReader(lines)
rows = list(reader)

print(f"\nTotal rows parsed: {len(rows)}")
print(f"First row keys: {list(rows[0].keys()) if rows else 'NO ROWS'}")

if rows:
    print(f"\nFirst row:")
    for k, v in rows[0].items():
        print(f"  {k}: {v}")

# Count mushroom rows
mushroom_rows = [r for r in rows if r.get('category', '').strip() == 'produce_mushrooms']
print(f"\nMushroom rows: {len(mushroom_rows)}")

if mushroom_rows:
    print("\nFirst mushroom product:")
    for k, v in mushroom_rows[0].items():
        print(f"  {k}: {v}")
