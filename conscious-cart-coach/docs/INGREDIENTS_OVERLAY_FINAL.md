# Ingredients Overlay - Final Design

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ HEADER (Fixed - Always Visible)                    │
│ 📋 Ingredients for Chicken Biryani          [× ]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ╔═══════════════════════════════════════════════╗ │
│ ║ SCROLLABLE CONTENT AREA                       ║ │
│ ║                                               ║ │
│ ║ 🛒 FRESHDIRECT (6 items) ← You are here      ║ │
│ ║ ┌────────────────────────────────────┐       ║ │
│ ║ │ ☑ Chicken (2 lb) - $4.49            │       ║ │
│ ║ │ ☑ Rice (2 cups) - $3.49             │       ║ │
│ ║ │ ...                                 │       ║ │
│ ║ │ Cart Total: $28.47                  │       ║ │
│ ║ └────────────────────────────────────┘       ║ │
│ ║                                               ║ │
│ ║ 🏪 PURE INDIAN FOODS (2 items)                ║ │
│ ║ ┌────────────────────────────────────┐       ║ │
│ ║ │ ☑ Garam Masala (2 tsp) - $7.99      │       ║ │
│ ║ │ ☑ Saffron (1 pinch) - $14.99        │       ║ │
│ ║ │ Cart Total: $22.98                  │       ║ │
│ ║ └────────────────────────────────────┘       ║ │
│ ║                                               ║ │
│ ║ ⚠️ UNAVAILABLE (1 item)                       ║ │
│ ║ ┌────────────────────────────────────┐       ║ │
│ ║ │ ☑ Kashmiri Chili (1 tsp)            │       ║ │
│ ║ │   🛒 [Buy on Amazon $8.99]          │       ║ │
│ ║ │   OR [× Skip]                       │       ║ │
│ ║ └────────────────────────────────────┘       ║ │
│ ║                                               ║ │
│ ║ Grand Total (Stores): $51.45                 ║ │
│ ║ + External items: ~$8.99                     ║ │
│ ║                                               ║ │
│ ╚═══════════════════════════════════════════════╝ │
│                                                     │
├─────────────────────────────────────────────────────┤
│ FOOTER (Fixed - Always Visible)                    │
│ [Download Shopping List]            [Close]        │
└─────────────────────────────────────────────────────┘
```

---

## Component Structure

```tsx
export function IngredientsOverlay({ ... }) {
  return (
    <div className="ingredients-overlay" onClick={onClose}>
      <div className="overlay-modal" onClick={(e) => e.stopPropagation()}>

        {/* FIXED HEADER - Always visible at top */}
        <div className="overlay-header">
          <h2>📋 Ingredients for {mealPlan}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {/* SCROLLABLE CONTENT - Middle section scrolls */}
        <div className="overlay-body">

          {/* Group 1 & 2: Available stores */}
          {availableStoreGroups.map(group => (
            <div
              key={group.store}
              className={`store-group ${group.isActive ? 'active' : ''}`}
              onClick={() => !group.isActive && onSwitchStore(group.store)}
            >
              {/* Store content */}
            </div>
          ))}

          {/* Group 3: Unavailable items */}
          {hasUnavailable && (
            <div className="store-group unavailable">
              {/* Unavailable content */}
            </div>
          )}

          {/* Totals within scrollable area */}
          <div className="totals-section">
            <div className="total-row">
              <span>Grand Total (Stores):</span>
              <strong>${totalAllCarts.toFixed(2)}</strong>
            </div>
            {hasUnavailable && (
              <div className="total-row external">
                <span>+ External items:</span>
                <span>~${totalExternal.toFixed(2)}</span>
              </div>
            )}
          </div>

        </div>

        {/* FIXED FOOTER - Always visible at bottom */}
        <div className="overlay-footer">
          <button className="secondary-button" onClick={handleDownload}>
            Download Shopping List
          </button>
          <button className="primary-button" onClick={onClose}>
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
```

---

## CSS with Fixed Header/Footer

```css
/* Overlay backdrop */
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
  padding: 1rem;
}

/* Modal container - Uses flexbox to layout header, body, footer */
.overlay-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 85vh;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Important: prevents scrolling of entire modal */
}

/* FIXED HEADER - Stays at top */
.overlay-header {
  flex-shrink: 0; /* Prevents header from shrinking */
  padding: 1.5rem;
  background: #f5d7b1;
  border-bottom: 2px solid #e5c7a1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 10;
}

.overlay-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #4a3f2a;
}

.close-button {
  background: none;
  border: none;
  font-size: 2rem;
  line-height: 1;
  color: #4a3f2a;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.close-button:hover {
  background: rgba(0, 0, 0, 0.1);
}

/* SCROLLABLE BODY - Middle section that scrolls */
.overlay-body {
  flex: 1; /* Takes up remaining space */
  overflow-y: auto; /* Only this section scrolls */
  padding: 0;
  background: #f5e6d3;
}

/* Custom scrollbar styling */
.overlay-body::-webkit-scrollbar {
  width: 8px;
}

.overlay-body::-webkit-scrollbar-track {
  background: #f5e6d3;
}

.overlay-body::-webkit-scrollbar-thumb {
  background: #e5c7a1;
  border-radius: 4px;
}

.overlay-body::-webkit-scrollbar-thumb:hover {
  background: #d5b791;
}

/* FIXED FOOTER - Stays at bottom */
.overlay-footer {
  flex-shrink: 0; /* Prevents footer from shrinking */
  padding: 1rem 1.5rem;
  background: white;
  border-top: 2px solid #e5c7a1;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  position: sticky;
  bottom: 0;
  z-index: 10;
}

.overlay-footer button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.secondary-button {
  background: white;
  color: #dd9057;
  border: 2px solid #dd9057 !important;
}

.secondary-button:hover {
  background: #f5e6d3;
}

.primary-button {
  background: #dd9057;
  color: white;
}

.primary-button:hover {
  background: #c87040;
}

/* Store groups within scrollable area */
.store-group {
  margin: 1rem;
  padding: 1rem;
  border: 2px solid #e5c7a1;
  border-radius: 8px;
  background: white;
  transition: all 0.2s;
}

.store-group.clickable {
  cursor: pointer;
}

.store-group.clickable:hover:not(.active) {
  background: #fefbf7;
  border-color: #dd9057;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.store-group.active {
  background: #fffaf5;
  border-color: #dd9057;
  border-width: 3px;
  cursor: default;
  box-shadow: 0 0 0 4px rgba(221, 144, 87, 0.1);
}

.store-group.unavailable {
  background: #fff5f5;
  border-color: #f5c7a1;
  cursor: default;
}

.store-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5c7a1;
}

.store-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #4a3f2a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tap-hint {
  font-size: 0.875rem;
  color: #dd9057;
  font-weight: 500;
}

/* Ingredient list */
.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.ingredient-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.5rem;
  background: #f5e6d3;
  border-radius: 4px;
  font-size: 0.9rem;
}

.ingredient-row .check {
  font-size: 1rem;
  color: #7a6f4a;
}

.ingredient-row .quantity {
  font-weight: 500;
  color: #4a3f2a;
  min-width: 60px;
}

.ingredient-row .name {
  flex: 1;
  color: #4a3f2a;
}

.ingredient-row .price {
  font-weight: 600;
  color: #dd9057;
}

/* Store total */
.store-total {
  padding: 0.75rem;
  background: #f5d7b1;
  border-radius: 4px;
  font-weight: 600;
  text-align: right;
  color: #4a3f2a;
}

/* Unavailable items styling */
.unavailable-ingredient {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f5c7a1;
}

.unavailable-ingredient:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.external-links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0.75rem 0 0.75rem 2.5rem;
}

.external-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #e5c7a1;
  border-radius: 4px;
  color: #dd9057;
  text-decoration: none;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.external-link:hover {
  background: #dd9057;
  color: white;
  border-color: #dd9057;
  transform: translateX(4px);
}

.skip-button {
  margin-left: 2.5rem;
  padding: 0.375rem 0.875rem;
  background: transparent;
  border: 1px solid #c87040;
  color: #c87040;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.skip-button:hover {
  background: #fff5f5;
}

/* Totals section within scrollable area */
.totals-section {
  margin: 1rem;
  padding: 1.5rem;
  background: white;
  border: 2px solid #dd9057;
  border-radius: 8px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 1.125rem;
  color: #4a3f2a;
}

.total-row:first-child {
  font-weight: 600;
  font-size: 1.25rem;
}

.total-row strong {
  color: #dd9057;
}

.total-row.external {
  font-size: 0.9rem;
  color: #6b5f4a;
  font-style: italic;
  border-top: 1px dashed #e5c7a1;
  margin-top: 0.5rem;
  padding-top: 1rem;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .overlay-modal {
    max-width: 100%;
    max-height: 95vh;
    margin: 0;
    border-radius: 12px 12px 0 0;
  }

  .overlay-header {
    padding: 1rem;
  }

  .overlay-header h2 {
    font-size: 1.125rem;
  }

  .overlay-footer {
    padding: 1rem;
    flex-direction: column;
  }

  .overlay-footer button {
    width: 100%;
  }

  .store-group {
    margin: 0.75rem;
    padding: 0.75rem;
  }

  .ingredient-row {
    font-size: 0.85rem;
  }

  .external-links {
    margin-left: 1.5rem;
  }

  .skip-button {
    margin-left: 1.5rem;
  }
}

/* Animation */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.overlay-modal {
  animation: slideIn 0.2s ease-out;
}
```

---

## Key CSS Features

### 1. **Fixed Header**
```css
.overlay-header {
  flex-shrink: 0;      /* Won't shrink when content overflows */
  position: sticky;     /* Stays at top */
  top: 0;
  z-index: 10;         /* Above scrolling content */
}
```

### 2. **Scrollable Body**
```css
.overlay-body {
  flex: 1;             /* Takes up remaining space */
  overflow-y: auto;    /* Only this section scrolls */
}
```

### 3. **Fixed Footer**
```css
.overlay-footer {
  flex-shrink: 0;      /* Won't shrink */
  position: sticky;     /* Stays at bottom */
  bottom: 0;
  z-index: 10;         /* Above scrolling content */
}
```

### 4. **Modal Container**
```css
.overlay-modal {
  display: flex;
  flex-direction: column;  /* Stack header, body, footer */
  overflow: hidden;        /* Prevents entire modal from scrolling */
}
```

---

## Visual Behavior

### When Content is Short (Fits in Viewport)
```
┌─────────────────────┐
│ HEADER (visible)    │
├─────────────────────┤
│                     │
│ Store 1             │
│                     │
│ Store 2             │
│                     │
│ Unavailable         │
│                     │
│ Totals              │
│                     │
├─────────────────────┤
│ FOOTER (visible)    │
└─────────────────────┘
```

### When Content is Long (Scrolls)
```
┌─────────────────────┐
│ HEADER (FIXED) ←────┼─ Always visible
├─────────────────────┤
│ Store 1             │
│                     │
│ Store 2             │  ← This area
│                     │     scrolls
│ ⬇ SCROLL ⬇         │
│                     │
│ Unavailable         │
│                     │
│ Totals              │
├─────────────────────┤
│ FOOTER (FIXED) ←────┼─ Always visible
└─────────────────────┘
```

### User Scrolls Down
```
┌─────────────────────┐
│ HEADER (FIXED) ←────┼─ Still visible
├─────────────────────┤
│ Store 2 (middle)    │
│                     │
│ Unavailable         │  ← Content
│                     │     scrolled
│ Totals              │
│                     │
│ ⬆ SCROLL ⬆         │
├─────────────────────┤
│ FOOTER (FIXED) ←────┼─ Still visible
└─────────────────────┘
```

---

## Complete Component Code

```tsx
export function IngredientsOverlay({
  allIngredients,
  storeSplit,
  unavailableItems,
  currentStore,
  carts,
  mealPlan,
  onSwitchStore,
  onClose
}: IngredientsOverlayProps) {

  // Group stores
  const availableStoreGroups = storeSplit.available_stores.map(storeInfo => {
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

  const hasUnavailable = unavailableItems && unavailableItems.length > 0;
  const totalAllCarts = carts.reduce((sum, c) => sum + c.total, 0);
  const totalExternal = unavailableItems?.reduce((sum, item) =>
    sum + (item.external_sources[0]?.price || 0), 0
  ) || 0;

  const handleDownload = () => {
    // Generate and download shopping list
    console.log('Download shopping list');
  };

  return (
    <div className="ingredients-overlay" onClick={onClose}>
      <div className="overlay-modal" onClick={(e) => e.stopPropagation()}>

        {/* FIXED HEADER */}
        <div className="overlay-header">
          <h2>📋 Ingredients for {mealPlan}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {/* SCROLLABLE BODY */}
        <div className="overlay-body">

          {/* Available stores (Groups 1 & 2) */}
          {availableStoreGroups.map(group => (
            <div
              key={group.store}
              className={`store-group clickable ${group.isActive ? 'active' : ''}`}
              onClick={() => !group.isActive && onSwitchStore(group.store)}
            >
              <div className="store-header">
                <h3>
                  {group.isPrimary ? '🛒' : '🏪'} {group.store.toUpperCase()} ({group.ingredients.length} items)
                  {group.isActive && ' ← You are here'}
                </h3>
                {!group.isActive && (
                  <span className="tap-hint">Tap to view this cart →</span>
                )}
              </div>

              <div className="ingredient-list">
                {group.ingredients.map(ing => {
                  const cartItem = group.cart?.items.find(item =>
                    item.ingredientName.toLowerCase() === ing.name.toLowerCase()
                  );
                  return (
                    <div key={ing.name} className="ingredient-row">
                      <span className="check">☑</span>
                      <span className="quantity">{ing.quantity} {ing.unit}</span>
                      <span className="name">{ing.name}</span>
                      {cartItem && (
                        <span className="price">${cartItem.price.toFixed(2)}</span>
                      )}
                    </div>
                  );
                })}
              </div>

              {group.cart && (
                <div className="store-total">
                  Cart Total: ${group.cart.total.toFixed(2)}
                </div>
              )}
            </div>
          ))}

          {/* Unavailable items (Group 3) */}
          {hasUnavailable && (
            <div className="store-group unavailable">
              <div className="store-header">
                <h3>⚠️ UNAVAILABLE ({unavailableItems.length} {unavailableItems.length === 1 ? 'item' : 'items'})</h3>
              </div>
              <p style={{ fontSize: '0.875rem', color: '#6b5f4a', marginBottom: '1rem' }}>
                Purchase separately - not available at stores
              </p>

              <div className="ingredient-list">
                {unavailableItems.map(item => (
                  <div key={item.ingredient} className="unavailable-ingredient">
                    <div className="ingredient-row">
                      <span className="check">☑</span>
                      <span className="quantity">{item.quantity}</span>
                      <span className="name">{item.ingredient}</span>
                    </div>

                    <div className="external-links">
                      {item.external_sources.map(source => (
                        <a
                          key={source.store}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="external-link"
                        >
                          🛒 Buy on {source.store} (${source.price.toFixed(2)})
                        </a>
                      ))}
                    </div>

                    <button className="skip-button">
                      × I already have this
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Totals */}
          <div className="totals-section">
            <div className="total-row">
              <span>Grand Total (Stores):</span>
              <strong>${totalAllCarts.toFixed(2)}</strong>
            </div>
            {hasUnavailable && totalExternal > 0 && (
              <div className="total-row external">
                <span>+ External items:</span>
                <span>~${totalExternal.toFixed(2)}</span>
              </div>
            )}
          </div>

        </div>

        {/* FIXED FOOTER */}
        <div className="overlay-footer">
          <button className="secondary-button" onClick={handleDownload}>
            Download Shopping List
          </button>
          <button className="primary-button" onClick={onClose}>
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
```

---

## Benefits

✅ **Header always visible** - User always sees what they're looking at
✅ **Footer always accessible** - Can close or download anytime
✅ **Smooth scrolling** - Only content area scrolls
✅ **Mobile friendly** - Works perfectly on small screens
✅ **Professional UX** - Standard pattern users expect

---

This ensures the header and footer stay in place while users scroll through potentially long lists of ingredients across multiple stores! Ready to implement?