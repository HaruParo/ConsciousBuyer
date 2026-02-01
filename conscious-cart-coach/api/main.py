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
    quantity: float
    unit: str
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

    # Generate tags
    why_pick_tags = []
    trade_off_tags = []

    # Product attributes
    if product.get("organic"):
        why_pick_tags.append("Organic")
    if product.get("local"):
        why_pick_tags.append("Local")
    if product.get("fair_trade"):
        why_pick_tags.append("Fair trade")

    # Item attributes
    attrs = item.attributes or []
    attr_lower = " ".join(attrs).lower()

    if "best value" in attr_lower or "best price" in attr_lower:
        why_pick_tags.append("Best value")
    if "farmer" in attr_lower or "co-op" in attr_lower:
        why_pick_tags.append("Farmer's co-op")
    if "human" in attr_lower or "worker" in attr_lower:
        why_pick_tags.append("Human Packed")
    if "recyclable" in attr_lower or "recycle" in attr_lower:
        why_pick_tags.append("Recyclable packaging")
    if "in season" in attr_lower or "seasonal" in attr_lower:
        why_pick_tags.append("In Season")

    # Safety notes
    safety_lower = " ".join(item.safety_notes or []).lower()
    if not any(x in safety_lower for x in ["recall", "dirty", "advisory"]):
        why_pick_tags.append("No recent recalls")

    # Trade-offs
    size = product.get("size", "").lower()
    if "plastic" in size or "clamshell" in size:
        trade_off_tags.append("Plastic packaging")

    for note in (item.safety_notes or []):
        lower = note.lower()
        if "dirty dozen" in lower:
            trade_off_tags.append("EWG Dirty Dozen")
        elif "recall match" in lower:
            trade_off_tags.append("Recall match")
        elif "category recall" in lower or "elevated" in lower:
            trade_off_tags.append("Recent recalls")

    if not product.get("local") and not product.get("fair_trade"):
        trade_off_tags.append("No supplier transparency")

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
        store="FreshDirect",
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

        # Get Anthropic client if available
        anthropic_client = orch.anthropic_client if hasattr(orch, 'anthropic_client') else None

        # Decide optimal store split using classification system with urgency inference
        store_split_result = decide_optimal_store_split(
            ingredients=ingredients,
            inventory=orch.state.candidates_by_ingredient,
            user_location=request.user_location,
            anthropic_client=anthropic_client,
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

        # Initialize orchestrator
        orch = Orchestrator(
            use_llm_extraction=False,  # We already have ingredients
            use_llm_explanations=False
        )

        # Parse store split
        store_split = request.store_split
        available_stores = store_split.get("available_stores", [])
        unavailable_items_data = store_split.get("unavailable_items", [])

        # Track which ingredients have been assigned to stores
        assigned_ingredient_names = set()
        for store_info in available_stores:
            assigned_ingredient_names.update(store_info.get("ingredients", []))

        # Find ingredients added by user that aren't in the original store split
        new_ingredients = [
            ing for ing in request.confirmed_ingredients
            if ing.get("name", "") not in assigned_ingredient_names
        ]

        # If there are new ingredients, add them to the primary store
        if new_ingredients:
            primary_store_info = None
            for store_info in available_stores:
                if store_info.get("is_primary", False):
                    primary_store_info = store_info
                    break

            # If no primary store found, use first store
            if not primary_store_info and available_stores:
                primary_store_info = available_stores[0]

            # Add new ingredients to the primary store's ingredient list
            if primary_store_info:
                for new_ing in new_ingredients:
                    primary_store_info["ingredients"].append(new_ing.get("name", ""))

        # Build carts for each store
        carts = []

        for store_info in available_stores:
            store_name = store_info.get("store", "")
            store_ingredients_names = store_info.get("ingredients", [])
            is_primary = store_info.get("is_primary", False)
            delivery_estimate = store_info.get("delivery_estimate", "1-2 days")

            # Filter ingredients for this store
            store_ingredients = [
                ing for ing in request.confirmed_ingredients
                if ing.get("name", "") in store_ingredients_names
            ]

            if not store_ingredients:
                continue

            # Confirm ingredients and get candidates
            orch.confirm_ingredients(store_ingredients)
            orch.step_candidates()

            # Enrich with safety and ethical data
            orch.step_enrich()

            # Make decisions
            bundle: DecisionBundle = orch.step_decide()

            if not bundle or not bundle.items:
                continue

            # Build product lookup
            lookup = build_product_lookup(orch.state.candidates_by_ingredient)

            # Create ingredient quantity lookup from confirmed ingredients
            ingredient_quantities = {
                ing.get("name", ""): (ing.get("quantity", 1.0), ing.get("unit", ""))
                for ing in store_ingredients
            }

            # Map to CartItem format with unique IDs per store
            cart_items = []
            total = 0.0

            # Create store prefix for unique IDs (e.g., "FreshDirect" -> "fd")
            store_prefix = ''.join([c for c in store_name.lower() if c.isalnum()])[:8]

            for idx, decision_item in enumerate(bundle.items):
                # Get quantity for this ingredient
                qty, unit = ingredient_quantities.get(decision_item.ingredient_name, (1.0, ""))
                cart_item = map_decision_to_cart_item(decision_item, lookup, idx, actual_servings, qty, unit, store_prefix, store_name)
                # Override store name to match the current store
                cart_item.store = store_name
                cart_items.append(cart_item)
                total += cart_item.price * cart_item.quantity

            carts.append(CartData(
                store=store_name,
                is_primary=is_primary,
                items=cart_items,
                total=round(total, 2),
                item_count=len(cart_items),
                delivery_estimate=delivery_estimate
            ))

        if not carts:
            raise HTTPException(
                status_code=500,
                detail="Failed to create any carts"
            )

        # Format unavailable items
        unavailable_list = [
            UnavailableItem(
                ingredient=item.get("ingredient", ""),
                quantity=item.get("quantity", ""),
                reason=item.get("reason", ""),
                external_sources=item.get("external_sources", [])
            )
            for item in unavailable_items_data
        ]

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
        # LLM extraction: disabled (no API key available)
        # LLM explanations: disabled (no API key available)
        orch = Orchestrator(
            use_llm_extraction=False,
            use_llm_explanations=False
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
            cart_item = map_decision_to_cart_item(decision_item, lookup, idx, actual_servings, qty, unit, "", "FreshDirect")
            cart_items.append(cart_item)
            total += cart_item.price * cart_item.quantity

        return CreateCartResponse(
            items=cart_items,
            total=round(total, 2),
            store="FreshDirect",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
