##Store Classification System - Version History

Track evolution of the store classification approach.

---

## v2.0 - Dynamic Rule-Based Classification (Current)

**Date**: 2026-01-29
**Status**: ✅ Active

### Approach
Dynamic classification using pattern matching and rules. No static `store_type` fields in product data.

### Key Features
- ✨ Handles NEW ingredients without manual intervention
- ⚡ Rule-based (fast, deterministic)
- 📦 Clean product data (no metadata pollution)
- 🎯 Implements 1-item rule
- 🕐 Urgency-aware (pantry vs urgent)

### Implementation
- **File**: `src/orchestrator/ingredient_classifier.py`
- **File**: `src/orchestrator/store_split.py`
- **Pattern Lists**: FRESH_CATEGORIES, ETHNIC_SPECIALTY, COMMON_SHELF_STABLE
- **Classification**: Runtime, based on ingredient name patterns

### Example
```python
# No store_type in product data
"turmeric": [
    {"id": "tu001", "brand": "ShopRite", "price": 1.99},
]

# Classified at runtime
classify_ingredient_store_type("turmeric") → "specialty"
classify_ingredient_store_type("saffron") → "both" (NEW ingredient, works!)
```

### Pros
- ✅ Extensible (works for any new ingredient)
- ✅ Maintainable (rules in one place)
- ✅ Testable (easy to test classification logic)
- ✅ Clean separation (data vs logic)
- ✅ Can add LLM fallback

### Cons
- ⚠️ Requires maintaining pattern lists
- ⚠️ Edge cases need rule updates

### Documentation
- [STORE_CLASSIFICATION_SYSTEM.md](STORE_CLASSIFICATION_SYSTEM.md)

---

## v1.0 - Static store_type Fields (Deprecated)

**Date**: 2026-01-29 (proposed but not fully implemented)
**Status**: ❌ Archived (never deployed)

### Approach
Add `store_type` field to each product in inventory.

### Implementation (Proposed)
```python
SIMULATED_INVENTORY = {
    "turmeric": [
        {"id": "tu001", "brand": "ShopRite", "store_type": "primary"},
        {"id": "tu002", "brand": "McCormick", "store_type": "primary"},
        {"id": "tu005", "brand": "Pure Indian Foods", "store_type": "specialty"},
    ],
}
```

### Why It Was Abandoned
1. ❌ **Not extensible**: Breaks for new ingredients
   - User adds "saffron" → no store_type → system breaks

2. ❌ **Data pollution**: Mixing product attributes with routing logic

3. ❌ **Maintenance burden**: Need to manually classify 40+ ingredients × 5 products each = 200+ manual assignments

4. ❌ **No dynamic behavior**: Can't adapt to urgency, user preferences

### What We Learned
- Static metadata doesn't scale
- Need runtime decision making
- Separation of data and logic matters

### Artifacts (Archived)
- `scripts/add_store_types.py` (unused)
- `scripts/add_store_types_bulk.py` (unused)

---

## v0.0 - Simulated Inventory Only (Baseline)

**Date**: 2026-01-14 to 2026-01-28
**Status**: 📦 Baseline (still in use for product data)

### Approach
Product inventory with no store classification at all.

### Implementation
```python
SIMULATED_INVENTORY = {
    "spinach": [
        {"id": "sp001", "brand": "ShopRite", "price": 1.99, "organic": False},
        {"id": "sp002", "brand": "Earthbound Farm", "price": 5.99, "organic": True},
    ],
}
```

### Purpose
Provide product candidates for demo/hackathon. Store routing was documented but not implemented.

### Documentation
- [MULTI_STORE_CART_SYSTEM.md](MULTI_STORE_CART_SYSTEM.md) (documented the vision)

---

## Migration Path

### From v0.0 to v2.0

**Before** (v0.0):
```python
# No store classification at all
ingredients = ["turmeric", "chicken"]
# No way to know which store to use
```

**After** (v2.0):
```python
# Dynamic classification
from orchestrator.ingredient_classifier import classify_ingredient_store_type

for ing in ingredients:
    store_type = classify_ingredient_store_type(ing)
    print(f"{ing} → {store_type}")

# Output:
# turmeric → specialty
# chicken → primary
```

### No Migration Needed for v1.0
v1.0 was never deployed, so no migration needed. Moved directly from v0.0 to v2.0.

---

## Design Decisions

### Why v2.0 Over v1.0?

**Question from User**: "How will you split stores if the user adds a new ingredient?"

This question revealed the fatal flaw in v1.0 (static fields). Answer:

**v1.0 approach**: ❌ Breaks for new ingredients (requires manual intervention)

**v2.0 approach**: ✅ Works for any ingredient (pattern matching + rules)

### Key Architectural Principle

**Data should be dumb. Logic should be smart.**

- Product data = facts (price, brand, size, organic)
- Classification logic = decisions (which store type?)

Mixing them leads to:
- Brittle systems
- Hard to maintain
- Doesn't scale

---

## Future Versions

### v3.0 - LLM-Enhanced Classification (Planned)

Add LLM fallback for truly unknown ingredients:

```python
def classify_ingredient_store_type(ingredient, use_llm_fallback=True):
    # Try rules first
    if is_fresh(ingredient):
        return "primary"

    if is_ethnic_specialty(ingredient):
        return "specialty"

    # Unknown ingredient - ask Claude
    if use_llm_fallback:
        return classify_with_llm(ingredient)

    return "both"
```

**Benefits:**
- ✅ Handles ANY ingredient (even obscure ones)
- ✅ Learns from patterns (Claude knows food categories)
- ✅ Fallback only (fast path is still rule-based)

**Cost:**
- ~$0.0001 per classification (Haiku)
- Only for unknown ingredients (rare)

### v4.0 - Real Store Inventory APIs (Production)

Replace simulated inventory with real store APIs:

```python
# Tier 1: Instacart API
instacart_products = instacart_client.search("turmeric", store="FreshDirect")

# Tier 2: Direct partnerships
pure_indian_products = pure_indian_foods_api.get_catalog()

# Tier 3: Manual curated
manual_products = load_curated_catalog("Patel Brothers")
```

**Store availability becomes real-time:**
- ✅ Actual inventory levels
- ✅ Real prices
- ✅ True delivery times

---

## Lessons Learned

### 1. Ask "What breaks when X?"
User question "What if user adds new ingredient?" exposed the design flaw immediately.

### 2. Prefer Dynamic Over Static
Rules > Hardcoded data

### 3. Separation of Concerns
Product data should not contain routing logic.

### 4. Start Simple, Evolve
- v0.0: No classification
- v1.0: Static (proposed, abandoned)
- v2.0: Rule-based
- v3.0: LLM-enhanced (future)
- v4.0: Real APIs (production)

Each step adds capability without breaking previous version.

---

## References

- [MULTI_STORE_CART_SYSTEM.md](MULTI_STORE_CART_SYSTEM.md) - Original vision
- [STORE_CLASSIFICATION_SYSTEM.md](STORE_CLASSIFICATION_SYSTEM.md) - Current implementation (v2.0)
- [5-technical-architecture.md](5-technical-architecture.md) - Overall architecture

---

Last updated: 2026-01-29
Current version: v2.0
