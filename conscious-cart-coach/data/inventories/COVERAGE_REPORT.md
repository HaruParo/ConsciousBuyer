# Synthetic Inventory Coverage Report

Generated: generate_synthetic_inventory.py

## Store Inventories

### FreshDirect (freshdirect)
- Total products: 47
- Private label: FreshDirect

### Whole Foods Market (wholefoods)
- Total products: 53
- Private label: 365 by Whole Foods Market

### ShopRite (shoprite)
- Total products: 53
- Private label: Bowl & Basket

### Pure Indian Foods (pure_indian_foods)
- Total products: 60
- Private label: Pure Indian Foods

### Kaiser Grocery (kaiser)
- Total products: 53
- Private label: Kaiser Select

## Coverage Matrix

| Ingredient | FreshDirect | Whole Foods | ShopRite | Pure Indian Foods | Kaiser |
|------------|-------------|-------------|----------|-------------------|--------|
| chicken | 4 | 4 | 4 | — | 4 |
| onions | 4 | 4 | 4 | — | 4 |
| tomatoes | 4 | 4 | 4 | — | 4 |
| yogurt | 4 | 4 | 4 | — | 4 |
| ginger | 3 | 3 | 3 | — | 3 |
| garlic | 3 | 3 | 3 | — | 3 |
| mint | 3 | 3 | 3 | — | 3 |
| cilantro | 3 | 3 | 3 | — | 3 |
| basmati rice | 4 | 4 | 4 | 6 | 4 |
| ghee | 3 | 3 | 3 | 7 | 3 |
| garam masala | — | 3 | 3 | 8 | 3 |
| turmeric | 3 | 3 | 3 | 8 | 3 |
| coriander | 3 | 3 | 3 | 8 | 3 |
| cumin | 3 | 3 | 3 | 8 | 3 |
| cardamom | — | 3 | 3 | 8 | 3 |
| bay leaves | 3 | 3 | 3 | 7 | 3 |

## Store Exclusivity Verification

Private label products are store-exclusive:
✅ No violations detected - all private labels are store-exclusive

## Multi-Store Split Test (Biryani)

Expected outcome for 'chicken biryani for 4':
- Primary store: FreshDirect or Whole Foods (produce, protein, dairy)
- Specialty store: Pure Indian Foods (spices: garam masala, cardamom)
- Unavailable: ~2-3 items (herbs: mint, cilantro; spices: bay leaves)

✅ Ready for Opik evaluation with meaningful candidate sets