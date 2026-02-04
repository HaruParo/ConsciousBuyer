# 365 by Whole Foods → FreshDirect Misassignment Diagnostic

## CSV Data Sample (Source Truth)

From `/conscious-cart-coach/data/alternatives/source_listings.csv`:

```csv
category,product_name,brand,price,unit,size,certifications,notes,product_type,availability,selected_tier,rationale
protein_poultry,Boneless Skinless Chicken Breast,365 by Whole Foods Market,5.99,lb,per lb,None (conventional),,staple,,Cheaper,Budget-friendly chicken breast
protein_poultry,Boneless Skinless Chicken Thighs,365 by Whole Foods Market,5.49,lb,per lb,None (conventional),,staple,,Cheaper,Budget-friendly chicken thighs
protein_poultry,Organic Boneless Skinless Chicken Breast,365 by Whole Foods Market,7.99,lb,per lb,USDA Organic,,staple,,Conscious,Organic store brand
```

**Brand field**: `"365 by Whole Foods Market"` (exact match)

---

## Code Logic That SHOULD Work

### 1. Brand Mapping (product_agent.py:29-32)

```python
STORE_EXCLUSIVE_BRANDS = {
    "365 by Whole Foods Market": ["Whole Foods", "Whole Foods Market"],
    "365": ["Whole Foods", "Whole Foods Market"],
    ...
}
```

When loading CSV (product_agent.py:126):
```python
available_stores = STORE_EXCLUSIVE_BRANDS.get(brand, ["all"])
```

**Result**: Products with brand `"365 by Whole Foods Market"` should get `available_stores = ["Whole Foods", "Whole Foods Market"]`

---

### 2. Store Assignment Override (api/main.py:415-424)

```python
# Determine actual store - BRAND-BASED ASSIGNMENT FIRST
brand_lower = brand.lower()

# Check brand exclusivity first (overrides everything)
if "365" in brand_lower or "whole foods" in brand_lower:
    actual_store = "Whole Foods"
elif "pure indian foods" in brand_lower:
    actual_store = "Pure Indian Foods"
elif "kesar grocery" in brand_lower or "swad" in brand_lower:
    actual_store = "Kesar Grocery"
else:
    # Fall back to available_stores from product agent
    ...
```

**Logic**:
- Get `brand` from product dict (loaded from CSV)
- Convert to lowercase: `brand_lower = "365 by whole foods market"`
- Check if `"365" in brand_lower` → ✅ YES
- Assign `actual_store = "Whole Foods"`

---

## User-Reported Issue

From ERROR_REPORT_2026-02-01.md:

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

---

## Diagnostic Test

### Test 1: Verify CSV Loading

```python
python3 -c "
import sys
sys.path.insert(0, 'conscious-cart-coach')
from src.agents.product_agent import ProductAgent

agent = ProductAgent()

# Find 365 products
for ing_name, products in agent.inventory.items():
    for p in products:
        if '365' in p.get('brand', ''):
            print(f'Ingredient: {ing_name}')
            print(f'  Title: {p[\"title\"]}')
            print(f'  Brand: {p[\"brand\"]}')
            print(f'  Available stores: {p[\"available_stores\"]}')
            print()
            break  # Only show first match per ingredient
"
```

**Expected Output**:
```
Ingredient: chicken
  Title: Organic Boneless Skinless Chicken Breast
  Brand: 365 by Whole Foods Market
  Available stores: ['Whole Foods', 'Whole Foods Market']
```

**Failure Mode**: If `available_stores: ['all']` → Brand mapping failed during CSV load

---

### Test 2: Trace Store Assignment in API

Add debug logging to `api/main.py:416-424`:

```python
# Determine actual store - BRAND-BASED ASSIGNMENT FIRST
brand = product.get("brand", "")
brand_lower = brand.lower()

# DEBUG LOGGING
print(f"\n=== STORE ASSIGNMENT DEBUG ===")
print(f"Product: {product.get('title', 'Unknown')}")
print(f"Brand: '{brand}'")
print(f"Brand lower: '{brand_lower}'")
print(f"'365' in brand_lower: {'365' in brand_lower}")
print(f"'whole foods' in brand_lower: {'whole foods' in brand_lower}")

# Check brand exclusivity first (overrides everything)
if "365" in brand_lower or "whole foods" in brand_lower:
    actual_store = "Whole Foods"
    print(f"→ Matched! Assigned: Whole Foods")
elif "pure indian foods" in brand_lower:
    actual_store = "Pure Indian Foods"
    print(f"→ Matched! Assigned: Pure Indian Foods")
else:
    print(f"→ No brand match, falling back...")
    # Fallback logic...
```

**Expected Output** (for 365 chicken):
```
=== STORE ASSIGNMENT DEBUG ===
Product: Organic Boneless Skinless Chicken Breast
Brand: '365 by Whole Foods Market'
Brand lower: '365 by whole foods market'
'365' in brand_lower: True
'whole foods' in brand_lower: True
→ Matched! Assigned: Whole Foods
```

**Failure Mode**: If brand is empty or doesn't match → Check if `product` dict has `brand` key

---

### Test 3: Check API Response Structure

```bash
# Start backend
cd conscious-cart-coach
python -m uvicorn api.main:app --reload

# Make test request
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "chicken breast",
    "servings": 2,
    "preferences": {
      "dietaryRestrictions": [],
      "allergies": [],
      "prioritizeOrganic": true
    }
  }' | jq '.cartItems[] | select(.brand | contains("365")) | {brand, store}'
```

**Expected Output**:
```json
{
  "brand": "365 by Whole Foods Market",
  "store": "Whole Foods"
}
```

**Failure Mode**: If `"store": "FreshDirect"` → Store assignment logic not being applied

---

## Root Cause Theories

### Theory 1: Brand field is empty in product dict
**Symptom**: `product.get("brand", "")` returns `""`
**Why**: CSV loading bug, or product dict not including brand
**Test**: Print `product` dict to verify keys

### Theory 2: Product dict is replaced after store assignment
**Symptom**: Store assigned correctly, but then overwritten
**Why**: Another part of code reassigns based on `available_stores`
**Test**: Add logging AFTER assignment and before return

### Theory 3: Frontend groups by different field
**Symptom**: API returns correct store, but UI groups wrong
**Why**: Frontend uses `available_stores[0]` instead of `store`
**Test**: Inspect API response JSON vs UI display

### Theory 4: CartItem model doesn't include store field
**Symptom**: `store=actual_store` is set but not serialized
**Why**: Pydantic model missing `store` field
**Test**: Check CartItem model definition

---

## Quick Fix Verification

1. **Restart backend** (ensure code changes are loaded)
2. **Clear browser cache** (ensure old responses aren't cached)
3. **Submit test prompt**: "chicken breast for 2"
4. **Inspect response**: Check `store` field for 365 products
5. **Check logs**: Look for "365" brand matching

---

## Additional Debugging Steps

### Step 1: Check CartItem Model Definition
```bash
grep -A 20 "class CartItem" conscious-cart-coach/api/main.py
```

Verify `store: str` field exists.

### Step 2: Check if store_split overwrites assignment
```bash
grep -n "cart_item\[" conscious-cart-coach/api/main.py
grep -n "\.store = " conscious-cart-coach/api/main.py
```

Look for any code that modifies `cart_item.store` after mapping.

### Step 3: Check frontend grouping logic
```bash
find conscious-cart-coach -name "*.tsx" -o -name "*.jsx" | xargs grep -l "group.*store"
```

Verify React code groups by `item.store` not `item.available_stores`.

---

## Expected vs Actual

| Product | CSV Brand | Expected Store | Actual Store (User Report) |
|---------|-----------|----------------|---------------------------|
| Organic Boneless Skinless Chicken Breast | 365 by Whole Foods Market | Whole Foods | FreshDirect ❌ |
| Boneless Skinless Chicken Breast | 365 by Whole Foods Market | Whole Foods | FreshDirect ❌ |
| Boneless Skinless Chicken Thighs | 365 by Whole Foods Market | Whole Foods | FreshDirect ❌ |

**All 365 products show under FreshDirect instead of Whole Foods**

---

## Next Steps

1. ✅ Run Test 1 to verify CSV loading
2. ✅ Run Test 2 with debug logging
3. ✅ Run Test 3 to check API response
4. ⚠️ Based on results, apply targeted fix
5. ⚠️ Verify fix with end-to-end test
