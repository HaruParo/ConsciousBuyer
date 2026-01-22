"""
Facts pack module.
Assembles decision context by combining baseline data, alternatives, and flags.

Uses Open Food Facts (https://openfoodfacts.org/) as a fallback data source
when local alternatives data is unavailable.

Supports two modes:
1. Static mode: Load from CSV/JSON files (original behavior)
2. Agent mode: Use multi-agent orchestrator for learning and personalization
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Optional

from .open_food_facts import get_off_alternatives_for_category

# Lazy import for agent system to avoid circular imports
_orchestrator = None

logger = logging.getLogger(__name__)

# Default data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
BASELINE_PATH = DATA_DIR / "processed" / "baseline_stats.json"
ALTERNATIVES_CSV_PATH = DATA_DIR / "alternatives" / "alternatives_template.csv"
FLAGS_PATH = DATA_DIR / "flags" / "product_flags.json"

# Predefined recipe mappings for common requests
# Each recipe maps to a list of ingredient categories
RECIPE_MAPPINGS = {
    # Asian
    # Miso soup: miso paste, tofu, seaweed (wakame), green onions/scallions, dashi (optional)
    "miso soup": ["miso_paste", "tofu", "seaweed", "produce_onions", "dashi"],
    "stir fry": ["produce_peppers", "produce_onions", "produce_greens", "oils_other", "grains"],
    "fried rice": ["grains", "eggs", "produce_onions", "produce_peppers", "oils_other"],
    "ramen": ["grains", "eggs", "produce_greens", "produce_onions", "fermented"],
    "sushi": ["grains", "produce_cucumbers", "fruit_tropical", "vinegar"],
    "pad thai": ["grains", "eggs", "produce_onions", "nuts_peanuts", "produce_beans"],
    "pho": ["grains", "produce_onions", "produce_aromatics", "spices", "produce_greens"],

    # Indian
    "sambar": ["produce_onions", "produce_tomatoes", "spices", "grains", "produce_root_veg"],
    "dal": ["grains", "produce_onions", "produce_tomatoes", "spices", "produce_aromatics"],
    "biryani": ["grains", "produce_onions", "yogurt", "spices", "produce_aromatics"],
    "curry": ["produce_onions", "produce_tomatoes", "spices", "canned_coconut", "grains"],
    "paneer": ["cheese", "produce_onions", "produce_tomatoes", "spices", "produce_peppers"],
    "chana masala": ["canned_beans", "produce_onions", "produce_tomatoes", "spices"],
    "aloo gobi": ["produce_root_veg", "produce_onions", "spices", "produce_aromatics"],
    "palak paneer": ["produce_greens", "cheese", "produce_onions", "spices"],
    "tikka masala": ["yogurt", "produce_onions", "produce_tomatoes", "spices", "chicken"],
    "butter chicken": ["chicken", "butter_ghee", "produce_tomatoes", "yogurt", "spices"],
    "dosa": ["grains", "produce_onions", "produce_root_veg", "canned_coconut", "spices"],
    "idli": ["grains", "produce_onions", "canned_coconut", "spices"],
    "upma": ["grains", "produce_onions", "produce_peppers", "nuts_cashews", "spices"],
    "poha": ["grains", "produce_onions", "produce_peppers", "nuts_peanuts", "spices"],

    # Mexican/Latin
    "tacos": ["produce_peppers", "produce_onions", "produce_tomatoes", "cheese", "spices"],
    "burrito": ["grains", "canned_beans", "cheese", "produce_tomatoes", "produce_onions"],
    "guacamole": ["fruit_tropical", "produce_onions", "produce_tomatoes", "produce_peppers", "spices"],
    "enchiladas": ["bread", "cheese", "produce_onions", "produce_tomatoes", "spices"],
    "quesadilla": ["bread", "cheese", "produce_peppers", "produce_onions"],
    "nachos": ["chips", "cheese", "canned_beans", "produce_tomatoes", "produce_peppers"],
    "salsa": ["produce_tomatoes", "produce_onions", "produce_peppers", "produce_aromatics", "spices"],

    # Italian/Mediterranean
    "pasta": ["grains", "produce_tomatoes", "produce_aromatics", "oils_olive", "cheese"],
    "pizza": ["bread", "cheese", "produce_tomatoes", "produce_peppers", "oils_olive"],
    "risotto": ["grains", "cheese", "produce_onions", "butter_ghee", "produce_mushrooms"],
    "lasagna": ["grains", "cheese", "produce_tomatoes", "produce_aromatics", "eggs"],
    "bruschetta": ["bread", "produce_tomatoes", "produce_aromatics", "oils_olive"],
    "caprese": ["produce_tomatoes", "cheese", "oils_olive", "produce_aromatics"],
    "hummus": ["hummus_dips", "produce_aromatics", "oils_olive", "spices"],
    "falafel": ["hummus_dips", "produce_onions", "produce_aromatics", "spices"],

    # American/Western
    "salad": ["produce_greens", "produce_tomatoes", "produce_cucumbers", "oils_olive", "vinegar"],
    "sandwich": ["bread", "produce_greens", "produce_tomatoes", "cheese", "hummus_dips"],
    "burger": ["bread", "produce_tomatoes", "produce_onions", "cheese", "produce_greens"],
    "soup": ["produce_onions", "produce_root_veg", "produce_aromatics", "spices"],
    "roasted vegetables": ["produce_root_veg", "produce_squash", "produce_peppers", "oils_olive", "spices"],
    "grilled cheese": ["bread", "cheese", "butter_ghee"],
    "mac and cheese": ["grains", "cheese", "milk", "butter_ghee"],
    "chili": ["canned_beans", "produce_tomatoes", "produce_onions", "produce_peppers", "spices"],

    # Breakfast
    "breakfast": ["eggs", "bread", "butter_ghee", "fruit_berries", "yogurt"],
    "omelette": ["eggs", "cheese", "produce_peppers", "produce_onions", "butter_ghee"],
    "pancakes": ["grains", "eggs", "milk", "butter_ghee", "fruit_berries"],
    "waffles": ["grains", "eggs", "milk", "butter_ghee", "fruit_berries"],
    "french toast": ["bread", "eggs", "milk", "butter_ghee", "fruit_berries"],
    "granola": ["grains", "nuts_almonds", "fruit_berries", "yogurt", "milk"],
    "acai bowl": ["fruit_berries", "fruit_tropical", "yogurt", "nuts_almonds", "grains"],
    "avocado toast": ["bread", "fruit_tropical", "eggs", "produce_tomatoes", "spices"],
    "oatmeal": ["grains", "milk", "fruit_berries", "nuts_almonds"],
    "cereal": ["grains", "milk", "fruit_berries"],

    # Smoothies/Drinks
    "smoothie": ["fruit_berries", "fruit_tropical", "yogurt", "milk"],
    "protein shake": ["milk", "fruit_tropical", "yogurt", "nuts_almonds"],
    "juice": ["fruit_citrus", "fruit_tropical", "produce_root_veg", "produce_greens"],

    # Snacks
    "trail mix": ["nuts_almonds", "nuts_cashews", "fruit_berries", "chocolate"],
    "chips and dip": ["chips", "hummus_dips", "produce_tomatoes"],
    "cheese plate": ["cheese", "nuts_almonds", "fruit_other", "crackers"],

    # Weekly/Bulk
    "groceries": ["produce_greens", "produce_tomatoes", "produce_onions", "eggs", "milk", "bread", "grains", "cheese"],
    "weekly groceries": ["produce_greens", "produce_tomatoes", "produce_onions", "eggs", "milk", "bread", "grains", "cheese", "fruit_berries", "yogurt"],
    "essentials": ["eggs", "milk", "bread", "butter_ghee", "produce_onions", "produce_aromatics"],
    "basics": ["eggs", "milk", "bread", "grains", "oils_olive", "produce_onions"],
    "pantry": ["grains", "oils_olive", "spices", "canned_beans", "canned_coconut", "vinegar"],
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
    "tofu": "tofu", "tempeh": "fermented", "miso": "miso_paste", "miso paste": "miso_paste",

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
    # Japanese/Asian ingredients
    "seaweed": "seaweed", "nori": "seaweed", "wakame": "seaweed", "kombu": "seaweed",
    "dashi": "dashi", "bonito": "dashi", "hon dashi": "dashi",
    "scallions": "produce_onions", "green onion": "produce_onions", "green onions": "produce_onions",
    # Indian ingredients
    "dal": "grains", "lentils": "grains", "chickpeas": "canned_beans", "paneer": "cheese",
    "ghee": "butter_ghee", "tamarind": "spices", "curry powder": "spices", "garam masala": "spices",
    "coriander": "spices", "cilantro": "produce_aromatics", "chutney": "hummus_dips",
    # More produce
    "broccoli": "produce_greens", "cauliflower": "produce_greens", "cabbage": "produce_greens",
    "celery": "produce_greens", "asparagus": "produce_beans", "corn": "produce_beans",
    "eggplant": "produce_squash", "okra": "produce_beans",
    # Canned goods
    "canned beans": "canned_beans", "black beans": "canned_beans", "kidney beans": "canned_beans",
    "coconut milk": "canned_coconut", "tomato sauce": "produce_tomatoes", "tomato paste": "produce_tomatoes",
    # Crackers
    "crackers": "cookies_crackers",
}

# Default user context
DEFAULT_USER_CONTEXT = {
    "budget_priority": "medium",
    "health_priority": "medium",
    "packaging_priority": "medium",
    "location": "",  # User's location (state, region, or city) for seasonal/recall filtering
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


def get_orchestrator(data_dir: str = None, user_id: str = "default"):
    """
    Get or create the agent orchestrator singleton.

    Args:
        data_dir: Base directory for agent data stores (defaults to DATA_DIR)
        user_id: User identifier for personalization

    Returns:
        AgentOrchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        # Import here to avoid circular imports
        # Use absolute import that works both as module and standalone
        import sys
        agents_path = Path(__file__).parent.parent / "agents"
        if str(agents_path.parent) not in sys.path:
            sys.path.insert(0, str(agents_path.parent))

        from agents.orchestrator import AgentOrchestrator

        data_path = Path(data_dir) if data_dir else DATA_DIR
        _orchestrator = AgentOrchestrator(data_path, user_id)
        logger.info(f"Initialized AgentOrchestrator for user '{user_id}'")

    return _orchestrator


def generate_facts_pack_with_agents(
    user_input: str,
    user_id: str = "default",
    store: str = "freshdirect",
    data_dir: str = None,
) -> dict:
    """
    Generate facts pack using the multi-agent system.

    This provides enhanced functionality over the static generate_facts_pack():
    - Learns from user purchases to identify personal staples
    - Tracks price and availability changes
    - Provides personalized tier recommendations
    - Enforces EWG Dirty Dozen/Clean Fifteen rules
    - Checks active recalls

    Args:
        user_input: User's request string (e.g., "miso soup ingredients")
        user_id: User identifier for personalization
        store: Store identifier (default: "freshdirect")
        data_dir: Optional override for data directory

    Returns:
        Enhanced facts pack with agent metadata and personalization
    """
    logger.info(f"Generating agent-enhanced facts pack for: {user_input}")

    # Parse user input to get categories
    categories = parse_user_input(user_input)

    if not categories:
        logger.warning(f"No categories extracted from: {user_input}")
        return {
            "request": user_input,
            "items": [],
            "user_context": DEFAULT_USER_CONTEXT.copy(),
            "agent_mode": True,
            "error": "No categories could be extracted from the request",
        }

    # Get orchestrator
    orchestrator = get_orchestrator(data_dir, user_id)

    # Build facts pack using agents
    agent_facts_pack = orchestrator.build_facts_pack(categories, store)

    # Transform to expected format while preserving agent enhancements
    items = []
    for agent_item in agent_facts_pack.get("items", []):
        # Get baseline from static data for backward compatibility
        baseline_data = load_baseline()
        baseline = get_baseline_for_category(agent_item["category"], baseline_data)

        item = {
            "category": agent_item["category"],
            "baseline": baseline,
            "alternatives": agent_item.get("alternatives", {}),
            "flags": agent_item.get("flags", []),
            # Agent-enhanced fields
            "ewg_classification": agent_item.get("ewg_classification"),
            "organic_required": agent_item.get("organic_required", False),
            "has_active_recall": agent_item.get("has_active_recall", False),
            "availability_issues": agent_item.get("availability_issues", []),
            "specialty_promotions": agent_item.get("specialty_promotions", []),
            "user_category_data": agent_item.get("user_category_data", {}),
        }
        items.append(item)

    # Merge user context
    agent_user_context = agent_facts_pack.get("user_context", {})
    merged_context = DEFAULT_USER_CONTEXT.copy()
    merged_context.update({
        "user_id": agent_user_context.get("user_id", user_id),
        "tier_preference": agent_user_context.get("tier_preference"),
        "personal_staples": agent_user_context.get("personal_staples", []),
        "frequent_categories": agent_user_context.get("frequent_categories", []),
        "dietary": agent_user_context.get("dietary", []),
        "organic_preference": agent_user_context.get("organic_preference", "flexible"),
        "local_preference": agent_user_context.get("local_preference", False),
        "cuisine_preferences": agent_user_context.get("cuisine_preferences", []),
        "avoid_categories": agent_user_context.get("avoid_categories", []),
    })

    facts_pack = {
        "request": user_input,
        "store": store,
        "timestamp": agent_facts_pack.get("timestamp"),
        "items": items,
        "user_context": merged_context,
        "agent_mode": True,
        "agent_metadata": agent_facts_pack.get("agent_metadata", {}),
    }

    # Validate
    is_valid, errors = validate_facts_pack(facts_pack)
    if not is_valid:
        logger.warning(f"Facts pack validation warnings: {errors}")
        facts_pack["validation_warnings"] = errors

    logger.info(f"Generated agent-enhanced facts pack with {len(items)} items")
    return facts_pack


def record_decision_feedback(
    decision: dict,
    feedback: dict = None,
    user_id: str = "default",
) -> None:
    """
    Record decision feedback for agent learning.

    Call this after a user interacts with a recommendation to help
    the agents learn and improve future recommendations.

    Args:
        decision: The decision output that was shown to user
        feedback: Optional feedback dict with:
            - purchased: bool - whether user purchased
            - product_name: str - what they bought
            - brand: str - brand purchased
            - price: float - actual price paid
            - rejected: bool - whether user rejected recommendation
            - reason: str - reason for rejection
        user_id: User identifier
    """
    orchestrator = get_orchestrator(user_id=user_id)
    orchestrator.learn_from_decision(decision, feedback)
    logger.info(f"Recorded decision feedback for user '{user_id}'")


def get_quick_recommendation(
    category: str,
    user_id: str = "default",
    tier_preference: str = None,
) -> dict:
    """
    Get a quick recommendation without full facts pack generation.

    Useful for simple single-category queries where the full LLM
    decision engine isn't needed.

    Args:
        category: Product category
        user_id: User identifier
        tier_preference: Override user's default tier preference

    Returns:
        Recommendation dict with product and reasoning
    """
    orchestrator = get_orchestrator(user_id=user_id)
    return orchestrator.get_recommendation(category, tier_preference)


def get_shopping_list_recommendations(
    categories: list[str],
    user_id: str = "default",
) -> list[dict]:
    """
    Get recommendations for a complete shopping list.

    Args:
        categories: List of categories to shop for
        user_id: User identifier

    Returns:
        List of recommendations, one per category
    """
    orchestrator = get_orchestrator(user_id=user_id)
    return orchestrator.get_shopping_list(categories)


if __name__ == "__main__":
    main()
