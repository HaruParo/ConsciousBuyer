#!/usr/bin/env python3
"""
Analyze real product prices from CSV samples to calibrate synthetic generator
"""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

def parse_size(size_str):
    """Parse size string like '3oz' or '100g' into (value, unit)"""
    if not size_str or size_str == '':
        return None, None

    size_str = str(size_str).lower().strip()

    # Extract number and unit
    import re
    match = re.match(r'([0-9.]+)\s*([a-z]+)', size_str)
    if match:
        return float(match.group(1)), match.group(2)
    return None, None

def normalize_size_to_oz(value, unit):
    """Convert size to oz for comparison"""
    if not value or not unit:
        return None

    conversions = {
        'oz': 1.0,
        'lb': 16.0,
        'g': 0.035274,  # grams to oz
        'floz': 1.0
    }

    return value * conversions.get(unit, 1.0)

def analyze_prices():
    """Analyze pricing from real product samples"""

    base_dir = Path(__file__).parent.parent / "data" / "alternatives"

    # Analysis results
    spice_prices = defaultdict(list)  # ingredient -> [(size_oz, price)]
    category_prices = defaultdict(list)  # category -> [prices]

    print("=" * 80)
    print("REAL PRODUCT PRICE ANALYSIS")
    print("=" * 80)

    # Analyze Pure Indian Foods (specialty spices)
    print("\n📊 Pure Indian Foods (Specialty Organic)")
    print("-" * 80)

    pif_file = base_dir / "pure_indian_foods_products.csv"
    if pif_file.exists():
        with open(pif_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                price_str = row.get('price', '')

                # Skip sold out or non-numeric prices
                if 'sold out' in price_str.lower() or not price_str:
                    continue

                try:
                    price = float(price_str.replace('$', '').replace(',', ''))
                except:
                    continue

                product_name = row.get('product_name', '').lower()
                category = row.get('category', '')
                size_str = row.get('size', '')

                size_val, size_unit = parse_size(size_str)
                size_oz = normalize_size_to_oz(size_val, size_unit)

                if size_oz:
                    # Categorize by ingredient type
                    ingredient = None
                    if 'turmeric' in product_name:
                        ingredient = 'turmeric'
                    elif 'garam masala' in product_name:
                        ingredient = 'garam masala'
                    elif 'cumin' in product_name:
                        ingredient = 'cumin'
                    elif 'coriander' in product_name:
                        ingredient = 'coriander'
                    elif 'cardamom' in product_name:
                        ingredient = 'cardamom'
                    elif 'bay' in product_name:
                        ingredient = 'bay leaves'
                    elif 'ginger' in product_name and 'powder' in product_name:
                        ingredient = 'ginger powder'

                    if ingredient:
                        spice_prices[ingredient].append((size_oz, price, product_name, size_str))
                        category_prices['spices'].append(price)

    # Print spice analysis
    print("\n🌶️  SPICE PRICING BREAKDOWN:")
    print()

    for ingredient, prices in sorted(spice_prices.items()):
        print(f"\n{ingredient.upper()}:")
        prices.sort(key=lambda x: x[0])  # Sort by size
        for size_oz, price, name, size_str in prices:
            price_per_oz = price / size_oz
            print(f"  {size_str:>8} ({size_oz:>5.2f}oz) = ${price:>6.2f}  (${price_per_oz:.2f}/oz)  [{name[:50]}]")

        if len(prices) >= 2:
            avg_price_per_oz = statistics.mean([p / s for s, p, _, _ in prices])
            print(f"  → Avg: ${avg_price_per_oz:.2f}/oz")

    # Analyze source listings (mainstream stores)
    print("\n\n📊 Mainstream Store Products")
    print("-" * 80)

    source_file = base_dir / "source_listings.csv"
    produce_prices = defaultdict(list)

    if source_file.exists():
        with open(source_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                price_str = row.get('price', '')

                if 'sold out' in price_str.lower() or not price_str:
                    continue

                try:
                    price = float(price_str.replace('$', '').replace(',', ''))
                except:
                    continue

                category = row.get('category', '')
                product_name = row.get('product_name', '').lower()
                certifications = row.get('certifications', '')
                is_organic = 'organic' in certifications.lower()

                if category.startswith('produce_'):
                    key = f"{category} ({'organic' if is_organic else 'conventional'})"
                    produce_prices[key].append(price)

    print("\n🥬 PRODUCE PRICING:")
    for cat, prices in sorted(produce_prices.items()):
        if prices:
            print(f"  {cat:.<50} ${min(prices):.2f} - ${max(prices):.2f}  (avg: ${statistics.mean(prices):.2f})")

    # Generate recommendations
    print("\n\n" + "=" * 80)
    print("🎯 PRICING CALIBRATION RECOMMENDATIONS")
    print("=" * 80)

    print("\n1. PURE INDIAN FOODS SPICES (Organic Specialty):")
    print("   Current synthetic ranges are TOO LOW by 30-50%")
    print()

    recommendations = {
        "turmeric": {
            "current_base": 4.99,
            "recommended_base": 6.99,
            "reason": "Actual PIF 3oz = $6.99, 8oz = $15.99"
        },
        "garam masala": {
            "current_base": 5.99,
            "recommended_base": 6.49,
            "reason": "Actual PIF 2oz = $6.49"
        },
        "cumin": {
            "current_base": 4.99,
            "recommended_base": 6.69,
            "reason": "Actual PIF 3oz = $6.69, 8oz = $14.99"
        },
        "coriander": {
            "current_base": 4.99,
            "recommended_base": 5.31,
            "reason": "Actual PIF 3oz = $5.31, 8oz = $11.99"
        },
        "cardamom": {
            "current_base": 12.99,
            "recommended_base": 12.99,
            "reason": "✓ Already correct: PIF 2oz = $12.99, 8oz = $28.99"
        },
        "bay leaves": {
            "current_base": 3.99,
            "recommended_base": 7.98,  # 0.5oz = $3.99, so 1oz = $7.98
            "reason": "Actual PIF 0.5oz = $3.99 (Indian bay leaves)"
        }
    }

    for ingredient, rec in recommendations.items():
        print(f"   {ingredient:.<20} ${rec['current_base']:.2f} → ${rec['recommended_base']:.2f}")
        print(f"   {'':21} {rec['reason']}")
        print()

    print("\n2. SPICE PRICING FORMULA FIX:")
    print("   For Pure Indian Foods specialty store:")
    print("   - 2-3oz sizes: Should be $5-$8 (not $3-$8)")
    print("   - 8oz bulk: Should be $11-$16 (not $8-$12)")
    print("   - Apply specialty tier multiplier: 1.15x")
    print("   - All Pure Indian Foods products are organic: 1.25x")
    print("   - Total multiplier for PIF: 1.15 * 1.25 = 1.44x over base")

    print("\n3. SIZE NORMALIZATION:")
    print("   Current generator uses grams (100g, 200g)")
    print("   Real PIF products use ounces (2oz, 3oz, 8oz)")
    print("   → Recommend switching to oz for accuracy")

    print("\n" + "=" * 80)
    print("✅ Analysis complete. Update base_price values in BIRYANI_INGREDIENTS.")
    print("=" * 80)

if __name__ == "__main__":
    analyze_prices()
