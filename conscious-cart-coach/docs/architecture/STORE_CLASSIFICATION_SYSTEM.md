# Store Classification System (v2.0)

**Status**: ✅ Implemented
**Date**: 2026-01-29
**Version**: Dynamic Rule-Based Classification

---

## Overview

The Store Classification System dynamically determines which store types can carry each ingredient, enabling intelligent multi-store cart splitting.

**Key Features:**
- ✨ Handles NEW ingredients without manual intervention
- ⚡ Rule-based (fast, deterministic)
- 🎯 Implements 1-item efficiency rule
- 🕐 Considers urgency (pantry restocking vs cooking soon)

---

## How It Works

### Step 1: Classify Ingredients

Each ingredient is classified into one of three store types:

| Store Type | Meaning | Examples |
|------------|---------|----------|
| **primary** | Only at primary stores (FreshDirect, Whole Foods) | Fresh spinach, chicken, yogurt |
| **specialty** | Better options at specialty stores (Pure Indian Foods) | Turmeric, ghee, garam masala |
| **both** | Available at both store types | Olive oil, pasta, salt |

**Classification Rules:**

```python
# Rule 1: Fresh/perishable → primary only
if is_fresh(ingredient):
    return "primary"  # Specialty stores can't ship fresh

# Rule 2: Ethnic specialty → specialty
if is_ethnic_specialty(ingredient):
    return "specialty"  # Better quality at specialty stores

# Rule 3: Common shelf-stable → both
if is_common_item(ingredient):
    return "both"

# Default → both
return "both"
```

**Examples:**
- `classify_ingredient_store_type("spinach")` → `"primary"` (fresh)
- `classify_ingredient_store_type("turmeric")` → `"specialty"` (ethnic spice)
- `classify_ingredient_store_type("saffron")` → `"both"` (not in predefined lists, defaults to both)
- `classify_ingredient_store_type("fresh fenugreek")` → `"primary"` (keyword "fresh")

### Step 2: Apply Store Split Logic

Once ingredients are classified, apply the multi-factor decision logic:

**THE 1-ITEM RULE** (Most Important)
```
If specialty_items == 0:
    → 1 store (primary only)

If specialty_items == 1:
    → 1 store (merge to primary for efficiency)
    ⚠️ Don't add specialty store for just 1 item!

If specialty_items >= 2:
    → 2 stores (specialty + primary)
```

**Urgency Factor:**
```
If urgency == "planning" (1-2 weeks OK):
    → Specialty Store: Pure Indian Foods (high transparency)

If urgency == "urgent" (need in 1-2 days):
    → Specialty Store: Kesar Grocery (fast delivery)
```

**Primary Store Selection:**
```
Primary store = store with MOST items

Example:
  Pure Indian Foods: 6 items ⭐ PRIMARY
  FreshDirect: 4 items
```

---

## Code Examples

### Basic Classification

```python
from orchestrator.ingredient_classifier import classify_ingredient_store_type

# Classify an ingredient
store_type = classify_ingredient_store_type("turmeric")
# Returns: "specialty"

# Works for new ingredients too!
store_type = classify_ingredient_store_type("sumac")  # Middle Eastern spice
# Returns: "specialty" (pattern matching)
```

### Store Split

```python
from orchestrator.store_split import split_ingredients_by_store, UserPreferences

# Scenario: Pasta carbonara + 1 spice
ingredients = ["pasta", "eggs", "bacon", "parmesan", "garam_masala"]
candidates = {...}  # Product candidates

result = split_ingredients_by_store(ingredients, candidates)

# Result:
# - 1 store (FreshDirect)
# - 1-item rule applied (garam_masala merged to primary)
# - Reasoning: "Not worth adding specialty store for 1 item"
```

```python
# Scenario: Chicken biryani (multiple spices)
ingredients = [
    "chicken", "onions", "yogurt",  # Fresh → primary
    "turmeric", "cumin", "ghee", "basmati_rice"  # Specialty
]
candidates = {...}

result = split_ingredients_by_store(
    ingredients,
    candidates,
    UserPreferences(urgency="planning")
)

# Result:
# - 2 stores: FreshDirect (3 items) + Pure Indian Foods (4 items, PRIMARY)
# - Primary store = Pure Indian Foods (more items)
```

---

## Architecture

### Module: `ingredient_classifier.py`

**Purpose**: Classify ingredients by store type

**Key Functions:**
- `classify_ingredient_store_type(ingredient_name)` → "primary" | "specialty" | "both"
- `is_fresh_ingredient(ingredient)` → bool
- `is_ethnic_specialty(ingredient)` → bool
- `get_ingredient_classification_reason(ingredient)` → str (for debugging)

**Pattern Lists:**
- `FRESH_CATEGORIES` - 100+ fresh items (produce, meat, dairy, herbs)
- `ETHNIC_SPECIALTY` - 80+ ethnic items (Indian, Middle Eastern, Asian, Latin spices)
- `COMMON_SHELF_STABLE` - 50+ common items (olive oil, pasta, rice, salt)

**Extensibility:**
- Keyword matching: "fresh fenugreek" contains "fresh" → primary
- Suffix matching: "sumac_powder" ends with "_powder" → likely spice → specialty
- Substring matching: "kashmiri_chili" contains "chili" → matches ethnic pattern

### Module: `store_split.py`

**Purpose**: Split ingredients across stores using multi-factor logic

**Key Functions:**
- `split_ingredients_by_store()` → StoreSplit
- `format_store_split_for_ui()` → dict (React-friendly format)

**Data Structures:**
```python
@dataclass
class StoreGroup:
    store: str  # "FreshDirect", "Pure Indian Foods"
    store_type: str  # "primary", "specialty"
    ingredients: List[str]
    count: int
    is_primary: bool  # Store with most items

@dataclass
class StoreSplit:
    stores: List[StoreGroup]
    unavailable: List[str]
    total_stores_needed: int
    applied_1_item_rule: bool
    reasoning: List[str]  # Human-readable decisions

@dataclass
class UserPreferences:
    urgency: str  # "planning" | "urgent"
    transparency_preference: str
    budget_conscious: bool
    location: str
```

---

## Testing

Run the demo:
```bash
cd /Users/hash/Documents/ConsciousBuyer/conscious-cart-coach
python3 test_classification_standalone.py
```

Shows:
- ✅ Classification of known ingredients
- ✨ Classification of NEW ingredients (saffron, sumac, kimchi, etc.)
- 📊 Pattern matching in action

---

## Integration with ProductAgent

ProductAgent remains clean - no static `store_type` fields in product data.

**Before (v1 - Static):**
```python
"turmeric": [
    {"id": "tu001", "brand": "ShopRite", "store_type": "primary"},  # ❌ Static
    {"id": "tu005", "brand": "Pure Indian Foods", "store_type": "specialty"},
]
```

**After (v2 - Dynamic):**
```python
"turmeric": [
    {"id": "tu001", "brand": "ShopRite"},  # ✅ Clean
    {"id": "tu005", "brand": "Pure Indian Foods"},
]

# Classification happens at runtime
store_type = classify_ingredient_store_type("turmeric")  # → "specialty"
```

**Benefits:**
- ✅ Product data stays clean
- ✅ Works for new ingredients
- ✅ Easy to update rules without touching product data
- ✅ Can add LLM fallback for truly unknown items

---

## Future Enhancements

### 1. LLM Fallback for Unknown Ingredients

```python
def classify_with_llm(ingredient: str) -> str:
    """Use Claude for truly unknown ingredients."""
    prompt = f"Classify '{ingredient}': primary, specialty, or both?"
    response = claude(prompt)
    return response  # "specialty"
```

### 2. Brand-Based Classification

```python
# Some products are exclusive to specialty stores
{"brand": "Pure Indian Foods", "specialty_exclusive": True}
```

### 3. Regional Variations

```python
# Different stores available by region
if user_location == "Edison, NJ":
    specialty_store = "Kesar Grocery"  # Fast delivery
elif user_location == "NYC":
    specialty_store = "Kalustyan's"  # Manhattan specialty store
```

---

## Design System Colors (for UI)

When building the ingredient confirmation UI, use these colors:

```css
/* From Figma design system */
--primary-brown: #6b5f3a;       /* Header background */
--cream: #fef9f5;               /* Main background */
--beige-border: #e5d5b8;        /* Card borders */
--text-dark: #2c2c2c;           /* Primary text */
--accent-green: #4a7c59;        /* Success, organic tags */
--accent-orange: #d4976c;       /* Primary store accent */
--accent-purple: #8b7ba8;       /* Specialty store accent */
```

**UI Component Colors:**
```jsx
// Primary Store tab
<div style={{
  backgroundColor: '#d4976c',  // Accent orange
  color: '#2c2c2c'
}}>
  Primary Store (5)
</div>

// Specialty Store tab
<div style={{
  backgroundColor: '#8b7ba8',  // Accent purple
  color: '#2c2c2c'
}}>
  Specialty Store (5)
</div>

// Unavailable tab
<div style={{
  backgroundColor: '#e5d5b8',  // Beige border
  color: '#6b5f3a'
}}>
  Unavailable (0)
</div>
```

---

## Migration from v1 (Static store_type)

If you have existing code using static `store_type` fields:

**Before:**
```python
products = agent.get_candidates(ingredients)
for product in products:
    if product["store_type"] == "specialty":
        # ...
```

**After:**
```python
products = agent.get_candidates(ingredients)
for ingredient_name in ingredients:
    store_type = classify_ingredient_store_type(ingredient_name)
    if store_type == "specialty":
        # ...
```

---

## References

- [MULTI_STORE_CART_SYSTEM.md](MULTI_STORE_CART_SYSTEM.md) - Full store splitting logic
- [ingredient_classifier.py](../../src/orchestrator/ingredient_classifier.py) - Classification implementation
- [store_split.py](../../src/orchestrator/store_split.py) - Store split implementation

---

Last updated: 2026-01-29
Version: 2.0 (Dynamic Rule-Based)
