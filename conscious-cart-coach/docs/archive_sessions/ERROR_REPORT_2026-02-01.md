# Error Report: System Architecture Analysis

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                      │
│                      http://localhost:5173                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │ POST /api/plan
                             │ {prompt, servings, preferences}
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                          │
│                      api/main.py:60-500                              │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 1. LLM INGREDIENT EXTRACTION                                  │  │
│  │    ✅ WORKING                                                 │  │
│  │    └─> src/llm/ingredient_extractor.py                        │  │
│  │         └─> OllamaClient (Mistral)                            │  │
│  │              Returns: 12-16 ingredients                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 2. PRODUCT AGENT (Candidate Lookup)                           │  │
│  │    ⚠️  PARTIALLY FAILING                                      │  │
│  │    └─> src/agents/product_agent.py:723-829                    │  │
│  │         ├─> Load inventory from CSV ✅                        │  │
│  │         ├─> Normalize ingredient names ✅                     │  │
│  │         ├─> Find matching products ✅                         │  │
│  │         └─> Sort by form/organic/price ❌ FAILING             │  │
│  │              Problem: Granules ranked above fresh             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 3. DECISION ENGINE (Scoring & Selection)                      │  │
│  │    ✅ WORKING                                                 │  │
│  │    └─> src/engine/decision_engine.py:181-348                  │  │
│  │         ├─> Stage 1: Hard constraints (recalls, diet) ✅     │  │
│  │         ├─> Stage 2: Soft scoring (EWG, organic, price) ✅   │  │
│  │         ├─> Pick recommended product ✅                       │  │
│  │         └─> Find cheaper/conscious neighbors ✅               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 4. STORE SPLIT (Multi-Store Orchestration)                    │  │
│  │    ✅ WORKING (but complex)                                   │  │
│  │    └─> src/orchestrator/store_split.py:105-487                │  │
│  │         ├─> Classify fresh vs specialty ✅                    │  │
│  │         ├─> Apply 3-item efficiency rule ✅                   │  │
│  │         └─> Assign stores based on available_stores ✅        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5. CART MAPPING (Tag Generation)                              │  │
│  │    ❌ FAILING (tags + store assignment)                       │  │
│  │    └─> api/main.py:242-420                                    │  │
│  │         ├─> Generate validator-safe tags ✅ (code)           │  │
│  │         ├─> Relative tradeoff comparisons ✅ (code)          │  │
│  │         └─> Brand-based store assignment ❌ FAILING           │  │
│  │              Problem: "365" → FreshDirect (should be WF)      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ JSON response
                             │ {cart_items, stores, total}
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND DISPLAY                             │
│                    Shows cart with tags                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✅ WORKING Components

### 1. LLM Ingredient Extraction
**File**: [`src/llm/ingredient_extractor.py`](src/llm/ingredient_extractor.py)

**Status**: ✅ **CONFIRMED WORKING**

**Evidence**:
```
User input: "chicken biryani for 4"
LLM output: 16 ingredients (chicken, rice, onions, tomatoes, yogurt,
            ginger, garlic, ghee, garam masala, turmeric,
            coriander powder, cumin seeds, cardamom, bay leaves,
            mint, cilantro)
```

**Why It Works**:
- Optional anthropic import pattern allows Ollama fallback
- Enhanced prompt with explicit 12-16 ingredient requirement
- `max_tokens=3000` allows full output
- `temperature=0.1` ensures consistency

**Test**:
```bash
python test_llm_extraction.py
# ✓ Returns 16 ingredients for "chicken biryani for 4"
```

---

### 2. Decision Engine (Scoring & Selection)
**File**: [`src/engine/decision_engine.py`](src/engine/decision_engine.py)

**Status**: ✅ **WORKING**

**Evidence**:
- Products are scored correctly (organic_specialty: +15, value_efficiency: +12)
- Cheaper/conscious neighbors identified
- Tier assignment (💰/⭐/🌍) based on price position

**Example Scoring**:
```
Organic Turmeric Powder:
  Base: 50
  + organic_specialty: +15
  + value_efficiency_best: +12
  = Final Score: 77

Non-organic Granules:
  Base: 50
  + value_efficiency_good: +6
  = Final Score: 56

→ Organic Turmeric selected (higher score) ✅
```

**Why It Works**:
- Deterministic scoring (same input → same output)
- Clear weight hierarchy (organic > price)
- Neighbor selection logic correct

---

### 3. Store Split Logic
**File**: [`src/orchestrator/store_split.py`](src/orchestrator/store_split.py)

**Status**: ✅ **WORKING** (complex but functional)

**Evidence**:
- Fresh items → primary store (FreshDirect)
- Specialty items (spices, rice) → specialty store (Pure Indian Foods)
- 3-item efficiency rule applied correctly

**Example**:
```
16 ingredients:
  - Fresh (7): chicken, onions, tomatoes, yogurt, ginger, garlic, cilantro
    → FreshDirect
  - Specialty (9): rice, ghee, garam masala, turmeric, coriander, cumin,
                   cardamom, bay leaves, mint
    → Pure Indian Foods (9 items > 3-item threshold ✅)

Result: 2 stores recommended
```

---

### 4. CSV Inventory Loading
**File**: [`src/data/inventory.py`](src/data/inventory.py)

**Status**: ✅ **WORKING**

**Evidence**:
```bash
Loaded 330 products into 35 ingredient categories
```

**Fresh Produce Confirmed in CSV**:
```csv
produce,Fresh Organic Ginger Root,FreshDirect,3.99,lb,per lb,USDA Organic,...
produce,Organic Garlic,FreshDirect,5.99,lb,per lb,USDA Organic,...
produce,Fresh Mint Bunch,FreshDirect,2.99,bunch,per bunch,...
produce,Fresh Cilantro Bunch,FreshDirect,1.99,bunch,per bunch,...
```

---

## ❌ FAILING Components

### 1. Product Form Sorting (Granules Over Fresh)
**File**: [`src/agents/product_agent.py:781-814`](src/agents/product_agent.py#L781-L814)

**Status**: ❌ **CRITICAL FAILURE**

**Problem**: Despite code fix, granules still ranked above fresh

**Evidence (User Cart)**:
```
❌ Pure Indian Foods, Ginger Root Coarse Granules ($6.99, 1.5oz)
❌ Pure Indian Foods, Garlic Minced ($6.50, 2oz)

Expected:
✅ Fresh Organic Ginger Root ($3.99, lb)
✅ Organic Garlic ($5.99, lb)
```

**Root Cause Analysis**:

**Theory 1**: Code changes not reloaded
```python
# Code was modified at 9:02 PM
# Backend restarted at 9:02 PM
# But inventory is loaded at import time, not runtime
# Sorting logic might be cached or not reapplied
```

**Theory 2**: Inventory normalization issue
```python
# User searches for: "ginger"
# Inventory has:
#   - "ginger" (category) → [Ginger Granules, Ginger Powder]
#   - "produce" (category) → [Fresh Organic Ginger Root]
#
# Problem: Fresh ginger might be under wrong category!
```

**Theory 3**: Sorting not applied to "produce" category
```python
# The sort_key function checks:
if name_lower in ["ginger", "garlic", "mint", "cilantro", "basil"]:
    # Apply fresh > dried logic

# But if "ginger" matches category "ginger" NOT "produce",
# the fresh ginger in "produce" category is never considered!
```

**Debug Steps**:
1. Check what category "Fresh Organic Ginger Root" is loaded under
2. Check what `name_lower` is when searching for "ginger"
3. Verify sorting is actually called
4. Add logging to see which products are being compared

**Fix Verification Needed**:
```python
# Add debug logging
logger.info(f"Searching for: {name_lower}")
logger.info(f"Found in inventory: {normalized}")
logger.info(f"Candidates before sort: {[c['title'] for c in candidates[:5]]}")
logger.info(f"Candidates after sort: {[c['title'] for c in candidates[:5]]}")
```

---

### 2. Brand-Based Store Assignment
**File**: [`api/main.py:372-398`](api/main.py#L372-L398)

**Status**: ❌ **CRITICAL FAILURE**

**Problem**: "365 by Whole Foods" showing under FreshDirect cart

**Evidence (User Cart)**:
```
FreshDirect ❌ (WRONG!)
├─ 365 by Whole Foods Market, Organic Boneless Skinless Chicken Breast
│  $7.99
```

**Expected**:
```
Whole Foods ✅
├─ 365 by Whole Foods Market, Organic Boneless Skinless Chicken Breast
│  $7.99
```

**Code That SHOULD Work**:
```python
# api/main.py:372-379
brand_lower = brand.lower()

# Check brand exclusivity first (overrides everything)
if "365" in brand_lower or "whole foods" in brand_lower:
    actual_store = "Whole Foods"
elif "pure indian foods" in brand_lower:
    actual_store = "Pure Indian Foods"
```

**Root Cause Analysis**:

**Theory 1**: Logic never reached
```python
# The map_decision_to_cart_item() function is called per ingredient
# But the store assignment might happen AFTER cart mapping
# Check: Is `actual_store` variable actually used in response?
```

**Theory 2**: Store grouping happens later
```python
# Cart items might be assigned `actual_store` correctly,
# but then the FRONTEND groups by store using a different field
# Check: What field does frontend use to group stores?
# Is it "store", "actual_store", "available_stores[0]"?
```

**Theory 3**: Response structure doesn't include `actual_store`
```python
# Check what's actually returned in CartItem:
return CartItem(
    id=...,
    catalogueName=...,
    price=...,
    store=actual_store,  # ← Is this field populated?
    ...
)
```

**Debug Steps**:
1. Add logging: `print(f"Brand: {brand}, actual_store: {actual_store}")`
2. Check CartItem model definition
3. Inspect API response JSON (does it have "store" field?)
4. Check frontend grouping logic

**Fix Verification Needed**:
```python
# api/main.py after store assignment
logger.info(f"Product: {title}")
logger.info(f"Brand: {brand}")
logger.info(f"Brand lower: {brand_lower}")
logger.info(f"Assigned store: {actual_store}")
```

---

### 3. Relative Tradeoff Tags Not Showing
**File**: [`api/main.py:301-370`](api/main.py#L301-L370)

**Status**: ⚠️  **CODE EXISTS, BUT NOT VISIBLE IN UI**

**Problem**: Tags show "USDA Organic", "No Active Recalls" but NOT "$3 more for organic"

**Evidence (User Cart)**:
```
✓ USDA Organic
✓ No Active Recalls
✓ Worth organic premium  ← This ONE works!
✓ Store Brand
⚠️ Premium Price

Missing:
❌ "$3 more for organic" (should show when conscious neighbor exists)
❌ "Not organic (saves $4)" (should show when cheaper but not organic)
❌ "Saves $4 vs organic" (should show when much cheaper than conscious)
```

**Code That SHOULD Work**:
```python
# api/main.py:355-370
if cheaper_neighbor:
    price_diff = price - cheaper_neighbor.get("price", 0)
    if price_diff > 2.0:
        trade_off_tags.append(f"${price_diff:.0f} more for organic")
```

**Root Cause Analysis**:

**Theory 1**: `cheaper_neighbor` is None
```python
# Check: Is cheaper_neighbor actually populated?
# The DecisionItem has cheaper_neighbor_id, but does product_lookup have it?

cheaper_neighbor = None
if item.cheaper_neighbor_id and item.cheaper_neighbor_id in product_lookup:
    cheaper_neighbor = product_lookup[item.cheaper_neighbor_id]
    # ↑ Does product_lookup actually contain cheaper_neighbor_id?
```

**Theory 2**: `product_lookup` doesn't include all products
```python
# product_lookup is built from candidates_by_ingredient
# But cheaper_neighbor might be from a DIFFERENT ingredient's candidates
# So it's not in the lookup dict!

# Example:
# Ginger candidates: [Product A, Product B, Product C]
# product_lookup = {"A": {...}, "B": {...}, "C": {...}}
#
# But cheaper_neighbor might be Product D (not in ginger candidates)
# So product_lookup["D"] → KeyError or None
```

**Theory 3**: Price difference calculation wrong
```python
# Check: Is price_diff actually > 2.0?
price = product.get("price", 0)  # Recommended product price
cheaper_price = cheaper_neighbor.get("price", 0)  # Cheaper neighbor price
price_diff = price - cheaper_price

# If recommended IS the cheapest, cheaper_neighbor would be None
# So the tag would never appear (correct behavior)
```

**Debug Steps**:
1. Log `item.cheaper_neighbor_id` (is it populated?)
2. Log `product_lookup.keys()` (does it contain the ID?)
3. Log `cheaper_neighbor` (is it None or a dict?)
4. Log `price_diff` (what's the actual value?)

**Fix Verification Needed**:
```python
# api/main.py after neighbor lookup
logger.info(f"Ingredient: {item.ingredient_name}")
logger.info(f"Cheaper neighbor ID: {item.cheaper_neighbor_id}")
logger.info(f"Product lookup keys: {list(product_lookup.keys())}")
logger.info(f"Cheaper neighbor: {cheaper_neighbor}")
if cheaper_neighbor:
    logger.info(f"Price diff: ${price - cheaper_neighbor.get('price', 0):.2f}")
```

---

## 🔍 Diagnostic Tests

### Test 1: Verify Fresh Ginger in Inventory
```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from src.agents.product_agent import ProductAgent

agent = ProductAgent()
inv = agent.inventory

# Check what's under 'ginger' category
if 'ginger' in inv:
    print('Products under ginger category:')
    for p in inv['ginger']:
        print(f'  - {p[\"title\"]} ({p.get(\"brand\", \"No brand\")})')

# Check what's under 'produce' category
if 'produce' in inv:
    print('\nProducts under produce category:')
    for p in inv['produce'][:10]:
        print(f'  - {p[\"title\"]} ({p.get(\"brand\", \"No brand\")})')
"
```

**Expected Output**:
```
Products under ginger category:
  - Ginger Root Coarse Granules (Pure Indian Foods)
  - Organic Ginger Powder (Pure Indian Foods)

Products under produce category:
  - Fresh Organic Ginger Root (FreshDirect)
  - Organic Garlic (FreshDirect)
  ...
```

**Problem**: If "Fresh Organic Ginger Root" is under "produce" but search is for "ginger" category, it won't be found!

---

### Test 2: Trace Product Selection
```bash
# Add logging to product_agent.py

# src/agents/product_agent.py:752
name_lower = name.lower().strip()
normalized = self._normalize(name_lower)

+ logger.info(f"🔍 Searching for: '{name_lower}' → normalized: '{normalized}'")

if normalized and normalized in self.inventory:
    raw_products = self.inventory[normalized]
+   logger.info(f"📦 Found {len(raw_products)} products in category '{normalized}'")
+   for p in raw_products[:5]:
+       logger.info(f"   - {p['title']} (brand: {p.get('brand', 'N/A')})")

    # After sorting
    candidates.sort(key=sort_key)
+   logger.info(f"🏆 Top 3 after sorting:")
+   for i, c in enumerate(candidates[:3]):
+       logger.info(f"   {i+1}. {c['title']} (form_score: {sort_key(c)[0]}, organic: {sort_key(c)[1]}, price: {sort_key(c)[2]:.2f})")
```

**Run**: Restart backend, submit "chicken biryani for 4", check logs

---

### Test 3: Verify Store Assignment
```bash
# Add logging to api/main.py

# api/main.py:373
brand_lower = brand.lower()
+ logger.info(f"🏪 Product: {title}")
+ logger.info(f"   Brand: '{brand}' → '{brand_lower}'")

if "365" in brand_lower or "whole foods" in brand_lower:
    actual_store = "Whole Foods"
+   logger.info(f"   ✅ Matched '365/whole foods' → Whole Foods")
elif "pure indian foods" in brand_lower:
    actual_store = "Pure Indian Foods"
+   logger.info(f"   ✅ Matched 'pure indian foods' → Pure Indian Foods")
else:
+   logger.info(f"   ⚠️  No brand match, using available_stores: {available_stores}")

+ logger.info(f"   → Final store: {actual_store}")
```

**Run**: Restart backend, check logs for "365 by Whole Foods Market" product

---

### Test 4: Check Product Lookup Dict
```bash
# Add logging to api/main.py

# api/main.py:300 (after getting neighbors)
if item.cheaper_neighbor_id and item.cheaper_neighbor_id in product_lookup:
    cheaper_neighbor = product_lookup[item.cheaper_neighbor_id]
+   logger.info(f"💰 Cheaper neighbor found: {cheaper_neighbor.get('title')} (${cheaper_neighbor.get('price', 0):.2f})")
+else:
+   logger.info(f"💰 Cheaper neighbor ID: {item.cheaper_neighbor_id}, in lookup: {item.cheaper_neighbor_id in product_lookup if item.cheaper_neighbor_id else False}")
```

---

## 🎯 Fix Priority Matrix

| Issue | Impact | Effort | Priority |
|-------|--------|--------|----------|
| **Fresh produce not selected** | 🔴 CRITICAL | Medium | **P0** - Breaks core value prop |
| **Store assignment wrong** | 🟡 HIGH | Low | **P1** - Confusing but not blocking |
| **Tradeoff tags missing** | 🟡 MEDIUM | Low | **P2** - Nice to have |
| **System too complex** | 🔴 HIGH | High | **P0** - Root cause of all issues |

---

## 🔧 Recommended Fixes

### Immediate (Today)
1. **Add diagnostic logging** (30 min)
   - Product selection flow
   - Store assignment flow
   - Tag generation flow
   - Restart backend, test "chicken biryani for 4"
   - Capture logs, analyze failure points

2. **Fix inventory categorization** (1 hour)
   - Ensure fresh ginger is in "ginger" category (not just "produce")
   - Or update search to check BOTH category AND aliases
   - Test: Does fresh ginger appear in candidates now?

3. **Verify store assignment** (30 min)
   - Check if CartItem model has "store" field
   - Check if frontend uses correct field for grouping
   - Fix field mapping if mismatched

### Short-term (This Week)
4. **Streamlit debugging prototype** (2 hours)
   - Visual inspection of product ranking
   - Live testing of inventory changes
   - Validate fixes without frontend rebuild

5. **Simplify to single store** (1 day)
   - Remove store_split.py complexity
   - Hardcode FreshDirect for all products
   - Focus on getting product selection + tags perfect

### Long-term
6. **Rebuild with recipe templates** (1 week)
   - Remove LLM extraction dependency
   - Hardcode 10 popular recipes
   - 100% reliable ingredient lists

---

## 💡 System Design Issues

### Problem 1: Too Many Abstraction Layers
```
Frontend Request
  └─> API Endpoint
       └─> LLM Extraction (PASS)
            └─> Product Agent (FAIL - sorting)
                 └─> Decision Engine (PASS)
                      └─> Store Split (PASS but complex)
                           └─> Cart Mapping (FAIL - assignment)
                                └─> Frontend Display
```

**Each layer adds**:
- Potential failure points
- Debugging difficulty
- State transformation bugs

**Recommendation**: **Flatten to 3 layers**
```
Frontend Request
  └─> API Endpoint
       ├─> Get Ingredients (template or LLM)
       ├─> Get Products (single store, simple sort)
       └─> Generate Tags (evidence-based)
```

---

### Problem 2: Inventory Structure Mismatch
```python
# Current structure:
inventory = {
    "ginger": [Ginger Granules, Ginger Powder],
    "produce": [Fresh Ginger Root, ...]
}

# Problem: Searching for "ginger" doesn't find "produce" category
```

**Recommendation**: **Ingredient-first indexing**
```python
inventory = {
    "ginger": [
        Fresh Ginger Root,  # form: fresh
        Ginger Granules,    # form: dried
        Ginger Powder       # form: powder
    ],
    "garlic": [...]
}
```

---

### Problem 3: Product Lookup Incomplete
```python
# product_lookup is built from current candidates only
product_lookup = {id: product for products in candidates_by_ingredient.values() for product in products}

# But cheaper_neighbor might be from a DIFFERENT ingredient!
# So it's not in the dict → neighbor comparison fails
```

**Recommendation**: **Build complete lookup**
```python
# Include ALL products from inventory, not just current candidates
product_lookup = {p["id"]: p for products in inventory.values() for p in products}
```

---

## 🚨 Critical Blocker Summary

### The Core Issue
The system has **3 critical bugs** preventing launch:

1. ❌ **Fresh produce not selected** → Recommends granules instead of fresh ginger
2. ❌ **Store assignment broken** → 365 by Whole Foods shows under FreshDirect
3. ⚠️  **System too complex to debug** → Can't quickly identify root cause

### Why Fixes Aren't Working
1. **Code changes not propagating** (inventory loading, import caching)
2. **Multi-layer architecture** (6 transformation steps, each can fail)
3. **No diagnostic logging** (can't see where failures occur)

### Next Steps
**Option A**: Debug current system (2-3 days, high risk)
**Option B**: Pivot to Streamlit (2 hours, low risk, proves value faster)

**Recommendation**: **Option B** → Build Streamlit MVP today, prove core value, then decide if React rebuild is worth it.

---

## 📊 Success Metrics

### What Success Looks Like
```
User Input: "chicken biryani for 4"

✅ 16 ingredients extracted (not 4)
✅ Fresh Organic Ginger Root recommended (not granules)
✅ 365 by Whole Foods shows under "Whole Foods" (not FreshDirect)
✅ Tags show "$3 more for organic" (not just "USDA Organic")
✅ Total time: <2 seconds
```

### Current State
```
User Input: "chicken biryani for 4"

✅ 16 ingredients extracted (WORKING)
❌ Ginger Root Coarse Granules recommended (FAILING)
❌ 365 by Whole Foods shows under "FreshDirect" (FAILING)
⚠️  Tags show "USDA Organic" but no price comparisons (PARTIAL)
✅ Total time: <2 seconds (WORKING)

Score: 2/5 (40%) → BLOCKING LAUNCH
```

---

## End of Report
