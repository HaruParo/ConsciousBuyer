# Simple Multi-Store Flow

## Core Principle

**LLM decides the most efficient way to split products across stores** - not the user.

User just:
1. Sees ingredient list grouped by store
2. Taps a store name to view that store's cart
3. One cart at a time on the right side

---

## User Flow

### Step 1: User enters meal plan
```
User: "chicken biryani for 4"
  ↓
POST /api/extract-ingredients
```

### Step 2: LLM decides optimal store split
```
LLM Analysis:
- 6 ingredients available at FreshDirect ✓
- 2 ingredients only at Pure Indian Foods
- Decision: Use FreshDirect (primary) + Pure Indian Foods (specialty)

Response:
{
  "ingredients": [...],
  "store_split": {
    "primary_store": "FreshDirect",
    "stores": [
      {
        "store": "FreshDirect",
        "ingredients": ["chicken", "rice", "onions", "yogurt", "ginger", "garlic"],
        "count": 6,
        "is_primary": true
      },
      {
        "store": "Pure Indian Foods",
        "ingredients": ["garam_masala", "saffron"],
        "count": 2,
        "is_primary": false
      }
    ]
  }
}
```

### Step 3: Ingredient confirmation overlay
```
┌─────────────────────────────────────────────────────┐
│  Confirm Ingredients for Chicken Biryani      [× ] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🛒 FRESHDIRECT (Primary - 6 items)                │
│  ┌────────────────────────────────────────────┐   │
│  │ ☑  2.0  lb    Chicken Thighs                │   │
│  │ ☑  2.0  cups  Basmati Rice                  │   │
│  │ ☑  2.0  large Yellow Onions                 │   │
│  │ ☑  0.5  cup   Greek Yogurt                  │   │
│  │ ☑  1.0  inch  Ginger Root                   │   │
│  │ ☑  6.0  cloves Garlic                       │   │
│  └────────────────────────────────────────────┘   │
│                                                     │
│  🏪 PURE INDIAN FOODS (Specialty - 2 items)        │
│  ┌────────────────────────────────────────────┐   │
│  │ ☑  2.0  tsp   Organic Garam Masala          │   │
│  │ ☑  1.0  pinch Saffron Threads               │   │
│  └────────────────────────────────────────────┘   │
│                                                     │
│  ℹ️  You'll need to checkout from 2 stores         │
│                                                     │
│  Servings: [4 ▼]                                   │
│                                                     │
│         [Cancel]        [Build Carts →]           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Step 4: User confirms → Build both carts

API call builds BOTH carts but shows primary first:

```
POST /api/create-cart
{
  "confirmed_ingredients": [...],
  "servings": 4
}

Response:
{
  "carts": [
    {
      "store": "FreshDirect",
      "is_primary": true,
      "items": [6 products],
      "total": 28.47
    },
    {
      "store": "Pure Indian Foods",
      "is_primary": false,
      "items": [2 products],
      "total": 22.98
    }
  ],
  "current_cart": "FreshDirect",  // Show this first
  "total_all_carts": 51.45
}
```

### Step 5: Cart displays (FreshDirect - Primary)

```
┌─────────────────────────────────────────────┐
│ 🛒 Your Cart                                │
│ FreshDirect • Edison, NJ • 4 servings      │
│                                             │
│ [📋 Ingredients]  [Share]                  │
├─────────────────────────────────────────────┤
│                                             │
│ [6 cart items from FreshDirect...]         │
│                                             │
│ Cart Total: $28.47                         │
│                                             │
│ ⚠️  Additional items from other stores:     │
│    Pure Indian Foods: $22.98               │
│    [View ingredients →]                    │
│                                             │
│ Grand Total (All Stores): $51.45          │
└─────────────────────────────────────────────┘
```

### Step 6: User clicks "📋 Ingredients" → Overlay opens

```
┌─────────────────────────────────────────────────────┐
│  📋 Ingredients for Chicken Biryani          [× ]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🛒 FRESHDIRECT (6 items) ← You are here          │
│  ┌────────────────────────────────────────────┐   │
│  │ ☑  Chicken Thighs (2 lb) - $4.49           │   │
│  │ ☑  Basmati Rice (2 cups) - $3.49           │   │
│  │ ☑  Yellow Onions (2 large) - $1.99         │   │
│  │ ☑  Greek Yogurt (0.5 cup) - $3.49          │   │
│  │ ☑  Ginger Root (1 inch) - $1.99            │   │
│  │ ☑  Garlic (6 cloves) - $1.49               │   │
│  │                                            │   │
│  │ Cart Total: $28.47                         │   │
│  └────────────────────────────────────────────┘   │
│                                                     │
│  🏪 PURE INDIAN FOODS (2 items)                    │
│  [Tap to view this cart →]                        │
│  ┌────────────────────────────────────────────┐   │
│  │ ☑  Organic Garam Masala (2 tsp) - $7.99    │   │
│  │ ☑  Saffron Threads (1 pinch) - $14.99      │   │
│  │                                            │   │
│  │ Cart Total: $22.98                         │   │
│  └────────────────────────────────────────────┘   │
│                                                     │
│  Grand Total: $51.45                               │
│                                                     │
│  [Download Shopping List]  [Close]                │
└─────────────────────────────────────────────────────┘
```

### Step 7: User taps "PURE INDIAN FOODS" section

Cart on right side **switches** to show Pure Indian Foods products:

```
┌─────────────────────────────────────────────┐
│ 🛒 Your Cart                                │
│ Pure Indian Foods • Online                  │
│                                             │
│ [📋 Ingredients]  [Share]                  │
├─────────────────────────────────────────────┤
│                                             │
│ [2 cart items from Pure Indian Foods...]   │
│                                             │
│ Cart Total: $22.98                         │
│                                             │
│ ⚠️  You also have a cart at:                │
│    FreshDirect: $28.47                     │
│    [View ingredients →]                    │
│                                             │
│ Grand Total (All Stores): $51.45          │
└─────────────────────────────────────────────┘
```

---

## LLM Prompt for Store Split Decision

When extracting ingredients, LLM decides optimal split:

```python
STORE_SPLIT_PROMPT = """
Given these ingredients for "{meal_plan}":
{ingredients_list}

And these available stores near {user_location}:
- FreshDirect (primary grocery, most items, local)
- ShopRite (grocery chain)
- Whole Foods (premium, organic)
- Pure Indian Foods (specialty spices/ingredients)
- Patel Brothers (ethnic grocery)

Decide the MOST EFFICIENT way to split this shopping across stores.

Rules:
1. Minimize number of stores (prefer 1 store if possible)
2. Use specialty stores ONLY if items unavailable at primary
3. Primary store should have the majority of items
4. Consider item type (fresh produce vs shelf-stable spices)

Return JSON:
{{
  "primary_store": "FreshDirect",
  "stores": [
    {{
      "store": "FreshDirect",
      "ingredients": ["chicken", "rice", "onions", ...],
      "reason": "Main grocery items, fresh produce available",
      "count": 6
    }},
    {{
      "store": "Pure Indian Foods",
      "ingredients": ["garam_masala", "saffron"],
      "reason": "Specialty Indian spices not available at primary store",
      "count": 2
    }}
  ],
  "total_stores": 2,
  "efficiency_note": "Using 2 stores: FreshDirect for fresh ingredients, Pure Indian Foods for authentic spices"
}}
"""
```

---

## Backend Implementation

### 1. Update Extract Ingredients Endpoint

**File**: `api/main.py`

```python
@app.post("/api/extract-ingredients")
async def extract_ingredients(request: CreateCartRequest) -> ExtractIngredientsResponse:
    """
    Extract ingredients AND decide optimal store split.

    LLM analyzes:
    1. What ingredients are needed
    2. Which stores have them
    3. Most efficient split (minimize stores)
    """

    orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=False)

    # Extract ingredients
    orch.step_ingredients(request.meal_plan, servings=request.servings)

    # Let LLM decide store split
    store_split = decide_optimal_store_split(
        ingredients=orch.state.ingredients,
        user_location=request.user_location
    )

    return ExtractIngredientsResponse(
        ingredients=orch.state.ingredients,
        servings=request.servings or 2,
        store_split=store_split,
        primary_store=store_split["primary_store"]
    )


def decide_optimal_store_split(ingredients: list[dict], user_location: str) -> dict:
    """
    Use LLM to decide optimal store split.

    Returns:
    {
      "primary_store": "FreshDirect",
      "stores": [
        {
          "store": "FreshDirect",
          "ingredients": ["chicken", "rice", ...],
          "count": 6,
          "is_primary": true
        },
        {
          "store": "Pure Indian Foods",
          "ingredients": ["garam_masala", "saffron"],
          "count": 2,
          "is_primary": false
        }
      ],
      "total_stores": 2
    }
    """
    # Check availability of each ingredient across stores
    ingredient_availability = {}

    for ing in ingredients:
        available_stores = check_which_stores_have(ing["name"])
        ingredient_availability[ing["name"]] = available_stores

    # Use LLM to decide split
    prompt = STORE_SPLIT_PROMPT.format(
        meal_plan=request.meal_plan,
        ingredients_list=format_ingredients(ingredients),
        user_location=user_location
    )

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )

    return json.loads(response.content[0].text)
```

### 2. Build Multiple Carts

**File**: `api/main.py`

```python
@app.post("/api/create-cart")
async def create_cart(request: CreateCartRequest) -> MultiCartResponse:
    """
    Build carts for each store in the split.

    Returns:
    {
      "carts": [
        {"store": "FreshDirect", "items": [...], "total": 28.47},
        {"store": "Pure Indian Foods", "items": [...], "total": 22.98}
      ],
      "current_cart": "FreshDirect",
      "total_all_carts": 51.45
    }
    """

    carts = []

    # Build cart for each store
    for store_info in request.store_split["stores"]:
        store_name = store_info["store"]
        store_ingredients = store_info["ingredients"]

        # Filter ingredients for this store
        ingredients_for_store = [
            ing for ing in request.confirmed_ingredients
            if ing["name"] in store_ingredients
        ]

        # Build cart for this store
        orch = Orchestrator(use_llm_extraction=False, use_llm_explanations=True)
        orch.state.ingredients = ingredients_for_store
        orch.state.stage = "ingredients_confirmed"

        # Override store preference
        orch.state.user_prefs.preferred_store = store_name

        orch.step_candidates()
        orch.step_enrich()
        bundle = orch.step_decide()

        # Convert to cart items
        cart_items = [map_decision_to_cart_item(item, ...) for item in bundle.items]

        carts.append({
            "store": store_name,
            "is_primary": store_info["is_primary"],
            "items": cart_items,
            "total": sum(item["price"] * item["quantity"] for item in cart_items),
            "item_count": len(cart_items)
        })

    # Calculate grand total
    total_all_carts = sum(cart["total"] for cart in carts)

    # Primary store is shown first
    primary_store = next(cart["store"] for cart in carts if cart["is_primary"])

    return MultiCartResponse(
        carts=carts,
        current_cart=primary_store,
        total_all_carts=total_all_carts,
        servings=request.servings
    )
```

---

## Frontend Implementation

### 1. Update App.tsx State

**File**: `Figma_files/src/app/App.tsx`

```tsx
export default function App() {
  const [flowState, setFlowState] = useState<'input' | 'confirming' | 'cart'>('input');

  // Multi-cart state
  const [carts, setCarts] = useState<CartData[]>([]);
  const [currentCart, setCurrentCart] = useState<string>('FreshDirect');
  const [storeSplit, setStoreSplit] = useState<StoreSplit | null>(null);

  const handleExtractIngredients = async () => {
    const response = await extractIngredients(mealPlan, servings);

    setExtractedIngredients(response.ingredients);
    setStoreSplit(response.store_split);  // LLM decided split
    setFlowState('confirming');
  };

  const handleConfirmIngredients = async (confirmed: IngredientItem[]) => {
    const response = await createCart({
      confirmed_ingredients: confirmed,
      store_split: storeSplit,  // Pass LLM's decision
      servings: servings
    });

    setCarts(response.carts);  // Array of carts (one per store)
    setCurrentCart(response.current_cart);  // Start with primary
    setFlowState('cart');
  };

  const handleSwitchStore = (storeName: string) => {
    setCurrentCart(storeName);
    setShowIngredientsOverlay(false);
  };

  // Get currently displayed cart
  const activeCart = carts.find(c => c.store === currentCart);
  const otherCarts = carts.filter(c => c.store !== currentCart);

  return (
    <div>
      {flowState === 'cart' && (
        <ShoppingCart
          cart={activeCart}
          otherCarts={otherCarts}
          allIngredients={extractedIngredients}
          storeSplit={storeSplit}
          onSwitchStore={handleSwitchStore}
        />
      )}
    </div>
  );
}
```

### 2. Ingredient Confirmation Component

**File**: `Figma_files/src/app/components/IngredientConfirmation.tsx`

```tsx
export function IngredientConfirmation({
  ingredients,
  servings,
  storeSplit,  // LLM's decision
  onConfirm,
  onCancel
}: IngredientConfirmationProps) {

  // Group ingredients by store (based on LLM decision)
  const ingredientsByStore = storeSplit.stores.map(storeInfo => ({
    store: storeInfo.store,
    isPrimary: storeInfo.is_primary,
    count: storeInfo.count,
    ingredients: ingredients.filter(ing =>
      storeInfo.ingredients.includes(ing.name)
    )
  }));

  const primaryStore = ingredientsByStore.find(s => s.isPrimary);
  const secondaryStores = ingredientsByStore.filter(s => !s.isPrimary);

  return (
    <div className="ingredient-confirmation-overlay">
      <div className="confirmation-modal">
        <h2>Confirm Ingredients for {mealPlan}</h2>

        {/* Primary store */}
        <section className="store-section primary">
          <h3>🛒 {primaryStore.store.toUpperCase()} (Primary - {primaryStore.count} items)</h3>
          <div className="ingredient-list">
            {primaryStore.ingredients.map(ing => (
              <IngredientRow key={ing.name} ingredient={ing} editable />
            ))}
          </div>
        </section>

        {/* Secondary stores */}
        {secondaryStores.map(storeInfo => (
          <section key={storeInfo.store} className="store-section secondary">
            <h3>🏪 {storeInfo.store.toUpperCase()} (Specialty - {storeInfo.count} items)</h3>
            <div className="ingredient-list">
              {storeInfo.ingredients.map(ing => (
                <IngredientRow key={ing.name} ingredient={ing} editable />
              ))}
            </div>
          </section>
        ))}

        {/* Info about multiple stores */}
        {secondaryStores.length > 0 && (
          <div className="multi-store-info">
            ℹ️ You'll need to checkout from {storeSplit.total_stores} stores
          </div>
        )}

        <div className="actions">
          <button onClick={onCancel}>Cancel</button>
          <button onClick={() => onConfirm(ingredients)}>
            Build Carts →
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 3. Shopping Cart Component

**File**: `Figma_files/src/app/components/ShoppingCart.tsx`

```tsx
export function ShoppingCart({
  cart,           // Current cart being displayed
  otherCarts,     // Other carts from other stores
  allIngredients, // All ingredients across all stores
  storeSplit,     // LLM's store split decision
  onSwitchStore
}: ShoppingCartProps) {
  const [showIngredientsOverlay, setShowIngredientsOverlay] = useState(false);

  const totalAllCarts = cart.total + otherCarts.reduce((sum, c) => sum + c.total, 0);

  return (
    <div className="shopping-cart">
      {/* Header */}
      <div className="cart-header">
        <h2>{cart.store}</h2>
        <p>{cart.location} • {cart.servings} servings</p>

        <div className="cart-actions">
          <button onClick={() => setShowIngredientsOverlay(true)}>
            📋 Ingredients
          </button>
          <button>Share</button>
        </div>
      </div>

      {/* Cart items */}
      <div className="cart-items">
        {cart.items.map(item => <CartItem key={item.id} {...item} />)}
      </div>

      {/* Cart total */}
      <div className="cart-total">
        <div className="this-store">
          Cart Total: ${cart.total.toFixed(2)}
        </div>

        {/* Show other carts */}
        {otherCarts.length > 0 && (
          <div className="other-carts-reminder">
            <h4>⚠️ Additional items from other stores:</h4>
            {otherCarts.map(otherCart => (
              <div key={otherCart.store} className="other-cart-link">
                <span>{otherCart.store}: ${otherCart.total.toFixed(2)}</span>
                <button onClick={() => setShowIngredientsOverlay(true)}>
                  View ingredients →
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Grand total */}
        <div className="grand-total">
          Grand Total (All Stores): ${totalAllCarts.toFixed(2)}
        </div>
      </div>

      {/* Ingredients overlay */}
      {showIngredientsOverlay && (
        <IngredientsOverlay
          allIngredients={allIngredients}
          storeSplit={storeSplit}
          currentStore={cart.store}
          carts={[cart, ...otherCarts]}
          onSwitchStore={onSwitchStore}
          onClose={() => setShowIngredientsOverlay(false)}
        />
      )}
    </div>
  );
}
```

### 4. Ingredients Overlay

**File**: `Figma_files/src/app/components/IngredientsOverlay.tsx`

```tsx
export function IngredientsOverlay({
  allIngredients,
  storeSplit,
  currentStore,
  carts,
  onSwitchStore,
  onClose
}: IngredientsOverlayProps) {

  // Group ingredients by store
  const storeGroups = storeSplit.stores.map(storeInfo => {
    const storeIngredients = allIngredients.filter(ing =>
      storeInfo.ingredients.includes(ing.name)
    );

    const cartForStore = carts.find(c => c.store === storeInfo.store);
    const isActive = storeInfo.store === currentStore;

    return {
      store: storeInfo.store,
      isPrimary: storeInfo.is_primary,
      ingredients: storeIngredients,
      cart: cartForStore,
      isActive
    };
  });

  const totalAllCarts = carts.reduce((sum, c) => sum + c.total, 0);

  return (
    <div className="ingredients-overlay" onClick={onClose}>
      <div className="overlay-content" onClick={(e) => e.stopPropagation()}>
        <div className="overlay-header">
          <h2>📋 Ingredients</h2>
          <button onClick={onClose}>×</button>
        </div>

        {/* Store groups */}
        {storeGroups.map(group => (
          <div
            key={group.store}
            className={`store-group ${group.isActive ? 'active' : ''}`}
            onClick={() => !group.isActive && onSwitchStore(group.store)}
          >
            <div className="store-header">
              <h3>
                {group.isPrimary ? '🛒' : '🏪'} {group.store.toUpperCase()}
                {group.isActive && ' ← You are here'}
              </h3>
              {!group.isActive && (
                <span className="tap-to-view">Tap to view this cart →</span>
              )}
            </div>

            <div className="ingredient-list">
              {group.ingredients.map(ing => (
                <div key={ing.name} className="ingredient-row">
                  <span className="check">☑</span>
                  <span className="quantity">{ing.quantity} {ing.unit}</span>
                  <span className="name">{ing.name}</span>
                  {group.cart && (
                    <span className="price">
                      ${group.cart.items.find(item =>
                        item.ingredientName === ing.name
                      )?.price || '?'}
                    </span>
                  )}
                </div>
              ))}
            </div>

            {group.cart && (
              <div className="store-total">
                Cart Total: ${group.cart.total.toFixed(2)}
              </div>
            )}
          </div>
        ))}

        {/* Grand total */}
        <div className="grand-total">
          Grand Total: ${totalAllCarts.toFixed(2)}
        </div>

        <div className="overlay-footer">
          <button onClick={handleDownload}>Download Shopping List</button>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
```

---

## CSS for Overlay

**File**: `Figma_files/src/styles/ingredients-overlay.css`

```css
.ingredients-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.overlay-content {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.store-group {
  margin: 1rem;
  padding: 1rem;
  border: 2px solid #e5c7a1;
  border-radius: 8px;
  background: #f5e6d3;
  cursor: pointer;
  transition: all 0.2s;
}

.store-group:hover:not(.active) {
  background: #f5d7b1;
  border-color: #dd9057;
}

.store-group.active {
  background: white;
  border-color: #dd9057;
  border-width: 3px;
  cursor: default;
}

.store-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.tap-to-view {
  font-size: 0.875rem;
  color: #dd9057;
  font-weight: 500;
}

.ingredient-list {
  margin: 0.5rem 0;
}

.ingredient-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.25rem 0;
  font-size: 0.9rem;
}

.grand-total {
  padding: 1.5rem;
  background: #f5e6d3;
  font-size: 1.25rem;
  font-weight: bold;
  text-align: center;
  border-top: 2px solid #e5c7a1;
}
```

---

## Summary of Changes

### ✅ What Changed from Previous Design

1. **No store comparison** - LLM decides, not user
2. **Ingredient list is overlay** - Not slide-in panel
3. **One cart at a time** - Right side shows only current store
4. **Tap store to switch** - In overlay, tap store name → cart switches
5. **LLM decides split** - Optimal 1-2 store split based on availability

### ✅ User Flow

```
1. Enter meal plan
2. See confirmation (ingredients grouped by LLM-chosen stores)
3. Confirm → Both carts built, FreshDirect shown first
4. Click "📋 Ingredients" → Overlay shows all ingredients by store
5. Tap "Pure Indian Foods" → Cart switches to show Pure Indian Foods items
6. Grand total shown across all stores
```

### ✅ Benefits

- **Simpler** - No complex store comparison UI
- **Smarter** - LLM chooses most efficient split
- **Cleaner** - One cart at a time, easy to understand
- **Faster** - Tap store name to switch, no confirmation needed
- **Honest** - Shows grand total across all stores upfront

---

## Updated Task List

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Get user approval on simplified multi-store design", "status": "in_progress", "activeForm": "Getting user approval"}, {"content": "Backend: Add LLM prompt for optimal store split decision", "status": "pending", "activeForm": "Adding store split LLM logic"}, {"content": "Backend: Update extract-ingredients to include LLM store split", "status": "pending", "activeForm": "Updating extract-ingredients endpoint"}, {"content": "Backend: Modify create-cart to build multiple carts (one per store)", "status": "pending", "activeForm": "Building multi-cart support"}, {"content": "Backend: Add store availability checking for each ingredient", "status": "pending", "activeForm": "Adding availability logic"}, {"content": "Frontend: Create IngredientsOverlay component (modal/dialog)", "status": "pending", "activeForm": "Creating IngredientsOverlay"}, {"content": "Frontend: Show ingredients grouped by store in overlay", "status": "pending", "activeForm": "Grouping by store in overlay"}, {"content": "Frontend: Add tap-to-switch store functionality", "status": "pending", "activeForm": "Adding store tap switching"}, {"content": "Frontend: Update IngredientConfirmation to show LLM store split", "status": "pending", "activeForm": "Updating confirmation screen"}, {"content": "Frontend: Update App.tsx for multi-cart state management", "status": "pending", "activeForm": "Adding multi-cart state"}, {"content": "Frontend: Update ShoppingCart to show current store only", "status": "pending", "activeForm": "Updating cart display"}, {"content": "Frontend: Add other stores reminder section in cart", "status": "pending", "activeForm": "Adding other stores reminder"}, {"content": "Frontend: Show grand total across all stores", "status": "pending", "activeForm": "Adding grand total display"}, {"content": "Add overlay CSS with backdrop and click-outside-to-close", "status": "pending", "activeForm": "Adding overlay styles"}, {"content": "Write Layer 1 unit tests for store split logic", "status": "pending", "activeForm": "Writing unit tests"}, {"content": "Test multi-store flow with various meal plans", "status": "pending", "activeForm": "Testing multi-store flow"}]