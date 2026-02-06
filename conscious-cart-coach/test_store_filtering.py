#!/usr/bin/env python3
"""Test store-specific brand filtering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import CSV loader
import csv
import os

csv_path = Path("data/alternatives/source_listings.csv")

# Load products
with open(csv_path, 'r') as f:
    lines = [line for line in f if not line.strip().startswith('#')]

reader = csv.DictReader(lines)
products = list(reader)

print("Store Brand Filtering Test")
print("=" * 60)

# Test 1: Check Whole Foods exclusive products
print("\n1. Whole Foods Store Brand (365 by Whole Foods Market):")
wf_products = [p for p in products if '365 by Whole Foods Market' in p.get('brand', '')]
print(f"   Found {len(wf_products)} products")
for p in wf_products[:3]:
    print(f"   • {p['product_name']} - ${p['price']}")

# Test 2: Check Peri & Sons Farms products
print("\n2. Peri & Sons Farms (found at Sprouts):")
peri_products = [p for p in products if 'Peri & Sons' in p.get('brand', '')]
print(f"   Found {len(peri_products)} products")
for p in peri_products[:5]:
    print(f"   • {p['product_name']} - ${p['price']}")

# Test 3: Check onion products
print("\n3. All Onion Products:")
onion_products = [p for p in products if p.get('category', '') == 'produce_onions']
print(f"   Found {len(onion_products)} onion products")
brands = set(p['brand'] for p in onion_products)
print(f"   Brands: {', '.join(sorted(brands))}")

# Test 4: Verify store exclusivity logic
print("\n4. Store Brand Exclusivity Check:")
store_brands = {
    "365 by Whole Foods Market": "Whole Foods",
    "ShopRite": "ShopRite",
    "Peri & Sons Farms": "Sprouts (also at Whole Foods)",
}

for brand, expected_store in store_brands.items():
    count = len([p for p in products if brand in p.get('brand', '')])
    if count > 0:
        print(f"   ✓ {brand}: {count} products → {expected_store}")
    else:
        print(f"   ✗ {brand}: No products found")

print("\n" + "=" * 60)
print("Test complete!")
