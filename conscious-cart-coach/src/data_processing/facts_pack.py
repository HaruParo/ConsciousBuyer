"""
Facts pack module.
Assembles decision context by combining baseline data, alternatives, and flags.

Uses Open Food Facts (https://openfoodfacts.org/) as a fallback data source
when local alternatives data is unavailable.
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Optional

from .open_food_facts import get_off_alternatives_for_category

logger = logging.getLogger(__name__)

# Default data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
BASELINE_PATH = DATA_DIR / "processed" / "baseline_stats.json"
ALTERNATIVES_CSV_PATH = DATA_DIR / "alternatives" / "alternatives_template.csv"
FLAGS_PATH = DATA_DIR / "flags" / "product_flags.json"

# Predefined recipe mappings for common requests
RECIPE_MAPPINGS = {
    "miso soup": ["fermented", "produce_greens", "produce_onions"],
    "miso": ["fermented", "produce_greens", "produce_onions"],
    "salad": ["produce_greens", "produce_tomatoes", "produce_cucumbers", "oils_olive", "vinegar"],
    "smoothie": ["fruit_berries", "fruit_tropical", "yogurt", "milk"],
    "stir fry": ["produce_peppers", "produce_onions", "produce_greens", "oils_other", "grains"],
    "pasta": ["grains", "produce_tomatoes", "produce_aromatics", "oils_olive", "cheese"],
    "curry": ["produce_onions", "produce_tomatoes", "spices", "canned_coconut", "grains"],
    "tacos": ["produce_peppers", "produce_onions", "produce_tomatoes", "cheese", "spices"],
    "omelette": ["eggs", "cheese", "produce_peppers", "produce_onions", "butter_ghee"],
    "breakfast": ["eggs", "bread", "butter_ghee", "fruit_berries", "yogurt"],
    "sandwich": ["bread", "produce_greens", "produce_tomatoes", "cheese", "hummus_dips"],
    "soup": ["produce_onions", "produce_root_veg", "produce_aromatics", "spices"],
    "roasted vegetables": ["produce_root_veg", "produce_squash", "produce_peppers", "oils_olive", "spices"],
    "guacamole": ["fruit_tropical", "produce_onions", "produce_tomatoes", "produce_peppers", "spices"],
}

# Keyword to category mappings for ingredient extraction
KEYWORD_CATEGORY_MAP = {
    # Produce
    "spinach": "produce_greens", "kale": "produce_greens", "lettuce": "produce_greens",
    "arugula": "produce_greens", "greens": "produce_greens", "chard": "produce_greens",
    "onion": "produce_onions", "onions": "produce_onions", "shallot": "produce_onions",
    "tomato": "produce_tomatoes", "tomatoes": "produce_tomatoes",
    "cucumber": "produce_cucumbers", "cucumbers": "produce_cucumbers",
    "carrot": "produce_root_veg", "carrots": "produce_root_veg", "beet": "produce_root_veg",
    "potato": "produce_root_veg", "potatoes": "produce_root_veg", "sweet potato": "produce_root_veg",
    "turnip": "produce_root_veg", "radish": "produce_root_veg",
    "squash": "produce_squash", "zucchini": "produce_squash", "pumpkin": "produce_squash",
    "butternut": "produce_squash", "spaghetti squash": "produce_squash",
    "pepper": "produce_peppers", "peppers": "produce_peppers", "bell pepper": "produce_peppers",
    "mushroom": "produce_mushrooms", "mushrooms": "produce_mushrooms",
    "garlic": "produce_aromatics", "ginger": "produce_aromatics",
    "beans": "produce_beans", "green beans": "produce_beans", "snap peas": "produce_beans",

    # Fruits
    "berries": "fruit_berries", "strawberry": "fruit_berries", "blueberry": "fruit_berries",
    "raspberry": "fruit_berries", "blackberry": "fruit_berries", "strawberries": "fruit_berries",
    "mango": "fruit_tropical", "banana": "fruit_tropical", "pineapple": "fruit_tropical",
    "avocado": "fruit_tropical", "papaya": "fruit_tropical", "kiwi": "fruit_tropical",
    "orange": "fruit_citrus", "lemon": "fruit_citrus", "lime": "fruit_citrus",
    "grapefruit": "fruit_citrus",
    "apple": "fruit_other", "pear": "fruit_other", "grape": "fruit_other",

    # Dairy
    "milk": "milk", "yogurt": "yogurt", "cheese": "cheese", "egg": "eggs", "eggs": "eggs",
    "butter": "butter_ghee", "ghee": "butter_ghee", "ice cream": "ice_cream",

    # Proteins
    "chicken": "chicken", "beef": "meat_other", "pork": "meat_other", "lamb": "meat_other",
    "tofu": "fermented", "tempeh": "fermented", "miso": "fermented", "miso paste": "fermented",

    # Pantry
    "rice": "grains", "pasta": "grains", "quinoa": "grains", "oats": "grains",
    "bread": "bread", "tortilla": "bread",
    "olive oil": "oils_olive", "coconut oil": "oils_coconut", "vegetable oil": "oils_other",
    "vinegar": "vinegar", "balsamic": "vinegar",
    "spices": "spices", "cumin": "spices", "paprika": "spices", "turmeric": "spices",
    "coconut milk": "canned_coconut", "coconut cream": "canned_coconut",
    "almonds": "nuts_almonds", "cashews": "nuts_cashews", "peanuts": "nuts_peanuts",
    "walnuts": "nuts_other", "pecans": "nuts_other",
    "hummus": "hummus_dips", "dip": "hummus_dips",
    "chocolate": "chocolate", "cookies": "cookies_crackers", "crackers": "cookies_crackers",
    "chips": "chips", "tea": "tea",
    "seaweed": "produce_greens", "nori": "produce_greens", "scallions": "produce_onions",
}

# Default user context
DEFAULT_USER_CONTEXT = {
    "budget_priority": "medium",
    "health_priority": "medium",
    "packaging_priority": "medium",
}


def load_baseline(path: Path = None) -> dict:
    """Load baseline statistics from JSON file."""
    path = path or BASELINE_PATH
    if not path.exists():
        logger.warning(f"Baseline file not found: {path}")
        return {"summary": {}, "categories": {}}

    with open(path) as f:
        return json.load(f)


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string to float.

    Handles formats like:
    - "$1.99/lb"
    - "$6.99/ea (16oz = $0.44/oz)"
    - "$4.99/gallon ($0.04/fl oz)"
    """
    if not price_str or price_str in ("", "null", None):
        return None

    # Extract first dollar amount
    match = re.search(r'\$(\d+\.?\d*)', str(price_str))
    if match:
        return float(match.group(1))
    return None


def load_alternatives_from_csv(path: Path = None) -> dict:
    """
    Load alternatives data from CSV file.

    CSV format has columns:
    category, tier, brand, product_name, est_price, packaging,
    why_this_tier, certifications, trade_offs, source_url, source_reasoning

    Returns:
        Dict with structure:
        {
            "category_name": {
                "cheaper": {...},
                "balanced": {...},
                "conscious": {...}
            },
            ...
        }
    """
    path = path or ALTERNATIVES_CSV_PATH
    if not path.exists():
        logger.warning(f"Alternatives CSV file not found: {path}")
        return {}

    alternatives = {}

    with open(path, newline='', encoding='utf-8') as f:
        # Skip the first two header rows (empty row and column labels)
        reader = csv.reader(f)
        next(reader)  # Skip empty row
        next(reader)  # Skip "Column 1, A, B, C..." row

        # Skip actual header row
        next(reader)
        # Headers are: row_num, category, tier, brand, product_name, est_price, packaging, why_this_tier, certifications, trade_offs, source_url, source_reasoning

        for row in reader:
            if len(row) < 11:
                continue

            # Skip if row number or category is empty
            if not row[1] or not row[2]:
                continue

            category = row[1].strip()
            tier = row[2].strip()

            if tier not in ("cheaper", "balanced", "conscious"):
                continue

            # Initialize category if needed
            if category not in alternatives:
                alternatives[category] = {}

            # Parse price
            est_price = parse_price(row[5])

            # Parse certifications (comma-separated)
            certifications = []
            if row[8]:
                certifications = [c.strip() for c in row[8].split(",") if c.strip()]

            alternatives[category][tier] = {
                "brand": row[3].strip() if row[3] else "",
                "product_name": row[4].strip() if row[4] else "",
                "est_price": est_price,
                "packaging": row[6].strip() if row[6] else "",
                "why_this_tier": row[7].strip() if row[7] else "",
                "certifications": certifications,
                "trade_offs": row[9].strip() if row[9] else "",
                "source_url": row[10].strip() if len(row) > 10 and row[10] else "",
            }

    logger.info(f"Loaded alternatives for {len(alternatives)} categories from CSV")
    return alternatives


def load_flags(path: Path = None) -> dict:
    """Load product flags (recalls, seasonal notices, etc.) from JSON file."""
    path = path or FLAGS_PATH
    if not path.exists():
        logger.debug(f"Flags file not found: {path}")
        return {}

    with open(path) as f:
        return json.load(f)


def parse_user_input(user_input: str) -> list[str]:
    """
    Parse user input to extract category intents.

    Uses predefined recipe mappings first, then keyword matching.

    Args:
        user_input: Raw user input string

    Returns:
        List of category names
    """
    user_input_lower = user_input.lower().strip()

    # Check for exact recipe match first
    for recipe, categories in RECIPE_MAPPINGS.items():
        if recipe in user_input_lower:
            logger.info(f"Matched recipe '{recipe}' -> {categories}")
            return categories

    # Fall back to keyword extraction
    categories = []
    seen = set()

    # Sort keywords by length (longest first) to match multi-word terms first
    sorted_keywords = sorted(KEYWORD_CATEGORY_MAP.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        if keyword in user_input_lower:
            category = KEYWORD_CATEGORY_MAP[keyword]
            if category not in seen:
                categories.append(category)
                seen.add(category)

    if categories:
        logger.info(f"Extracted categories from keywords: {categories}")
    else:
        logger.warning(f"No categories extracted from input: {user_input}")

    return categories


def get_baseline_for_category(category: str, baseline_data: dict) -> Optional[dict]:
    """
    Get baseline data for a specific category.

    Args:
        category: Category name
        baseline_data: Full baseline data dict

    Returns:
        Baseline dict for category with 'your_usual' flag
    """
    categories = baseline_data.get("categories", {})
    cat_data = categories.get(category)

    if not cat_data:
        return None

    return {
        "brand": cat_data.get("usual_brand", "Unknown"),
        "price": cat_data.get("median_price"),
        "packaging": cat_data.get("common_packaging", "Unknown"),
        "your_usual": True,
    }


def get_alternatives_for_category(
    category: str,
    alternatives_data: dict,
    use_off_fallback: bool = True,
) -> Optional[dict]:
    """
    Get alternatives for a specific category.

    Falls back to Open Food Facts API when local data is unavailable.

    Args:
        category: Category name
        alternatives_data: Full alternatives data dict
        use_off_fallback: Whether to use Open Food Facts as fallback

    Returns:
        Alternatives dict with cheaper/balanced/conscious tiers
    """
    # Try local data first
    local_alternatives = alternatives_data.get(category)
    if local_alternatives:
        return local_alternatives

    # Fallback to Open Food Facts
    if use_off_fallback:
        logger.info(f"No local alternatives for '{category}', trying Open Food Facts...")
        off_alternatives = get_off_alternatives_for_category(category)
        if off_alternatives:
            logger.info(f"Found alternatives from Open Food Facts for '{category}'")
            return off_alternatives

    return None


def get_flags_for_category(category: str, flags_data: dict) -> list[dict]:
    """
    Get any flags (recalls, seasonal notices, etc.) for a category.

    Args:
        category: Category name
        flags_data: Full flags data dict

    Returns:
        List of flag dictionaries
    """
    return flags_data.get(category, [])


def validate_facts_pack(facts_pack: dict) -> tuple[bool, list[str]]:
    """
    Validate the assembled facts pack.

    Checks:
    - All categories have alternatives
    - Prices are reasonable (0 < price < 1000)
    - No missing required fields

    Args:
        facts_pack: The assembled facts pack

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if not facts_pack.get("items"):
        errors.append("No items in facts pack")
        return False, errors

    for item in facts_pack["items"]:
        category = item.get("category", "unknown")

        # Check baseline
        baseline = item.get("baseline")
        if baseline:
            price = baseline.get("price")
            if price is not None and (price <= 0 or price > 1000):
                errors.append(f"{category}: baseline price {price} is out of reasonable range")

        # Check alternatives exist
        alternatives = item.get("alternatives")
        if not alternatives:
            errors.append(f"{category}: missing alternatives data")
        else:
            # Check each tier has required fields
            for tier in ["cheaper", "balanced", "conscious"]:
                tier_data = alternatives.get(tier, {})
                if not tier_data:
                    errors.append(f"{category}: missing '{tier}' alternative tier")
                else:
                    # Check if tier is populated (has brand)
                    brand = tier_data.get("brand")
                    if not brand:
                        errors.append(f"{category}: '{tier}' tier missing brand")

                    # Validate price if present
                    est_price = tier_data.get("est_price")
                    if est_price is not None and (est_price <= 0 or est_price > 1000):
                        errors.append(f"{category}: '{tier}' price {est_price} is out of range")

    return len(errors) == 0, errors


def generate_facts_pack(
    user_input: str,
    user_context: dict = None,
    baseline_path: Path = None,
    alternatives_path: Path = None,
    flags_path: Path = None,
    use_off_fallback: bool = True,
) -> dict:
    """
    Assemble decision context for a user request.

    Args:
        user_input: User's request string (e.g., "miso soup ingredients")
        user_context: Optional user preferences dict
        baseline_path: Optional override for baseline data path
        alternatives_path: Optional override for alternatives CSV path
        flags_path: Optional override for flags data path
        use_off_fallback: Whether to use Open Food Facts API as fallback
            when local alternatives data is missing (default: True)

    Returns:
        Facts pack dictionary with request, items, and user_context
    """
    logger.info(f"Generating facts pack for: {user_input}")

    # Load data
    baseline_data = load_baseline(baseline_path)
    alternatives_data = load_alternatives_from_csv(alternatives_path)
    flags_data = load_flags(flags_path)

    # Parse user input to get categories
    categories = parse_user_input(user_input)

    # Build items list
    items = []
    for category in categories:
        item = {
            "category": category,
            "baseline": get_baseline_for_category(category, baseline_data),
            "alternatives": get_alternatives_for_category(
                category, alternatives_data, use_off_fallback=use_off_fallback
            ),
            "flags": get_flags_for_category(category, flags_data),
        }
        items.append(item)

    # Assemble facts pack
    facts_pack = {
        "request": user_input,
        "items": items,
        "user_context": user_context or DEFAULT_USER_CONTEXT.copy(),
    }

    # Validate
    is_valid, errors = validate_facts_pack(facts_pack)
    if not is_valid:
        logger.warning(f"Facts pack validation warnings: {errors}")
        facts_pack["validation_warnings"] = errors

    logger.info(f"Generated facts pack with {len(items)} items")
    return facts_pack


def main():
    """CLI entry point for testing facts pack generation."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Generate facts pack for a user request"
    )
    parser.add_argument(
        "request",
        type=str,
        help="User request (e.g., 'miso soup ingredients')"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for JSON (prints to stdout if not specified)"
    )

    args = parser.parse_args()

    facts_pack = generate_facts_pack(args.request)

    output = json.dumps(facts_pack, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Facts pack written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
