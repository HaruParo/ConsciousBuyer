"""
Category mapping module.
Analyzes items and assigns them to categories using fuzzy matching and rules.

Categories are designed for conscious shopping analysis:
- Tracking consumption patterns
- Identifying sustainable alternatives
- Grouping similar products for comparison
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ingest import (
    Category,
    Item,
    ItemCategory,
    create_tables,
    get_engine,
    get_session,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Category Definitions
# =============================================================================

# Category definitions with patterns for matching
# Format: (category_name, [patterns], priority)
# Higher priority = matched first for items that could match multiple categories
CATEGORY_DEFINITIONS = [
    # Dairy & Eggs
    ("milk", [r"\bmilk\b", r"creamline.*milk"], 10),
    ("yogurt", [r"\byogurt\b"], 10),
    ("cheese", [r"\bcheese\b", r"\bcheddar\b", r"\bswiss\s+cheese\b", r"\bpaneer\b"], 10),
    ("eggs", [r"\beggs?\b"], 10),
    ("ice_cream", [r"ice\s*cream", r"\bmochi\b"], 10),
    ("butter_ghee", [r"\bghee\b", r"\bbutter\b"], 10),

    # Proteins
    ("chicken", [r"\bchicken\b"], 10),
    ("meat_other", [r"\bbeef\b", r"\bpork\b", r"\blamb\b", r"\bturkey\b"], 10),

    # Nuts & Seeds
    ("nuts_almonds", [r"\balmonds?\b"], 10),
    ("nuts_cashews", [r"\bcashews?\b"], 10),
    ("nuts_peanuts", [r"\bpeanuts?\b"], 10),
    ("nuts_other", [r"\bnuts?\b", r"\bpistachi"], 8),

    # Grains & Bread
    ("bread", [r"\bbread\b", r"\bsourdough\b", r"\bbagels?\b", r"\bmuffins?\b"], 10),
    ("grains", [r"\bquinoa\b", r"\brice\b", r"\boats?\b", r"\bbarley\b"], 10),

    # Produce - Onions & Alliums
    ("produce_onions", [r"\bonions?\b", r"\bshallots?\b", r"\bscallions?\b", r"\bleeks?\b", r"\bgarlic\b"], 10),

    # Produce - Tomatoes
    ("produce_tomatoes", [r"\btomato(?:es)?\b"], 10),

    # Produce - Cucumbers
    ("produce_cucumbers", [r"\bcucumbers?\b"], 10),

    # Produce - Greens & Leafy
    ("produce_greens", [
        r"\bspinach\b", r"\bkale\b", r"\bchard\b", r"\blettuce\b",
        r"\bgreens?\b", r"\bcollard\b", r"\btatsoi\b", r"\bcabbage\b",
        r"\bbroccoli\b", r"\bbasil\b", r"\bcilantro\b", r"\bmint\b",
        r"\bspearmint\b", r"\bherbs?\b"
    ], 8),

    # Produce - Root Vegetables
    ("produce_root_veg", [
        r"\bcarrots?\b", r"\bbeets?\b", r"\bpotato(?:es)?\b",
        r"\bturnips?\b", r"\bradish(?:es)?\b", r"\bsweet\s*potato",
        r"\bginger\b", r"\bfenway\b"
    ], 9),

    # Produce - Squash & Gourds
    ("produce_squash", [
        r"\bsquash\b", r"\bzucchini\b", r"\beggplant\b",
        r"\bpumpkin\b", r"\bdelicata\b", r"\bacorn\b",
        r"\bhoneynut\b", r"\bkabocha\b", r"\bchayote\b"
    ], 9),

    # Produce - Beans & Peas
    ("produce_beans", [
        r"\bbeans?\b", r"\bpeas?\b", r"\bedamame\b",
        r"\bokra\b", r"\blong\s*beans?\b"
    ], 9),

    # Produce - Peppers
    ("produce_peppers", [r"\bpeppers?\b", r"\bjalapeno\b", r"\bthai\s*peppers?\b"], 10),

    # Produce - Mushrooms
    ("produce_mushrooms", [r"\bmushrooms?\b", r"lion'?s?\s*mane"], 10),

    # Produce - Fruits (Berries)
    ("fruit_berries", [
        r"\bberries\b", r"\bblueberr", r"\bstrawberr",
        r"\bblackberr", r"\braspberr", r"\bcranberr"
    ], 10),

    # Produce - Fruits (Tropical)
    ("fruit_tropical", [
        r"\bbananas?\b", r"\bplantains?\b", r"\bmango\b",
        r"\bpineapple\b", r"\bcoconut\b", r"\bpapaya\b",
        r"\bguava\b", r"\bdrag[oi]n\s*fruit\b", r"\bbreadfruit\b",
        r"\bavocados?\b"
    ], 9),

    # Produce - Fruits (Citrus)
    ("fruit_citrus", [
        r"\boranges?\b", r"\blemons?\b", r"\blimes?\b",
        r"\bgrapefruit\b", r"\bcitrus\b", r"\bnavel\b"
    ], 10),

    # Produce - Fruits (Other)
    ("fruit_other", [
        r"\bapples?\b", r"\bpears?\b", r"\bgrapes?\b",
        r"\bmelon\b", r"\bwatermelon\b", r"\bcantaloupe\b"
    ], 8),

    # Oils
    ("oils_olive", [r"olive\s*oil"], 10),
    ("oils_coconut", [r"coconut\s*oil"], 10),
    ("oils_other", [r"\boil\b"], 5),

    # Vinegars
    ("vinegar", [r"\bvinegar\b"], 10),

    # Spices & Seasonings
    ("spices", [
        r"\bturmeric\b", r"\bcumin\b", r"crushed.*red.*pepper",
        r"\biodized\s*salt\b", r"\bsea\s*salt\b", r"\bkosher\s*salt\b",
        r"^morton\b", r"\bspices?\b", r"\bseasoning",
        r"\bza'?atar\b", r"red\s*pepper\s*flakes?"
    ], 10),

    # Fermented Foods
    ("fermented", [r"\bkimchi\b", r"\bmiso\b", r"\bsauerkraut\b"], 10),

    # Canned & Jarred
    ("canned_coconut", [r"coconut\s*(cream|milk)", r"native\s*forest"], 10),

    # Snacks & Sweets
    ("chocolate", [r"\bchocolate\b", r"\bcocoa\b"], 10),
    ("cookies_crackers", [r"\bcookies?\b", r"\bcrackers?\b", r"\bshortbread\b"], 10),
    ("chips", [r"\bchips\b"], 10),
    ("hummus_dips", [r"\bhummus\b", r"\bdips?\b"], 10),

    # Beverages
    ("tea", [r"\btea\b", r"\bchamomile\b", r"\bherbal\b"], 8),

    # Frozen
    ("frozen_veg", [r"frozen\s*(peas|veg|corn)"], 10),
    ("corn", [r"\bcorn\b"], 8),

    # Personal Care (non-food)
    ("personal_care", [r"\btoothpaste\b", r"\bshampoo\b", r"\bsoap\b", r"\bsensodyne\b"], 10),

    # Lemongrass (herb/aromatic)
    ("produce_aromatics", [r"\blemongrass\b"], 10),
]

# Manual overrides for specific items (item_name -> category_name)
# Use this for edge cases where pattern matching fails
MANUAL_OVERRIDES = {
    "Sour Cream & Onion Chips": "chips",
    "Sweet Potato Chips": "chips",
    "Zesty Za'atar Hummus": "hummus_dips",
    "Headwater Food Hub Frozen Peas": "frozen_veg",
    "Saunderskill Farms Bi-color Sweet Corn": "corn",
    "Fresh Coconut Chunks": "fruit_tropical",
    "Organic Coconut Milk": "canned_coconut",
    "Native Forest Unsweetened Organic Coconut Cream": "canned_coconut",
    "Simply Organic Crushed Red Pepper": "spices",
    "Beyond Good 85% Sea Salt Dark Chocolate Bar": "chocolate",
}

# Brand-based category hints (brand pattern -> category)
BRAND_CATEGORY_HINTS = {
    r"driscoll": "fruit_berries",
    r"family\s*tree\s*farms": "fruit_berries",
    r"naturipe": "fruit_berries",
    r"farmer\s*focus": "chicken",
    r"vital\s*farms": "eggs",
    r"bread\s*alone": "bread",
    r"black\s*seed\s*bagels": "bread",
    r"dam\s*good": "bread",
    r"van\s*leeuwen": "ice_cream",
    r"new\s*city\s*microcreamery": "ice_cream",
    r"adirondack\s*creamery": "ice_cream",
    r"bubbies": "ice_cream",
    r"ronnybrook": "milk",
    r"alexandre": "milk",
    r"organic\s*valley": "milk",
    r"family\s*farmstead": "milk",
    r"hawthorne\s*valley": "yogurt",
    r"white\s*moustache": "yogurt",
    r"miso\s*master": "fermented",
    r"mama\s*o": "fermented",
    r"burlap.*barrel": "spices",
    r"simply\s*organic": "spices",
    r"bob'?s\s*red\s*mill": "grains",
    r"bragg": "vinegar",
    r"de\s*nigris": "vinegar",
    r"la\s*tourangelle": "oils_olive",
    r"nutiva": "oils_coconut",
    r"spectrum": "oils_coconut",
    r"beyond\s*good": "chocolate",
    r"hu\s*kitchen": "chocolate",
    r"mulino\s*bianco": "cookies_crackers",
    r"rustic\s*bakery": "cookies_crackers",
    r"celestial": "tea",
    r"sensodyne": "personal_care",
}


# =============================================================================
# Categorization Logic
# =============================================================================


def _match_patterns(text: str, patterns: list[str]) -> bool:
    """Check if text matches any of the patterns."""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def _get_category_from_brand(brand: str) -> Optional[str]:
    """Get category hint from brand name."""
    if not brand:
        return None
    brand_lower = brand.lower()
    for pattern, category in BRAND_CATEGORY_HINTS.items():
        if re.search(pattern, brand_lower, re.IGNORECASE):
            return category
    return None


def categorize_item(name: str, brand: Optional[str] = None) -> str:
    """
    Determine the category for an item based on name and brand.

    Args:
        name: Item name
        brand: Brand name (optional)

    Returns:
        Category name
    """
    # Check manual overrides first
    if name in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[name]

    # Check brand hints
    brand_category = _get_category_from_brand(brand)

    # Sort categories by priority (highest first)
    sorted_categories = sorted(
        CATEGORY_DEFINITIONS,
        key=lambda x: x[2],
        reverse=True
    )

    # Try to match item name against patterns
    for category_name, patterns, priority in sorted_categories:
        if _match_patterns(name, patterns):
            return category_name

    # Fall back to brand hint if no pattern matched
    if brand_category:
        return brand_category

    # Default category for unmatched items
    return "uncategorized"


def assign_category(item_id: int, engine=None) -> str:
    """
    Get category name for an item by ID.

    Args:
        item_id: The item ID to look up
        engine: SQLAlchemy engine (optional)

    Returns:
        Category name for the item
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)
    try:
        item = session.query(Item).filter(Item.item_id == item_id).first()
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        return categorize_item(item.name, item.brand)
    finally:
        session.close()


# =============================================================================
# Database Operations
# =============================================================================


def get_or_create_category(session: Session, category_name: str) -> Category:
    """Get existing category or create new one."""
    category = session.query(Category).filter(
        Category.category_name == category_name
    ).first()

    if not category:
        category = Category(category_name=category_name)
        session.add(category)
        session.flush()

    return category


def categorize_all_items(engine=None, clear_existing: bool = False) -> dict:
    """
    Categorize all items in the database.

    Args:
        engine: SQLAlchemy engine (optional)
        clear_existing: Whether to clear existing category mappings

    Returns:
        Statistics about categorization
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)
    stats = {
        "items_processed": 0,
        "categories_created": 0,
        "mappings_created": 0,
        "category_counts": {},
    }

    try:
        # Clear existing mappings if requested
        if clear_existing:
            session.query(ItemCategory).delete()
            session.query(Category).delete()
            session.commit()
            logger.info("Cleared existing category mappings")

        # Get all items
        items = session.query(Item).all()
        logger.info(f"Processing {len(items)} items...")

        # Track categories we've created
        categories_cache = {}

        for item in items:
            category_name = categorize_item(item.name, item.brand)

            # Get or create category
            if category_name not in categories_cache:
                category = get_or_create_category(session, category_name)
                categories_cache[category_name] = category
                if category.category_id is None or session.new:
                    stats["categories_created"] += 1
            else:
                category = categories_cache[category_name]

            # Check if mapping already exists
            existing = session.query(ItemCategory).filter(
                ItemCategory.item_id == item.item_id,
                ItemCategory.category_id == category.category_id
            ).first()

            if not existing:
                mapping = ItemCategory(
                    item_id=item.item_id,
                    category_id=category.category_id
                )
                session.add(mapping)
                stats["mappings_created"] += 1

            # Track counts
            stats["category_counts"][category_name] = \
                stats["category_counts"].get(category_name, 0) + 1
            stats["items_processed"] += 1

        session.commit()
        logger.info(
            f"Categorization complete: {stats['items_processed']} items, "
            f"{stats['categories_created']} new categories, "
            f"{stats['mappings_created']} mappings"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error during categorization: {e}")
        raise
    finally:
        session.close()

    return stats


def export_category_mapping(output_path: Path, engine=None) -> dict:
    """
    Export category mapping to JSON file.

    Args:
        output_path: Path to output JSON file
        engine: SQLAlchemy engine (optional)

    Returns:
        The mapping dictionary that was exported
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)

    try:
        # Build mapping
        mapping = {
            "categories": {},
            "items": {},
            "summary": {
                "total_items": 0,
                "total_categories": 0,
            }
        }

        # Get all categories with their items
        categories = session.query(Category).all()

        for category in categories:
            # Get items in this category
            item_mappings = session.query(ItemCategory).filter(
                ItemCategory.category_id == category.category_id
            ).all()

            item_ids = [m.item_id for m in item_mappings]
            items = session.query(Item).filter(Item.item_id.in_(item_ids)).all()

            mapping["categories"][category.category_name] = {
                "category_id": category.category_id,
                "items": [
                    {
                        "item_id": item.item_id,
                        "name": item.name,
                        "brand": item.brand,
                    }
                    for item in items
                ]
            }

        # Build item -> category mapping
        all_items = session.query(Item).all()
        for item in all_items:
            item_category = session.query(ItemCategory).filter(
                ItemCategory.item_id == item.item_id
            ).first()

            if item_category:
                category = session.query(Category).filter(
                    Category.category_id == item_category.category_id
                ).first()
                mapping["items"][str(item.item_id)] = {
                    "name": item.name,
                    "brand": item.brand,
                    "category": category.category_name if category else "uncategorized"
                }

        mapping["summary"]["total_items"] = len(mapping["items"])
        mapping["summary"]["total_categories"] = len(mapping["categories"])

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(mapping, f, indent=2)

        logger.info(f"Exported category mapping to {output_path}")
        return mapping

    finally:
        session.close()


def get_items_by_category(category_name: str, engine=None) -> list[dict]:
    """
    Get all items in a specific category.

    Args:
        category_name: Name of the category
        engine: SQLAlchemy engine (optional)

    Returns:
        List of item dictionaries
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)

    try:
        category = session.query(Category).filter(
            Category.category_name == category_name
        ).first()

        if not category:
            return []

        item_mappings = session.query(ItemCategory).filter(
            ItemCategory.category_id == category.category_id
        ).all()

        item_ids = [m.item_id for m in item_mappings]
        items = session.query(Item).filter(Item.item_id.in_(item_ids)).all()

        return [
            {
                "item_id": item.item_id,
                "name": item.name,
                "brand": item.brand,
                "size": item.size,
                "packaging_type": item.packaging_type,
            }
            for item in items
        ]
    finally:
        session.close()


def get_category_summary(engine=None) -> dict:
    """
    Get summary of all categories and item counts.

    Args:
        engine: SQLAlchemy engine (optional)

    Returns:
        Dictionary with category names and item counts
    """
    if engine is None:
        engine = get_engine()

    session = get_session(engine)

    try:
        categories = session.query(Category).all()
        summary = {}

        for category in categories:
            count = session.query(ItemCategory).filter(
                ItemCategory.category_id == category.category_id
            ).count()
            summary[category.category_name] = count

        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))
    finally:
        session.close()


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """CLI entry point for category mapping."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Categorize items and export mapping"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing category mappings before processing"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/category_mapping.json",
        help="Output path for category mapping JSON"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Only show category summary (no changes)"
    )

    args = parser.parse_args()

    try:
        if args.summary:
            summary = get_category_summary()
            print("\nCategory Summary:")
            print("-" * 40)
            for category, count in summary.items():
                print(f"  {category}: {count} items")
            print("-" * 40)
            print(f"Total categories: {len(summary)}")
        else:
            # Run categorization
            stats = categorize_all_items(clear_existing=args.clear)

            print(f"\nCategorization Complete:")
            print(f"  Items processed: {stats['items_processed']}")
            print(f"  Categories created: {stats['categories_created']}")
            print(f"  Mappings created: {stats['mappings_created']}")

            # Export mapping
            mapping = export_category_mapping(args.output)
            print(f"\nExported to: {args.output}")
            print(f"  Total categories: {mapping['summary']['total_categories']}")
            print(f"  Total items: {mapping['summary']['total_items']}")

            # Show category breakdown
            print("\nCategory Breakdown:")
            for category, count in sorted(
                stats["category_counts"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {category}: {count}")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
