"""
FastAPI Backend for Conscious Cart Coach
Integrates Orchestrator with React Frontend
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestrator.orchestrator import Orchestrator
from src.contracts.models import DecisionBundle, DecisionItem
from src.orchestrator.store_split import decide_optimal_store_split
from src.agents.product_agent import SIMULATED_INVENTORY
from src.utils.quantity_converter import convert_ingredient_to_product_quantity

# NEW: V2 Architecture imports
from src.planner.engine import PlannerEngine
from src.planner.product_index import ProductIndex
from src.contracts.cart_plan import CartPlan, CartPlanDebug, PlannerDebugInfo


# =============================================================================
# Pydantic Models
# =============================================================================

class CreateCartRequest(BaseModel):
    meal_plan: str
    servings: int = 2
    confirmed_ingredients: list[dict] | None = None  # For 2-step flow
    store_split: dict | None = None  # LLM's store split decision
    user_location: str = "Edison, NJ"


class CartItemTag(BaseModel):
    whyPick: list[str]
    tradeOffs: list[str]


class CartItem(BaseModel):
    id: str
    name: str
    brand: str
    catalogueName: str
    price: float
    quantity: float  # Changed from int to float to support fractional quantities (e.g., 0.5 cups)
    size: str
    image: str
    tags: CartItemTag
    store: str
    location: str
    unitPrice: float | None = None
    unitPriceUnit: str | None = None
    ingredientName: str | None = None


class CreateCartResponse(BaseModel):
    items: list[CartItem]
    total: float
    store: str
    location: str
    servings: int


# New models for multi-store flow
class ExtractedIngredient(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
    category: str | None = None


class StoreInfo(BaseModel):
    store: str
    ingredients: list[str]
    count: int
    is_primary: bool


class UnavailableItem(BaseModel):
    ingredient: str
    quantity: str
    reason: str
    external_sources: list[dict]


class StoreSplit(BaseModel):
    available_stores: list[StoreInfo]
    unavailable_items: list[UnavailableItem]
    total_stores_needed: int


class ExtractIngredientsResponse(BaseModel):
    ingredients: list[ExtractedIngredient]
    servings: int
    store_split: StoreSplit
    primary_store: str


class CartData(BaseModel):
    store: str
    is_primary: bool
    items: list[CartItem]
    total: float
    item_count: int


class MultiCartResponse(BaseModel):
    carts: list[CartData]
    current_cart: str
    total_all_carts: float
    servings: int
    confirmed_ingredients: list[dict]
    unavailable_items: list[UnavailableItem]


# =============================================================================
# Helper Functions
# =============================================================================

def extract_servings_from_text(text: str, default: int = 2) -> int:
    """
    Extract serving size from meal plan text.
    Looks for patterns like "for 4 people", "serves 6", "4 servings", etc.
    Returns default if no serving size is found.
    """
    import re

    # Patterns to match serving sizes
    # Order matters - more specific patterns first
    patterns = [
        r'for\s+(\d+)\s+(?:people|person|ppl)',  # "for 4 people"
        r'serves?\s+(\d+)',                       # "serves 6"
        r'(\d+)\s+servings?',                     # "4 servings"
        r'(\d+)\s+portions?',                     # "6 portions"
        r'(?:meal|dinner|lunch|breakfast)\s+for\s+(\d+)',  # "meal for 4", "dinner for 6"
        r'for\s+(\d+)(?:\s|$)',                  # "for 12" (must be followed by space or end)
    ]

    text_lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                servings = int(match.group(1))
                # Reasonable bounds: 1-20 servings
                if 1 <= servings <= 20:
                    return servings
            except (ValueError, IndexError):
                continue

    return default


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(title="Conscious Cart Coach API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Figma_files dev server
        "http://localhost:3000",  # Alternative React port
        "https://*.vercel.app",   # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Helper Functions
# =============================================================================

def get_product_image(ingredient_name: str, product_title: str = "") -> str:
    """Get a product-specific image URL based on ingredient name or product title."""
    # Normalize the search text
    search_text = (ingredient_name + " " + product_title).lower()

    # Ingredient-to-image mapping with high-quality, appealing Unsplash images
    image_map = {
        "spinach": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=800&auto=format&fit=crop&q=80",
        "carrot": "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=800&auto=format&fit=crop&q=80",
        "brussels": "https://images.unsplash.com/photo-1599818101570-447ae8e93480?w=800&auto=format&fit=crop&q=80",
        "tofu": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&auto=format&fit=crop&q=80",
        "miso": "https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800&auto=format&fit=crop&q=80",
        "onion": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=800&auto=format&fit=crop&q=80",
        "scallion": "https://images.unsplash.com/photo-1603569283847-aa295f0d016a?w=800&auto=format&fit=crop&q=80",
        "green onion": "https://images.unsplash.com/photo-1603569283847-aa295f0d016a?w=800&auto=format&fit=crop&q=80",
        "mushroom": "https://images.unsplash.com/photo-1618639149721-92c6b0c69004?w=800&auto=format&fit=crop&q=80",
        "shiitake": "https://images.unsplash.com/photo-1516714435131-44d6b64dc6a2?w=800&auto=format&fit=crop&q=80",
        "pasta": "https://images.unsplash.com/photo-1551462147-37e03df97613?w=800&auto=format&fit=crop&q=80",
        "spaghetti": "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=800&auto=format&fit=crop&q=80",
        "tomato": "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=800&auto=format&fit=crop&q=80",
        "cherry tomato": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=800&auto=format&fit=crop&q=80",
        "pepper": "https://images.unsplash.com/photo-1525607551316-4a8e16d1f9ba?w=800&auto=format&fit=crop&q=80",
        "bell pepper": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=800&auto=format&fit=crop&q=80",
        "broccoli": "https://images.unsplash.com/photo-1628773822990-03d9e5692f38?w=800&auto=format&fit=crop&q=80",
        "kale": "https://images.unsplash.com/photo-1560196836-5b3dad4c71e6?w=800&auto=format&fit=crop&q=80",
        "lettuce": "https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=800&auto=format&fit=crop&q=80",
        "chicken": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=800&auto=format&fit=crop&q=80",
        "rice": "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=800&auto=format&fit=crop&q=80",
        "beans": "https://images.unsplash.com/photo-1588167863150-f79e7c58a742?w=800&auto=format&fit=crop&q=80",
        "potato": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800&auto=format&fit=crop&q=80",
        "milk": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=800&auto=format&fit=crop&q=80",
        "egg": "https://images.unsplash.com/photo-1518569656558-1f25e69d93d7?w=800&auto=format&fit=crop&q=80",
        "bread": "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=800&auto=format&fit=crop&q=80",
        "cheese": "https://images.unsplash.com/photo-1452195100486-9cc805987862?w=800&auto=format&fit=crop&q=80",
        "yogurt": "https://images.unsplash.com/photo-1571212515935-f2a93d8c2a6a?w=800&auto=format&fit=crop&q=80",
        "apple": "https://images.unsplash.com/photo-1619546813926-a78fa6372cd2?w=800&auto=format&fit=crop&q=80",
        "banana": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=800&auto=format&fit=crop&q=80",
        "avocado": "https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=800&auto=format&fit=crop&q=80",
        "cucumber": "https://images.unsplash.com/photo-1568584711271-7a6ae4f0f001?w=800&auto=format&fit=crop&q=80",
        "garlic": "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=800&auto=format&fit=crop&q=80",
        "ginger": "https://images.unsplash.com/photo-1577003833154-a7e6d12c0e79?w=800&auto=format&fit=crop&q=80",
        "cilantro": "https://images.unsplash.com/photo-1556906918-cbd1c58d72ad?w=800&auto=format&fit=crop&q=80",
        "basil": "https://images.unsplash.com/photo-1618375569909-3c8616cf7733?w=800&auto=format&fit=crop&q=80",
        "lemon": "https://images.unsplash.com/photo-1590502593747-42a996133562?w=800&auto=format&fit=crop&q=80",
        "lime": "https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=800&auto=format&fit=crop&q=80",
        "coconut": "https://images.unsplash.com/photo-1581426846984-d0a1dd9d83f6?w=800&auto=format&fit=crop&q=80",
        "flour": "https://images.unsplash.com/photo-1628518608608-71e51fb27f59?w=800&auto=format&fit=crop&q=80",
        "sugar": "https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=800&auto=format&fit=crop&q=80",
        "salt": "https://images.unsplash.com/photo-1596485284083-e1a6c7632f73?w=800&auto=format&fit=crop&q=80",
        "oil": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&auto=format&fit=crop&q=80",
    }

    # Find matching image
    for keyword, image_url in image_map.items():
        if keyword in search_text:
            return image_url

    # Default placeholder for unmatched items - fresh produce
    return "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=800&auto=format&fit=crop&q=80"


def map_decision_to_cart_item(
    item: DecisionItem,
    product_lookup: dict[str, dict],
    index: int,
    servings: int = 2,
    quantity: float = 1.0,
    ingredient_unit: str = "",
    store_prefix: str = "",
    target_store: str = ""
) -> CartItem:
    """Map Orchestrator DecisionItem to React CartItem format."""

    # Get the ethical pick product
    ethical_id = item.conscious_neighbor_id or item.selected_product_id
    product = product_lookup.get(ethical_id, {})

    # Filter by store - check if product is available at target store
    if target_store and product:
        available_stores = product.get("available_stores", ["all"])
        # If product has specific store restrictions, check if target store is allowed
        if available_stores != ["all"] and target_store not in available_stores:
            # Product not available at this store, skip it or find alternative
            # For now, we'll allow it but this should trigger a product re-selection
            print(f"Warning: {product.get('title', 'Product')} from {product.get('brand', 'Unknown')} not available at {target_store}")
            print(f"  Available stores: {available_stores}")

    # Convert ingredient quantity to product quantity using smart conversion
    size_str = product.get("size", "")
    product_unit = product.get("unit", "ea")

    # Build ingredient quantity string for converter
    ingredient_qty_str = f"{quantity} {ingredient_unit}" if ingredient_unit else f"{quantity}"

    # Use quantity converter to calculate product quantity
    try:
        product_quantity, display_qty = convert_ingredient_to_product_quantity(
            ingredient_qty_str, size_str, product_unit
        )
        base_quantity = product_quantity
    except Exception as e:
        # Fallback to original quantity if conversion fails
        print(f"Warning: Quantity conversion failed for {item.ingredient_name}: {e}")
        base_quantity = quantity

    # === VALIDATOR-SAFE TAG GENERATION ===
    # All tags must be evidence-based and fact-checkable
    why_pick_tags = []
    trade_off_tags = []

    brand_name = product.get("brand", "").lower()
    ingredient = item.ingredient_name.lower()
    title_lower = product.get("title", "").lower()
    attrs = item.attributes or []
    attr_lower = " ".join(attrs).lower()
    safety_notes = item.safety_notes or []
    safety_lower = " ".join(safety_notes).lower()
    tier = getattr(item, 'tier_symbol', '')
    unit_price = product.get("unit_price", 0)
    price = product.get("price", 0)

    # Get neighbor products for relative comparisons
    cheaper_neighbor = None
    conscious_neighbor = None
    if item.cheaper_neighbor_id and item.cheaper_neighbor_id in product_lookup:
        cheaper_neighbor = product_lookup[item.cheaper_neighbor_id]
    if item.conscious_neighbor_id and item.conscious_neighbor_id in product_lookup:
        conscious_neighbor = product_lookup[item.conscious_neighbor_id]

    # 1. ORGANIC STATUS (USDA Certified with relative comparison)
    is_organic = product.get("organic", False)
    conscious_is_organic = conscious_neighbor.get("organic", False) if conscious_neighbor else False

    if is_organic:
        why_pick_tags.append("USDA Organic")
    else:
        # Check if organic option exists (conscious neighbor)
        if conscious_is_organic:
            # There IS an organic option available, but we didn't pick it
            conscious_price = conscious_neighbor.get("price", 0)
            price_diff = conscious_price - price
            if price_diff > 2.0:
                trade_off_tags.append(f"Not organic (saves ${price_diff:.0f})")
            else:
                trade_off_tags.append("Not organic")
        elif ingredient in ["strawberries", "spinach", "kale", "apples", "grapes", "bell peppers"]:
            # No organic option available at all
            trade_off_tags.append("No organic available")

    # 2. EWG PRODUCE GUIDE (Evidence-based)
    EWG_DIRTY_DOZEN = ["strawberries", "spinach", "kale", "peaches", "pears", "nectarines",
                       "apples", "grapes", "bell peppers", "cherries", "blueberries"]
    EWG_CLEAN_FIFTEEN = ["avocados", "onions", "pineapple", "papaya", "asparagus"]

    is_dirty_dozen = any(item in ingredient for item in EWG_DIRTY_DOZEN)
    is_clean_fifteen = any(item in ingredient for item in EWG_CLEAN_FIFTEEN)

    if is_dirty_dozen and product.get("organic"):
        why_pick_tags.append("EWG Safe Choice")
    elif is_dirty_dozen and not product.get("organic"):
        trade_off_tags.append("EWG Dirty Dozen")
    elif is_clean_fifteen:
        why_pick_tags.append("EWG Clean Fifteen")

    # 3. RECALL & SAFETY (FDA Data)
    if "recall" in safety_lower or "advisory" in safety_lower:
        trade_off_tags.append("FDA Advisory")
    else:
        why_pick_tags.append("No Active Recalls")

    # 4. SOURCING (Verifiable)
    if "pure indian foods" in brand_name:
        why_pick_tags.append("Direct Import")
    elif "lancaster" in brand_name or ("farm" in brand_name and "fresh" in brand_name):
        why_pick_tags.append("Local Farm")
    elif product.get("local"):
        why_pick_tags.append("Locally Sourced")

    # 5. COST POSITIONING (Data-driven with relative comparisons)
    if tier == "💰":
        why_pick_tags.append("Best Value")
    elif tier == "⭐":
        why_pick_tags.append("Balanced Choice")
    elif unit_price > 2.0:
        trade_off_tags.append("Premium Price")

    # Relative price comparisons (show what you're trading off)
    if cheaper_neighbor:
        price_diff = price - cheaper_neighbor.get("price", 0)
        if price_diff > 2.0:
            # Significantly more expensive - explain why
            if product.get("organic") and not cheaper_neighbor.get("organic"):
                trade_off_tags.append(f"${price_diff:.0f} more for organic")
            else:
                trade_off_tags.append(f"${price_diff:.0f} more than cheapest")
        elif price_diff > 0.5:
            if product.get("organic") and not cheaper_neighbor.get("organic"):
                why_pick_tags.append("Worth organic premium")

    if conscious_neighbor:
        price_diff = conscious_neighbor.get("price", 0) - price
        if price_diff > 2.0:
            # Much cheaper than conscious option - that's a win
            why_pick_tags.append(f"Saves ${price_diff:.0f} vs organic")
        elif price_diff < -1.0:
            # We are more expensive than the "conscious" option (shouldn't happen often)
            pass

    # 6. SPECIFIC CERTIFICATIONS (Verifiable)
    if "free range" in attr_lower or "pasture" in attr_lower:
        why_pick_tags.append("Free-Range")
    if "grass fed" in attr_lower:
        why_pick_tags.append("Grass-Fed")
    if "fair trade" in attr_lower or product.get("fair_trade"):
        why_pick_tags.append("Fair Trade")

    # 7. BRAND TRUST (Store-specific)
    if "365" in brand_name or "whole foods" in brand_name:
        why_pick_tags.append("Store Brand")

    # Get product details
    brand = product.get("brand", "")
    title = product.get("title", "")
    price = product.get("price", 0)
    size_str = product.get("size", "")
    unit_price = product.get("unit_price", 0)
    unit_price_unit = product.get("unit_price_unit", "oz")

    # Get product-specific image based on ingredient name
    image = get_product_image(item.ingredient_name, title)

    # Build catalogue name - product titles already include brand, so just use title
    catalogue_name = title[:60] if title else item.ingredient_name

    # Determine actual store - BRAND-BASED ASSIGNMENT FIRST
    brand_lower = brand.lower()

    # Check brand exclusivity first (overrides everything)
    if "365" in brand_lower or "whole foods" in brand_lower:
        actual_store = "Whole Foods"
    elif "pure indian foods" in brand_lower:
        actual_store = "Pure Indian Foods"
    elif "kesar grocery" in brand_lower or "swad" in brand_lower:
        actual_store = "Kesar Grocery"
    else:
        # Fall back to available_stores from product agent
        available_stores = product.get("available_stores", ["all"])
        store_type = product.get("store_type", "primary")

        if available_stores and available_stores[0] != "all":
            first_store = available_stores[0]
            # Map "specialty" type to actual specialty store name
            if first_store == "specialty" or store_type == "specialty":
                actual_store = "Pure Indian Foods"
            else:
                # Use the actual store name from available_stores
                actual_store = first_store
        elif target_store:
            actual_store = target_store
        else:
            actual_store = "FreshDirect"

    # Generate unique ID with store prefix to avoid duplicates across stores
    unique_id = f"{store_prefix}-item-{index}" if store_prefix else f"item-{index}"

    return CartItem(
        id=unique_id,
        name=title or item.ingredient_name,
        brand=brand,
        catalogueName=catalogue_name,
        price=price,
        quantity=base_quantity,
        size=size_str,
        image=image,
        tags=CartItemTag(
            whyPick=why_pick_tags[:5],
            tradeOffs=trade_off_tags[:4]
        ),
        store=actual_store,
        location="NJ",
        unitPrice=unit_price if unit_price > 0 else None,
        unitPriceUnit=unit_price_unit if unit_price > 0 else None,
        ingredientName=item.ingredient_name
    )


def build_product_lookup(candidates_by_ingredient: dict[str, list[dict]]) -> dict[str, dict]:
    """Build a product_id -> product data lookup."""
    lookup = {}
    for ingredient, candidates in candidates_by_ingredient.items():
        for candidate in candidates:
            lookup[candidate["product_id"]] = {
                "product_id": candidate["product_id"],
                "ingredient_name": candidate.get("ingredient_name", ingredient),
                "title": candidate.get("title", ""),
                "brand": candidate.get("brand", ""),
                "size": candidate.get("size", ""),
                "price": candidate.get("price", 0),
                "unit_price": candidate.get("unit_price", 0),
                "unit_price_unit": candidate.get("unit_price_unit", "oz"),
                "organic": candidate.get("organic", False),
                "local": candidate.get("local", False),
                "fair_trade": candidate.get("fair_trade", False),
                "in_stock": candidate.get("in_stock", True),
                "available_stores": candidate.get("available_stores", ["all"]),
                "store_type": candidate.get("store_type", "primary"),
            }
    return lookup


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Conscious Cart Coach API",
        "version": "1.0.0"
    }


@app.post("/api/extract-ingredients", response_model=ExtractIngredientsResponse)
def extract_ingredients(request: CreateCartRequest):
    """
    Extract ingredients and determine optimal store split.

    This is Step 1 of the 2-step cart creation flow:
    1. Extract ingredients (this endpoint)
    2. User confirms/edits
    3. Build carts (create-cart endpoint)
    """
    try:
        # Extract servings
        actual_servings = extract_servings_from_text(request.meal_plan, default=request.servings)

        # Initialize orchestrator with LLM extraction for comprehensive ingredient parsing
        orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=False)

        # Extract ingredients
        result = orch.step_ingredients(request.meal_plan, servings=actual_servings)

        if result.status != "ok":
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract ingredients: {result.message}"
            )

        ingredients = result.facts.get("ingredients", [])

        if not ingredients:
            raise HTTPException(
                status_code=400,
                detail="No ingredients found in meal plan"
            )

        # Get product candidates to enable proper store classification
        orch.confirm_ingredients(ingredients)
        orch.step_candidates()

        # Get LLM client if available
        llm_client = orch.llm_client if hasattr(orch, 'llm_client') else None

        # Decide optimal store split using classification system with urgency inference
        store_split_result = decide_optimal_store_split(
            ingredients=ingredients,
            inventory=orch.state.candidates_by_ingredient,
            user_location=request.user_location,
            anthropic_client=llm_client,  # Note: store_split still uses old parameter name
            meal_plan_text=request.meal_plan
        )

        # Format response
        extracted_ingredients = [
            ExtractedIngredient(
                name=ing.get("name", ""),
                quantity=ing.get("qty", 1),  # IngredientAgent returns "qty", not "quantity"
                unit=ing.get("unit", ""),
                category=ing.get("canonical")  # IngredientAgent returns "canonical", not "category"
            )
            for ing in ingredients
        ]

        store_info_list = [
            StoreInfo(
                store=store.get("store", ""),
                ingredients=store.get("ingredients", []),
                count=store.get("count", 0),
                is_primary=store.get("is_primary", False)
            )
            for store in store_split_result.get("available_stores", [])
        ]

        unavailable_list = [
            UnavailableItem(
                ingredient=item.get("ingredient", ""),
                quantity=item.get("quantity", ""),
                reason=item.get("reason", ""),
                external_sources=item.get("external_sources", [])
            )
            for item in store_split_result.get("unavailable_items", [])
        ]

        store_split = StoreSplit(
            available_stores=store_info_list,
            unavailable_items=unavailable_list,
            total_stores_needed=store_split_result.get("summary", {}).get("total_stores_needed", 1)
        )

        # Determine primary store
        primary_store = "FreshDirect"
        for store in store_info_list:
            if store.is_primary:
                primary_store = store.store
                break

        return ExtractIngredientsResponse(
            ingredients=extracted_ingredients,
            servings=actual_servings,
            store_split=store_split,
            primary_store=primary_store
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] extract_ingredients: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create-multi-cart", response_model=MultiCartResponse)
def create_multi_cart(request: CreateCartRequest):
    """
    Create shopping carts for multiple stores based on store split.

    This endpoint:
    1. Uses confirmed_ingredients and store_split from the request
    2. Builds separate carts for each store based on their assigned ingredients
    3. Returns array of carts with unavailable items
    """
    try:
        if not request.confirmed_ingredients or not request.store_split:
            raise HTTPException(
                status_code=400,
                detail="confirmed_ingredients and store_split are required"
            )

        # Extract servings
        actual_servings = extract_servings_from_text(request.meal_plan, default=request.servings)

        # Initialize orchestrator - get ALL products without store filtering
        orch = Orchestrator(
            use_llm_extraction=False,  # We already have ingredients
            use_llm_explanations=False,
            target_store=None  # Allow products from all stores
        )

        # Get products for ALL confirmed ingredients at once
        orch.confirm_ingredients(request.confirmed_ingredients)
        orch.step_candidates()
        orch.step_enrich()
        bundle: DecisionBundle = orch.step_decide()

        if not bundle or not bundle.items:
            raise HTTPException(status_code=500, detail="Failed to create cart bundle")

        # Build product lookup
        lookup = build_product_lookup(orch.state.candidates_by_ingredient)

        # Create ingredient quantity lookup
        ingredient_quantities = {
            ing.get("name", ""): (ing.get("quantity", 1.0), ing.get("unit", ""))
            for ing in request.confirmed_ingredients
        }

        # Map ALL items to CartItem format
        all_cart_items = []
        for idx, decision_item in enumerate(bundle.items):
            qty, unit = ingredient_quantities.get(decision_item.ingredient_name, (1.0, ""))
            cart_item = map_decision_to_cart_item(decision_item, lookup, idx, actual_servings, qty, unit, "", None)
            all_cart_items.append(cart_item)

        # Group items by their actual store (as determined by product agent)
        from collections import defaultdict
        items_by_store = defaultdict(list)
        for item in all_cart_items:
            items_by_store[item.store].append(item)

        # EFFICIENCY CONSOLIDATION: Merge stores with <3 items into primary store
        PRIMARY_STORE = "FreshDirect"
        MIN_ITEMS_PER_STORE = 3

        consolidated_items = defaultdict(list)
        stores_to_consolidate = []

        for store_name, items in items_by_store.items():
            if store_name == PRIMARY_STORE:
                # Always keep primary store items
                consolidated_items[PRIMARY_STORE].extend(items)
            elif len(items) < MIN_ITEMS_PER_STORE:
                # <3 items: consolidate to primary for efficiency
                stores_to_consolidate.append((store_name, len(items)))
                # Change item.store to primary for these items
                for item in items:
                    item.store = PRIMARY_STORE
                consolidated_items[PRIMARY_STORE].extend(items)
            else:
                # ≥3 items: keep as separate store
                consolidated_items[store_name].extend(items)

        if stores_to_consolidate:
            print(f"[EFFICIENCY] Consolidated {len(stores_to_consolidate)} stores to {PRIMARY_STORE}:")
            for store, count in stores_to_consolidate:
                print(f"  - {store}: {count} items (< {MIN_ITEMS_PER_STORE} threshold)")

        # Build carts for each store (after consolidation)
        carts = []
        for store_name, items in consolidated_items.items():
            total = sum(item.price * item.quantity for item in items)

            carts.append(CartData(
                store=store_name,
                is_primary=(store_name == "FreshDirect"),  # Primary = most common grocery store
                items=items,
                total=round(total, 2),
                item_count=len(items),
                delivery_estimate="1-2 days" if store_name == "FreshDirect" else "3-5 days"
            ))

        if not carts:
            raise HTTPException(
                status_code=500,
                detail="Failed to create any carts"
            )

        # Check for unavailable items (ingredients with no products)
        unavailable_list = []
        confirmed_ingredient_names = {ing.get("name") for ing in request.confirmed_ingredients}
        found_ingredient_names = {item.ingredientName for item in all_cart_items if item.ingredientName}
        missing_ingredient_names = confirmed_ingredient_names - found_ingredient_names

        for missing_name in missing_ingredient_names:
            unavailable_list.append(UnavailableItem(
                ingredient=missing_name,
                quantity="",
                reason="Not available in any store",
                external_sources=[]
            ))

        # Determine current cart (primary store)
        current_cart = carts[0].store
        for cart in carts:
            if cart.is_primary:
                current_cart = cart.store
                break

        # Calculate total across all carts
        total_all_carts = sum(cart.total for cart in carts)

        return MultiCartResponse(
            carts=carts,
            current_cart=current_cart,
            total_all_carts=round(total_all_carts, 2),
            servings=actual_servings,
            confirmed_ingredients=request.confirmed_ingredients,
            unavailable_items=unavailable_list
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] create_multi_cart: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create-cart", response_model=CreateCartResponse)
def create_cart(request: CreateCartRequest):
    """
    Create a shopping cart from a meal plan description.

    This endpoint:
    1. Extracts ingredients from the meal plan
    2. Finds product candidates for each ingredient
    3. Enriches products with safety and ethical data
    4. Makes ethical-first product decisions
    5. Returns formatted cart items for the UI
    """
    try:
        # Extract servings from meal plan text if mentioned, otherwise use default
        actual_servings = extract_servings_from_text(request.meal_plan, default=request.servings)

        # Debug logging
        print(f"[DEBUG] Meal plan: '{request.meal_plan}'")
        print(f"[DEBUG] Default servings: {request.servings}")
        print(f"[DEBUG] Extracted servings: {actual_servings}")

        # Initialize orchestrator
        # LLM extraction: enabled for natural language understanding
        orch = Orchestrator(
            use_llm_extraction=True,    # Extract ingredients using LLM
            use_llm_explanations=False,  # Disabled: causes timeouts, use smart rules instead
            target_store=None  # Allow products from all stores, then split by actual store
        )

        # Step 1: Extract ingredients with extracted serving size
        result = orch.step_ingredients(request.meal_plan, servings=actual_servings)

        if result.status != "ok":
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract ingredients: {result.message}"
            )

        ingredients = result.facts.get("ingredients", [])

        if not ingredients:
            raise HTTPException(
                status_code=400,
                detail="No ingredients found in meal plan"
            )

        # Step 2: Confirm ingredients and get candidates
        orch.confirm_ingredients(ingredients)
        orch.step_candidates()

        # Step 3: Enrich with safety and ethical data
        orch.step_enrich()

        # Step 4: Make decisions
        bundle: DecisionBundle = orch.step_decide()

        if not bundle or not bundle.items:
            raise HTTPException(
                status_code=500,
                detail="Failed to create cart bundle"
            )

        # Step 5: Build product lookup
        lookup = build_product_lookup(orch.state.candidates_by_ingredient)

        # Create ingredient quantity lookup
        ingredient_quantities = {
            ing.get("name", ""): (ing.get("quantity", 1.0), ing.get("unit", ""))
            for ing in ingredients
        }

        # Step 6: Map to CartItem format
        cart_items = []
        total = 0.0

        for idx, decision_item in enumerate(bundle.items):
            # Get quantity for this ingredient
            qty, unit = ingredient_quantities.get(decision_item.ingredient_name, (1.0, ""))
            cart_item = map_decision_to_cart_item(decision_item, lookup, idx, actual_servings, qty, unit, "", None)
            cart_items.append(cart_item)
            total += cart_item.price * cart_item.quantity

        # Determine primary store (most items) for the response
        store_counts = {}
        for item in cart_items:
            store_counts[item.store] = store_counts.get(item.store, 0) + 1
        primary_store = max(store_counts, key=store_counts.get) if store_counts else "Multi-Store"

        return CreateCartResponse(
            items=cart_items,
            total=round(total, 2),
            store=primary_store,
            location="NJ",
            servings=actual_servings
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# =============================================================================
# V2 Architecture Endpoints (New Planner Engine)
# =============================================================================

class PlanRequestV2(BaseModel):
    """Request for v2 planner"""
    prompt: str
    servings: int = 2
    preferences: dict | None = None
    ingredients_override: list[str] | None = None  # Confirmed ingredients from modal
    include_trace: bool = False  # Include decision traces for scoring drawer (opt-in to avoid bloat)


@app.post("/api/plan-v2", response_model=dict)
def plan_v2(request: PlanRequestV2):
    """
    V2 Architecture: Uses new PlannerEngine (deterministic)

    This endpoint:
    1. Extracts ingredients (LLM with fallback)
    2. Runs deterministic PlannerEngine
    3. Returns CartPlan (single source of truth)

    Fixes:
    - P0: Fresh produce selected correctly
    - P1: Store assignment never overwritten
    - P2: Tradeoff tags always present
    """
    try:
        import time
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"V2 PLAN REQUEST")
        print(f"{'='*60}")
        print(f"Prompt: {request.prompt}")
        print(f"Servings: {request.servings}")

        # Step 1: Get ingredients (either from override or extraction)
        if request.ingredients_override:
            # Use confirmed ingredients from modal (trim whitespace, drop empties)
            raw_ingredients = [ing.strip() for ing in request.ingredients_override if ing.strip()]
            print(f"\n✓ Using confirmed ingredients override ({len(raw_ingredients)} items)")

            # Deduplicate synonyms (cilantro/coriander/cilantros → cilantro)
            from src.agents.ingredient_synonyms import deduplicate_ingredients
            ingredients, duplicates_removed = deduplicate_ingredients(raw_ingredients)

            if duplicates_removed:
                print(f"\n⚠️  Removed {sum(len(v) for v in duplicates_removed.values())} duplicate ingredients:")
                for kept, removed in duplicates_removed.items():
                    print(f"  Kept '{kept}', removed: {', '.join(removed)}")

            print(f"\nFinal ingredient list ({len(ingredients)} items):")
            for ing in ingredients:
                print(f"  - {ing}")
        else:
            # Extract ingredients using LLM (with fallback)
            ingredients = _simple_ingredient_extraction(request.prompt)

            if not ingredients:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract ingredients from prompt"
                )

            print(f"\nExtracted {len(ingredients)} ingredients:")
            for ing in ingredients:
                print(f"  - {ing}")

        # Step 2: Run PlannerEngine (deterministic)
        # Use source_listings.csv (has mushrooms!) instead of inventories_trusted
        product_index = ProductIndex(use_synthetic=False)
        engine = PlannerEngine(product_index=product_index)
        plan = engine.create_plan(
            prompt=request.prompt,
            ingredients=ingredients,
            servings=request.servings,
            include_trace=request.include_trace  # Pass through for scoring drawer
        )

        execution_time = (time.time() - start_time) * 1000

        print(f"\n✓ CartPlan created in {execution_time:.0f}ms")
        print(f"  - Items: {len(plan.items)}")
        print(f"  - Stores: {[s.store_name for s in plan.store_plan.stores]}")
        print(f"  - Ethical total: ${plan.totals.ethical_total}")
        print(f"  - Cheaper total: ${plan.totals.cheaper_total}")
        print(f"  - Savings: ${plan.totals.savings_potential}")

        # Return as dict (Pydantic serialization)
        return plan.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] plan_v2: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/debug", response_model=dict)
def debug_plan(request: PlanRequestV2):
    """
    Debug endpoint: Shows planner execution details

    Returns CartPlanDebug with:
    - Full CartPlan
    - Candidate lists per ingredient
    - Store assignment reasoning
    - Execution time
    """
    try:
        import time
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"DEBUG PLAN REQUEST")
        print(f"{'='*60}")

        # Extract ingredients
        ingredients = _simple_ingredient_extraction(request.prompt)

        if not ingredients:
            raise HTTPException(
                status_code=400,
                detail="Could not extract ingredients"
            )

        # Run planner with debug info collection
        # Use source_listings.csv (has mushrooms!) instead of inventories_trusted
        product_index = ProductIndex(use_synthetic=False)
        engine = PlannerEngine(product_index=product_index)
        index = engine.product_index

        debug_info = []

        # Collect candidate info for each ingredient
        from src.contracts.cart_plan import CandidateDebugInfo
        for ingredient in ingredients:
            candidates = index.retrieve(ingredient, max_candidates=10)

            # Build detailed candidate info
            candidate_debug_list = [
                CandidateDebugInfo(
                    title=c.title,
                    brand=c.brand,
                    price=c.price,
                    store=c.source_store_id,
                    form_score=c.form_score,
                    organic=c.organic,
                    unit_price=c.unit_price
                )
                for c in candidates
            ]

            winner = candidate_debug_list[0] if len(candidate_debug_list) > 0 else None
            runner_up = candidate_debug_list[1] if len(candidate_debug_list) > 1 else None

            # Get reason (from cart plan if available)
            reason_line = None
            reason_code = None
            # TODO: Extract from cart plan after it's created

            debug_info.append(PlannerDebugInfo(
                ingredient_name=ingredient,
                candidates_found=len(candidates),
                candidate_titles=[c.title for c in candidates],
                candidate_stores=[c.source_store_id for c in candidates],
                winner=winner,
                runner_up=runner_up,
                all_candidates=candidate_debug_list,
                reason_code=reason_code,
                reason_line=reason_line,
                chosen_product_id=candidates[0].product_id if candidates else "none",
                chosen_title=candidates[0].title if candidates else "not found",
                chosen_store_id=candidates[0].source_store_id if candidates else "none",
                store_assignment_reason="Primary store (most items)" if candidates else "N/A"
            ))

        # Create plan (debug always includes trace)
        plan = engine.create_plan(
            prompt=request.prompt,
            ingredients=ingredients,
            servings=request.servings,
            include_trace=True  # Debug endpoint always includes traces
        )

        execution_time = (time.time() - start_time) * 1000

        # Build debug response
        debug_response = CartPlanDebug(
            plan=plan,
            debug_info=debug_info,
            execution_time_ms=execution_time
        )

        print(f"\n✓ Debug info collected")
        print(f"  - Execution time: {execution_time:.0f}ms")
        print(f"  - Debug entries: {len(debug_info)}")

        return debug_response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] debug_plan: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _canonicalize_ingredients(ingredients: list[str], prompt: str) -> list[str]:
    """
    Canonicalize ambiguous ingredient names based on context

    Rules:
    - If prompt contains "biryani": replace "rice" with "basmati rice"
    - Only rename ambiguous ingredients, don't add new ones
    """
    prompt_lower = prompt.lower()
    canonicalized = []

    for ingredient in ingredients:
        ingredient_lower = ingredient.lower()

        # Biryani-specific canonicalization
        if "biryani" in prompt_lower:
            if ingredient_lower == "rice":
                canonicalized.append("basmati rice")
                continue

        # Default: keep original
        canonicalized.append(ingredient)

    return canonicalized


def _simple_ingredient_extraction(prompt: str) -> list[str]:
    """
    Ingredient extraction using LLM (Ollama/Llama) with template fallback

    Uses IngredientAgent with Ollama for proper extraction.
    Falls back to templates only if LLM fails.
    """
    from src.agents.ingredient_agent import IngredientAgent

    # Try LLM extraction first
    agent = IngredientAgent(use_llm=True)
    result = agent.extract(prompt, servings=None)

    if not result.is_error and result.facts.get("ingredients"):
        # Extract just the ingredient names from the structured result
        ingredients = [ing.get("name") for ing in result.facts["ingredients"] if ing.get("name")]
        print(f"  ✓ LLM extracted {len(ingredients)} ingredients")
        return _canonicalize_ingredients(ingredients, prompt)

    # Fallback to templates if LLM fails
    print(f"  ⚠️  LLM extraction failed, using template fallback")
    prompt_lower = prompt.lower()

    # Common meal patterns
    if "biryani" in prompt_lower:
        ingredients = [
            "chicken", "rice", "onions", "tomatoes", "yogurt",
            "ginger", "garlic", "ghee", "garam masala", "turmeric",
            "coriander", "cumin", "cardamom", "bay leaves", "mint", "cilantro"
        ]
    elif "pasta" in prompt_lower:
        ingredients = ["pasta", "tomatoes", "garlic", "olive oil", "basil", "parmesan"]
    elif "tacos" in prompt_lower:
        ingredients = ["ground beef", "taco shells", "lettuce", "tomatoes", "cheese", "sour cream"]
    elif "salad" in prompt_lower:
        ingredients = ["lettuce", "tomatoes", "cucumber", "carrots", "dressing"]
    else:
        # Generic extraction (look for common ingredients in prompt)
        ingredients = []
        common_ingredients = [
            "chicken", "beef", "pork", "fish", "shrimp",
            "rice", "pasta", "noodles", "bread",
            "onions", "garlic", "ginger", "tomatoes", "lettuce",
            "carrots", "broccoli", "spinach", "kale",
            "cheese", "milk", "yogurt", "eggs",
            "oil", "butter", "ghee", "salt", "pepper"
        ]

        for ingredient in common_ingredients:
            if ingredient in prompt_lower:
                ingredients.append(ingredient)

        ingredients = ingredients if ingredients else ["chicken", "rice", "onions"]  # Fallback

    # Apply canonicalization BEFORE returning
    return _canonicalize_ingredients(ingredients, prompt)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
