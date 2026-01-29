# Multi-Store Cart System: The Conscious Buyer's Shopping Optimizer

**Status**: ✅ Implemented
**Version**: 1.0
**Last Updated**: 2026-01-28

---

## The Problem We Solved

Imagine you're cooking chicken biryani for dinner. You need fresh chicken, vegetables, AND specialty Indian spices. Where do you shop?

**Before**: You'd either:
- Buy everything from FreshDirect (convenient but generic turmeric)
- Visit 3 different stores (exhausting and inefficient)
- Skip the specialty spices altogether (compromise on quality)

**After**: The system automatically splits your shopping between FreshDirect (fresh items) and Pure Indian Foods (organic spices with full transparency), optimizing for both efficiency AND ethics.

---

## How It Works: The Decision Flow

### 1. User Enters Meal Plan

```
User: "Chicken biryani for 4"
System: "Got it! Let me find the best stores for you..."
```

### 2. Extract Ingredients (via LLM)

```python
# Extracted ingredients
[
    {"name": "chicken", "quantity": 3, "unit": "lb"},
    {"name": "basmati rice", "quantity": 2, "unit": "cups"},
    {"name": "garam masala", "quantity": 2, "unit": "tbsp"},
    {"name": "turmeric", "quantity": 1, "unit": "tsp"},
    # ... 16 more ingredients
]
```

### 3. Check Ingredient Availability

For each ingredient, the system asks:
1. **Is it in our inventory?** → Use store data
2. **Is it truly rare?** (saffron, truffle) → Mark unavailable
3. **Is it fresh specialty?** (fresh fenugreek leaves) → Mark unavailable
4. **Is it ethnic shelf-stable?** (dried spices) → Pure Indian Foods
5. **Is it sustainable seafood?** → Wild Alaskan Company
6. **Otherwise** → Default to FreshDirect

### 4. Apply Efficiency Threshold

**The 1-Item Rule**: Don't add a second store for just 1 specialty item.

```python
# Example: Pasta with 1 specialty spice
If specialty_items == 1:
    # Route everything to FreshDirect (efficiency wins)
    return [FreshDirect]  # 1 store

If specialty_items >= 2:
    # Worth adding Pure Indian Foods
    return [FreshDirect, Pure Indian Foods]  # 2 stores
```

### 5. Select Primary Store

Primary store = **store with MOST items**

```python
# Chicken biryani result:
Pure Indian Foods: 12 items ⭐ PRIMARY
FreshDirect: 8 items
```

Even though FreshDirect has fresh items, Pure Indian Foods gets more items (12 vs 8), so it becomes primary.

---

## Store Routing Logic: The Decision Tree

### Fresh Items (Always → Full-Service Grocers)

```
Fresh produce, meat, dairy → FreshDirect or Whole Foods
```

**Why?** Specialty stores (Pure Indian Foods, Patel Brothers online) don't carry fresh produce.

### Ethnic Shelf-Stable Items (Priority: Pure Indian Foods)

```
Indian spices, rice, lentils, ghee → Pure Indian Foods > Patel Brothers > Whole Foods
```

**Why?** Pure Indian Foods offers:
- Organic/high-quality products
- Full transparency (know the sourcing)
- Ethical practices

**Examples**:
- ✅ Turmeric powder → Pure Indian Foods
- ✅ Basmati rice → Pure Indian Foods
- ✅ Garam masala → Pure Indian Foods
- ✅ Ghee → Pure Indian Foods
- ❌ Fresh fenugreek leaves → UNAVAILABLE (not available online)

### Sustainable Seafood

```
Wild-caught salmon → Wild Alaskan Company > FreshDirect
```

**Why?** Transparency in sourcing, sustainable practices.

### Common Grocery Items

```
Chicken, onions, pasta, eggs → FreshDirect
```

**Why?** Next-day delivery, full grocery selection.

---

## The Two Shopping Modes

### Mode 1: Pantry Restocking (Current Default)

**Use Case**: Monthly stock-up of shelf-stable items
**Timeline**: 1-2 weeks shipping is fine
**Priority**: Transparency > Speed

```
Store Priority:
1. Pure Indian Foods (1-2 weeks) ✅ High transparency
2. Patel Brothers (varies)
3. Whole Foods (2-3 days)
4. FreshDirect (next day)
```

**Example**: "I restock my pantry every month with Pure Indian Foods - organic spices, lentils, rice, ghee. I value knowing where they source from, and 1-2 weeks shipping is fine since I'm planning ahead."

### Mode 2: Immediate Cooking (Future Enhancement)

**Use Case**: Cooking tonight or this week
**Timeline**: Need it in 1-2 days
**Priority**: Speed > Transparency

```
Store Priority:
1. FreshDirect (next day) ✅ Fast
2. Patel Brothers (local pickup/delivery)
3. Kesar Grocery (faster than Pure Indian Foods)
4. Pure Indian Foods (too slow - 1-2 weeks)
```

**Example**: "I'm cooking biryani tomorrow - I can't wait 2 weeks for spices. Route me to Patel Brothers or Kesar Grocery instead."

---

## Store Selection: The Multi-Factor Decision Process

### The Real Question: When Is a Split Even Necessary?

This isn't just about availability. Just because an item *is available* at a specialty store doesn't mean we should route it there. The decision involves balancing **six key factors**:

#### 1. **Transparency & Ethics** 🌱

**What it means**: Can you see where the product comes from? Who grew it? How was it processed?

**Why it matters**: Conscious buyers want to know the story behind their food.

**Example**:
```
Pure Indian Foods → Full transparency pages for every product
Patel Brothers → Some organic brands, but limited sourcing info
FreshDirect → Generic products, minimal transparency
```

**Decision**: Prefer Pure Indian Foods for spices/staples where transparency matters most (organic turmeric, grass-fed ghee, hand-pounded rice).

#### 2. **Delivery Timing** ⏰

**What it means**: How fast do you need this ingredient?

**Two Scenarios**:

**Scenario A: Pantry Restocking** (Current Default)
```
Timeline: 1-2 weeks is fine
Use Case: Monthly stock-up of shelf-stable items
Store Priority: Pure Indian Foods (1-2 weeks) ✅

User Quote: "I restock my pantry every month with Pure Indian Foods -
organic spices, lentils, rice, ghee. I'm planning ahead, so 1-2 weeks
shipping is totally fine. I value knowing where they source from."
```

**Scenario B: Cooking Tonight/This Week**
```
Timeline: Need it in 1-2 days
Use Case: Immediate cooking
Store Priority: Patel Brothers (local), Kesar Grocery (fast), FreshDirect (next-day) ✅

User Quote: "I'm cooking biryani tomorrow - I can't wait 2 weeks for
spices. Route me to Patel Brothers or Kesar Grocery instead."
```

**Decision**: Current system assumes pantry restocking. Future enhancement: Add urgency toggle.

#### 3. **Fresh vs. Shelf-Stable Constraint** 🥬

**The Hard Constraint**: Online specialty stores (Pure Indian Foods, Patel Brothers online) **cannot ship fresh produce**.

**Fresh Items** → FreshDirect, Whole Foods, or local pickup ONLY
```
✅ Fresh chicken, onions, tomatoes, yogurt → FreshDirect
✅ Fresh herbs (mint, cilantro) → FreshDirect
❌ Fresh fenugreek leaves → UNAVAILABLE (can't be shipped)
```

**Shelf-Stable Items** → Can route to specialty stores
```
✅ Dried fenugreek (kasuri methi) → Pure Indian Foods
✅ Ghee, basmati rice, lentils → Pure Indian Foods
✅ Whole spices in sealed packages → Pure Indian Foods
```

**Decision**: This is NON-NEGOTIABLE. Fresh = full-service grocer. Shelf-stable = specialty store eligible.

#### 4. **Product Quality & Sourcing** 🏆

**The Difference**:
```
FreshDirect turmeric: Generic ground turmeric, $1.99/2oz
  → No origin info, conventional farming

Pure Indian Foods turmeric: Organic turmeric powder, $6.49/4oz
  → Sourced from certified organic farms in India
  → Transparency page shows exact farm location
  → Hand-processed to preserve curcumin
```

**When Quality Justifies Specialty Store**:
- Spices (organic, hand-pounded, specific varieties like Kashmiri chili)
- Rice (specific types like Sona Masoori, hand-pounded)
- Ghee (grass-fed, cultured, from specific dairy farms)
- Lentils/dal (heirloom varieties, organic)

**When Generic Is Fine**:
- Common vegetables (onions, tomatoes)
- Dairy (milk, yogurt) - freshness matters more than sourcing
- Protein (chicken, eggs) - unless seeking specific certification

**Decision**: Specialty stores for items where sourcing makes a meaningful difference.

#### 5. **Budget & Value** 💰

**The Conscious Buyer Paradox**: Ethical sourcing is important, BUT it must be affordable.

**Budget-Conscious Ethics**:
```
Pure Indian Foods organic turmeric: $6.49/4oz (~$1.62/oz)
Patel Brothers generic turmeric: $2.99/3.5oz (~$0.85/oz)
FreshDirect turmeric: $1.99/2oz (~$1.00/oz)

Decision: Pure Indian Foods is 60% more expensive than Patel Brothers,
but the transparency and organic certification justify it for a
4oz jar (lasts 6 months). User prefers quality over price for staples.
```

**When to Skip Specialty Store for Budget**:
```
If the price difference is 3x or more for the same product,
default to FreshDirect (unless user explicitly requests premium).
```

**Decision**: Transparency preferred, but only if reasonably priced. Current system assumes reasonable budget tolerance.

#### 6. **Efficiency Threshold** (The 1-Item Rule) ⚖️

**The Core Trade-off**: Ethics vs. Practicality

**Question**: Is it worth adding a second store for just 1 specialty item?

**Answer**: Usually NO.

**Why?**
- Managing 2 separate orders (different delivery dates, tracking, returns)
- Potential for extra shipping costs
- User friction (switching between stores, separate checkouts)

**The 1-Item Rule**:
```python
If specialty_items == 0:
    → 1 store (FreshDirect only)

If specialty_items == 1:
    → 1 store (merge to FreshDirect for efficiency)
    Rationale: Not worth adding Pure Indian Foods for just 1 spice

If specialty_items >= 2:
    → 2 stores (justified)
    Rationale: Multiple items make the second store worthwhile
```

**Real Examples**:

**Example 1: Pasta Carbonara with Garam Masala** (1 specialty item)
```
Ingredients:
  - Pasta
  - Eggs
  - Bacon
  - Parmesan cheese
  - 1 tsp garam masala  ← Only specialty item

Decision: 1 STORE (FreshDirect)
  ✅ Route everything to FreshDirect (including garam masala)
  ❌ Don't add Pure Indian Foods for just 1 spice

Why: User won't wait 2 weeks for Pure Indian Foods delivery just for
1 tsp of garam masala. They'll buy it from FreshDirect (even if
generic) for convenience.
```

**Example 2: Chicken Tikka Masala** (7 specialty items)
```
Ingredients:
  - Chicken (fresh)
  - Onions (fresh)
  - Tomatoes (fresh)
  - Yogurt (fresh)
  - Garam masala (shelf-stable specialty)
  - Kashmiri chili powder (shelf-stable specialty)
  - Dried fenugreek (shelf-stable specialty)
  - Turmeric (shelf-stable specialty)
  - Cumin (shelf-stable specialty)
  - Coriander (shelf-stable specialty)
  - Cardamom (shelf-stable specialty)

Decision: 2 STORES
  Store 1: FreshDirect (4 items)
    - All fresh items

  Store 2: Pure Indian Foods (7 items) ⭐ PRIMARY
    - All specialty spices

Why: 7 specialty spices justify adding Pure Indian Foods. The quality
difference (organic, hand-ground, specific varieties) matters for
authentic Indian cooking. Worth the 2-week wait for pantry restocking.
```

---

### Decision Matrix: When to Use 1 vs. 2 Stores

| Scenario | Specialty Items | Fresh Items | Urgency | Stores Used | Rationale |
|----------|----------------|-------------|---------|-------------|-----------|
| Pasta carbonara + 1 spice | 1 (garam masala) | 4 | Any | **1 store** (FreshDirect) | Efficiency wins - not worth 2nd store for 1 item |
| Chicken tikka masala | 7 (spices) | 4 | Planning | **2 stores** (Pure Indian Foods primary + FreshDirect) | Multiple specialty items justify transparency |
| Chicken tikka masala | 7 (spices) | 4 | Urgent | **2 stores** (Patel Brothers primary + FreshDirect) | Multiple items justify 2nd store, but need fast delivery |
| Simple salad | 0 | 8 | Any | **1 store** (FreshDirect) | No specialty items needed |
| Lentil dal (pantry restock) | 5 (lentils, spices) | 0 | Planning | **1 store** (Pure Indian Foods) | All shelf-stable, no fresh needed, transparency valued |
| Same dal (cooking tonight) | 5 (lentils, spices) | 0 | Urgent | **1 store** (Patel Brothers or FreshDirect) | All shelf-stable, but need it fast |

---

### The Question Flow: How the System Decides

For each meal plan, the system asks these questions **in order**:

#### Step 1: Classify Ingredients
```
For each ingredient:
  → Is it FRESH? (chicken, vegetables, dairy, herbs)
     YES → Can only go to FreshDirect, Whole Foods
     NO → Continue to Step 2

  → Is it TRULY RARE? (saffron, truffle oil, caviar)
     YES → Mark UNAVAILABLE, suggest external sources
     NO → Continue to Step 3

  → Is it ETHNIC SPECIALTY? (matches ethnic_keywords)
     YES → Eligible for Pure Indian Foods, Patel Brothers
     NO → Route to FreshDirect (common grocery item)
```

#### Step 2: Count Specialty Items
```
Count shelf-stable specialty items:
  → 0 items → Use 1 store (FreshDirect)
  → 1 item → Use 1 store (merge to FreshDirect for efficiency)
  → 2+ items → Consider 2 stores (continue to Step 3)
```

#### Step 3: Check User Context
```
What's the urgency?
  → Planning ahead (pantry restock) → Pure Indian Foods OK (1-2 weeks)
  → Cooking soon (1-2 days) → Need faster store (Patel Brothers, Kesar Grocery)

What's the budget tolerance?
  → High transparency preference → Pure Indian Foods (organic, premium)
  → Budget-conscious → Patel Brothers (good quality, lower cost)
  → Very budget-conscious → FreshDirect (generic but cheap)
```

#### Step 4: Apply Constraints
```
HARD CONSTRAINTS (non-negotiable):
  ✅ Fresh items MUST go to full-service grocer
  ✅ Specialty stores (online) CANNOT ship fresh produce
  ✅ Maximum 2 stores (too many = user friction)

SOFT CONSTRAINTS (preferences):
  ✅ Prefer transparency when practical (Pure Indian Foods > Patel Brothers)
  ✅ Prefer efficiency (don't add 2nd store for 1 item)
  ✅ Prefer budget-friendly options (within reason)
```

#### Step 5: Select Primary Store
```
Primary store = Store with MOST items

Why?
  → Users start shopping where they have the longest list
  → Reduces cognitive load (deal with biggest cart first)
  → Natural prioritization (tackle the bigger task first)

Example:
  Pure Indian Foods: 12 items ⭐ PRIMARY
  FreshDirect: 8 items

  User sees Pure Indian Foods cart first, shops there, then handles
  the smaller FreshDirect order.
```

---

### What Makes This More Than Just "Availability"?

**Traditional Grocery App** (availability-only):
```
Ingredient: Turmeric
  ✅ Available at FreshDirect
  ✅ Available at Pure Indian Foods
  ✅ Available at Patel Brothers

Decision: Pick the first available → FreshDirect
Result: User gets generic turmeric for $1.99
```

**Conscious Cart Coach** (multi-factor):
```
Ingredient: Turmeric
  ✅ Available at FreshDirect (generic, $1.99, no sourcing info)
  ✅ Available at Pure Indian Foods (organic, $6.49, full transparency)
  ✅ Available at Patel Brothers (MDH brand, $3.49, decent quality)

Context:
  - User is pantry restocking (1-2 weeks OK)
  - Recipe has 7 specialty spices (efficiency threshold met)
  - User values transparency
  - Budget tolerates premium for staples

Decision: Route to Pure Indian Foods
Result: User gets organic turmeric with full sourcing transparency
```

**The Difference**: We don't just ask "Where can I get this?" We ask:
1. **Where SHOULD I get this?** (quality, transparency)
2. **Is it WORTH adding a 2nd store?** (efficiency threshold)
3. **Does the timing work?** (delivery urgency)
4. **Is the price reasonable?** (budget constraints)
5. **What's the use case?** (immediate cooking vs. pantry restock)

That's what makes this a **conscious buying** system, not just a grocery availability checker.

---

## Technical Implementation

### Backend: Store Split Logic

**File**: [`src/orchestrator/store_split.py`](../../src/orchestrator/store_split.py)

#### Key Functions

**1. Check Ingredient Availability**

```python
def check_ingredient_availability(ingredient_name: str, inventory: dict) -> dict:
    """
    Determines which stores carry this ingredient.

    Returns:
        {
            "available_stores": ["Pure Indian Foods", "Patel Brothers"],
            "unavailable": False
        }
    """
```

**Classification Logic**:

```python
# Truly rare items (mark unavailable)
truly_rare_keywords = ["saffron", "truffle", "caviar", "foie gras"]

# Fresh specialty items (mark unavailable - online stores don't carry)
fresh_specialty_keywords = ["fresh fenugreek", "fresh curry leaf"]

# Ethnic shelf-stable items (route to specialty stores)
ethnic_store_keywords = [
    # Spices
    "turmeric", "garam masala", "cumin", "coriander", "cardamom",
    "red chili powder", "kashmiri chili", "dried fenugreek",

    # Staples
    "basmati rice", "ghee", "lentils", "dal",

    # Ingredients
    "tamarind", "asafoetida", "curry leaves"
]
```

**2. Simple Store Split (Heuristic-Based)**

```python
def _simple_store_split(available_ingredients, unavailable_ingredients):
    """
    Rules:
    1. Group items by available stores
    2. Ethnic items → Prefer Pure Indian Foods > Patel Brothers > Whole Foods
    3. Common items → Prefer FreshDirect
    4. EFFICIENCY: If secondary store has only 1 item, merge to primary
    5. Primary = store with MOST items
    """
```

**Ethnic Item Routing**:

```python
# Check if this is an ethnic specialty item
is_ethnic = any(keyword in ing_name_lower for keyword in ethnic_keywords)

if is_ethnic:
    # Prefer specialty stores (transparency priority)
    if "Pure Indian Foods" in stores:
        chosen_store = "Pure Indian Foods"
    elif "Patel Brothers" in stores:
        chosen_store = "Patel Brothers"
    elif "Whole Foods" in stores:
        chosen_store = "Whole Foods"
else:
    # Common items: prefer FreshDirect (speed priority)
    if "FreshDirect" in stores:
        chosen_store = "FreshDirect"
```

**Efficiency Threshold**:

```python
# Check ALL secondary stores (not just the first one)
stores_to_remove = []
for store, items in sorted_stores[1:]:
    if len(items) == 1:
        print(f"Moving {items[0]} from {store} to {primary_store} (efficiency: only 1 item)")
        store_groups[primary_store].extend(items)
        stores_to_remove.append(store)
```

**3. LLM Store Split (AI-Powered)**

```python
def _llm_store_split(available_ingredients, unavailable_ingredients, user_location, anthropic_client):
    """
    Uses Claude Sonnet 4 to decide optimal store split.

    LLM receives detailed prompt with:
    - Ingredient list with availability
    - Store capabilities (delivery, fresh vs shelf-stable)
    - Efficiency rules (1-item threshold)
    - Transparency preferences
    """
```

**LLM Prompt Highlights**:

```
CRITICAL EFFICIENCY RULE - THE 1-ITEM THRESHOLD:
❌ DO NOT add a 2nd store for just 1 specialty item
✅ Only add 2nd store if 2-3+ items need it

Decision logic:
1. Fresh items ALWAYS need full-service grocery
   - FreshDirect or Whole Foods
   - Pure Indian Foods doesn't carry fresh produce

2. Count SHELF-STABLE specialty items
   - 0 items → 1 store (FreshDirect)
   - 1 specialty item → 1 store (efficiency wins)
   - 2+ specialty items → 2 stores (worth it)

3. Transparency preference (when practical)
   - Pure Indian Foods > Patel Brothers
   - But only if multiple items justify it
```

### API Endpoints

**File**: [`api/main.py`](../../api/main.py)

#### 1. Extract Ingredients + Store Split

```python
@app.post("/api/extract-ingredients")
def extract_ingredients(request: CreateCartRequest):
    """
    Step 1: Extract ingredients and decide store split

    Input:
        {
            "meal_plan": "Chicken biryani for 4",
            "servings": 4,
            "user_location": "Edison, NJ"
        }

    Output:
        {
            "ingredients": [...],
            "store_split": {
                "available_stores": [
                    {
                        "store": "Pure Indian Foods",
                        "ingredients": ["basmati rice", "garam masala", ...],
                        "count": 12,
                        "is_primary": true
                    },
                    {
                        "store": "FreshDirect",
                        "ingredients": ["chicken", "onions", ...],
                        "count": 8,
                        "is_primary": false
                    }
                ],
                "unavailable_items": [],
                "total_stores_needed": 2
            }
        }
    """
```

#### 2. Create Multi-Cart

```python
@app.post("/api/create-multi-cart")
def create_multi_cart(request: CreateCartRequest):
    """
    Step 2: Build separate carts for each store

    Input:
        {
            "meal_plan": "Chicken biryani for 4",
            "servings": 4,
            "confirmed_ingredients": [...],
            "store_split": {...},
            "user_location": "Edison, NJ"
        }

    Output:
        {
            "carts": [
                {
                    "store": "Pure Indian Foods",
                    "is_primary": true,
                    "items": [
                        {
                            "id": "tu005",
                            "name": "Organic Turmeric Powder",
                            "brand": "Pure Indian Foods",
                            "size": "4oz",
                            "price": 6.49,
                            "quantity": 1,
                            "ingredientName": "turmeric"
                        },
                        ...
                    ],
                    "total": 45.67
                },
                {
                    "store": "FreshDirect",
                    "is_primary": false,
                    "items": [...],
                    "total": 28.99
                }
            ],
            "current_cart": "Pure Indian Foods",
            "servings": 4
        }
    """
```

### Frontend: Multi-Cart State Management

**File**: [`Figma_files/src/app/App.tsx`](../../Figma_files/src/app/App.tsx)

#### State Structure

```typescript
// Multi-cart state
const [carts, setCarts] = useState<CartData[]>([]);  // Array of carts, one per store
const [currentStore, setCurrentStore] = useState<string>('');  // Which cart is displayed
const [storeSplit, setStoreSplit] = useState<StoreSplit | null>(null);  // Store split info

interface CartData {
  store: string;
  is_primary: boolean;
  items: CartItem[];
  total: number;
}
```

#### Cart Creation Flow

```typescript
const handleCreateCart = async () => {
  // Step 1: Extract ingredients + get store split
  const extractData = await fetch('/api/extract-ingredients', {
    method: 'POST',
    body: JSON.stringify({ meal_plan, servings, user_location })
  });

  setStoreSplit(extractData.store_split);

  // Step 2: Build carts for each store
  const multiCartData = await fetch('/api/create-multi-cart', {
    method: 'POST',
    body: JSON.stringify({
      meal_plan,
      servings,
      confirmed_ingredients: extractData.ingredients,
      store_split: extractData.store_split,
      user_location
    })
  });

  setCarts(multiCartData.carts);
  setCurrentStore(multiCartData.current_cart);  // Start with primary store

  // Show ingredients overlay
  setShowIngredientsOverlay(true);
};
```

#### Store Switching

```typescript
const handleSwitchStore = (storeName: string) => {
  setCurrentStore(storeName);
  setCartMetadata(prev => ({
    store: storeName,
    location: prev?.location || '',
    servings: prev?.servings || servings
  }));
};
```

### Ingredients Overlay: 3-Group Display

**File**: [`Figma_files/src/app/components/IngredientsOverlay.tsx`](../../Figma_files/src/app/components/IngredientsOverlay.tsx)

#### Layout

```
┌────────────────────────────────────┐
│ 📋 Ingredients for [Meal Plan]   × │  ← Fixed Header
├────────────────────────────────────┤
│                                    │
│  🛒 PURE INDIAN FOODS (12 items)  │  ← Group 1: Primary Store (clickable)
│  ← You are here                    │
│  ☑ Organic Turmeric Powder         │
│     Pure Indian Foods • 4oz • $6.49│  ← Product specs (not recipe measurements)
│  ☑ Organic Garam Masala            │
│     Pure Indian Foods • 3oz • $7.99│
│  ...                               │
│  Cart Total: $45.67                │
│                                    │
│  🏪 FRESHDIRECT (8 items)          │  ← Group 2: Secondary Store (clickable)
│  Tap to view this cart →           │
│  ☑ Chicken Breast                  │
│     FreshDirect • 3lb • $12.99     │
│  ...                               │
│  Cart Total: $28.99                │
│                                    │
│  ⚠️ UNAVAILABLE (0 items)          │  ← Group 3: Unavailable (if any)
│                                    │
│  Grand Total (Stores): $74.66      │  ← Totals Section
│                                    │
├────────────────────────────────────┤
│  [Download List]        [Close]    │  ← Fixed Footer
└────────────────────────────────────┘
```

#### Key Features

**1. Product Specifications (Not Recipe Measurements)**

```typescript
// BEFORE (showing recipe measurements):
<span className="quantity">{ing.quantity} {ing.unit}</span>  // "1 tsp"
<span className="name">{ing.name}</span>                      // "turmeric"

// AFTER (showing product specifications):
<span className="name">{cartItem.name}</span>                       // "Organic Turmeric Powder"
<span className="quantity">{cartItem.brand} • {cartItem.size}</span> // "Pure Indian Foods • 4oz"
<span className="price">${cartItem.price}</span>                    // "$6.49"
```

**2. Store Switching**

```typescript
<div
  className={`store-group clickable ${group.isActive ? 'active' : ''}`}
  onClick={() => !group.isActive && onSwitchStore(group.store)}
>
  {!group.isActive && (
    <span className="tap-hint">Tap to view this cart →</span>
  )}
</div>
```

**3. Fixed Header/Footer with Scrollable Body**

```css
.overlay-modal {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 90vh;
}

.overlay-header { flex-shrink: 0; }  /* Fixed */
.overlay-body { flex: 1; overflow-y: auto; }  /* Scrollable */
.overlay-footer { flex-shrink: 0; }  /* Fixed */
```

---

## Test Coverage

### Backend Logic Tests

**File**: [`tests/test_store_split_flow.py`](../../tests/test_store_split_flow.py)

```python
✅ test_efficiency_threshold()          # 1 specialty item → 1 store
✅ test_multi_specialty_items()         # 2+ items → 2 stores
✅ test_fresh_vs_shelf_stable()         # Fresh → unavailable, dried → specialty
✅ test_store_priority_order()          # Pure Indian Foods > Patel Brothers
✅ test_common_items_fallback()         # Unknown items → FreshDirect
✅ test_sustainable_seafood()           # Wild salmon → Wild Alaskan Company
```

### API Integration Tests

**File**: [`tests/test_api_integration.py`](../../tests/test_api_integration.py)

```python
✅ test_extract_ingredients_endpoint()  # API format validation
✅ test_create_multi_cart_endpoint()    # Multi-cart creation
⚠️ test_efficiency_threshold_via_api() # Skipped (needs API key)
✅ test_primary_store_selection()       # Primary = most items
```

### Real-World Test Case

**File**: [`tests/test_chicken_biryani.py`](../../tests/test_chicken_biryani.py)

```
Input: Chicken biryani for 4 servings (20 ingredients)

Result:
  ✅ 2 stores needed (efficient)

  Pure Indian Foods - 12 items ⭐ PRIMARY
    • All Indian spices (turmeric, cumin, coriander, cardamom, etc.)
    • Basmati rice
    • Ghee
    • Garam masala
    • Saffron

  FreshDirect - 8 items
    • All fresh items (chicken, onions, tomatoes, yogurt, ginger, garlic, mint, cilantro)
```

---

## Design Decisions & Trade-offs

### 1. **Efficiency vs. Transparency**

**Decision**: Default to transparency (Pure Indian Foods), but enforce efficiency threshold (1-item rule)

**Rationale**:
- Target user is a "conscious buyer" who values ethics
- BUT won't visit 2 stores for just 1 item (impractical)
- Balance: 2+ specialty items justifies the second store

### 2. **Fresh vs. Shelf-Stable Constraint**

**Decision**: Route fresh items to full-service grocers ONLY

**Rationale**:
- Pure Indian Foods (online-only) doesn't carry fresh produce
- Fresh fenugreek leaves → UNAVAILABLE (not available online)
- Dried fenugreek → Pure Indian Foods (available)

### 3. **Primary Store = Most Items**

**Decision**: Store with most items becomes primary (not most expensive or "best")

**Rationale**:
- Efficiency: Start shopping at the store with the longest list
- User opens Pure Indian Foods cart first (12 items) before FreshDirect (8 items)

### 4. **Delivery Timing (Current vs. Future)**

**Current**: Assumes pantry restocking (1-2 weeks OK)
**Future**: Add urgency toggle for immediate cooking

**Rationale**:
- Current target user: Monthly pantry restocking
- Pure Indian Foods delivery time (1-2 weeks) is acceptable
- Future users cooking tonight would need faster stores (Patel Brothers, Kesar Grocery)

### 5. **Product Specs vs. Recipe Measurements**

**Decision**: Show product specifications in ingredients overlay

**Before**: `☑ 1 tsp turmeric`
**After**: `☑ Organic Turmeric Powder • Pure Indian Foods • 4oz • $6.49`

**Rationale**:
- Users want to see what they're actually buying
- Product details (brand, size) matter for conscious buyers
- Can compare products across stores

---

## Future Enhancements

### 1. Urgency Toggle

```typescript
// In Preferences
<toggle>
  🚀 Cooking soon (1-2 days)
  📅 Restocking pantry (1+ week)
</toggle>
```

**Impact on Routing**:
- Urgent → Patel Brothers, Kesar Grocery (fast delivery)
- Planning → Pure Indian Foods (high transparency, slow shipping)

### 2. Editable Ingredients List

**Current**: Read-only list
**Future**: Allow users to edit quantities, add/remove items

```typescript
// Editable ingredient row
<input type="number" value={quantity} onChange={handleEdit} />
<button onClick={() => removeIngredient(id)}>Remove</button>
<button onClick={() => addAlternative(id)}>Find Alternative</button>
```

### 3. Add Kesar Grocery

Currently supported stores:
- FreshDirect (next-day)
- Pure Indian Foods (1-2 weeks)
- Patel Brothers (varies)
- Whole Foods (2-3 days)
- Wild Alaskan Company (seafood only)

**Add**: Kesar Grocery (kesargrocery.com) - Faster than Pure Indian Foods

### 4. Store-Specific Delivery Times

```typescript
// Show delivery estimate in overlay
Pure Indian Foods (12 items)
⏰ Delivery: 1-2 weeks
💡 Order now for future use
```

### 5. User Preferences Storage

```typescript
// Save user's shopping preferences
{
  "urgency": "planning",  // or "urgent"
  "transparency_preference": "high",
  "budget_limit": null,
  "favorite_stores": ["Pure Indian Foods", "FreshDirect"],
  "dietary_restrictions": ["vegetarian"]
}
```

---

## Key Files Reference

### Backend
- **Store Split Logic**: [`src/orchestrator/store_split.py`](../../src/orchestrator/store_split.py)
- **Product Inventory**: [`src/agents/product_agent.py`](../../src/agents/product_agent.py)
- **API Endpoints**: [`api/main.py`](../../api/main.py)

### Frontend
- **Main App**: [`Figma_files/src/app/App.tsx`](../../Figma_files/src/app/App.tsx)
- **Ingredients Overlay**: [`Figma_files/src/app/components/IngredientsOverlay.tsx`](../../Figma_files/src/app/components/IngredientsOverlay.tsx)
- **Shopping Cart**: [`Figma_files/src/app/components/ShoppingCart.tsx`](../../Figma_files/src/app/components/ShoppingCart.tsx)
- **Overlay Styles**: [`Figma_files/src/styles/theme.css`](../../Figma_files/src/styles/theme.css)

### Tests
- **Store Split Tests**: [`tests/test_store_split_flow.py`](../../tests/test_store_split_flow.py)
- **API Integration Tests**: [`tests/test_api_integration.py`](../../tests/test_api_integration.py)
- **Chicken Biryani Test**: [`tests/test_chicken_biryani.py`](../../tests/test_chicken_biryani.py)
- **Test Summary**: [`tests/MULTI_STORE_TESTING_SUMMARY.md`](../../tests/MULTI_STORE_TESTING_SUMMARY.md)

---

## Conclusion

The multi-store cart system solves a real problem for conscious buyers: **How do you shop efficiently across multiple stores while staying true to your ethical values?**

By automatically routing ingredients to the right stores (fresh items to FreshDirect, specialty spices to Pure Indian Foods), applying smart efficiency rules (1-item threshold), and showing full product transparency (brand, size, sourcing), we've built a system that respects both the user's time AND their values.

**Result**: Users can cook authentic meals with high-quality, ethically-sourced ingredients without spending hours shopping across multiple stores.

---

**Next Steps**: Run the app end-to-end, test with real meal plans, and iterate based on user feedback!
