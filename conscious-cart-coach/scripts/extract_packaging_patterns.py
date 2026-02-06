#!/usr/bin/env python3
"""Extract unique packaging patterns from alternatives_template.csv"""

import csv
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
template_path = PROJECT_ROOT / "data" / "alternatives" / "alternatives_template.csv"

packaging_patterns = []

with open(template_path, 'r', encoding='utf-8') as f:
    # Skip first two rows (empty + column letters)
    next(f)
    next(f)

    reader = csv.DictReader(f)
    for row in reader:
        # Column F is "packaging"
        packaging = row.get('packaging', '').strip()
        if packaging and packaging not in ['', 'packaging']:
            packaging_patterns.append(packaging)

# Count occurrences
counter = Counter(packaging_patterns)

print("=" * 80)
print("UNIQUE PACKAGING PATTERNS FROM ALTERNATIVES_TEMPLATE.CSV")
print("=" * 80)
print()

for pattern, count in counter.most_common():
    print(f"{count:2}x  {pattern}")

print()
print(f"Total unique patterns: {len(counter)}")
print(f"Total products analyzed: {len(packaging_patterns)}")
