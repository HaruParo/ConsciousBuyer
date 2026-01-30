"""
Store Split Logic - Multi-Store Cart System

Implements the 6-factor decision logic from MULTI_STORE_CART_SYSTEM.md:
1. Transparency & Ethics
2. Delivery Timing (urgency)
3. Fresh vs Shelf-Stable (hard constraint)
4. Product Quality & Sourcing
5. Budget & Value
6. Efficiency Threshold (1-item rule)

Key Rule: Don't add a specialty store for just 1 item - merge to primary for efficiency.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

# Support both package import and standalone import
try:
    from .ingredient_classifier import classify_ingredient_store_type
except ImportError:
    from ingredient_classifier import classify_ingredient_store_type


@dataclass
class StoreGroup:
    """A group of ingredients assigned to a specific store."""
    store: str  # "FreshDirect", "Pure Indian Foods", etc.
    store_type: str  # "primary", "specialty"
    ingredients: List[str]
    count: int
    is_primary: bool  # Primary = store with MOST items


@dataclass
class StoreSplit:
    """Result of store splitting algorithm."""
    stores: List[StoreGroup]
    unavailable: List[str]
    total_stores_needed: int
    applied_1_item_rule: bool  # Whether 1-item rule was applied
    reasoning: List[str]  # Human-readable decision reasoning


@dataclass
class UserPreferences:
    """User preferences for store selection."""
    urgency: str = "planning"  # "planning" (1-2 weeks OK) or "urgent" (need in 1-2 days)
    transparency_preference: str = "high"  # "high", "medium", "low"
    budget_conscious: bool = False
    location: str = "Edison, NJ"
    avoided_stores: List[str] = None

    def __post_init__(self):
        if self.avoided_stores is None:
            self.avoided_stores = []


def split_ingredients_by_store(
    ingredients: List[str],
    candidates_by_ingredient: Dict[str, List[dict]],
    user_prefs: Optional[UserPreferences] = None
) -> StoreSplit:
    """
    Split ingredients across stores based on multi-factor decision logic.

    Implements:
    - Fresh/shelf-stable constraint (fresh → primary only)
    - 1-item rule (don't add specialty store for just 1 item)
    - Urgency (planning → Pure Indian Foods, urgent → Patel Brothers)
    - Primary store = store with MOST items

    Args:
        ingredients: List of ingredient names
        candidates_by_ingredient: Product candidates per ingredient
        user_prefs: User preferences (urgency, transparency, etc.)

    Returns:
        StoreSplit with store assignments and reasoning

    Example:
        Input: ["chicken", "spinach", "turmeric", "cumin", "ghee", "onions"]

        Output:
            StoreGroup(store="FreshDirect", ingredients=["chicken", "spinach", "onions"], count=3)
            StoreGroup(store="Pure Indian Foods", ingredients=["turmeric", "cumin", "ghee"], count=3)
    """
    if user_prefs is None:
        user_prefs = UserPreferences()

    reasoning = []
    unavailable = []

    # Step 1: Classify each ingredient
    classified = {}
    for ing_name in ingredients:
        # Check if we have products for this ingredient
        if ing_name not in candidates_by_ingredient or not candidates_by_ingredient[ing_name]:
            unavailable.append(ing_name)
            reasoning.append(f"❌ {ing_name}: Not available in inventory")
            continue

        # Classify ingredient store type
        store_type = classify_ingredient_store_type(ing_name)
        classified[ing_name] = store_type

        reasoning.append(f"✓ {ing_name}: {store_type}")

    # Step 2: Group ingredients by store type
    primary_items = [ing for ing, stype in classified.items() if stype == "primary"]
    specialty_items = [ing for ing, stype in classified.items() if stype == "specialty"]
    both_items = [ing for ing, stype in classified.items() if stype == "both"]

    reasoning.append(f"\n📊 Classification:")
    reasoning.append(f"  - Primary only (fresh): {len(primary_items)} items")
    reasoning.append(f"  - Specialty: {len(specialty_items)} items")
    reasoning.append(f"  - Both: {len(both_items)} items")

    # Step 3: Apply the 1-ITEM RULE
    # Don't add specialty store for just 1 specialty item
    applied_1_item_rule = False

    if len(specialty_items) == 0:
        # No specialty items - everything goes to primary
        reasoning.append(f"\n✅ No specialty items → 1 store (primary)")
        stores = [
            StoreGroup(
                store=_select_primary_store(user_prefs),
                store_type="primary",
                ingredients=primary_items + both_items,
                count=len(primary_items + both_items),
                is_primary=True
            )
        ]

    elif len(specialty_items) == 1:
        # THE 1-ITEM RULE: Merge to primary for efficiency
        reasoning.append(f"\n⚠️  1-ITEM RULE APPLIED")
        reasoning.append(f"  - Only 1 specialty item: {specialty_items[0]}")
        reasoning.append(f"  - Not worth adding specialty store for 1 item")
        reasoning.append(f"  - Merging to primary store for efficiency")

        applied_1_item_rule = True

        stores = [
            StoreGroup(
                store=_select_primary_store(user_prefs),
                store_type="primary",
                ingredients=primary_items + both_items + specialty_items,
                count=len(primary_items + both_items + specialty_items),
                is_primary=True
            )
        ]

    else:
        # 2+ specialty items - worth splitting
        reasoning.append(f"\n✅ {len(specialty_items)} specialty items → 2 stores justified")

        # Assign "both" items to the larger group
        if len(specialty_items) >= len(primary_items):
            # Specialty store has more items - assign "both" to specialty
            specialty_group = specialty_items + both_items
            primary_group = primary_items
        else:
            # Primary store has more items - assign "both" to primary
            primary_group = primary_items + both_items
            specialty_group = specialty_items

        # Select stores based on urgency
        primary_store_name = _select_primary_store(user_prefs)
        specialty_store_name = _select_specialty_store(user_prefs)

        reasoning.append(f"  - Primary store: {primary_store_name}")
        reasoning.append(f"  - Specialty store: {specialty_store_name}")

        # Determine which is primary (most items)
        primary_is_larger = len(primary_group) >= len(specialty_group)

        stores = [
            StoreGroup(
                store=primary_store_name,
                store_type="primary",
                ingredients=primary_group,
                count=len(primary_group),
                is_primary=primary_is_larger
            ),
            StoreGroup(
                store=specialty_store_name,
                store_type="specialty",
                ingredients=specialty_group,
                count=len(specialty_group),
                is_primary=not primary_is_larger
            )
        ]

        # Sort by count (descending) to put primary first
        stores.sort(key=lambda s: s.count, reverse=True)
        stores[0].is_primary = True  # Ensure first store is marked primary

        reasoning.append(f"\n🎯 Primary store (most items): {stores[0].store} ({stores[0].count} items)")

    return StoreSplit(
        stores=stores,
        unavailable=unavailable,
        total_stores_needed=len(stores),
        applied_1_item_rule=applied_1_item_rule,
        reasoning=reasoning
    )


def _select_primary_store(user_prefs: UserPreferences) -> str:
    """
    Select primary store based on user preferences.

    Primary stores: FreshDirect, Whole Foods, ShopRite
    """
    # For MVP, default to FreshDirect
    # TODO: Add user location-based selection
    return "FreshDirect"


def _select_specialty_store(user_prefs: UserPreferences) -> str:
    """
    Select specialty store based on urgency and preferences.

    Urgency modes:
    - Planning (1-2 weeks): Pure Indian Foods (high transparency, slow shipping)
    - Urgent (1-2 days): Kesar Grocery (fast delivery, faster than Pure Indian Foods)
    """
    if user_prefs.urgency == "urgent":
        return "Kesar Grocery"  # Fast delivery
    else:
        return "Pure Indian Foods"  # High transparency, worth the wait


def format_store_split_for_ui(store_split: StoreSplit) -> dict:
    """
    Format StoreSplit for React UI consumption.

    Returns format matching the ingredient confirmation UI:
    {
        "primary_store": {"store": "FreshDirect", "count": 5, "ingredients": [...]},
        "specialty_store": {"store": "Pure Indian Foods", "count": 5, "ingredients": [...]},
        "unavailable": [],
        "reasoning": [...]
    }
    """
    result = {
        "total_stores_needed": store_split.total_stores_needed,
        "applied_1_item_rule": store_split.applied_1_item_rule,
        "unavailable": store_split.unavailable,
        "reasoning": store_split.reasoning,
    }

    # Find primary and specialty stores
    for store_group in store_split.stores:
        if store_group.store_type == "primary":
            result["primary_store"] = {
                "store": store_group.store,
                "count": store_group.count,
                "ingredients": store_group.ingredients,
                "is_primary": store_group.is_primary
            }
        elif store_group.store_type == "specialty":
            result["specialty_store"] = {
                "store": store_group.store,
                "count": store_group.count,
                "ingredients": store_group.ingredients,
                "is_primary": store_group.is_primary
            }

    # Ensure both keys exist even if empty
    if "primary_store" not in result:
        result["primary_store"] = {"store": None, "count": 0, "ingredients": []}
    if "specialty_store" not in result:
        result["specialty_store"] = {"store": None, "count": 0, "ingredients": []}

    return result


# =============================================================================
# COMPATIBILITY WRAPPER for old API
# =============================================================================

def decide_optimal_store_split(ingredients, inventory, user_location="Edison, NJ", anthropic_client=None):
    """
    Compatibility wrapper for old API that used LLM-based store split.
    Now uses deterministic classification instead.

    Args:
        ingredients: List of ingredient dicts with 'name', 'quantity', etc.
        inventory: Can be either:
            - Dict[str, List[dict]]: candidates_by_ingredient from orchestrator
            - List[dict]: SIMULATED_INVENTORY (legacy, not used)
        user_location: User location
        anthropic_client: Claude client (not used in new system)

    Returns:
        Dict with 'available_stores', 'unavailable_items', and 'summary' keys
    """
    # Extract ingredient names from dict format
    ingredient_names = []
    for ing in ingredients:
        if isinstance(ing, dict):
            ingredient_names.append(ing.get('name', ''))
        else:
            ingredient_names.append(str(ing))

    # Use inventory as candidates_by_ingredient if it's a dict
    # Otherwise create empty dict (will mark all as unavailable)
    if isinstance(inventory, dict):
        candidates_by_ingredient = inventory
    else:
        candidates_by_ingredient = {name: [] for name in ingredient_names}

    # Use default user preferences
    user_prefs = UserPreferences(
        urgency="planning",
        location=user_location
    )

    # Run new classification system
    store_split = split_ingredients_by_store(
        ingredients=ingredient_names,
        candidates_by_ingredient=candidates_by_ingredient,
        user_prefs=user_prefs
    )

    # Convert to API format with available_stores array
    available_stores = []
    for store_group in store_split.stores:
        available_stores.append({
            "store": store_group.store,
            "ingredients": store_group.ingredients,
            "count": store_group.count,
            "is_primary": store_group.is_primary
        })

    unavailable_items = [
        {
            "ingredient": item,
            "quantity": "",
            "reason": "Not available in any store",
            "external_sources": []
        }
        for item in store_split.unavailable
    ]

    return {
        "available_stores": available_stores,
        "unavailable_items": unavailable_items,
        "summary": {
            "total_stores_needed": store_split.total_stores_needed
        }
    }
