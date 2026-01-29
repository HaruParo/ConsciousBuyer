# Feature Proposal: Ingredient Confirmation Flow

## 📋 Summary

Add a two-step cart creation process:
1. **Extract** ingredients from user prompt
2. **Confirm** ingredients (editable list with store grouping)
3. **Build** cart with confirmed ingredients

---

## 🎯 User Goals

From your requirements:

1. ✅ **Editable ingredient list** - Users can modify quantities, remove items, add missing ingredients
2. ✅ **Store-based grouping** - Show which ingredients come from which stores ("garam masala from Pure Indian Foods")
3. ✅ **Empty cart improvements** - Don't show store/location until after confirmation
4. ⚠️ **Store switching** - Simplified to store selection during confirmation (see concerns below)

---

## 🏗️ Architecture Design

### Current Flow (One-Step)
```
User: "chicken biryani for 4"
  ↓
POST /api/create-cart
  ↓
[Orchestrator runs all 4 steps]
  ↓
Cart with 12 items returned
```

### Proposed Flow (Two-Step)
```
User: "chicken biryani for 4"
  ↓
POST /api/extract-ingredients
  ↓
Ingredients list returned (no products yet)
  ↓
User confirms/edits ingredients
  ↓
POST /api/create-cart (with confirmed ingredients)
  ↓
Cart with 12 items returned
```

---

## 🔧 Technical Implementation

### Backend Changes

#### 1. New Endpoint: Extract Ingredients Only

**File**: `api/main.py`

```python
@app.post("/api/extract-ingredients")
async def extract_ingredients(request: CreateCartRequest) -> ExtractIngredientsResponse:
    """
    Extract ingredients from meal plan without building cart.

    This is step 1 of 2-step cart creation:
    1. Extract ingredients (this endpoint)
    2. Confirm and build cart (existing /api/create-cart)
    """
    orch = Orchestrator(
        use_llm_extraction=True,
        use_llm_explanations=False  # Not needed yet
    )

    # Only run step 1: ingredient extraction
    orch.step_ingredients(request.meal_plan, servings=request.servings)

    # Check which stores are needed (based on product availability)
    stores_needed = determine_stores_for_ingredients(orch.state.ingredients)

    return ExtractIngredientsResponse(
        ingredients=[
            IngredientItem(
                name=ing["name"],
                quantity=ing["quantity"],
                unit=ing["unit"],
                category=ing["category"],
                store=ing.get("preferred_store", "FreshDirect")
            )
            for ing in orch.state.ingredients
        ],
        servings=request.servings or 2,
        stores_needed=stores_needed,
        primary_store="FreshDirect"
    )
```

#### 2. Modified Endpoint: Build Cart from Confirmed Ingredients

**File**: `api/main.py`

```python
@app.post("/api/create-cart")
async def create_cart(request: CreateCartRequest) -> CartResponse:
    """
    Build cart from confirmed ingredients.

    Now accepts EITHER:
    - meal_plan (string) - for backward compatibility
    - confirmed_ingredients (list) - for 2-step flow
    """
    if request.confirmed_ingredients:
        # 2-step flow: User has confirmed ingredients
        orch = Orchestrator(
            use_llm_extraction=False,  # Already extracted
            use_llm_explanations=True
        )

        # Inject confirmed ingredients directly
        orch.state.ingredients = request.confirmed_ingredients
        orch.state.stage = "ingredients_confirmed"

        # Run remaining steps
        orch.step_candidates()
        orch.step_enrich()
        bundle = orch.step_decide()
    else:
        # Original 1-step flow: Process prompt directly
        orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=True)
        bundle = orch.process_prompt(request.meal_plan, servings=request.servings)

    # ... rest of existing logic
```

#### 3. Add Store Field to Synthetic Inventory

**File**: `src/agents/product_agent.py`

```python
SIMULATED_INVENTORY: dict[str, list[dict]] = {
    "spinach": [
        {
            "id": "sp001",
            "title": "Spinach Bunch Value",
            "brand": "FreshDirect",
            "size": "10oz",
            "price": 1.99,
            "organic": False,
            "store": "FreshDirect"  # ← ADD THIS
        },
        # ...
    ],
    "garam_masala": [
        {
            "id": "gm001",
            "title": "Garam Masala",
            "brand": "Pure Indian Foods",
            "size": "3oz",
            "price": 7.99,
            "organic": True,
            "store": "Pure Indian Foods"  # ← Specialty store
        },
        # ...
    ],
    # ... rest of inventory
}
```

---

### Frontend Changes

#### 1. New Component: IngredientConfirmation

**File**: `Figma_files/src/app/components/IngredientConfirmation.tsx`

```tsx
interface IngredientConfirmationProps {
  ingredients: IngredientItem[];
  servings: number;
  storesNeeded: string[];
  primaryStore: string;
  onConfirm: (confirmed: IngredientItem[], store: string) => void;
  onCancel: () => void;
  onEdit: (index: number, updates: Partial<IngredientItem>) => void;
  onRemove: (index: number) => void;
  onAdd: () => void;
}

export function IngredientConfirmation({...}) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2>We found these ingredients:</h2>

      {/* Group by store */}
      {Object.entries(groupByStore(ingredients)).map(([store, items]) => (
        <div key={store} className="mb-6">
          <h3>{store} {store === primaryStore && "(Primary)"}</h3>

          {items.map((item, idx) => (
            <div key={idx} className="ingredient-row">
              <input
                type="checkbox"
                checked={item.included}
                onChange={() => onEdit(idx, { included: !item.included })}
              />
              <input
                value={item.quantity}
                onChange={(e) => onEdit(idx, { quantity: e.target.value })}
              />
              <select
                value={item.unit}
                onChange={(e) => onEdit(idx, { unit: e.target.value })}
              >
                <option>lb</option>
                <option>oz</option>
                <option>cup</option>
                {/* ... */}
              </select>
              <span>{item.name}</span>
              <button onClick={() => onRemove(idx)}>Remove</button>
            </div>
          ))}
        </div>
      ))}

      {/* Store preference */}
      <div className="mt-6">
        <label>Primary store:</label>
        <select value={selectedStore} onChange={...}>
          {storesNeeded.map(store => (
            <option key={store} value={store}>{store}</option>
          ))}
        </select>
      </div>

      {/* Servings */}
      <div className="mt-4">
        <label>Servings:</label>
        <input type="number" value={servings} onChange={...} />
      </div>

      <div className="mt-6 flex gap-4">
        <button onClick={onCancel}>Cancel</button>
        <button onClick={() => onConfirm(ingredients, selectedStore)}>
          Build My Cart →
        </button>
      </div>
    </div>
  );
}
```

#### 2. Update App.tsx Flow

**File**: `Figma_files/src/app/App.tsx`

```tsx
export default function App() {
  const [flowState, setFlowState] = useState<'input' | 'confirming' | 'cart'>('input');
  const [extractedIngredients, setExtractedIngredients] = useState<IngredientItem[]>([]);
  const [storesNeeded, setStoresNeeded] = useState<string[]>([]);

  const handleExtractIngredients = async () => {
    setIsLoading(true);

    // Step 1: Extract ingredients
    const response = await extractIngredients(mealPlan, servings);
    setExtractedIngredients(response.ingredients);
    setStoresNeeded(response.stores_needed);
    setFlowState('confirming');

    setIsLoading(false);
  };

  const handleConfirmIngredients = async (confirmed: IngredientItem[], store: string) => {
    setIsLoading(true);

    // Step 2: Build cart with confirmed ingredients
    const response = await createCart({
      confirmed_ingredients: confirmed,
      servings: servings,
      preferred_store: store
    });

    setCartItems(response.items);
    setCartMetadata({
      store: response.store,
      location: `${userLocation.city}, ${userLocation.state}`,
      servings: response.servings
    });
    setFlowState('cart');

    setIsLoading(false);
  };

  return (
    <div>
      {flowState === 'input' && (
        <MealPlanInput
          onSubmit={handleExtractIngredients}
          buttonText="Extract Ingredients"
        />
      )}

      {flowState === 'confirming' && (
        <IngredientConfirmation
          ingredients={extractedIngredients}
          servings={servings}
          storesNeeded={storesNeeded}
          onConfirm={handleConfirmIngredients}
          onCancel={() => setFlowState('input')}
        />
      )}

      {flowState === 'cart' && (
        <ShoppingCart
          items={cartItems}
          metadata={cartMetadata}  // Now has store info
        />
      )}
    </div>
  );
}
```

#### 3. Empty Cart State

**File**: `Figma_files/src/app/components/ShoppingCart.tsx`

```tsx
export function ShoppingCart({ items, metadata, ... }) {
  // Empty state: no metadata shown
  if (items.length === 0) {
    return (
      <div className="empty-cart">
        <p>Your cart is empty</p>
        <p>Enter a meal plan to get started</p>
        {/* NO store/location shown here */}
      </div>
    );
  }

  // Full cart: show metadata
  return (
    <div>
      {/* Header with store info */}
      <div className="cart-header">
        <h2>{metadata.store}</h2>
        <p>{metadata.location}</p>
        <p>{metadata.servings} servings</p>
      </div>

      {/* Cart items */}
      {items.map(item => <CartItem key={item.id} {...item} />)}
    </div>
  );
}
```

---

## 🎨 UI Mockup

### Ingredient Confirmation Screen

```
┌─────────────────────────────────────────────────────────────┐
│                  Confirm Your Ingredients                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  We found these ingredients for "chicken biryani for 4":   │
│                                                             │
│  FreshDirect (Primary Store)                               │
│  ┌───────────────────────────────────────────────────┐    │
│  │ ☑  2.0  lb   Chicken                     [Edit] [×] │    │
│  │ ☑  2.0  cups Basmati Rice                [Edit] [×] │    │
│  │ ☑  2.0  large Onions                     [Edit] [×] │    │
│  │ ☑  0.5  cup  Yogurt                      [Edit] [×] │    │
│  │ ☑  1.0  inch Ginger                      [Edit] [×] │    │
│  │ ☑  6.0  cloves Garlic                    [Edit] [×] │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
│  Pure Indian Foods (Specialty Items)                       │
│  ┌───────────────────────────────────────────────────┐    │
│  │ ☑  2.0  tsp  Garam Masala                [Edit] [×] │    │
│  │ ☑  1.0  pinch Saffron                    [Edit] [×] │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
│  [+ Add ingredient]                                        │
│                                                             │
│  ─────────────────────────────────────────────────────    │
│                                                             │
│  Primary Store: [FreshDirect ▼]                           │
│  Servings: [4 ▼]                                           │
│                                                             │
│  ℹ️  Multiple stores needed for specialty items            │
│                                                             │
│         [← Back]              [Build My Cart →]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Concerns & Trade-offs

### 1. **Store Switching After Cart Built**

**Your original request**: "Allow store switching to see cart from different store"

**My concern**: This is very complex because:
- Different stores = different products available
- Different prices, different brands
- Would need to re-run entire orchestrator
- Need to store multiple cart versions

**My recommendation**:
- ✅ **Allow store selection BEFORE cart is built** (in confirmation step)
- ❌ **Don't allow switching AFTER cart is built**
- Alternative: Show "Also available at ShopRite" with a "Rebuild with ShopRite" button that restarts the flow

**Your decision needed**: Accept this limitation or we need to scope a much larger feature?

---

### 2. **Multi-Store Inventory**

**Current reality**: All products in one `SIMULATED_INVENTORY` dict

**For demo**: We can fake it by adding `"store": "FreshDirect"` field to each product

**For production**: Would need:
- Store-specific product catalogs
- Store availability checks
- Store distance calculations
- Multi-store checkout flow

**My recommendation**:
- ✅ For hackathon demo: Fake it with store field
- ⏰ For production: Major refactor needed later

**Your decision needed**: Is faking it OK for demo?

---

### 3. **Ingredient Editing Complexity**

**Simple edits are easy**:
- ✅ Change quantity: 2 lbs → 3 lbs
- ✅ Remove ingredient: uncheck cilantro
- ✅ Change unit: cups → oz

**Complex edits are hard**:
- ❌ Add entirely new ingredient: "I want to add turmeric"
  - Need to determine quantity for servings
  - Need to find products for it
  - Need to re-run safety/seasonal checks
- ❌ Change ingredient name: "chicken" → "turkey"
  - Essentially a new ingredient search

**My recommendation**:
- ✅ Support simple edits (quantity, remove)
- ⚠️ For adding new ingredients: Let user go back to input step

**Your decision needed**: How complex should editing be?

---

## 📊 Testing Strategy

Following your 3-layer approach:

### Layer 1: Unit Tests (0 tokens)
```python
def test_ingredient_confirmation_flow():
    """Test 2-step flow without LLM."""
    orch = Orchestrator(use_llm=False)

    # Step 1: Extract
    orch.step_ingredients("chicken biryani for 4", servings=4)
    ingredients = orch.state.ingredients
    assert len(ingredients) >= 10

    # Step 2: User edits (simulation)
    ingredients[0]["quantity"] = 3.0  # Change chicken to 3 lbs

    # Step 3: Confirm
    orch.confirm_ingredients()

    # Step 4: Build cart
    orch.step_candidates()
    orch.step_enrich()
    bundle = orch.step_decide()

    assert bundle.item_count >= 10
```

### Layer 2: Integration Tests (Haiku + cache)
```python
def test_extract_ingredients_with_llm():
    """Test ingredient extraction with LLM (Haiku)."""
    response = await extract_ingredients(
        meal_plan="something healthy with chicken",
        model="claude-haiku-20250514"
    )
    assert len(response.ingredients) >= 5
```

### Layer 3: E2E Tests (Full LLM)
```python
@pytest.mark.expensive
def test_full_confirmation_flow():
    """Test complete 2-step flow with Sonnet."""
    # Extract
    ingredients = await extract_ingredients("chicken biryani for 4")

    # Edit
    ingredients[0].quantity = 3.0

    # Build
    cart = await create_cart(confirmed_ingredients=ingredients)

    assert cart.item_count >= 10
```

---

## 📋 Implementation Checklist

### Phase 1: Backend (2-3 hours)
- [ ] Add `POST /api/extract-ingredients` endpoint
- [ ] Modify `POST /api/create-cart` to accept `confirmed_ingredients`
- [ ] Add `"store"` field to synthetic inventory
- [ ] Create `determine_stores_for_ingredients()` helper
- [ ] Test endpoints manually with curl/Postman

### Phase 2: Frontend (3-4 hours)
- [ ] Create `IngredientConfirmation.tsx` component
- [ ] Add ingredient editing (quantity, unit, remove)
- [ ] Group ingredients by store in UI
- [ ] Add store selector dropdown
- [ ] Update `App.tsx` to handle 3-state flow (input → confirming → cart)
- [ ] Update empty cart state (hide metadata)
- [ ] Add loading states for extraction step

### Phase 3: Polish (1-2 hours)
- [ ] Add error handling for extraction failures
- [ ] Add "Back to edit" button from cart
- [ ] Show ingredient count badge ("8 ingredients")
- [ ] Add tooltips for store grouping
- [ ] Test on mobile viewport

### Phase 4: Testing (1 hour)
- [ ] Write Layer 1 unit tests (template mode)
- [ ] Test manually with 5 different meal plans
- [ ] Test edge cases (0 ingredients, 20 ingredients)
- [ ] Test store grouping display

**Total estimate**: 7-10 hours

---

## 🤔 Questions for You

1. **Store switching**: Accept limitation that you choose store BEFORE cart is built, not after?

2. **Multi-store demo**: OK to fake it with store field for now?

3. **Ingredient editing**: Simple edits only (quantity/remove) or full add/edit capability?

4. **API design**: Should `/api/extract-ingredients` be a separate endpoint or a parameter on `/api/create-cart`?

5. **UI flow**: After cart is built, should there be a "Back to Edit Ingredients" button?

6. **Store priority**: If ingredient is available at multiple stores, how to decide which store to show?

---

## 🚀 Next Steps

1. **You review this proposal**
2. **You answer the 6 questions above**
3. **You approve/reject/modify the task list**
4. **I start implementation**

---

Please let me know:
- ✅ What you approve
- ⚠️ What needs modification
- ❌ What to remove/simplify

I'll wait for your feedback before starting implementation!
