# Unavailable Items Design

## Problem Statement

Not all ingredients are available at the user's primary store (FreshDirect). Example:
- **Garam masala** → Only at Pure Indian Foods, Patel Brothers, or Amazon
- **Saffron** → Specialty item, not at regular grocery stores

**User question**: "How should they complete purchase from Pure Indian Foods afterwards?"

---

## Solution: Hybrid Approach

### 1. Ingredient Confirmation Screen Groups

Three distinct sections:

#### Group A: ✅ Available at Primary Store
```
✅ AVAILABLE AT FRESHDIRECT (6 items)
  ☑  2.0  lb    Chicken
  ☑  2.0  cups  Basmati Rice
  ☑  2.0  large Onions
  ☑  0.5  cup   Yogurt
  ☑  1.0  inch  Ginger
  ☑  6.0  cloves Garlic

→ These go into your FreshDirect cart
```

#### Group B: ⚠️ Unavailable (Specialty Items)
```
⚠️  UNAVAILABLE AT FRESHDIRECT (2 items)

  ☑  2.0  tsp   Garam Masala
     🛒 Buy from:
        • [Pure Indian Foods ($7.99)] (opens in new tab)
        • [Amazon ($6.49)] (opens in new tab)
        • [Patel Brothers ($5.99)] (opens in new tab)
     OR
        [×] I already have this

  ☑  1.0  pinch Saffron
     🛒 Buy from:
        • [La Tourangelle ($18.99)] (opens in new tab)
        • [Amazon ($14.99)] (opens in new tab)
     OR
        [×] I already have this

→ These will NOT be in your cart. Purchase separately or skip if you have them.
```

#### Group C: ℹ️ Optional Add-ons
```
ℹ️  OPTIONAL (Recommended but not essential)
  ☐  0.5  cup   Cilantro (garnish)
  ☐  0.25 bunch Mint (garnish)

→ Uncheck if you don't want these
```

---

## User Flow

### Step 1: Extract Ingredients
```
User: "chicken biryani for 4"
  ↓
POST /api/extract-ingredients
  ↓
Response:
{
  "ingredients": [
    {
      "name": "chicken",
      "quantity": 2.0,
      "unit": "lb",
      "availability": "available",
      "stores": ["FreshDirect", "Whole Foods", "ShopRite"]
    },
    {
      "name": "garam_masala",
      "quantity": 2.0,
      "unit": "tsp",
      "availability": "unavailable_at_primary",  ← Key field
      "stores": ["Pure Indian Foods", "Patel Brothers"],
      "external_links": [
        {
          "store": "Pure Indian Foods",
          "price": 7.99,
          "url": "https://pureindianfoods.com/garam-masala"
        },
        {
          "store": "Amazon",
          "price": 6.49,
          "url": "https://amazon.com/dp/B00ABC123"
        }
      ]
    }
  ],
  "summary": {
    "available_count": 6,
    "unavailable_count": 2,
    "optional_count": 2
  }
}
```

### Step 2: User Sees Confirmation Screen
```
┌─────────────────────────────────────────────┐
│ ✅ Available at FreshDirect: 6 items        │
│ ⚠️  Unavailable: 2 items (see below)        │
│ ℹ️  Optional: 2 items                       │
├─────────────────────────────────────────────┤
│ [Show groups as above]                     │
│                                             │
│ Summary:                                    │
│ • Your FreshDirect cart: 6 items (~$28)    │
│ • Specialty items: 2 items (buy separately)│
│                                             │
│      [Build FreshDirect Cart →]            │
└─────────────────────────────────────────────┘
```

### Step 3: User Confirms → Builds Cart
```
User clicks "Build FreshDirect Cart"
  ↓
POST /api/create-cart
{
  "confirmed_ingredients": [
    {"name": "chicken", "quantity": 2.0, ...},
    {"name": "basmati_rice", "quantity": 2.0, ...},
    // Only available items
  ],
  "excluded_ingredients": ["garam_masala", "saffron"]
}
  ↓
Cart built with 6 items
```

### Step 4: Cart Display with Specialty Item Reminder
```
┌─────────────────────────────────────────────┐
│ 🛒 Your FreshDirect Cart                   │
│ Edison, NJ • 4 servings                    │
├─────────────────────────────────────────────┤
│ [6 items displayed]                        │
│                                             │
│ Total: $28.47                              │
├─────────────────────────────────────────────┤
│ ⚠️  Don't forget specialty items!           │
│                                             │
│ You'll also need:                          │
│ • Garam Masala (2 tsp)                     │
│   → [Buy on Pure Indian Foods]             │
│ • Saffron (1 pinch)                        │
│   → [Buy on Amazon]                        │
│                                             │
│ [Show recipe card with all ingredients]   │
└─────────────────────────────────────────────┘
```

---

## Backend Implementation

### 1. Check Product Availability

**File**: `src/agents/product_agent.py`

```python
def check_ingredient_availability(
    ingredient_name: str,
    primary_store: str = "FreshDirect"
) -> dict:
    """
    Check if ingredient is available at primary store.

    Returns:
        {
            "ingredient": "garam_masala",
            "availability": "unavailable_at_primary" | "available" | "optional",
            "available_stores": ["Pure Indian Foods", "Patel Brothers"],
            "external_links": [
                {
                    "store": "Pure Indian Foods",
                    "price": 7.99,
                    "url": "https://...",
                    "product_id": "pif_gm001"
                }
            ]
        }
    """
    # Check if ingredient exists in primary store inventory
    inventory = SIMULATED_INVENTORY.get(ingredient_name, [])

    available_at_primary = any(
        p.get("store") == primary_store for p in inventory
    )

    if available_at_primary:
        return {
            "ingredient": ingredient_name,
            "availability": "available",
            "available_stores": [primary_store],
            "external_links": []
        }

    # Not available at primary - find specialty stores
    specialty_stores = [
        p.get("store") for p in inventory if p.get("store") != primary_store
    ]

    # Generate external links
    external_links = []
    for product in inventory:
        if product.get("store") != primary_store:
            external_links.append({
                "store": product["store"],
                "price": product["price"],
                "url": f"https://{product['store'].lower().replace(' ', '')}.com/{ingredient_name}",
                "product_id": product["id"]
            })

    return {
        "ingredient": ingredient_name,
        "availability": "unavailable_at_primary",
        "available_stores": specialty_stores,
        "external_links": external_links
    }
```

### 2. Update Extract Ingredients Endpoint

**File**: `api/main.py`

```python
@app.post("/api/extract-ingredients")
async def extract_ingredients(request: CreateCartRequest) -> ExtractIngredientsResponse:
    """Extract ingredients and check availability."""

    orch = Orchestrator(use_llm_extraction=True, use_llm_explanations=False)
    orch.step_ingredients(request.meal_plan, servings=request.servings)

    primary_store = request.preferred_store or "FreshDirect"

    # Check availability for each ingredient
    ingredients_with_availability = []
    available_count = 0
    unavailable_count = 0

    for ing in orch.state.ingredients:
        availability_info = check_ingredient_availability(
            ing["name"],
            primary_store=primary_store
        )

        ingredient_item = {
            **ing,
            "availability": availability_info["availability"],
            "available_stores": availability_info["available_stores"],
            "external_links": availability_info["external_links"]
        }

        ingredients_with_availability.append(ingredient_item)

        if availability_info["availability"] == "available":
            available_count += 1
        else:
            unavailable_count += 1

    return ExtractIngredientsResponse(
        ingredients=ingredients_with_availability,
        servings=request.servings or 2,
        primary_store=primary_store,
        summary={
            "available_count": available_count,
            "unavailable_count": unavailable_count,
            "total_count": len(ingredients_with_availability)
        }
    )
```

### 3. Update Synthetic Inventory with External Stores

**File**: `src/agents/product_agent.py`

```python
SIMULATED_INVENTORY: dict[str, list[dict]] = {
    # ... existing ingredients ...

    "garam_masala": [
        {
            "id": "pif_gm001",
            "title": "Organic Garam Masala",
            "brand": "Pure Indian Foods",
            "size": "3oz",
            "price": 7.99,
            "organic": True,
            "store": "Pure Indian Foods",  # Specialty store
            "external_url": "https://pureindianfoods.com/garam-masala"
        },
        {
            "id": "pb_gm001",
            "title": "Garam Masala Powder",
            "brand": "Patel Brothers",
            "size": "3.5oz",
            "price": 5.99,
            "organic": False,
            "store": "Patel Brothers",
            "external_url": "https://patelbrothersusa.com/garam-masala"
        },
        {
            "id": "amz_gm001",
            "title": "Simply Organic Garam Masala",
            "brand": "Simply Organic",
            "size": "2.3oz",
            "price": 6.49,
            "organic": True,
            "store": "Amazon",
            "external_url": "https://amazon.com/dp/B000WS1KJO"
        },
        # NO FreshDirect option - unavailable!
    ],

    "saffron": [
        {
            "id": "lt_saf001",
            "title": "La Tourangelle Saffron Threads",
            "brand": "La Tourangelle",
            "size": "0.5g",
            "price": 18.99,
            "organic": True,
            "store": "Whole Foods",
            "external_url": "https://wholefoodsmarket.com/saffron"
        },
        {
            "id": "amz_saf001",
            "title": "Zaran Saffron Threads",
            "brand": "Zaran",
            "size": "1g",
            "price": 14.99,
            "organic": True,
            "store": "Amazon",
            "external_url": "https://amazon.com/dp/B00K0OZ5J8"
        },
        # NO FreshDirect option!
    ],

    # Regular ingredients still have FreshDirect options
    "chicken": [
        {
            "id": "fd_ch001",
            "title": "Chicken Thighs",
            "brand": "FreshDirect",
            "size": "16oz",
            "price": 4.49,
            "organic": False,
            "store": "FreshDirect"  # Available at primary store
        },
        # ... more options
    ],
}
```

---

## Frontend Implementation

### 1. Update IngredientConfirmation Component

**File**: `Figma_files/src/app/components/IngredientConfirmation.tsx`

```tsx
export function IngredientConfirmation({ ingredients, ... }) {
  // Group ingredients by availability
  const available = ingredients.filter(i => i.availability === 'available');
  const unavailable = ingredients.filter(i => i.availability === 'unavailable_at_primary');
  const optional = ingredients.filter(i => i.availability === 'optional');

  const [skippedItems, setSkippedItems] = useState<Set<string>>(new Set());

  return (
    <div className="ingredient-confirmation">
      {/* Group A: Available */}
      <section>
        <h3>✅ Available at {primaryStore} ({available.length} items)</h3>
        {available.map(ing => (
          <IngredientRow key={ing.name} ingredient={ing} />
        ))}
      </section>

      {/* Group B: Unavailable */}
      {unavailable.length > 0 && (
        <section className="unavailable-section">
          <h3>⚠️ Unavailable at {primaryStore} ({unavailable.length} items)</h3>
          <p className="text-sm text-gray-600">
            Purchase separately from specialty stores
          </p>

          {unavailable.map(ing => (
            <div key={ing.name} className="unavailable-item">
              <IngredientRow ingredient={ing} />

              {/* External links */}
              <div className="external-links">
                <span className="text-sm">🛒 Buy from:</span>
                {ing.external_links.map(link => (
                  <a
                    key={link.store}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="external-link-button"
                  >
                    {link.store} (${link.price})
                  </a>
                ))}
              </div>

              {/* Skip option */}
              <button
                onClick={() => {
                  const newSkipped = new Set(skippedItems);
                  if (skippedItems.has(ing.name)) {
                    newSkipped.delete(ing.name);
                  } else {
                    newSkipped.add(ing.name);
                  }
                  setSkippedItems(newSkipped);
                }}
                className="skip-button"
              >
                {skippedItems.has(ing.name)
                  ? '✓ Will purchase separately'
                  : 'I already have this'}
              </button>
            </div>
          ))}
        </section>
      )}

      {/* Group C: Optional */}
      {optional.length > 0 && (
        <section>
          <h3>ℹ️ Optional ({optional.length} items)</h3>
          {optional.map(ing => (
            <IngredientRow key={ing.name} ingredient={ing} optional />
          ))}
        </section>
      )}

      {/* Summary */}
      <div className="summary">
        <p>📦 Your {primaryStore} cart will have {available.length} items</p>
        {unavailable.length > 0 && (
          <p>⚠️ {unavailable.length} items need separate purchase</p>
        )}
      </div>

      <button onClick={handleConfirm}>
        Build {primaryStore} Cart →
      </button>
    </div>
  );
}
```

### 2. Update Cart Display with Reminder

**File**: `Figma_files/src/app/components/ShoppingCart.tsx`

```tsx
export function ShoppingCart({ items, specialtyItems, ... }) {
  return (
    <div>
      {/* Main cart */}
      <div className="cart-items">
        {items.map(item => <CartItem key={item.id} {...item} />)}
      </div>

      <div className="cart-total">
        <h3>Total: ${total}</h3>
      </div>

      {/* Specialty items reminder */}
      {specialtyItems && specialtyItems.length > 0 && (
        <div className="specialty-reminder">
          <h4>⚠️ Don't forget specialty items!</h4>
          <p>You'll also need:</p>
          <ul>
            {specialtyItems.map(item => (
              <li key={item.name}>
                <span>{item.name} ({item.quantity} {item.unit})</span>
                {item.external_links.map(link => (
                  <a
                    key={link.store}
                    href={link.url}
                    target="_blank"
                    className="buy-link"
                  >
                    Buy on {link.store}
                  </a>
                ))}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## User Experience Examples

### Example 1: User Already Has Specialty Items
```
User: "chicken biryani for 4"
  ↓
System shows:
  ✅ 6 items available at FreshDirect
  ⚠️  2 items unavailable (garam masala, saffron)

User clicks: "I already have garam masala" ✓
User clicks: "I already have saffron" ✓
  ↓
User builds cart with 6 items
Recipe card shows: "Make sure you have: garam masala (2 tsp), saffron (1 pinch)"
```

### Example 2: User Needs to Buy Specialty Items
```
User: "chicken biryani for 4"
  ↓
System shows:
  ✅ 6 items available at FreshDirect
  ⚠️  2 items unavailable
     • Garam masala → [Pure Indian Foods $7.99]
     • Saffron → [Amazon $14.99]

User builds FreshDirect cart (6 items)
  ↓
Reminder shown in cart:
  "Don't forget:
   • Garam masala → [Buy on Pure Indian Foods]
   • Saffron → [Buy on Amazon]"

User clicks external links → Opens in new tabs
User purchases from those stores separately
```

### Example 3: User Skips Specialty Items
```
User: "chicken biryani for 4"
  ↓
System shows unavailable items
User unchecks: ☐ Garam masala (removes from recipe)
User unchecks: ☐ Saffron (removes from recipe)
  ↓
Cart built with 6 items
Recipe card shows modified recipe without those spices
```

---

## Summary

**Three groups**:
1. ✅ **Available** → Go into main cart
2. ⚠️ **Unavailable** → Show external links, let user skip
3. ℹ️ **Optional** → User can uncheck

**Purchase flow**:
1. Build main cart (FreshDirect) with available items
2. Show reminder with external links for unavailable items
3. User purchases specialty items separately (opens in new tab)

**Key features**:
- Clear visual separation of availability
- External links to specialty stores
- "I already have this" option
- Recipe card reminder in final cart

---

## Questions for You

1. Should unavailable items be **required** (user must acknowledge them) or **optional** (can skip entirely)?

2. Should we track external purchases? (e.g., "You bought garam masala from Pure Indian Foods") or just provide links?

3. Should the recipe card in the final cart show ALL ingredients (including unavailable) or just what's in the cart?

4. For specialty stores, should we show real URLs or mock URLs for demo?

5. Should unavailable items affect the servings calculation? (e.g., if user skips garam masala, should we warn "Recipe won't be authentic"?)

Let me know your preferences!
