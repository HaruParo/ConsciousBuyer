"""
Test/Demo for Store Split Logic

Shows how the 1-item rule and dynamic classification work.
"""

import sys
import importlib.util

# Add orchestrator directory to sys.path for absolute imports
orchestrator_path = '/Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/src/orchestrator'
if orchestrator_path not in sys.path:
    sys.path.insert(0, orchestrator_path)

# Direct module loading to bypass package __init__ issues
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load modules directly
base_path = '/Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/src/orchestrator'
ingredient_classifier = load_module('ingredient_classifier', f'{base_path}/ingredient_classifier.py')
store_split = load_module('store_split', f'{base_path}/store_split.py')

# Import functions from loaded modules
split_ingredients_by_store = store_split.split_ingredients_by_store
UserPreferences = store_split.UserPreferences
format_store_split_for_ui = store_split.format_store_split_for_ui
classify_ingredient_store_type = ingredient_classifier.classify_ingredient_store_type


def test_1_item_rule():
    """Test: 1 specialty item should merge to primary store."""
    print("\n" + "="*60)
    print("TEST 1: 1-ITEM RULE")
    print("="*60)

    # Scenario: Pasta carbonara + 1 spice (garam masala)
    ingredients = ["pasta", "bacon", "eggs", "parmesan", "garam_masala"]

    # Mock candidates (simplified)
    candidates = {ing: [{"id": f"{ing}_001"}] for ing in ingredients}

    # Split stores
    result = split_ingredients_by_store(ingredients, candidates)

    print("\n📋 Ingredients:")
    for ing in ingredients:
        classification = classify_ingredient_store_type(ing)
        print(f"  - {ing}: {classification}")

    print(f"\n🏪 Result: {result.total_stores_needed} store(s)")
    for store in result.stores:
        print(f"  {store.store} ({store.store_type}): {store.count} items")
        for ing in store.ingredients:
            print(f"    - {ing}")

    print(f"\n⚖️ 1-item rule applied: {result.applied_1_item_rule}")

    print("\n💬 Reasoning:")
    for reason in result.reasoning:
        print(f"  {reason}")

    # Assertions
    assert result.total_stores_needed == 1, "Should use 1 store (1-item rule)"
    assert result.applied_1_item_rule == True, "Should apply 1-item rule"
    assert "garam_masala" in result.stores[0].ingredients, "Specialty item should merge to primary"

    print("\n✅ TEST PASSED")


def test_multiple_specialty_items():
    """Test: 2+ specialty items justifies splitting stores."""
    print("\n" + "="*60)
    print("TEST 2: MULTIPLE SPECIALTY ITEMS (Chicken Biryani)")
    print("="*60)

    # Scenario: Chicken biryani with multiple spices
    ingredients = [
        # Fresh items (primary)
        "chicken", "onions", "tomatoes", "yogurt", "cilantro",
        # Specialty spices
        "turmeric", "cumin", "coriander", "garam_masala", "basmati_rice", "ghee"
    ]

    # Mock candidates
    candidates = {ing: [{"id": f"{ing}_001"}] for ing in ingredients}

    # Split stores
    result = split_ingredients_by_store(ingredients, candidates)

    print("\n📋 Ingredients:")
    for ing in ingredients:
        classification = classify_ingredient_store_type(ing)
        print(f"  - {ing}: {classification}")

    print(f"\n🏪 Result: {result.total_stores_needed} store(s)")
    for store in result.stores:
        marker = "⭐ PRIMARY" if store.is_primary else ""
        print(f"  {store.store} ({store.store_type}): {store.count} items {marker}")
        for ing in store.ingredients:
            print(f"    - {ing}")

    print(f"\n⚖️ 1-item rule applied: {result.applied_1_item_rule}")

    print("\n💬 Reasoning:")
    for reason in result.reasoning[-5:]:  # Last 5 lines
        print(f"  {reason}")

    # Assertions
    assert result.total_stores_needed == 2, "Should use 2 stores (multiple specialty items)"
    assert result.applied_1_item_rule == False, "Should NOT apply 1-item rule"

    print("\n✅ TEST PASSED")


def test_urgency_affects_store_selection():
    """Test: Urgency changes which specialty store is selected."""
    print("\n" + "="*60)
    print("TEST 3: URGENCY AFFECTS STORE SELECTION")
    print("="*60)

    ingredients = ["chicken", "turmeric", "cumin", "ghee"]
    candidates = {ing: [{"id": f"{ing}_001"}] for ing in ingredients}

    # Scenario A: Planning ahead (1-2 weeks OK)
    print("\n📅 Scenario A: Planning Ahead")
    result_planning = split_ingredients_by_store(
        ingredients,
        candidates,
        UserPreferences(urgency="planning")
    )

    specialty_store_planning = [s for s in result_planning.stores if s.store_type == "specialty"][0]
    print(f"  Specialty store: {specialty_store_planning.store}")

    # Scenario B: Urgent (need in 1-2 days)
    print("\n⚡ Scenario B: Urgent")
    result_urgent = split_ingredients_by_store(
        ingredients,
        candidates,
        UserPreferences(urgency="urgent")
    )

    specialty_store_urgent = [s for s in result_urgent.stores if s.store_type == "specialty"][0]
    print(f"  Specialty store: {specialty_store_urgent.store}")

    # Assertions
    assert specialty_store_planning.store == "Pure Indian Foods", "Planning → Pure Indian Foods"
    assert specialty_store_urgent.store == "Kesar Grocery", "Urgent → Kesar Grocery"

    print("\n✅ TEST PASSED")


def test_ui_format():
    """Test: Format for React UI."""
    print("\n" + "="*60)
    print("TEST 4: UI FORMAT")
    print("="*60)

    ingredients = ["chicken", "spinach", "turmeric", "cumin", "ghee"]
    candidates = {ing: [{"id": f"{ing}_001"}] for ing in ingredients}

    result = split_ingredients_by_store(ingredients, candidates)
    ui_format = format_store_split_for_ui(result)

    print("\n📦 UI Format:")
    print(f"  Primary Store: {ui_format['primary_store']['store']} ({ui_format['primary_store']['count']} items)")
    print(f"  Specialty Store: {ui_format['specialty_store']['store']} ({ui_format['specialty_store']['count']} items)")
    print(f"  Unavailable: {ui_format['unavailable']}")

    print("\n✅ TEST PASSED")


if __name__ == "__main__":
    test_1_item_rule()
    test_multiple_specialty_items()
    test_urgency_affects_store_selection()
    test_ui_format()

    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED")
    print("="*60)
