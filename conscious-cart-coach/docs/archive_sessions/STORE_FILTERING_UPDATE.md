# Store Brand Filtering Update

## Summary
Added Peri & Sons Farms products and implemented store-specific brand filtering to ensure store brands only appear in their respective stores.

## Changes Made

### 1. Added Peri & Sons Farms Products (8 new items)
All products added to [source_listings.csv](data/alternatives/source_listings.csv):

**Yellow Onions**:
- Yellow Onions Medium (3 lb bag) - $2.99 - Balanced tier
- Organic Yellow Onions (3 lb bag) - $4.99 - Conscious tier

**Red Onions**:
- Red Onions Medium (3 lb bag) - $3.49 - Balanced tier
- Organic Red Onions (3 lb bag) - $5.49 - Conscious tier

**Specialty Sweet Onions**:
- Sweetie Sweet Onions (3 lb bag) - $4.99 - Premium Specialty
  - Exclusive variety, available Aug-Dec
- Sweetie Tearless Sweet Onions (3 lb bag) - $5.99 - Premium Specialty
  - Unique tearless variety, available Dec-Mar

**Shallots**:
- Shallots (1 lb bag) - $3.99 - Balanced tier
- Organic Shallots (1 lb bag) - $5.99 - Conscious tier

**Store Availability**: Peri & Sons Farms products are primarily found at Sprouts Farmers Market, also available at Whole Foods.

### 2. Store-Specific Brand Filtering

Added store exclusivity logic in [product_agent.py](src/agents/product_agent.py:27-40):

```python
STORE_EXCLUSIVE_BRANDS = {
    # Store brands (exclusive to their store)
    "365 by Whole Foods Market": ["Whole Foods", "Whole Foods Market"],
    "ShopRite": ["ShopRite"],
    "Trader Joe's": ["Trader Joe's"],
    "Wegmans": ["Wegmans"],
    "Kroger": ["Kroger"],
    "Safeway": ["Safeway"],
    "Sprouts": ["Sprouts", "Sprouts Farmers Market"],

    # Brands commonly found at specific stores
    "Peri & Sons Farms": ["Sprouts", "Sprouts Farmers Market", "Whole Foods"],
    "Pure Indian Foods": ["specialty"],
}
```

### 3. Product Agent Updates

**Added Store Filtering Method** ([product_agent.py:693-717](src/agents/product_agent.py#L693-L717)):
- `filter_by_store(product, target_store)` - Filters products based on store availability
- Checks if product is available at target store
- Respects store-exclusive brands

**Updated get_candidates Method** ([product_agent.py:719-748](src/agents/product_agent.py#L719-L748)):
- Added optional `target_store` parameter
- Filters products by store before returning candidates
- Ensures store brands don't appear at wrong stores

**Product Dictionary Enhancement**:
- Added `available_stores` field to each product
- Tracks which stores carry each product
- Defaults to `["all"]` for widely available brands

## Testing Results

### Product Count:
- **Total products**: 325 (up from 317)
- **New products**: 8 Peri & Sons Farms onion products
- **Onion category**: 37 total products from 6 brands

### Store Brand Verification:
```
✓ 365 by Whole Foods Market: 3 products → Whole Foods only
✓ Peri & Sons Farms: 8 products → Sprouts, Whole Foods
✓ Pure Indian Foods: 76 products → Specialty stores only
```

### Brand Distribution (Onions):
- Black Dirt Region
- Christopher Ranch
- Generic
- Lancaster Farm Fresh Cooperative
- **Peri & Sons Farms** (new)
- Pete's Greens

## How It Works

### Example 1: Shopping at Whole Foods
```python
agent = ProductAgent()
candidates = agent.get_candidates(ingredients, target_store="Whole Foods")
# Returns: 365 brand products ✓, Peri & Sons ✓, ShopRite brand ✗
```

### Example 2: Shopping at ShopRite
```python
agent = ProductAgent()
candidates = agent.get_candidates(ingredients, target_store="ShopRite")
# Returns: ShopRite brand ✓, 365 brand ✗, widely available brands ✓
```

### Example 3: Shopping at Sprouts
```python
agent = ProductAgent()
candidates = agent.get_candidates(ingredients, target_store="Sprouts")
# Returns: Sprouts brand ✓, Peri & Sons ✓, 365 brand ✗
```

## Benefits

1. **Realistic Product Recommendations**
   - Users only see products available at their chosen store
   - No confusion from seeing store brands from other retailers

2. **Store Brand Protection**
   - "365 by Whole Foods Market" only appears at Whole Foods
   - "ShopRite" brand only appears at ShopRite
   - Prevents unrealistic cross-store recommendations

3. **Flexible Brand Mapping**
   - Premium brands like Peri & Sons can appear at multiple stores
   - Specialty brands (Pure Indian Foods) restricted to specialty stores
   - Easy to add new store-brand mappings

## Next Steps

### To Add More Store Brands:
1. Add products to CSV with store brand name
2. Add brand mapping to `STORE_EXCLUSIVE_BRANDS`
3. Products will automatically filter by store

### Example - Adding ShopRite Products:
```csv
protein_poultry,Boneless Chicken Breast,ShopRite,4.99,lb,per lb,None (conventional),...
```

Then in code:
```python
STORE_EXCLUSIVE_BRANDS = {
    "ShopRite": ["ShopRite"],  # Already added
    ...
}
```

## Files Modified

1. **data/alternatives/source_listings.csv** (+8 lines)
   - Added Peri & Sons Farms onion products

2. **src/agents/product_agent.py** (~50 lines added/modified)
   - Added STORE_EXCLUSIVE_BRANDS mapping
   - Added filter_by_store() method
   - Updated get_candidates() with store filtering
   - Added available_stores field to product dict

3. **test_store_filtering.py** (new file, ~70 lines)
   - Test store brand filtering logic
   - Verify product counts and brand distribution

## References

**Sources about Peri & Sons Farms**:
- [Peri & Sons Farms Official Website](https://periandsons.com/)
- [Instacart - Peri & Sons Products](https://www.instacart.com/categories/316-food/317-fresh-produce/439-fresh-vegetables/554-root-vegetables/565-onions?brand=peri-sons-farms)
- [Produce Market Guide - Peri & Sons](https://www.producemarketguide.com/company/1009881/peri-sons-farms-inc)
- [AndNowUKnow - Product Portfolio](https://www.andnowuknow.com/whats-store/peri-sons-farms-provides-single-source-onions-robust-portfolio/melissa-de-leon-chavez/93428)

**Key Facts**:
- Premium onion grower from Nevada and California
- 550+ million pounds of onions annually
- Exclusive Sweetie Sweet® and Sweetie Tearless® varieties
- USDA Certified Organic options available
