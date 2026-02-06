#!/usr/bin/env python3
"""
Add nutritional information and labels columns to source_listings.csv.

This script:
1. Adds 'nutrition' column with key nutritional facts
2. Adds 'labels' column with certifications/labels beyond organic
3. Optionally fetches data from Open Food Facts API

Nutritional format: "Calories: 50/100g, Protein: 3g, Carbs: 10g, Fat: 1g"
Labels format: "Non-GMO Project Verified, Fair Trade, Gluten-Free, B Corp"
"""

import csv
import json
import requests
import time
from pathlib import Path
from typing import Dict, Optional, List

PROJECT_ROOT = Path(__file__).parent.parent
source_path = PROJECT_ROOT / "data" / "alternatives" / "source_listings.csv"
backup_path = PROJECT_ROOT / "data" / "alternatives" / "source_listings_with_packaging_backup.csv"

# Cache for Open Food Facts API calls
CACHE_FILE = PROJECT_ROOT / "data" / "alternatives" / "openfoodfacts_cache.json"


def load_cache() -> Dict:
    """Load cached API responses"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache: Dict):
    """Save cached API responses"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def search_openfoodfacts(product_name: str, brand: str, cache: Dict) -> Optional[Dict]:
    """
    Search Open Food Facts for product information.

    Returns nutrition and labels data if found.
    """
    cache_key = f"{brand}_{product_name}".lower()

    # Check cache first
    if cache_key in cache:
        print(f"  📦 Using cached data for {product_name}")
        return cache[cache_key]

    try:
        # Search by product name and brand
        search_url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": f"{brand} {product_name}",
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 1
        }

        response = requests.get(search_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('products') and len(data['products']) > 0:
                product = data['products'][0]

                # Extract nutrition
                nutrition = {}
                nutriments = product.get('nutriments', {})
                if nutriments:
                    nutrition = {
                        'calories': nutriments.get('energy-kcal_100g', nutriments.get('energy-kcal')),
                        'protein': nutriments.get('proteins_100g', nutriments.get('proteins')),
                        'carbs': nutriments.get('carbohydrates_100g', nutriments.get('carbohydrates')),
                        'fat': nutriments.get('fat_100g', nutriments.get('fat')),
                        'fiber': nutriments.get('fiber_100g', nutriments.get('fiber')),
                        'sugar': nutriments.get('sugars_100g', nutriments.get('sugars')),
                        'sodium': nutriments.get('sodium_100g', nutriments.get('sodium')),
                    }

                # Extract labels
                labels = product.get('labels_tags', [])
                labels_clean = [
                    label.replace('en:', '').replace('-', ' ').title()
                    for label in labels
                ]

                result = {
                    'nutrition': nutrition,
                    'labels': labels_clean,
                    'found': True
                }

                # Cache result
                cache[cache_key] = result
                print(f"  ✓ Found data for {product_name}")

                # Rate limit: 1 request per second
                time.sleep(1)

                return result

    except Exception as e:
        print(f"  ⚠️  Error fetching {product_name}: {e}")

    # Cache negative result
    cache[cache_key] = {'found': False}
    return None


def infer_labels_from_certifications(certifications: str, product_name: str, brand: str, notes: str = "") -> List[str]:
    """
    Infer additional labels based on certifications and product characteristics.

    Common labels to look for:
    - Non-GMO Project Verified
    - Fair Trade Certified
    - B Corp
    - Gluten-Free
    - Kosher
    - Halal
    - Vegan
    - Vegetarian
    - Cage-Free
    - Pasture-Raised
    - Grass-Fed
    - Free-Range
    - Keto-Friendly
    - Paleo-Friendly
    """
    labels = []

    cert_lower = certifications.lower()
    name_lower = product_name.lower()
    brand_lower = brand.lower()
    notes_lower = notes.lower()

    combined_text = f"{cert_lower} {name_lower} {brand_lower} {notes_lower}"

    # Check for label keywords
    if 'non-gmo' in combined_text or 'non gmo' in combined_text:
        labels.append('Non-GMO Project Verified')

    if 'fair trade' in combined_text or 'fairtrade' in combined_text:
        labels.append('Fair Trade Certified')

    if 'gluten-free' in combined_text or 'gluten free' in combined_text:
        labels.append('Gluten-Free')

    if 'kosher' in combined_text:
        labels.append('Kosher')

    if 'halal' in combined_text:
        labels.append('Halal')

    if 'vegan' in combined_text:
        labels.append('Vegan')

    if 'vegetarian' in combined_text:
        labels.append('Vegetarian')

    # Animal welfare labels
    if 'cage-free' in combined_text or 'cage free' in combined_text:
        labels.append('Cage-Free')

    if 'pasture-raised' in combined_text or 'pasture raised' in combined_text:
        labels.append('Pasture-Raised')

    if 'grass-fed' in combined_text or 'grass fed' in combined_text or 'grassfed' in combined_text:
        labels.append('Grass-Fed')

    if 'free-range' in combined_text or 'free range' in combined_text:
        labels.append('Free-Range')

    # Environmental labels
    if 'b corp' in combined_text or 'b-corp' in combined_text or 'bcorp' in combined_text:
        labels.append('B Corp Certified')

    if 'rainforest alliance' in combined_text:
        labels.append('Rainforest Alliance Certified')

    if 'regenerative' in combined_text:
        labels.append('Regenerative Agriculture')

    # Infer from product category (naturally vegan/gluten-free produce)
    if any(word in name_lower for word in ['kale', 'spinach', 'onion', 'garlic', 'mushroom', 'tomato', 'carrot', 'beet', 'radish']):
        if 'Naturally Gluten-Free' not in labels:
            labels.append('Naturally Gluten-Free')
        if 'Vegan' not in labels:
            labels.append('Vegan')

    return labels


def format_nutrition(nutrition: Optional[Dict]) -> str:
    """Format nutrition data as a compact string"""
    if not nutrition or not any(nutrition.values()):
        return ""

    parts = []
    if nutrition.get('calories'):
        parts.append(f"Calories: {nutrition['calories']}/100g")
    if nutrition.get('protein'):
        parts.append(f"Protein: {nutrition['protein']}g")
    if nutrition.get('carbs'):
        parts.append(f"Carbs: {nutrition['carbs']}g")
    if nutrition.get('fat'):
        parts.append(f"Fat: {nutrition['fat']}g")
    if nutrition.get('fiber'):
        parts.append(f"Fiber: {nutrition['fiber']}g")

    return ", ".join(parts)


def add_nutrition_and_labels(use_api: bool = False):
    """Add nutrition and labels columns to source_listings.csv"""

    # Backup original file
    import shutil
    shutil.copy(source_path, backup_path)
    print(f"✓ Created backup: {backup_path}")

    # Load API cache
    cache = load_cache() if use_api else {}

    # Read all rows
    rows = []
    comments = []
    header = None

    with open(source_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue

            # Check if it's a comment
            first_cell = row[0] if row else ""
            if first_cell.strip().strip('"').startswith('#'):
                comments.append(row)
            elif header is None:
                header = row
            else:
                rows.append(row)

    print(f"✓ Read {len(rows)} products")
    print(f"✓ Current columns ({len(header)}): {', '.join(header)}")

    # Check if columns already exist
    if 'nutrition' in header or 'labels' in header:
        print("⚠️  Nutrition or labels column already exists!")
        return

    # Find packaging column index
    packaging_idx = header.index('packaging')

    # Add nutrition and labels after packaging
    new_header = header[:packaging_idx+1] + ['nutrition', 'labels'] + header[packaging_idx+1:]

    print(f"✓ New columns ({len(new_header)}): {', '.join(new_header)}")

    # Process each row
    new_rows = []
    api_hits = 0
    inferred_labels = 0

    for i, row in enumerate(rows):
        # Ensure row has enough columns
        while len(row) < len(header):
            row.append('')

        category = row[0] if len(row) > 0 else ''
        product_name = row[1] if len(row) > 1 else ''
        brand = row[2] if len(row) > 2 else ''
        certifications = row[6] if len(row) > 6 else ''
        # packaging is now at index 7
        notes = row[8] if len(row) > 8 else ''

        nutrition_str = ""
        labels_str = ""

        # Try to fetch from API if enabled
        if use_api and brand and product_name:
            api_data = search_openfoodfacts(product_name, brand, cache)
            if api_data and api_data.get('found'):
                nutrition_str = format_nutrition(api_data.get('nutrition'))
                labels_str = ", ".join(api_data.get('labels', []))
                api_hits += 1

        # If no API data, infer labels from certifications
        if not labels_str:
            inferred = infer_labels_from_certifications(certifications, product_name, brand, notes)
            if inferred:
                labels_str = ", ".join(inferred)
                inferred_labels += 1

        # Insert nutrition and labels after packaging
        new_row = row[:packaging_idx+1] + [nutrition_str, labels_str] + row[packaging_idx+1:]
        new_rows.append(new_row)

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(rows)} products...")

    # Write new CSV
    with open(source_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

        # Write comments
        for comment_row in comments:
            writer.writerow(comment_row)

        # Write header
        writer.writerow(new_header)

        # Write rows
        for row in new_rows:
            writer.writerow(row)

    print(f"\n✓ Updated {source_path}")
    print(f"\n📊 Stats:")
    print(f"  API hits: {api_hits}")
    print(f"  Inferred labels: {inferred_labels}")
    print(f"  Total products: {len(rows)}")

    # Save cache
    if use_api:
        save_cache(cache)
        print(f"✓ Saved API cache to {CACHE_FILE}")


if __name__ == '__main__':
    import sys

    # Check if user wants to use API
    use_api = '--api' in sys.argv

    if use_api:
        print("🌐 Will fetch data from Open Food Facts API (this may take several minutes)")
        print("Note: Rate limited to 1 request/second")
    else:
        print("📝 Will infer labels from product information (no API calls)")
        print("Tip: Use --api flag to fetch from Open Food Facts")

    add_nutrition_and_labels(use_api=use_api)
