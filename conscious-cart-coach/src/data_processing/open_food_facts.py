"""
Open Food Facts API client.
Provides fallback product information when local data is unavailable.

API Documentation: https://openfoodfacts.github.io/openfoodfacts-server/api/
Packaging Data: https://openfoodfacts.github.io/openfoodfacts-server/dev/explain-packaging-data/
Rate Limits: 10 req/min for search queries
"""

import logging
import time
from typing import Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

# API Configuration
OFF_API_BASE = "https://world.openfoodfacts.org/api/v2"
OFF_SEARCH_BASE = "https://world.openfoodfacts.org/cgi/search.pl"
USER_AGENT = "ConsciousCartCoach/1.0 (conscious-cart-coach@example.com)"

# Rate limiting
_last_request_time = 0.0
MIN_REQUEST_INTERVAL = 6.0  # 10 req/min = 1 req per 6 seconds


def _rate_limit():
    """Enforce rate limiting for API requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - elapsed
        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)
    _last_request_time = time.time()


def _make_request(url: str, params: dict = None) -> Optional[dict]:
    """
    Make a rate-limited request to Open Food Facts API.

    Args:
        url: API endpoint URL
        params: Query parameters

    Returns:
        JSON response dict or None on error
    """
    _rate_limit()

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.warning(f"Request timeout for {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error for {url}: {e}")
        return None
    except ValueError as e:
        logger.warning(f"JSON decode error for {url}: {e}")
        return None


# Common fields to request from API
PRODUCT_FIELDS = (
    "code,product_name,brands,categories_tags,nutrition_grades,nutriments,"
    "ingredients_text,labels_tags,packaging,packagings,packaging_tags,"
    "ecoscore_grade,ecoscore_data,nova_group"
)


def get_product_by_barcode(barcode: str) -> Optional[dict]:
    """
    Fetch product details by barcode.

    Args:
        barcode: Product barcode (EAN/UPC)

    Returns:
        Product info dict or None if not found
    """
    url = f"{OFF_API_BASE}/product/{barcode}.json"
    params = {"fields": PRODUCT_FIELDS}

    data = _make_request(url, params)
    if not data or data.get("status") != 1:
        logger.debug(f"Product not found for barcode: {barcode}")
        return None

    return _normalize_product(data.get("product", {}))


def search_products(
    query: str,
    category: str = None,
    page_size: int = 5,
) -> list[dict]:
    """
    Search for products by text query.

    Args:
        query: Search text (product name, brand, etc.)
        category: Optional category filter
        page_size: Number of results to return (max 100)

    Returns:
        List of normalized product dicts
    """
    # Use the search.pl endpoint for full-text search (v2 doesn't support it well)
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": min(page_size, 100),
        "fields": PRODUCT_FIELDS,
    }

    if category:
        params["tagtype_0"] = "categories"
        params["tag_contains_0"] = "contains"
        params["tag_0"] = category

    data = _make_request(OFF_SEARCH_BASE, params)
    if not data:
        return []

    products = data.get("products", [])
    return [_normalize_product(p) for p in products if p]


def search_by_category(
    category: str,
    nutrition_grade: str = None,
    page_size: int = 10,
) -> list[dict]:
    """
    Search products by category tag.

    Args:
        category: Category tag (e.g., "en:organic-milks", "en:miso")
        nutrition_grade: Optional nutrition grade filter (a, b, c, d, e)
        page_size: Number of results

    Returns:
        List of normalized product dicts
    """
    url = f"{OFF_API_BASE}/search"
    params = {
        "categories_tags": category,
        "fields": PRODUCT_FIELDS,
        "page_size": min(page_size, 100),
        "sort_by": "popularity_key",
    }

    if nutrition_grade:
        params["nutrition_grades_tags"] = nutrition_grade

    data = _make_request(url, params)
    if not data:
        return []

    products = data.get("products", [])
    return [_normalize_product(p) for p in products if p]


def _parse_packaging(product: dict) -> dict:
    """
    Parse detailed packaging information from Open Food Facts product.

    The packagings field is an array of components, each with:
    - shape: general form (bottle, box, bag, etc.)
    - material: component material (plastic, glass, cardboard, etc.)
    - recycling: status (recycle, discard, reuse)
    - number: quantity of units

    Args:
        product: Raw product dict from API

    Returns:
        Parsed packaging dict with summary and components
    """
    # Get the structured packagings array (preferred)
    packagings = product.get("packagings", []) or []

    # Parse packaging components
    components = []
    materials = set()
    recyclable_count = 0
    total_components = 0

    for pkg in packagings:
        if not isinstance(pkg, dict):
            continue

        total_components += 1
        component = {}

        # Parse shape
        shape = pkg.get("shape")
        if shape:
            # Clean up format (e.g., "en:bottle" -> "bottle")
            if isinstance(shape, str) and ":" in shape:
                shape = shape.split(":")[-1]
            component["shape"] = shape.replace("-", " ")

        # Parse material
        material = pkg.get("material")
        if material:
            if isinstance(material, str) and ":" in material:
                material = material.split(":")[-1]
            material = material.replace("-", " ")
            component["material"] = material
            materials.add(material.lower())

        # Parse recycling status
        recycling = pkg.get("recycling")
        if recycling:
            if isinstance(recycling, str) and ":" in recycling:
                recycling = recycling.split(":")[-1]
            component["recycling"] = recycling.replace("-", " ")
            if "recycle" in recycling.lower() or "reuse" in recycling.lower():
                recyclable_count += 1

        # Parse quantity
        number = pkg.get("number_of_units") or pkg.get("number")
        if number:
            component["quantity"] = number

        if component:
            components.append(component)

    # Fall back to simple packaging text if no structured data
    packaging_text = product.get("packaging", "")
    packaging_tags = product.get("packaging_tags", []) or []

    # Determine eco-friendliness based on materials
    eco_friendly_materials = {"glass", "cardboard", "paper", "metal", "aluminum"}
    less_eco_materials = {"plastic", "polystyrene", "styrofoam"}

    has_eco_friendly = bool(materials & eco_friendly_materials)
    has_less_eco = bool(materials & less_eco_materials)

    if materials:
        if has_eco_friendly and not has_less_eco:
            packaging_rating = "good"
        elif has_less_eco and not has_eco_friendly:
            packaging_rating = "poor"
        else:
            packaging_rating = "mixed"
    else:
        packaging_rating = "unknown"

    return {
        "text": packaging_text,
        "components": components,
        "materials": list(materials),
        "recyclable_ratio": recyclable_count / total_components if total_components > 0 else None,
        "packaging_rating": packaging_rating,
        "tags": [t.split(":")[-1].replace("-", " ") if ":" in t else t for t in packaging_tags[:5]],
    }


def _normalize_product(product: dict) -> dict:
    """
    Normalize Open Food Facts product data to a consistent format.

    Args:
        product: Raw product dict from API

    Returns:
        Normalized product dict
    """
    nutriments = product.get("nutriments", {})

    # Extract key nutritional info
    nutrition = {}
    if nutriments:
        nutrition = {
            "energy_kcal_100g": nutriments.get("energy-kcal_100g"),
            "fat_100g": nutriments.get("fat_100g"),
            "saturated_fat_100g": nutriments.get("saturated-fat_100g"),
            "carbohydrates_100g": nutriments.get("carbohydrates_100g"),
            "sugars_100g": nutriments.get("sugars_100g"),
            "fiber_100g": nutriments.get("fiber_100g"),
            "proteins_100g": nutriments.get("proteins_100g"),
            "salt_100g": nutriments.get("salt_100g"),
            "sodium_100g": nutriments.get("sodium_100g"),
        }
        # Remove None values
        nutrition = {k: v for k, v in nutrition.items() if v is not None}

    # Parse labels for certifications
    labels = product.get("labels_tags", []) or []
    certifications = []
    for label in labels:
        # Clean up label format (e.g., "en:organic" -> "Organic")
        if label.startswith("en:"):
            cert = label[3:].replace("-", " ").title()
            certifications.append(cert)

    # Parse categories
    categories = product.get("categories_tags", []) or []
    clean_categories = []
    for cat in categories[:5]:  # Limit to first 5
        if cat.startswith("en:"):
            clean_categories.append(cat[3:].replace("-", " "))

    # Parse detailed packaging info
    packaging_info = _parse_packaging(product)

    # Extract ecoscore details if available
    ecoscore_data = product.get("ecoscore_data", {}) or {}
    ecoscore_details = None
    if ecoscore_data:
        ecoscore_details = {
            "score": ecoscore_data.get("score"),
            "grade": ecoscore_data.get("grade"),
            "packaging_score": ecoscore_data.get("adjustments", {}).get("packaging", {}).get("score"),
        }

    return {
        "barcode": product.get("code"),
        "product_name": product.get("product_name", "Unknown"),
        "brand": product.get("brands", "Unknown"),
        "categories": clean_categories,
        "nutrition_grade": product.get("nutrition_grades"),  # a, b, c, d, e
        "nova_group": product.get("nova_group"),  # 1-4 (food processing level)
        "ecoscore": product.get("ecoscore_grade"),  # a, b, c, d, e
        "ecoscore_details": ecoscore_details,
        "packaging": packaging_info.get("text", ""),
        "packaging_details": packaging_info,
        "certifications": certifications,
        "nutrition": nutrition,
        "source": "open_food_facts",
    }


def get_product_alternatives(
    product_name: str,
    category: str = None,
    prefer_better_nutrition: bool = True,
) -> dict:
    """
    Find alternative products, organized by quality tier.

    Args:
        product_name: Name of product to find alternatives for
        category: Optional category to search within
        prefer_better_nutrition: If True, prioritize nutrition grade

    Returns:
        Dict with 'cheaper', 'balanced', 'conscious' alternatives
    """
    # Search for similar products
    products = search_products(product_name, category=category, page_size=20)

    if not products:
        logger.info(f"No alternatives found for: {product_name}")
        return {}

    # Sort by nutrition grade if available
    def grade_score(grade):
        if not grade:
            return 5
        return {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}.get(grade.lower(), 5)

    if prefer_better_nutrition:
        products.sort(key=lambda p: grade_score(p.get("nutrition_grade")))

    # Organize into tiers based on available data
    alternatives = {}

    # Find products with different characteristics
    for product in products:
        nutrition_grade = product.get("nutrition_grade")
        ecoscore = product.get("ecoscore")
        certifications = product.get("certifications", [])

        # Conscious: organic, good ecoscore, or good nutrition
        if "conscious" not in alternatives:
            is_organic = any("organic" in c.lower() for c in certifications)
            has_good_eco = ecoscore in ("a", "b")
            has_good_nutrition = nutrition_grade in ("a", "b")
            if is_organic or has_good_eco or has_good_nutrition:
                alternatives["conscious"] = product
                continue

        # Balanced: decent nutrition grade
        if "balanced" not in alternatives:
            if nutrition_grade in ("a", "b", "c"):
                alternatives["balanced"] = product
                continue

        # Cheaper: any remaining product (typically more processed)
        if "cheaper" not in alternatives:
            alternatives["cheaper"] = product

        if len(alternatives) >= 3:
            break

    return alternatives


# Category mapping from our internal categories to OFF category tags
CATEGORY_TO_OFF_TAG = {
    "milk": "en:milks",
    "yogurt": "en:yogurts",
    "cheese": "en:cheeses",
    "eggs": "en:eggs",
    "butter_ghee": "en:butters",
    "ice_cream": "en:ice-creams",
    "bread": "en:breads",
    "grains": "en:cereals-and-potatoes",
    "oils_olive": "en:olive-oils",
    "oils_coconut": "en:coconut-oils",
    "vinegar": "en:vinegars",
    "spices": "en:spices",
    "chocolate": "en:chocolates",
    "tea": "en:teas",
    "fermented": "en:fermented-foods",
    "miso_paste": "en:misos",
    "hummus_dips": "en:hummus",
    "chips": "en:crisps",
    "cookies_crackers": "en:biscuits-and-cakes",
    "nuts_almonds": "en:almonds",
    "nuts_cashews": "en:cashew-nuts",
    "nuts_peanuts": "en:peanuts",
    "nuts_other": "en:nuts",
    "canned_coconut": "en:coconut-milks",
    # Japanese/Asian ingredients for miso soup
    "tofu": "en:tofu",
    "seaweed": "en:seaweeds",
    "dashi": "en:dashi",
    # Produce categories
    "produce_onions": "en:onions",
    "produce_greens": "en:leaf-vegetables",
    "produce_tomatoes": "en:tomatoes",
    "produce_peppers": "en:peppers",
    "produce_mushrooms": "en:mushrooms",
    "produce_aromatics": "en:herbs",
}


def get_off_alternatives_for_category(category: str) -> Optional[dict]:
    """
    Get product alternatives from Open Food Facts for a category.

    This is the main fallback function used when local alternatives are missing.

    Args:
        category: Internal category name (e.g., "milk", "fermented")

    Returns:
        Dict with cheaper/balanced/conscious alternatives, or None if not found
    """
    off_tag = CATEGORY_TO_OFF_TAG.get(category)
    if not off_tag:
        logger.debug(f"No OFF category mapping for: {category}")
        return None

    # Search by category, get products with various nutrition grades
    products = search_by_category(off_tag, page_size=20)

    if not products:
        # Fallback to text search with category name
        search_term = category.replace("_", " ")
        products = search_products(search_term, page_size=20)

    if not products:
        return None

    return _organize_into_tiers(products)


def _organize_into_tiers(products: list[dict]) -> dict:
    """
    Organize products into cheaper/balanced/conscious tiers.

    Considers:
    - Certifications (organic, fair trade, etc.)
    - Ecoscore (environmental impact A-E)
    - NOVA group (food processing level 1-4)
    - Packaging (materials, recyclability)
    - Nutrition grade (Nutri-Score A-E)

    Args:
        products: List of normalized products

    Returns:
        Dict with tier keys and product values
    """
    alternatives = {}

    for product in products:
        nutrition_grade = product.get("nutrition_grade")
        ecoscore = product.get("ecoscore")
        certifications = product.get("certifications", [])
        nova_group = product.get("nova_group")
        packaging_details = product.get("packaging_details", {})
        packaging_rating = packaging_details.get("packaging_rating", "unknown")

        # Conscious tier: organic, good ecoscore, minimally processed, eco-friendly packaging
        if "conscious" not in alternatives:
            is_organic = any("organic" in c.lower() for c in certifications)
            has_good_eco = ecoscore in ("a", "b")
            is_minimally_processed = nova_group in (1, 2)
            has_good_packaging = packaging_rating == "good"
            if is_organic or has_good_eco or is_minimally_processed or has_good_packaging:
                alternatives["conscious"] = _format_as_alternative(product, "conscious")
                continue

        # Balanced tier: decent nutrition, moderate processing
        if "balanced" not in alternatives:
            if nutrition_grade in ("a", "b", "c") or nova_group in (1, 2, 3):
                alternatives["balanced"] = _format_as_alternative(product, "balanced")
                continue

        # Cheaper tier: remaining products
        if "cheaper" not in alternatives:
            alternatives["cheaper"] = _format_as_alternative(product, "cheaper")

        if len(alternatives) >= 3:
            break

    return alternatives if alternatives else None


def _format_as_alternative(product: dict, tier: str) -> dict:
    """
    Format a product as an alternative in the expected structure.

    Args:
        product: Normalized product dict
        tier: Tier name (cheaper, balanced, conscious)

    Returns:
        Alternative dict matching local data structure
    """
    # Build why_this_tier based on product attributes
    reasons = []
    nutrition_grade = product.get("nutrition_grade")
    ecoscore = product.get("ecoscore")
    nova_group = product.get("nova_group")
    certifications = product.get("certifications", [])
    packaging_details = product.get("packaging_details", {})
    packaging_rating = packaging_details.get("packaging_rating", "unknown")

    if tier == "conscious":
        if any("organic" in c.lower() for c in certifications):
            reasons.append("Organic certified")
        if ecoscore in ("a", "b"):
            reasons.append(f"Ecoscore {ecoscore.upper()}")
        if nova_group in (1, 2):
            reasons.append("Minimally processed")
        if packaging_rating == "good":
            reasons.append("Eco-friendly packaging")
    elif tier == "balanced":
        if nutrition_grade:
            reasons.append(f"Nutrition grade {nutrition_grade.upper()}")
        if nova_group:
            reasons.append(f"NOVA group {nova_group}")
    else:  # cheaper
        reasons.append("Budget-friendly option")
        if nutrition_grade:
            reasons.append(f"Nutrition grade {nutrition_grade.upper()}")

    why_this_tier = ". ".join(reasons) if reasons else f"Available {tier} option"

    # Build trade-offs
    trade_offs = []
    if nova_group and nova_group >= 3:
        trade_offs.append(f"NOVA {nova_group} (more processed)")
    if nutrition_grade and nutrition_grade in ("d", "e"):
        trade_offs.append(f"Nutrition grade {nutrition_grade.upper()}")
    if ecoscore and ecoscore in ("d", "e"):
        trade_offs.append(f"Ecoscore {ecoscore.upper()}")
    if packaging_rating == "poor":
        materials = packaging_details.get("materials", [])
        if materials:
            trade_offs.append(f"Packaging: {', '.join(materials)}")
        else:
            trade_offs.append("Non-eco-friendly packaging")

    # Build packaging summary
    packaging_text = product.get("packaging", "")
    if not packaging_text and packaging_details.get("materials"):
        packaging_text = ", ".join(packaging_details.get("materials", []))

    return {
        "brand": product.get("brand", "Unknown"),
        "product_name": product.get("product_name", "Unknown"),
        "est_price": None,  # OFF doesn't have price data
        "packaging": packaging_text,
        "packaging_details": packaging_details,
        "why_this_tier": why_this_tier,
        "certifications": certifications,
        "trade_offs": ". ".join(trade_offs) if trade_offs else "",
        "source_url": f"https://world.openfoodfacts.org/product/{product.get('barcode', '')}",
        "nutrition": product.get("nutrition", {}),
        "nutrition_grade": nutrition_grade,
        "ecoscore": ecoscore,
        "ecoscore_details": product.get("ecoscore_details"),
        "nova_group": nova_group,
        "source": "open_food_facts",
    }
