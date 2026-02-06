# Current Architecture - Conscious Cart Coach

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                      │
│                      http://localhost:5173                           │
│                                                                       │
│  User enters: "chicken biryani for 4"                                │
│  Preferences: Organic priority, No allergies                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │ POST /api/plan
                             │ {prompt, servings, preferences}
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                          │
│                      api/main.py (500 lines)                         │
│                                                                       │
│  Main Endpoint: /api/plan (line 60)                                 │
│  ├─ Parse request                                                    │
│  ├─ Orchestrate 5 processing stages                                 │
│  └─ Return CartResponse JSON                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
         [STAGE 1]     [STAGE 2]    [STAGE 3]
      LLM Extract   Product Lookup  Decision
                                    Engine
                             │
                    ┌────────┼────────┐
                    ▼                 ▼
              [STAGE 4]         [STAGE 5]
            Store Split       Cart Mapping
```

---

## Processing Pipeline (5 Stages)

### STAGE 1: LLM Ingredient Extraction
**Status**: ✅ WORKING

**File**: `src/llm/ingredient_extractor.py`

**Input**:
```json
{
  "prompt": "chicken biryani for 4",
  "servings": 4
}
```

**Process**:
1. Build enhanced prompt with examples
2. Call Ollama (Mistral) or Claude API
3. Parse LLM response into structured ingredients

**Output**:
```json
[
  {"name": "chicken", "quantity": "1.5 lb", "notes": "bone-in thighs preferred"},
  {"name": "rice", "quantity": "2 cups", "notes": "basmati"},
  {"name": "onions", "quantity": "2 medium"},
  {"name": "tomatoes", "quantity": "3 medium"},
  {"name": "yogurt", "quantity": "1 cup"},
  {"name": "ginger", "quantity": "2 inches"},
  {"name": "garlic", "quantity": "8 cloves"},
  {"name": "ghee", "quantity": "3 tbsp"},
  {"name": "garam masala", "quantity": "2 tsp"},
  {"name": "turmeric", "quantity": "1 tsp"},
  {"name": "coriander powder", "quantity": "1 tbsp"},
  {"name": "cumin seeds", "quantity": "1 tsp"},
  {"name": "cardamom", "quantity": "4 pods"},
  {"name": "bay leaves", "quantity": "2"},
  {"name": "mint", "quantity": "1/4 cup"},
  {"name": "cilantro", "quantity": "1/4 cup"}
]
```

**Why it works**:
- Optional anthropic import allows Ollama fallback
- Enhanced prompt with explicit 12-16 ingredient requirement
- `max_tokens=3000` allows full output
- `temperature=0.1` ensures consistency

---

### STAGE 2: Product Agent (Candidate Lookup)
**Status**: ⚠️ PARTIALLY FAILING (granules ranked above fresh)

**File**: `src/agents/product_agent.py` (800+ lines)

**Input**: List of ingredients from Stage 1

**Process**:
```python
# 1. Load inventory from CSV (happens at import time)
inventory = {
    "ginger": [
        {id: "prod001", title: "Ginger Root Coarse Granules", brand: "Pure Indian Foods", price: 6.99},
        {id: "prod002", title: "Organic Ginger Powder", brand: "Pure Indian Foods", price: 4.99},
        {id: "prod003", title: "Fresh Organic Ginger Root", brand: "FreshDirect", price: 3.99}
    ],
    "chicken": [...],
    ...
}

# 2. For each ingredient, find matching products
for ingredient in ingredients:
    normalized = normalize(ingredient.name)  # "ginger" → "ginger"
    candidates = inventory.get(normalized, [])

    # 3. Sort by form preference (FAILING HERE)
    candidates.sort(key=sort_key)
    # sort_key should prioritize: fresh > dried > powder > granules
    # BUT granules still ranking above fresh!

    # 4. Return top 5-6 candidates
    yield candidates[:6]
```

**Output**:
```json
{
  "candidates_by_ingredient": {
    "ginger": [
      {"id": "prod001", "title": "Ginger Root Coarse Granules", ...},  // ❌ WRONG - granules first
      {"id": "prod003", "title": "Fresh Organic Ginger Root", ...},     // Should be first!
      {"id": "prod002", "title": "Organic Ginger Powder", ...}
    ],
    "chicken": [...],
    ...
  }
}
```

**Critical Bug**: Despite code fix at line 781-814, granules still rank above fresh produce

**Root Cause Theories**:
1. Code changes not reloaded (import-time caching)
2. Fresh ginger under "produce" category, search only checks "ginger" category
3. Sorting not applied to cross-category matches

---

### STAGE 3: Decision Engine (Scoring & Selection)
**Status**: ✅ WORKING

**File**: `src/engine/decision_engine.py` (lines 181-348)

**Input**: Candidates from Stage 2

**Process**:
```python
for ingredient, candidates in candidates_by_ingredient.items():
    # Stage 1: Hard constraints (MUST pass)
    filtered = []
    for product in candidates:
        if has_recall(product):
            continue  # Skip recalled products
        if violates_diet(product, user_preferences):
            continue  # Skip allergens
        filtered.append(product)

    # Stage 2: Soft scoring (0-100 points)
    for product in filtered:
        score = 50  # Base score

        # Organic bonus
        if product.organic:
            score += 15

        # EWG rating (for produce)
        if ewg_rating == "Clean 15":
            score += 5
        elif ewg_rating == "Dirty Dozen":
            if product.organic:
                score += 10  # Organic is critical for dirty dozen

        # Price efficiency
        if product.price == min_price:
            score += 12  # Best value
        elif product.price <= median_price:
            score += 6   # Good value

        product.score = score

    # Stage 3: Pick recommended product (highest score)
    recommended = max(filtered, key=lambda p: p.score)

    # Stage 4: Find neighbors
    cheaper_neighbor = find_cheapest(filtered)
    conscious_neighbor = find_most_organic(filtered)

    yield DecisionItem(
        ingredient_name=ingredient,
        selected_product_id=recommended.id,
        cheaper_neighbor_id=cheaper_neighbor.id,
        conscious_neighbor_id=conscious_neighbor.id,
        tier_symbol="💰" if recommended == cheaper_neighbor else "⭐"
    )
```

**Output**:
```json
{
  "decisions": [
    {
      "ingredient_name": "ginger",
      "selected_product_id": "prod001",
      "cheaper_neighbor_id": "prod003",
      "conscious_neighbor_id": "prod003",
      "tier_symbol": "⭐",
      "attributes": ["USDA Organic"],
      "safety_notes": []
    },
    ...
  ]
}
```

**Why it works**:
- Deterministic scoring (same input → same output)
- Clear weight hierarchy (organic > price)
- Neighbor selection logic correct

---

### STAGE 4: Store Split (Multi-Store Orchestration)
**Status**: ✅ WORKING (complex but functional)

**File**: `src/orchestrator/store_split.py` (lines 105-487)

**Input**: Decisions from Stage 3

**Process**:
```python
# 1. Classify ingredients
fresh_items = []
specialty_items = []

for decision in decisions:
    product = product_lookup[decision.selected_product_id]

    # Check if fresh produce
    if product.category in ["produce", "protein_meat", "protein_poultry"]:
        fresh_items.append(decision)
    # Check if specialty (ethnic, hard-to-find)
    elif product.store_type == "specialty":
        specialty_items.append(decision)
    else:
        fresh_items.append(decision)  # Default to fresh/primary store

# 2. Apply 3-item efficiency rule
if len(specialty_items) >= 3:
    # Worth a trip to specialty store
    stores = {
        "FreshDirect": fresh_items,
        "Pure Indian Foods": specialty_items
    }
else:
    # Not worth it, buy specialty items at primary store if available
    all_items = fresh_items + specialty_items
    stores = {
        "FreshDirect": all_items
    }

return stores
```

**Output**:
```json
{
  "stores": {
    "FreshDirect": [
      {"ingredient": "chicken", ...},
      {"ingredient": "onions", ...},
      {"ingredient": "tomatoes", ...},
      {"ingredient": "yogurt", ...},
      {"ingredient": "ginger", ...},
      {"ingredient": "garlic", ...},
      {"ingredient": "mint", ...},
      {"ingredient": "cilantro", ...}
    ],
    "Pure Indian Foods": [
      {"ingredient": "rice", ...},
      {"ingredient": "ghee", ...},
      {"ingredient": "garam masala", ...},
      {"ingredient": "turmeric", ...},
      {"ingredient": "coriander powder", ...},
      {"ingredient": "cumin seeds", ...},
      {"ingredient": "cardamom", ...},
      {"ingredient": "bay leaves", ...}
    ]
  }
}
```

---

### STAGE 5: Cart Mapping (Tag Generation + Store Assignment)
**Status**: ❌ PARTIALLY FAILING (store assignment broken)

**File**: `api/main.py` (lines 242-464)

**Input**: Store-split decisions from Stage 4

**Process**:
```python
def map_decision_to_cart_item(item, product_lookup, target_store):
    product = product_lookup[item.selected_product_id]

    # 1. Generate validator-safe tags
    why_pick_tags = []
    trade_off_tags = []

    # Organic status
    if product.organic:
        why_pick_tags.append("USDA Organic")

    # Recall check
    if not has_recall(product):
        why_pick_tags.append("No Active Recalls")

    # Price comparison (FAILING - neighbors not found)
    cheaper_neighbor = product_lookup.get(item.cheaper_neighbor_id)
    if cheaper_neighbor:
        price_diff = product.price - cheaper_neighbor.price
        if price_diff > 2.0:
            trade_off_tags.append(f"${price_diff:.0f} more for organic")

    # 2. Store assignment (FAILING - wrong store)
    brand_lower = product.brand.lower()

    if "365" in brand_lower or "whole foods" in brand_lower:
        actual_store = "Whole Foods"  # ← CODE SAYS THIS
    elif "pure indian foods" in brand_lower:
        actual_store = "Pure Indian Foods"
    else:
        actual_store = target_store or "FreshDirect"

    # 3. Build cart item
    return CartItem(
        id=f"item-{index}",
        name=product.title,
        brand=product.brand,
        price=product.price,
        quantity=1.0,
        store=actual_store,  # ← BUT USER SEES "FreshDirect"!
        tags={
            "whyPick": why_pick_tags,
            "tradeOffs": trade_off_tags
        }
    )
```

**Output** (Expected):
```json
{
  "cartItems": [
    {
      "id": "item-1",
      "name": "Organic Boneless Skinless Chicken Breast",
      "brand": "365 by Whole Foods Market",
      "price": 7.99,
      "store": "Whole Foods",  // ← SHOULD BE THIS
      "tags": {
        "whyPick": ["USDA Organic", "No Active Recalls", "Store Brand"],
        "tradeOffs": []
      }
    },
    ...
  ]
}
```

**Output** (Actual - User Report):
```json
{
  "cartItems": [
    {
      "id": "item-1",
      "name": "Organic Boneless Skinless Chicken Breast",
      "brand": "365 by Whole Foods Market",
      "price": 7.99,
      "store": "FreshDirect",  // ❌ WRONG!
      "tags": {
        "whyPick": ["USDA Organic", "No Active Recalls", "Store Brand"],
        "tradeOffs": []  // ❌ Missing price comparisons!
      }
    },
    ...
  ]
}
```

**Critical Bugs**:
1. **Store assignment**: 365 products showing under FreshDirect
2. **Missing tags**: Price comparison tags not appearing

---

## Data Flow

### 1. CSV Inventory → In-Memory Dict

**Source**: `data/alternatives/source_listings.csv` (330 products)

**Loader**: `src/agents/product_agent.py:74-155`

```python
inventory = {
    "ginger": [
        {
            "id": "prod001",
            "title": "Ginger Root Coarse Granules",
            "brand": "Pure Indian Foods",
            "price": 6.99,
            "size": "1.5oz",
            "unit": "ea",
            "organic": False,
            "store_type": "specialty",
            "available_stores": ["Pure Indian Foods"],
            "category": "ginger"
        },
        ...
    ],
    "chicken": [...],
    ...
}
```

**Store Mapping** (product_agent.py:29-46):
```python
STORE_EXCLUSIVE_BRANDS = {
    "365 by Whole Foods Market": ["Whole Foods", "Whole Foods Market"],
    "365": ["Whole Foods", "Whole Foods Market"],
    "Pure Indian Foods": ["specialty"],
    ...
}

# During CSV load:
available_stores = STORE_EXCLUSIVE_BRANDS.get(brand, ["all"])
```

---

### 2. Request → Response Flow

```
User Request
  ↓
┌─────────────────────────────────────────┐
│ POST /api/plan                           │
│ {                                        │
│   "prompt": "chicken biryani for 4",    │
│   "servings": 4,                         │
│   "preferences": {...}                   │
│ }                                        │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ STAGE 1: LLM Extraction                 │
│ → 16 ingredients                         │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ STAGE 2: Product Lookup                 │
│ → 5-6 candidates per ingredient         │
│ → 80-96 total candidates                │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ STAGE 3: Decision Engine                │
│ → Score each candidate (0-100)          │
│ → Pick best per ingredient              │
│ → Find cheaper/conscious neighbors      │
│ → 16 DecisionItems                      │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ STAGE 4: Store Split                    │
│ → Classify fresh vs specialty           │
│ → Apply 3-item rule                     │
│ → Assign stores                          │
│ → {FreshDirect: 8 items,                │
│    Pure Indian Foods: 8 items}          │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ STAGE 5: Cart Mapping                   │
│ → Generate tags                          │
│ → Assign actual_store (FAILING)         │
│ → Build CartItem objects                │
│ → 16 CartItems                           │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ CartResponse JSON                        │
│ {                                        │
│   "cartItems": [...],                    │
│   "stores": {                            │
│     "FreshDirect": {...},                │
│     "Pure Indian Foods": {...}           │
│   },                                     │
│   "totalCost": 87.42                     │
│ }                                        │
└─────────────────┬───────────────────────┘
                  ↓
          Frontend Display
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM Client**: Ollama (local) or Claude API (fallback)
- **Data**: CSV files (no database)
- **Dependencies**:
  - `pydantic` for models
  - `httpx` for HTTP requests
  - `anthropic` (optional) for Claude API

### Frontend
- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: React hooks (no Redux)

### Data Storage
- **Inventory**: CSV (`data/alternatives/source_listings.csv`)
- **Facts**: SQLite (`data/facts_store.db`)
- **No user database** (stateless)

---

## File Structure

```
conscious-cart-coach/
├── api/
│   └── main.py                      # FastAPI app (500 lines)
│       ├── POST /api/plan           # Main endpoint
│       ├── map_decision_to_cart_item()  # Stage 5 logic
│       └── get_product_image()      # Image mapping
│
├── src/
│   ├── agents/
│   │   └── product_agent.py         # Stage 2 (800 lines)
│   │       ├── STORE_EXCLUSIVE_BRANDS  # Brand → Store mapping
│   │       ├── _load_inventory_from_csv()
│   │       ├── get_candidates()     # Main API
│   │       └── _sort_by_form_preference()  # FAILING
│   │
│   ├── engine/
│   │   └── decision_engine.py       # Stage 3 (350 lines)
│   │       ├── filter_hard_constraints()
│   │       ├── score_products()
│   │       └── pick_recommended()
│   │
│   ├── orchestrator/
│   │   └── store_split.py           # Stage 4 (480 lines)
│   │       ├── classify_fresh_vs_specialty()
│   │       ├── apply_efficiency_rule()
│   │       └── assign_stores()
│   │
│   ├── llm/
│   │   ├── ingredient_extractor.py  # Stage 1 (200 lines)
│   │   ├── decision_explainer.py    # (unused in current flow)
│   │   └── recipe_product_matcher.py  # (unused in current flow)
│   │
│   └── utils/
│       └── llm_client.py            # Ollama/Claude client
│
├── data/
│   ├── alternatives/
│   │   └── source_listings.csv      # 330 products
│   └── facts_store.db               # Recalls, EWG ratings
│
└── frontend/ (React app)
    ├── src/
    │   ├── components/
    │   │   └── CartDisplay.tsx      # Shows cart items
    │   └── App.tsx                   # Main app
    └── ...
```

---

## Critical Issues

### 1. Fresh Produce Not Selected (P0 - CRITICAL)
**Impact**: Recommends granules over fresh ginger
**File**: `src/agents/product_agent.py:781-814`
**Fix Status**: Code updated, but NOT working

### 2. Store Assignment Wrong (P1 - HIGH)
**Impact**: 365 by Whole Foods shows under FreshDirect
**File**: `api/main.py:415-424`
**Fix Status**: Code looks correct, but NOT working

### 3. Price Comparison Tags Missing (P2 - MEDIUM)
**Impact**: Tags show "USDA Organic" but not "$3 more for organic"
**File**: `api/main.py:368-388`
**Fix Status**: Code exists, but tags not appearing

---

## System Complexity

### Abstraction Layers
```
User Request
  └─> API Endpoint (1)
       └─> LLM Extraction (2)
            └─> Product Agent (3)
                 └─> Decision Engine (4)
                      └─> Store Split (5)
                           └─> Cart Mapping (6)
                                └─> Frontend Display (7)
```

**Problem**: 7 layers = 7 potential failure points

### Lines of Code
- `api/main.py`: 500 lines
- `product_agent.py`: 800 lines
- `decision_engine.py`: 350 lines
- `store_split.py`: 480 lines
- **Total**: ~2,100 lines for core flow

**Problem**: Too complex to debug quickly

---

## Recommended Simplifications

### Option A: Flatten to 3 Layers
```
User Request
  └─> API Endpoint
       ├─> Get Ingredients (template or LLM)
       ├─> Get Products (single store, simple sort)
       └─> Generate Tags (evidence-based)
```

### Option B: Remove Store Split
- Hardcode FreshDirect for all products
- Focus on getting product selection + tags perfect
- Add multi-store later

### Option C: Streamlit Prototype
- Visual debugging of product ranking
- Live testing of inventory changes
- Validate fixes without frontend rebuild

---

## Success Metrics

### What Success Looks Like
```
✅ 16 ingredients extracted (not 4)
✅ Fresh Organic Ginger Root recommended (not granules)
✅ 365 by Whole Foods shows under "Whole Foods" (not FreshDirect)
✅ Tags show "$3 more for organic" (not just "USDA Organic")
✅ Total time: <2 seconds
```

### Current State
```
✅ 16 ingredients extracted (WORKING)
❌ Ginger Root Coarse Granules recommended (FAILING)
❌ 365 by Whole Foods shows under "FreshDirect" (FAILING)
⚠️  Tags show "USDA Organic" but no price comparisons (PARTIAL)
✅ Total time: <2 seconds (WORKING)

Score: 2/5 (40%) → BLOCKING LAUNCH
```
