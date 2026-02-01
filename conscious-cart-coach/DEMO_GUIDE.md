# Conscious Cart Coach - Demo Guide

**Last Updated:** February 1, 2026
**Status:** ✅ Demo Ready

## Quick Start

### Running the Demo

**Step 1: Start Backend API**
```bash
cd /Users/hash/Documents/ConsciousBuyer/conscious-cart-coach
python -m uvicorn api.main:app --reload
```
Backend runs on: **http://localhost:8000**

**Step 2: Start Frontend (new terminal)**
```bash
cd /Users/hash/Documents/ConsciousBuyer/conscious-cart-coach/frontend
npm run dev
```
Frontend runs on: **http://localhost:5173**

**Step 3: Open Demo**
Open your browser to: **http://localhost:5173**

---

## Demo Features

### Current Working Features

1. **Left/Right Panel Layout**
   - Left panel: Meal plan input (prompt area)
   - Right panel: Shopping cart view
   - Fully responsive mobile/desktop

2. **Multi-Store Cart Planning**
   - Automatically splits items between FreshDirect and specialty stores
   - Shows store tabs to filter items by store
   - Multi-store awareness in cart header

3. **Ingredient Confirmation Flow**
   - User enters meal plan (e.g., "chicken biryani for 4")
   - System extracts ingredients
   - Modal appears for ingredient confirmation
   - User can add/remove/edit ingredients
   - Cart created after confirmation

4. **Product Details**
   - Organic/safety certifications shown
   - "Why this pick?" tags
   - Trade-offs displayed
   - Size information (when available)
   - Store assignments

5. **Size Variants** (NEW)
   - Common spices now have 3oz + 8oz options
   - Smart size selection based on recipe needs
   - Bulk pricing for 8oz sizes

---

## Recent Changes (This Session)

### 1. UI/Frontend Changes

**File:** `frontend/src/app/components/CartItemCard.tsx`
- **Change:** Hide size dropdown when size is "varies"
- **Code:**
  ```tsx
  {item.size && item.size !== 'varies' && (
    <button className="...">
      Size: {item.size}
      <ChevronDown />
    </button>
  )}
  ```
- **Reason:** Products without specific sizes shouldn't show size selector

### 2. Product Data Updates

**File:** `data/alternatives/pure_indian_foods_products.csv`

**Changes:**
- **Fixed all "varies" sizes** - replaced with actual sizes (2oz, 3oz, etc.)
- **Added bulk variants** for common spices:
  - Cumin Seeds: 3oz ($6.69) + 8oz ($14.99)
  - Coriander Seeds: 3oz ($5.31) + 8oz ($11.99)
  - Turmeric Ground: 3oz ($6.99) + 8oz ($15.99)
  - Cardamom Green: 2oz ($12.99) + 8oz ($28.99)
  - Ginger Powder: 2oz ($5.34) + 8oz ($12.99)
  - Fenugreek Seeds: 3oz ($4.99) + 8oz ($10.99)

**Pricing Logic:**
- Bulk sizes offer 10-20% discount per ounce
- Example: Cumin 3oz = $2.23/oz, 8oz = $1.87/oz (savings)

### 3. Store Brand Filtering

**File:** `src/agents/product_agent.py`

**Changes:**
```python
STORE_EXCLUSIVE_BRANDS = {
    # Store brands (exclusive to their store)
    "365 by Whole Foods Market": ["Whole Foods", "Whole Foods Market"],
    "365": ["Whole Foods", "Whole Foods Market"],  # NEW
    "ShopRite": ["ShopRite"],
    "Just Direct": ["FreshDirect"],  # NEW - FreshDirect's brand
    "Trader Joe's": ["Trader Joe's"],
    # ... other brands

    # Specialty stores
    "Pure Indian Foods": ["specialty"],  # NEW - only specialty stores
}
```

**Purpose:** Ensure store-exclusive brands only appear in their correct stores

### 4. Backend Store Filtering Logic

**File:** `api/main.py`

**Changes:**
- Added `target_store` parameter to `map_decision_to_cart_item()` function
- Added validation to check if product is available at target store
- Logs warnings when products are incorrectly assigned

**Code Added:**
```python
def map_decision_to_cart_item(
    # ... existing params
    target_store: str = ""
) -> CartItem:
    # ... existing code

    # Filter by store - check if product is available at target store
    if target_store and product:
        available_stores = product.get("available_stores", ["all"])
        if available_stores != ["all"] and target_store not in available_stores:
            print(f"Warning: {product.get('title')} from {product.get('brand')} not available at {target_store}")
```

### 5. Directory Cleanup

**Changes:**
- Removed old `frontend-old-backup` directory
- Consolidated to single `frontend/` directory (was `Figma_files/`)
- No more multiple frontend versions

---

## Known Issues (To Fix)

### Issue 1: Store Filtering Not Complete
**Problem:** Products from wrong stores still appearing in carts
- 365 by Whole Foods showing in FreshDirect
- Pure Indian Foods showing in FreshDirect

**Status:** Partial fix implemented (logging warnings)
**Next Step:** Need to filter products BEFORE selection in Orchestrator

### Issue 2: Size Variants Not Selectable in Cart
**Problem:** Multiple size options exist but user can't switch between them in cart UI
**Status:** Backend has variants, frontend needs UI for size selection
**Next Step:** Add variety/size selector buttons like screenshot mockup

---

## Data Structure

### Product CSV Format
```csv
category,product_name,brand,price,unit,size,certifications,notes,item_type,seasonality,selected_tier,selection_reason
spices,Cumin Seeds (Jeera),Pure Indian Foods,6.69,ea,3oz,USDA Organic,Best Seller,staple,,Premium Specialty,Whole cumin seeds
spices,Cumin Seeds (Jeera),Pure Indian Foods,14.99,ea,8oz,USDA Organic,Best Seller,staple,,Premium Specialty,Whole cumin seeds - bulk size
```

### Key Fields
- **size:** Product size (3oz, 8oz, 2lb bag, etc.)
- **price:** Price per unit
- **certifications:** USDA Organic, None (conventional)
- **item_type:** staple or specialty
- **selected_tier:** Premium Specialty, Budget Friendly, etc.

---

## Testing the Demo

### Test Scenarios

1. **Biryani (Multi-Store)**
   - Prompt: "chicken biryani for 4"
   - Expected: 2 stores (FreshDirect + specialty)
   - FreshDirect: chicken, onions, tomatoes, yogurt, cilantro
   - Specialty: biryani masala, turmeric, cumin, cardamom, coriander

2. **Simple Meal (Single Store)**
   - Prompt: "fresh salad for 2"
   - Expected: 1 store (FreshDirect only)
   - All fresh ingredients

3. **Spice Check**
   - Verify cumin shows size (3oz or 8oz)
   - Verify no "varies" sizes showing
   - Verify Pure Indian Foods products in specialty store only

---

## Architecture

### Tech Stack
- **Frontend:** React 18 + TypeScript + Vite
- **Backend:** Python FastAPI
- **Database:** CSV files (product inventory)
- **LLM:** Anthropic Claude (optional, for ingredient extraction)

### File Structure
```
conscious-cart-coach/
├── frontend/                    # React UI (main demo)
│   ├── src/app/
│   │   ├── App.tsx             # Main app with left/right panels
│   │   ├── components/         # UI components
│   │   └── services/           # API calls
│   └── package.json
├── api/
│   └── main.py                 # FastAPI backend
├── src/
│   ├── agents/                 # Product selection agents
│   ├── orchestrator/           # Main orchestration logic
│   └── utils/                  # Helpers
└── data/alternatives/
    └── pure_indian_foods_products.csv  # Spice inventory
```

---

## Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Python Dependencies
```bash
pip install fastapi uvicorn anthropic
```

### Frontend Dependencies
```bash
cd frontend
npm install
```

---

## Troubleshooting

### Frontend Not Loading
- Check if Vite server is running on port 5173
- Check browser console for errors
- Verify `npm run dev` completed successfully

### Backend Errors
- Check if port 8000 is already in use
- Verify Python dependencies installed
- Check backend logs for errors

### Products Not Showing
- Verify CSV files are loaded correctly
- Check backend logs for "Loaded X products" message
- Ensure product data has proper format

### CORS Errors
- Backend must be running on port 8000
- Frontend must be on port 5173
- Check `api/main.py` CORS configuration includes both ports

---

## Next Steps (Future Enhancements)

1. **Complete Store Filtering**
   - Filter products in Orchestrator before selection
   - Ensure 365 never appears in FreshDirect
   - Ensure Pure Indian Foods only in specialty stores

2. **Size Selector UI**
   - Add variety/size toggle buttons in cart
   - Allow users to switch between 3oz/8oz options
   - Update cart total when size changes

3. **Smart Size Selection**
   - Calculate needed quantity from recipe
   - Auto-select optimal size (3oz vs 8oz)
   - Show value comparison

4. **Product Images**
   - Replace "Image Unavailable" placeholders
   - Add actual product images

---

## Contact & Support

- **Project:** Conscious Cart Coach
- **Demo Location:** http://localhost:5173
- **Documentation:** `/architecture/` folder

---

**End of Demo Guide**
