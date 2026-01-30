#!/usr/bin/env python3
"""
Bulk-add store_type to products in product_agent.py.

Strategy:
- Fresh produce/meat/dairy → "primary" (can't ship fresh from specialty stores)
- Ethnic spices/specialty → change last 1-2 items to "specialty" brand
- Common groceries → "both"
"""

import re

# Categories and their store type classifications
CLASSIFICATIONS = {
    # Fresh items - MUST be primary (specialty stores can't ship fresh)
    "primary_only": [
        "spinach", "kale", "lettuce", "tomatoes", "cherry_tomatoes",
        "strawberries", "blueberries", "bell_pepper", "hot_peppers",
        "cilantro", "mint", "potatoes", "broccoli", "avocado",
        "cucumber", "carrots", "celery", "mushrooms", "lemon",
        "chicken", "ground_beef", "salmon", "eggs", "milk", "yogurt", "butter",
    ],

    # Spices and specialty items - can be at specialty stores
    "specialty_items": [
        "ghee", "cumin", "turmeric", "coriander", "rice",
    ],

    # Common items - available at both
    "both": [
        "onion", "garlic", "ginger", "olive_oil", "salt", "black_pepper",
        "pasta", "canned_tomatoes", "coconut_milk", "tofu", "soy_sauce",
    ],
}

def add_store_types():
    file_path = "/Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/src/agents/product_agent.py"

    with open(file_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    current_ingredient = None
    item_count = 0

    for i, line in enumerate(lines):
        # Detect ingredient category start
        if re.match(r'\s+"(\w+)":\s*\[', line):
            match = re.match(r'\s+"(\w+)":\s*\[', line)
            current_ingredient = match.group(1)
            item_count = 0

        # Check if this is a product line that needs store_type
        if current_ingredient and '{"id":' in line and '"store_type"' not in line:
            item_count += 1

            # Determine store type
            if current_ingredient in CLASSIFICATIONS["primary_only"]:
                store_type = "primary"
            elif current_ingredient in CLASSIFICATIONS["specialty_items"]:
                # For specialty items: first 3 are "primary"/"both", last 2 are "specialty"
                if item_count <= 3:
                    store_type = "primary" if item_count <= 2 else "both"
                else:
                    store_type = "specialty"
            elif current_ingredient in CLASSIFICATIONS["both"]:
                store_type = "both"
            else:
                store_type = "primary"  # Default

            # Add store_type before closing brace
            line = line.rstrip()
            if line.endswith('},'):
                line = line[:-2] + f', "store_type": "{store_type}"' + '},'
            elif line.endswith('}'):
                line = line[:-1] + f', "store_type": "{store_type}"' + '}'

        new_lines.append(line)

    new_content = '\n'.join(new_lines)

    with open(file_path, 'w') as f:
        f.write(new_content)

    print(f"✅ Added store_type to all products")
    print(f"\nClassifications:")
    print(f"  - Primary only (fresh items): {len(CLASSIFICATIONS['primary_only'])} categories")
    print(f"  - Specialty items (spices/ghee/rice): {len(CLASSIFICATIONS['specialty_items'])} categories")
    print(f"  - Both: {len(CLASSIFICATIONS['both'])} categories")

if __name__ == "__main__":
    add_store_types()
