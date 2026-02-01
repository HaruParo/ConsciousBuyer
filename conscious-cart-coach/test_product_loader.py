#!/usr/bin/env python3
"""Test script to verify CSV product loading works correctly."""

import sys
from pathlib import Path
from typing import Union, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only the loader functions
import csv
import os

csv_path = Path("data/alternatives/source_listings.csv")

def _load_inventory_from_csv(csv_path: Union[str, Path]) -> Dict[str, List[dict]]:
    """Load product inventory from CSV file."""
    inventory: dict[str, list[dict]] = {}
    product_counter = 0

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return inventory

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip comment lines
        lines = [line for line in f if not line.strip().startswith('#')]

    # Parse CSV from filtered lines
    reader = csv.DictReader(lines)
    for row in reader:
        # Skip empty rows or rows with no category
        if not row.get('category') or not row.get('category').strip():
            continue

        category = row['category'].strip()
        product_name = row.get('product_name', '').strip()
        brand = row.get('brand', '').strip()
        price_str = row.get('price', '').strip()
        unit = row.get('unit', 'ea').strip()
        size = row.get('size', '').strip()
        certifications = row.get('certifications', '').strip()
        selected_tier = row.get('selected_tier', '').strip()

        # Parse price (remove $ and commas)
        try:
            price_clean = price_str.replace('$', '').replace(',', '').strip()
            price = float(price_clean)
        except (ValueError, TypeError):
            print(f"Warning: Invalid price '{price_str}' for {product_name}, skipping")
            continue

        # Determine if organic
        organic = 'USDA Organic' in certifications or 'Organic' in certifications

        # Determine store type
        if selected_tier == "Premium Specialty" or "Pure Indian Foods" in brand:
            store_type = "specialty"
        else:
            store_type = "primary"

        # Generate product ID
        product_counter += 1
        product_id = f"prod{product_counter:04d}"

        # Build product dict
        product = {
            "id": product_id,
            "title": product_name,
            "brand": brand,
            "size": size,
            "price": price,
            "organic": organic,
            "store_type": store_type,
            "unit": unit,
            "category": category,
        }

        # Map category to ingredient name(s)
        ingredient_names = _map_category_to_ingredients(category, product_name)

        for ing_name in ingredient_names:
            if ing_name not in inventory:
                inventory[ing_name] = []
            inventory[ing_name].append(product)

    print(f"✓ Loaded {product_counter} products into {len(inventory)} ingredient categories")
    return inventory


def _map_category_to_ingredients(category: str, product_name: str) -> list[str]:
    """Map CSV category and product name to ingredient name(s)."""
    category_lower = category.lower()
    product_lower = product_name.lower()

    # Handle chicken/poultry
    if "protein_poultry" in category_lower or "chicken" in product_lower:
        ingredients = ["chicken"]
        if "breast" in product_lower:
            ingredients.append("chicken_breast")
        if "thigh" in product_lower:
            ingredients.append("chicken_thigh")
        return ingredients

    # Handle spices
    if category_lower == "spices":
        ingredients = ["spices"]

        spice_keywords = {
            "turmeric": "turmeric",
            "cumin": "cumin",
            "coriander": "coriander",
            "cardamom": "cardamom",
            "cinnamon": "cinnamon",
            "clove": "cloves",
            "garam masala": "garam_masala",
            "curry": "curry_powder",
            "chili": "chili",
            "pepper": "pepper",
            "ginger": "ginger",
            "garlic": "garlic",
            "fennel": "fennel",
            "fenugreek": "fenugreek",
            "mustard": "mustard",
            "bay": "bay_leaf",
            "saffron": "saffron",
            "biryani": "biryani_masala",
            "ghee": "ghee",
            "hing": "asafoetida",
            "asafoetida": "asafoetida",
        }

        for keyword, spice_name in spice_keywords.items():
            if keyword in product_lower:
                ingredients.append(spice_name)
                break

        return ingredients

    # Handle produce greens
    if "produce_greens" in category_lower:
        if "spinach" in product_lower:
            return ["spinach"]
        if "kale" in product_lower:
            return ["kale"]
        if "lettuce" in product_lower:
            return ["lettuce"]
        return ["greens"]

    # Handle onions
    if "onion" in category_lower or "onion" in product_lower:
        return ["onion"]

    # Handle rice/grains
    if "grain" in category_lower or "rice" in product_lower:
        ingredients = ["rice"]
        if "basmati" in product_lower:
            ingredients.append("basmati_rice")
        return ingredients

    # Handle yogurt
    if "yogurt" in category_lower or "yogurt" in product_lower:
        return ["yogurt"]

    # Fallback
    return [category_lower]


if __name__ == "__main__":
    print("Testing CSV product loader...")
    print("=" * 60)

    inventory = _load_inventory_from_csv(csv_path)

    print(f"\nInventory summary:")
    print(f"  Total ingredient categories: {len(inventory)}")
    print(f"  Available ingredients: {', '.join(list(inventory.keys())[:15])}")

    # Test chicken
    if 'chicken' in inventory:
        print(f"\n✓ Chicken products: {len(inventory['chicken'])}")
        for p in inventory['chicken'][:3]:
            organic_label = " (organic)" if p['organic'] else ""
            print(f"    • {p['brand']} {p['title']}: ${p['price']}/{p['unit']}{organic_label}")
    else:
        print("\n✗ No chicken products found!")

    # Test spices
    if 'garam_masala' in inventory:
        print(f"\n✓ Garam masala products: {len(inventory['garam_masala'])}")
        for p in inventory['garam_masala'][:2]:
            print(f"    • {p['brand']} {p['title']}: ${p['price']}")
    else:
        print("\n✗ No garam masala found!")

    if 'ghee' in inventory:
        print(f"\n✓ Ghee products: {len(inventory['ghee'])}")
        for p in inventory['ghee'][:2]:
            print(f"    • {p['brand']} {p['title']}: ${p['price']}")
    else:
        print("\n✗ No ghee found!")

    print("\n" + "=" * 60)
    print("Test complete!")
