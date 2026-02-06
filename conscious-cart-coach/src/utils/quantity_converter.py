"""
Quantity Conversion Utilities
Converts recipe quantities (e.g., "1 lb chicken") to product quantities (e.g., "1x 1lb package")
"""

import re
from typing import Tuple, Optional


# Weight conversions to ounces
WEIGHT_TO_OZ = {
    "oz": 1,
    "ounce": 1,
    "ounces": 1,
    "lb": 16,
    "lbs": 16,
    "pound": 16,
    "pounds": 16,
    "kg": 35.274,
    "g": 0.03527,
    "gram": 0.03527,
    "grams": 0.03527,
}

# Volume conversions to fluid ounces
VOLUME_TO_FL_OZ = {
    "fl oz": 1,
    "floz": 1,
    "fluid ounce": 1,
    "fluid ounces": 1,
    "cup": 8,
    "cups": 8,
    "c": 8,
    "pint": 16,
    "pints": 16,
    "pt": 16,
    "quart": 32,
    "quarts": 32,
    "qt": 32,
    "gallon": 128,
    "gallons": 128,
    "gal": 128,
    "ml": 0.033814,
    "milliliter": 0.033814,
    "milliliters": 0.033814,
    "liter": 33.814,
    "liters": 33.814,
    "l": 33.814,
}

# Count-based units
COUNT_UNITS = {"bunch", "bunches", "ea", "each", "piece", "pieces", "clove", "cloves", "head", "heads", "bulb", "bulbs"}


def parse_numeric_quantity(quantity_str: str) -> Tuple[float, str]:
    """
    Parse quantity string like "1.5 lb", "2 cups", "1 bunch" into (amount, unit).

    Returns:
        (amount, unit) - e.g., (1.5, "lb"), (2.0, "cups"), (1.0, "bunch")
    """
    if not quantity_str:
        return (1.0, "ea")

    quantity_str = quantity_str.strip().lower()

    # Pattern: number + unit
    # Handles: "1.5 lb", "2 cups", "1 bunch", "16oz", "2.5kg"
    pattern = r'([\d.]+)\s*([a-z]+)?'
    match = re.match(pattern, quantity_str)

    if match:
        amount_str, unit = match.groups()
        try:
            amount = float(amount_str)
            unit = unit or "ea"
            return (amount, unit)
        except ValueError:
            pass

    # If no numeric value found, default to 1 ea
    return (1.0, "ea")


def parse_product_size(size_str: str) -> Tuple[float, str]:
    """
    Parse product size string like "16oz", "1 lb", "5oz bag", "per lb" into (size, unit).

    Returns:
        (size, unit) - e.g., (16.0, "oz"), (1.0, "lb"), (5.0, "oz")
    """
    if not size_str:
        return (1.0, "ea")

    size_str = size_str.strip().lower()

    # Handle "per lb", "per oz" - treat as 1 unit
    if size_str.startswith("per "):
        unit = size_str.replace("per ", "").strip()
        return (1.0, unit)

    # Pattern: number + unit (with optional text like "bag", "pack", "jar")
    # Handles: "16oz", "1 lb", "5oz bag", "2.2oz jar"
    pattern = r'([\d.]+)\s*([a-z]+)'
    match = re.search(pattern, size_str)

    if match:
        size_num_str, unit = match.groups()
        try:
            size_num = float(size_num_str)
            # Clean unit (remove "bag", "pack", "jar" suffix)
            unit = unit.replace("bag", "").replace("pack", "").replace("jar", "").strip()
            return (size_num, unit)
        except ValueError:
            pass

    # Default: treat as 1 ea
    return (1.0, "ea")


def convert_to_common_unit(amount: float, unit: str) -> Tuple[float, str]:
    """
    Convert quantity to a common unit (ounces for weight, fl oz for volume).

    Returns:
        (converted_amount, common_unit) - e.g., (16.0, "oz"), (8.0, "fl oz")
    """
    unit_lower = unit.lower().strip()

    # Check if it's a weight unit
    if unit_lower in WEIGHT_TO_OZ:
        return (amount * WEIGHT_TO_OZ[unit_lower], "oz")

    # Check if it's a volume unit
    if unit_lower in VOLUME_TO_FL_OZ:
        return (amount * VOLUME_TO_FL_OZ[unit_lower], "fl oz")

    # Check if it's a count unit
    if unit_lower in COUNT_UNITS or unit_lower == "ea":
        return (amount, "ea")

    # Unknown unit - return as-is
    return (amount, unit_lower)


def calculate_product_quantity(
    ingredient_qty: float,
    ingredient_unit: str,
    product_size: float,
    product_unit: str,
    product_pricing_unit: str = "ea",
    round_up: bool = True
) -> float:
    """
    Calculate how many products are needed to fulfill ingredient quantity.

    Args:
        ingredient_qty: Amount needed (e.g., 1.5)
        ingredient_unit: Unit of ingredient (e.g., "lb")
        product_size: Size of product (e.g., 16)
        product_unit: Unit of product (e.g., "oz")
        product_pricing_unit: How product is priced ("ea", "lb", etc.)
        round_up: If True, round packaged products to whole numbers

    Returns:
        Number of products needed (e.g., 1.5 if buying 1.5 lbs, or 2.0 if buying 2 packages)

    Examples:
        - Need 1 lb chicken, product is "16oz package": returns 1.0 (one package)
        - Need 2 lb chicken, product is "1 lb package": returns 2.0 (two packages)
        - Need 8 oz spinach, product is "5oz bag": returns 2.0 (two bags, rounded up)
        - Need 1.5 lb chicken, product is "per lb" (priced by weight): returns 1.5 (1.5 lbs)
    """
    import math

    # Special case: if product is sold by weight ("per lb", "per oz"), return exact ingredient quantity
    if product_pricing_unit in ["lb", "lbs", "pound", "pounds", "oz", "ounce", "ounces"]:
        # Convert ingredient to product's pricing unit
        ing_amount_common, ing_unit_common = convert_to_common_unit(ingredient_qty, ingredient_unit)
        product_amount_common, product_unit_common = convert_to_common_unit(1.0, product_pricing_unit)

        if ing_unit_common == product_unit_common:
            # Return exact quantity for weight-based pricing (no rounding)
            return round(ing_amount_common / product_amount_common, 2)

    # Convert both to common units
    ingredient_amount_common, ingredient_common_unit = convert_to_common_unit(ingredient_qty, ingredient_unit)
    product_amount_common, product_common_unit = convert_to_common_unit(product_size, product_unit)

    # If units don't match (e.g., weight vs volume), can't convert - return 1
    if ingredient_common_unit != product_common_unit:
        return 1.0

    # Calculate how many products needed
    if product_amount_common == 0:
        return 1.0

    packages_needed = ingredient_amount_common / product_amount_common

    # For packaged products (sold "each"), round up to whole numbers
    # You can't buy 1.3 packages - you buy 2
    if round_up:
        return math.ceil(packages_needed)
    else:
        # Return fractional packages (for display purposes)
        return round(packages_needed, 2)


def convert_ingredient_to_product_quantity(
    ingredient_qty_str: str,
    product_size_str: str,
    product_pricing_unit: str = "ea"
) -> Tuple[float, str]:
    """
    High-level function to convert ingredient quantity to product quantity.

    Args:
        ingredient_qty_str: Ingredient quantity (e.g., "1 lb", "2 cups")
        product_size_str: Product size (e.g., "16oz", "5oz bag", "per lb")
        product_pricing_unit: How product is priced (e.g., "ea", "lb")

    Returns:
        (quantity, display_string) - e.g., (1.0, "1x 16oz"), (2.0, "2x 5oz bags")

    Examples:
        >>> convert_ingredient_to_product_quantity("1 lb", "16oz", "ea")
        (1.0, "1x 16oz")
        >>> convert_ingredient_to_product_quantity("2 cups", "5oz bag", "ea")
        (2.0, "2x 5oz bags")
        >>> convert_ingredient_to_product_quantity("1.5 lb", "per lb", "lb")
        (1.5, "1.5 lb")
    """

    # Parse ingredient quantity
    ing_qty, ing_unit = parse_numeric_quantity(ingredient_qty_str)

    # Parse product size
    product_size, product_unit = parse_product_size(product_size_str)

    # Calculate product quantity
    product_qty = calculate_product_quantity(
        ing_qty, ing_unit, product_size, product_unit, product_pricing_unit
    )

    # Build display string
    if product_pricing_unit in ["lb", "lbs", "pound", "pounds", "oz", "ounce", "ounces"]:
        # Sold by weight
        display = f"{product_qty:.1f} {product_pricing_unit}"
    else:
        # Sold by package/count
        qty_display = int(product_qty) if product_qty == int(product_qty) else f"{product_qty:.2f}"
        display = f"{qty_display}x {product_size_str}"

    return (product_qty, display)


# Test cases for development
if __name__ == "__main__":
    test_cases = [
        ("1 lb", "16oz", "ea"),
        ("2 lb", "1 lb", "ea"),
        ("8 oz", "5oz bag", "ea"),
        ("1.5 lb", "per lb", "lb"),
        ("2 cups", "8fl oz", "ea"),
        ("1 bunch", "1 bunch", "ea"),
    ]

    print("Quantity Conversion Tests:")
    print("=" * 60)
    for ingredient_qty, product_size, pricing_unit in test_cases:
        qty, display = convert_ingredient_to_product_quantity(ingredient_qty, product_size, pricing_unit)
        print(f"Ingredient: {ingredient_qty:12} | Product: {product_size:10} | Result: {display}")
