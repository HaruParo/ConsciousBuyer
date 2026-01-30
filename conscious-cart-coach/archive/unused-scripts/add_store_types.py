#!/usr/bin/env python3
"""
Add store_type field to all products in SIMULATED_INVENTORY.

Classification:
- primary: Fresh items (produce, meat, dairy) - only at FreshDirect/Whole Foods
- specialty: Ethnic spices, specialty items - only at Pure Indian Foods/Patel Brothers
- both: Common groceries - available at both types
"""

import re

# Classification by ingredient category
STORE_TYPE_MAPPING = {
    # FRESH ITEMS → Primary Store Only (can't ship fresh from specialty stores)
    "primary": [
        "spinach", "kale", "lettuce", "tomatoes", "cherry_tomatoes",
        "strawberries", "blueberries", "bell_pepper", "hot_peppers",
        "cilantro", "mint", "potatoes", "broccoli", "avocado",
        "cucumber", "carrots", "celery", "mushrooms", "lemon",
        "chicken", "ground_beef", "salmon",  # Fresh protein
        "eggs", "milk", "yogurt", "butter",  # Dairy
    ],

    # ETHNIC SPECIALTY → Specialty Store (Pure Indian Foods, Patel Brothers)
    "specialty": [
        "cumin", "turmeric", "coriander",  # Indian spices
        "ghee",  # Specialty dairy product
    ],

    # COMMON GROCERIES → Both store types
    "both": [
        "onion", "garlic", "ginger",  # Basic aromatics
        "rice",  # Staple grain
        "olive_oil", "salt", "black_pepper",  # Pantry basics
        "pasta", "canned_tomatoes", "coconut_milk",  # Shelf-stable
        "tofu", "soy_sauce",  # Asian staples
    ],
}

def get_store_type(ingredient: str) -> str:
    """Determine store type for ingredient."""
    for store_type, ingredients in STORE_TYPE_MAPPING.items():
        if ingredient in ingredients:
            return store_type
    # Default to primary for unlisted items
    return "primary"

def add_store_types_to_file():
    """Add store_type to product_agent.py inventory."""
    file_path = "/Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/src/agents/product_agent.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Find all ingredient categories and their products
    # Pattern: "ingredient_name": [ {...}, {...}, ]

    pattern = r'"(\w+)":\s*\[(.*?)\],'

    def add_store_type_to_products(match):
        ingredient = match.group(1)
        products_block = match.group(2)

        store_type = get_store_type(ingredient)

        # Add store_type to each product dict if not already present
        # Pattern: {"id": "...", "title": "...", ..., "organic": ...}
        # Add: , "store_type": "primary"

        def add_field(product_match):
            product_dict = product_match.group(0)
            # Only add if not already present
            if '"store_type"' not in product_dict:
                # Add before the closing brace
                return product_dict[:-1] + f', "store_type": "{store_type}"' + product_dict[-1]
            return product_dict

        updated_products = re.sub(
            r'\{[^}]+\}',
            add_field,
            products_block
        )

        return f'"{ingredient}": [{updated_products}],'

    updated_content = re.sub(pattern, add_store_type_to_products, content, flags=re.DOTALL)

    with open(file_path, 'w') as f:
        f.write(updated_content)

    print(f"✅ Added store_type to all products in {file_path}")

    # Print summary
    for store_type, ingredients in STORE_TYPE_MAPPING.items():
        print(f"\n{store_type.upper()}:")
        print(f"  {len(ingredients)} categories: {', '.join(ingredients[:10])}...")

if __name__ == "__main__":
    add_store_types_to_file()
