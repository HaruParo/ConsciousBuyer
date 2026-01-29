# Cart Ingredients Panel Design

## Overview

Replace the "Download list" button in the cart with an "Ingredients" button that opens a side panel showing:
1. All ingredients grouped by store and availability
2. Store switcher to rebuild cart from different stores
3. Quick access to external purchase links for unavailable items

---

## UI Design

### Cart Header (Updated)

**Before:**
```
┌─────────────────────────────────────────────┐
│ 🛒 Your Cart                                │
│ FreshDirect • Edison, NJ • 4 servings      │
│                                             │
│ [Download list ↓]  [Share]                 │
└─────────────────────────────────────────────┘
```

**After:**
```
┌─────────────────────────────────────────────┐
│ 🛒 Your Cart                                │
│ FreshDirect • Edison, NJ • 4 servings      │
│                                             │
│ [📋 Ingredients]  [Switch Store ▼]  [Share]│
└─────────────────────────────────────────────┘
```

---

## Ingredients Side Panel

### Panel Layout

```
┌─────────────────────────────────────────────────────┐
│ 📋 Ingredients for Chicken Biryani      [× Close]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 🏪 Store View: [By Store ▼] [By Availability]     │
│                                                     │
│ ─────────────────────────────────────────────────  │
│                                                     │
│ ✅ FROM FRESHDIRECT (6 items)                      │
│ ┌─────────────────────────────────────────────┐   │
│ │ ☑  2.0  lb    Chicken Thighs                │   │
│ │ ☑  2.0  cups  Basmati Rice                  │   │
│ │ ☑  2.0  large Yellow Onions                 │   │
│ │ ☑  0.5  cup   Greek Yogurt                  │   │
│ │ ☑  1.0  inch  Ginger Root                   │   │
│ │ ☑  6.0  cloves Garlic                       │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ⚠️  FROM OTHER STORES (2 items)                    │
│ ┌─────────────────────────────────────────────┐   │
│ │ ⚠️  2.0  tsp   Garam Masala                  │   │
│ │    Not available at FreshDirect              │   │
│ │    🛒 [Buy on Pure Indian Foods $7.99]       │   │
│ │    🛒 [Buy on Amazon $6.49]                  │   │
│ │                                              │   │
│ │ ⚠️  1.0  pinch Saffron Threads               │   │
│ │    Not available at FreshDirect              │   │
│ │    🛒 [Buy on Amazon $14.99]                 │   │
│ │    🛒 [Buy on Whole Foods $18.99]            │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ─────────────────────────────────────────────────  │
│                                                     │
│ 🔄 Switch Primary Store:                           │
│ ┌─────────────────────────────────────────────┐   │
│ │ Current: FreshDirect ✓                       │   │
│ │ Available alternatives:                       │   │
│ │  • ShopRite (10 mins away)                   │   │
│ │    → 8 items available, 0 unavailable        │   │
│ │    → Estimated total: $32.50                 │   │
│ │    [Rebuild with ShopRite →]                │   │
│ │                                              │   │
│ │  • Whole Foods (15 mins away)                │   │
│ │    → 8 items available, 0 unavailable        │   │
│ │    → Estimated total: $45.20                 │   │
│ │    [Rebuild with Whole Foods →]             │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ─────────────────────────────────────────────────  │
│                                                     │
│ [Download PDF Recipe Card]  [Print Checklist]     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Two View Modes

### View 1: By Store (Default)

Groups ingredients by which store they come from:

```
✅ FROM FRESHDIRECT (6 items)
  • Chicken (2 lb)
  • Basmati rice (2 cups)
  • Onions (2 large)
  • Yogurt (0.5 cup)
  • Ginger (1 inch)
  • Garlic (6 cloves)

⚠️  FROM OTHER STORES (2 items)
  • Garam masala (2 tsp) → Pure Indian Foods, Amazon
  • Saffron (1 pinch) → Amazon, Whole Foods
```

### View 2: By Availability

Groups by availability status:

```
✅ IN YOUR CART (6 items)
  • Chicken (2 lb) - FreshDirect $4.49
  • Basmati rice (2 cups) - FreshDirect $3.49
  • Onions (2 large) - FreshDirect $1.99
  • Yogurt (0.5 cup) - FreshDirect $3.49
  • Ginger (1 inch) - FreshDirect $1.99
  • Garlic (6 cloves) - FreshDirect $1.49

⚠️  NEEDS SEPARATE PURCHASE (2 items)
  • Garam masala (2 tsp)
    → [Pure Indian Foods $7.99]
    → [Amazon $6.49]
  • Saffron (1 pinch)
    → [Amazon $14.99]
    → [Whole Foods $18.99]
```

---

## Store Switching Flow

### Current Implementation

**Panel shows:**
```
🔄 Switch Primary Store:

Current: FreshDirect ✓

Available alternatives:
┌─────────────────────────────────────┐
│ ShopRite (10 mins away)             │
│ → 8/8 items available               │
│ → Estimated: $32.50 vs $28.47       │
│ → 14% more expensive                │
│                                     │
│ [Rebuild Cart with ShopRite →]     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Whole Foods (15 mins away)          │
│ → 8/8 items available (inc. saffron!)│
│ → Estimated: $45.20 vs $28.47       │
│ → 59% more expensive                │
│ → ✨ All specialty items available  │
│                                     │
│ [Rebuild Cart with Whole Foods →]  │
└─────────────────────────────────────┘
```

### User Clicks "Rebuild with ShopRite"

**Flow:**
```
1. Show confirmation modal:
   ┌────────────────────────────────────┐
   │ Switch to ShopRite?                │
   ├────────────────────────────────────┤
   │ This will rebuild your entire cart │
   │ with products from ShopRite.       │
   │                                    │
   │ Current (FreshDirect): $28.47      │
   │ New (ShopRite): ~$32.50            │
   │                                    │
   │ Changes:                           │
   │ • Different brands available       │
   │ • Different prices                 │
   │ • Same 8 items                     │
   │                                    │
   │  [Cancel]    [Switch to ShopRite] │
   └────────────────────────────────────┘

2. User confirms → Show loading

3. Call API: POST /api/create-cart
   {
     "confirmed_ingredients": [...],
     "preferred_store": "ShopRite"
   }

4. Replace cart with new items from ShopRite

5. Update cart header:
   "ShopRite • Edison, NJ • 4 servings"
```

---

## Backend API Changes

### 1. Add Store Comparison Endpoint

**New endpoint**: `GET /api/compare-stores`

```python
@app.get("/api/compare-stores")
async def compare_stores(
    ingredients: list[str],
    current_store: str,
    user_location: str
) -> StoreComparisonResponse:
    """
    Compare availability and pricing across stores.

    Returns:
    {
      "comparisons": [
        {
          "store": "ShopRite",
          "distance_miles": 3.2,
          "drive_time_mins": 10,
          "items_available": 8,
          "items_unavailable": 0,
          "estimated_total": 32.50,
          "price_difference_percent": 14,
          "specialty_items_available": ["garam_masala", "saffron"],
          "can_fulfill_all": true
        },
        {
          "store": "Whole Foods",
          "distance_miles": 5.1,
          "drive_time_mins": 15,
          "items_available": 8,
          "items_unavailable": 0,
          "estimated_total": 45.20,
          "price_difference_percent": 59,
          "specialty_items_available": ["garam_masala", "saffron"],
          "can_fulfill_all": true
        }
      ]
    }
    """
    # For each nearby store, check:
    # 1. How many ingredients are available
    # 2. Estimated price (cheapest option per ingredient)
    # 3. Distance from user
```

### 2. Modify Create Cart to Store Original Ingredients

**Update**: Save original confirmed ingredients in response

```python
@app.post("/api/create-cart")
async def create_cart(request: CreateCartRequest) -> CartResponse:
    """Build cart and return with original ingredients for reference."""

    # ... existing cart building logic ...

    return CartResponse(
        items=cart_items,
        total=total,
        store=primary_store,
        servings=servings,
        confirmed_ingredients=request.confirmed_ingredients,  # ← Add this
        unavailable_ingredients=unavailable_items,  # ← Add this
        location=user_location
    )
```

---

## Frontend Implementation

### 1. New Component: IngredientsPanel

**File**: `Figma_files/src/app/components/IngredientsPanel.tsx`

```tsx
interface IngredientsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  ingredients: IngredientItem[];
  unavailableItems: IngredientItem[];
  currentStore: string;
  onStoreSwitch: (newStore: string) => void;
}

export function IngredientsPanel({
  isOpen,
  onClose,
  ingredients,
  unavailableItems,
  currentStore,
  onStoreSwitch
}: IngredientsPanelProps) {
  const [viewMode, setViewMode] = useState<'store' | 'availability'>('store');
  const [storeComparisons, setStoreComparisons] = useState([]);
  const [isLoadingComparison, setIsLoadingComparison] = useState(false);

  // Fetch store comparisons when panel opens
  useEffect(() => {
    if (isOpen) {
      loadStoreComparisons();
    }
  }, [isOpen]);

  const loadStoreComparisons = async () => {
    setIsLoadingComparison(true);
    try {
      const response = await fetch('/api/compare-stores', {
        method: 'POST',
        body: JSON.stringify({
          ingredients: ingredients.map(i => i.name),
          current_store: currentStore,
          user_location: userLocation
        })
      });
      const data = await response.json();
      setStoreComparisons(data.comparisons);
    } finally {
      setIsLoadingComparison(false);
    }
  };

  return (
    <div className={`ingredients-panel ${isOpen ? 'open' : ''}`}>
      <div className="panel-header">
        <h2>📋 Ingredients</h2>
        <button onClick={onClose}>× Close</button>
      </div>

      {/* View mode toggle */}
      <div className="view-toggle">
        <button
          className={viewMode === 'store' ? 'active' : ''}
          onClick={() => setViewMode('store')}
        >
          By Store
        </button>
        <button
          className={viewMode === 'availability' ? 'active' : ''}
          onClick={() => setViewMode('availability')}
        >
          By Availability
        </button>
      </div>

      {/* Ingredients list */}
      {viewMode === 'store' ? (
        <IngredientsByStore
          ingredients={ingredients}
          unavailable={unavailableItems}
          currentStore={currentStore}
        />
      ) : (
        <IngredientsByAvailability
          ingredients={ingredients}
          unavailable={unavailableItems}
        />
      )}

      {/* Store switcher section */}
      <div className="store-switcher">
        <h3>🔄 Switch Primary Store</h3>
        <p className="current-store">Current: {currentStore} ✓</p>

        {isLoadingComparison ? (
          <div className="loading">Loading alternatives...</div>
        ) : (
          <div className="store-options">
            {storeComparisons.map(comparison => (
              <StoreOption
                key={comparison.store}
                comparison={comparison}
                currentStore={currentStore}
                onSwitch={onStoreSwitch}
              />
            ))}
          </div>
        )}
      </div>

      {/* Download options */}
      <div className="panel-footer">
        <button onClick={handleDownloadPDF}>
          Download PDF Recipe Card
        </button>
        <button onClick={handlePrintChecklist}>
          Print Checklist
        </button>
      </div>
    </div>
  );
}
```

### 2. Store Option Component

```tsx
function StoreOption({ comparison, currentStore, onSwitch }) {
  const [showConfirm, setShowConfirm] = useState(false);

  const priceDiff = comparison.price_difference_percent;
  const priceLabel = priceDiff > 0
    ? `${priceDiff}% more expensive`
    : `${Math.abs(priceDiff)}% cheaper`;

  const handleSwitch = () => {
    setShowConfirm(true);
  };

  return (
    <>
      <div className="store-option">
        <div className="store-header">
          <h4>{comparison.store}</h4>
          <span className="distance">{comparison.distance_miles} mi away</span>
        </div>

        <div className="store-details">
          <div className="detail-row">
            <span>Availability:</span>
            <strong>
              {comparison.items_available}/{comparison.items_available + comparison.items_unavailable} items
            </strong>
          </div>

          <div className="detail-row">
            <span>Estimated total:</span>
            <strong>${comparison.estimated_total}</strong>
            <span className={priceDiff > 0 ? 'text-red' : 'text-green'}>
              {priceLabel}
            </span>
          </div>

          {comparison.specialty_items_available.length > 0 && (
            <div className="detail-row highlight">
              ✨ All specialty items available!
            </div>
          )}
        </div>

        <button
          className="rebuild-button"
          onClick={handleSwitch}
        >
          Rebuild with {comparison.store} →
        </button>
      </div>

      {showConfirm && (
        <StoreSwitchModal
          newStore={comparison.store}
          currentStore={currentStore}
          comparison={comparison}
          onConfirm={() => onSwitch(comparison.store)}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </>
  );
}
```

### 3. Store Switch Confirmation Modal

```tsx
function StoreSwitchModal({ newStore, currentStore, comparison, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Switch to {newStore}?</h3>

        <p>This will rebuild your entire cart with products from {newStore}.</p>

        <div className="comparison-table">
          <div className="comparison-row">
            <span>Current ({currentStore}):</span>
            <strong>${comparison.current_total}</strong>
          </div>
          <div className="comparison-row">
            <span>New ({newStore}):</span>
            <strong>${comparison.estimated_total}</strong>
          </div>
        </div>

        <div className="changes-info">
          <h4>What will change:</h4>
          <ul>
            <li>Different brands available</li>
            <li>Different prices</li>
            <li>Same {comparison.items_available} items</li>
            {comparison.specialty_items_available.length > 0 && (
              <li>✨ Includes specialty items: {comparison.specialty_items_available.join(', ')}</li>
            )}
          </ul>
        </div>

        <div className="modal-actions">
          <button onClick={onCancel}>Cancel</button>
          <button
            className="primary"
            onClick={onConfirm}
          >
            Switch to {newStore}
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 4. Update ShoppingCart Component

**File**: `Figma_files/src/app/components/ShoppingCart.tsx`

```tsx
export function ShoppingCart({ items, metadata, ... }) {
  const [showIngredientsPanel, setShowIngredientsPanel] = useState(false);

  const handleStoreSwitch = async (newStore: string) => {
    setIsLoading(true);

    try {
      // Rebuild cart with new store
      const response = await createCart({
        confirmed_ingredients: metadata.confirmedIngredients,
        preferred_store: newStore,
        servings: metadata.servings
      });

      // Update cart
      setCartItems(response.items);
      setCartMetadata({
        ...metadata,
        store: newStore
      });

      // Close panel
      setShowIngredientsPanel(false);
    } catch (error) {
      console.error('Failed to switch stores:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="shopping-cart">
      {/* Header */}
      <div className="cart-header">
        <h2>{metadata.store}</h2>
        <p>{metadata.location} • {metadata.servings} servings</p>

        <div className="cart-actions">
          <button onClick={() => setShowIngredientsPanel(true)}>
            📋 Ingredients
          </button>
          <button>Share</button>
        </div>
      </div>

      {/* Cart items */}
      <div className="cart-items">
        {items.map(item => <CartItem key={item.id} {...item} />)}
      </div>

      {/* Total */}
      <div className="cart-total">
        <h3>Total: ${total}</h3>
      </div>

      {/* Ingredients panel (slide-in) */}
      <IngredientsPanel
        isOpen={showIngredientsPanel}
        onClose={() => setShowIngredientsPanel(false)}
        ingredients={metadata.confirmedIngredients}
        unavailableItems={metadata.unavailableIngredients}
        currentStore={metadata.store}
        onStoreSwitch={handleStoreSwitch}
      />
    </div>
  );
}
```

---

## CSS for Slide-in Panel

**File**: `Figma_files/src/styles/ingredients-panel.css`

```css
.ingredients-panel {
  position: fixed;
  top: 0;
  right: -500px; /* Hidden by default */
  width: 500px;
  height: 100vh;
  background: white;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease;
  z-index: 1000;
  overflow-y: auto;
}

.ingredients-panel.open {
  right: 0; /* Slide in */
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5c7a1;
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  background: #f5e6d3;
}

.view-toggle button {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #e5c7a1;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.view-toggle button.active {
  background: #dd9057;
  color: white;
  border-color: #dd9057;
}

.store-switcher {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f9f9f9;
  border-top: 2px solid #e5c7a1;
}

.store-option {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border: 1px solid #e5c7a1;
  border-radius: 8px;
}

.rebuild-button {
  width: 100%;
  padding: 0.75rem;
  background: #dd9057;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.rebuild-button:hover {
  background: #c87040;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .ingredients-panel {
    width: 100%;
    right: -100%;
  }

  .ingredients-panel.open {
    right: 0;
  }
}
```

---

## Updated Task List

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Review testing docs and align validation approach", "status": "completed", "activeForm": "Reviewing testing docs"}, {"content": "Get user approval on updated design (ingredients panel + store switching)", "status": "in_progress", "activeForm": "Getting user approval on updated design"}, {"content": "Backend: Add availability checking logic to product_agent.py", "status": "pending", "activeForm": "Adding availability checking logic"}, {"content": "Backend: Add external store links to synthetic inventory", "status": "pending", "activeForm": "Adding external store products"}, {"content": "Backend: New endpoint GET /api/compare-stores (store comparison)", "status": "pending", "activeForm": "Adding compare-stores endpoint"}, {"content": "Backend: New endpoint POST /api/extract-ingredients (with availability)", "status": "pending", "activeForm": "Adding extract-ingredients endpoint"}, {"content": "Backend: Modify POST /api/create-cart to return confirmed + unavailable ingredients", "status": "pending", "activeForm": "Modifying create-cart response"}, {"content": "Frontend: Create IngredientsPanel component (slide-in)", "status": "pending", "activeForm": "Creating IngredientsPanel component"}, {"content": "Frontend: Add two view modes (by store / by availability)", "status": "pending", "activeForm": "Adding view mode toggle"}, {"content": "Frontend: Create StoreOption component with comparison details", "status": "pending", "activeForm": "Creating StoreOption component"}, {"content": "Frontend: Create StoreSwitchModal confirmation dialog", "status": "pending", "activeForm": "Creating switch confirmation modal"}, {"content": "Frontend: Add external links for unavailable items in panel", "status": "pending", "activeForm": "Adding external purchase links"}, {"content": "Frontend: Update ShoppingCart to show Ingredients button", "status": "pending", "activeForm": "Adding ingredients button to cart"}, {"content": "Frontend: Implement store switching flow (rebuild cart)", "status": "pending", "activeForm": "Implementing store switch logic"}, {"content": "Frontend: Add slide-in animation CSS for panel", "status": "pending", "activeForm": "Adding panel animations"}, {"content": "Frontend: Create IngredientConfirmation component for initial flow", "status": "pending", "activeForm": "Creating confirmation screen"}, {"content": "Update App.tsx for 3-state flow (input → confirm → cart)", "status": "pending", "activeForm": "Updating App.tsx flow"}, {"content": "Add loading states for all async operations", "status": "pending", "activeForm": "Adding loading states"}, {"content": "Write Layer 1 unit tests (availability + store comparison)", "status": "pending", "activeForm": "Writing unit tests"}, {"content": "Test store switching flow manually with different stores", "status": "pending", "activeForm": "Testing store switching"}]