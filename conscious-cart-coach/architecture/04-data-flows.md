# Data Flows: From CSV to Cart - The Journey of a Product

## The Philosophy: Data Tells a Story

Every product in Conscious Cart Coach isn't just a name and price. It's a story:
- Where it comes from (local co-op vs national chain)
- How it's made (organic certification, production methods)
- Why it matters (Dirty Dozen item, authentic specialty ingredient)
- What you trade off (price vs quality, convenience vs values)

This document traces how that story flows through the system.

## Flow 1: Product Data Loading (Startup)

### The Source: source_listings.csv
```csv
category,product_name,brand,price,unit,size,certifications,packaging,nutrition,labels,notes,item_type,seasonality,selected_tier,selection_reason
spices,Cumin Seeds (Jeera),Pure Indian Foods,6.69,ea,3oz,USDA Organic,"Glass jar with plastic cap","Cal: 375, Fat: 22g, Carb: 44g, Protein: 18g","No Gluten, Organic",Best Seller - 54 Reviews,staple,,Premium Specialty,Whole cumin seeds
produce_greens,Organic Red Kale,Generic,$1.99,ea,1lb,USDA Organic,"Clear plastic clamshell","Cal: 33, Fat: 0.6g, Carb: 6g, Protein: 3g","Naturally Gluten-Free, Vegan",CHEAPEST ORGANIC - $0.12/oz,staple,cheaper,Lowest cost organic that satisfies Dirty Dozen #3 rule
```

**What Each Field Means**:
- `category`: Broad type (spices, produce_greens, protein, etc.)
- `product_name`: Display name
- `brand`: Manufacturer/grower
- `price`: As listed (may include $ symbol)
- `unit`: ea (each), lb (per pound), oz (per ounce)
- `size`: Package size (3oz, 1lb, etc.)
- `certifications`: USDA Organic, Local, etc.
- **`packaging`**: Physical packaging type (NEW - Feb 2026)
- **`nutrition`**: Nutrition facts from Open Food Facts API (NEW - Feb 2026)
- **`labels`**: Ethical/dietary labels like Grass-Fed, Vegan, Non-GMO (NEW - Feb 2026)
- `notes`: Additional context (reviews, sales, warnings)
- `item_type`: staple, specialty, convenience
- `seasonality`: When product is in season (if produce)
- `selected_tier`: cheaper, balanced, conscious (pre-categorized)
- `selection_reason`: Why this tier was chosen

### Metadata Enrichment (New - February 2026)

Three new metadata fields were added to enhance decision-making transparency:

**1. Packaging (100% coverage)**
- Inferred from product category and brand-specific rules
- Examples: "Glass jar with aluminum cap" (Pure Indian Foods), "Clear plastic clamshell" (produce), "Loose bulk in produce bag"
- **Why it matters**: Influences scoring (+6 for loose/paper, +4 for glass, -4 for plastic clamshells)
- **Source**: Rules-based inference in `scripts/add_packaging_column.py`

**2. Nutrition (12% coverage)**
- Fetched from Open Food Facts API (1 req/sec rate limit)
- Format: "Cal: 45, Fat: 0g, Carb: 11g, Protein: 3g"
- **Why it matters**: Enables future nutrition-based filtering and recommendations
- **Source**: API integration in `scripts/add_nutrition_and_labels.py` with caching

**3. Labels (31% coverage)**
- Animal welfare: Grass-Fed, Cage-Free, Pasture-Raised, Free-Range
- Dietary: Vegan, Gluten-Free, Kosher, Halal
- Ethical: Non-GMO, Fair Trade, B Corp, Rainforest Alliance
- **Why it matters**: Powers transparent decision explanations ("chose grass-fed butter for animal welfare")
- **Source**: Inferred from certifications + Open Food Facts API

### Loading Process
```python
# In src/agents/product_agent.py

class ProductAgent:
    def __init__(self):
        csv_path = Path(__file__).parent.parent.parent / "data" / "alternatives" / "source_listings.csv"

        # Load CSV, skip comment lines
        self.df = pd.read_csv(csv_path, comment='#')

        # Add derived fields
        self.df['available_stores'] = self.df.apply(self._infer_store, axis=1)
        self.df['price_numeric'] = self.df['price'].apply(self._parse_price)

        # Create search index (for fast lookups)
        self._build_search_index()
```

### Store Inference Logic
```python
def _infer_store(row) -> List[str]:
    """
    Determine which stores carry this product based on brand
    and category.

    STORE_EXCLUSIVE_BRANDS = {
        "365 by Whole Foods Market": ["Whole Foods"],
        "Pure Indian Foods": ["Pure Indian Foods"],
        "FreshDirect": ["FreshDirect"],
        # ... etc
    }
    """
    brand = row['brand']

    # Check exclusive brand mapping
    if brand in STORE_EXCLUSIVE_BRANDS:
        return STORE_EXCLUSIVE_BRANDS[brand]

    # Generic products available at multiple stores
    if brand == "Generic":
        return ["FreshDirect", "Whole Foods", "Trader Joe's"]

    # Default: assume FreshDirect carries it
    return ["FreshDirect"]
```

**Result**: Each product now knows which stores carry it

## Flow 2: User Input → Ingredients (Ingredient Agent)

### Input
```json
{
  "meal_plan": "chicken biryani for 4"
}
```

### Ingredient Extraction (Rule-Based)
```python
# In src/agents/ingredient_agent.py

class IngredientAgent:
    def extract_ingredients(self, meal_plan: str) -> List[Ingredient]:
        # Pattern matching for known dishes
        if "biryani" in meal_plan.lower():
            return self._get_biryani_ingredients(servings=4)

        # Fallback: generic parsing
        return self._generic_parse(meal_plan)

    def _get_biryani_ingredients(self, servings: int) -> List[Ingredient]:
        base_recipe = [
            Ingredient(name="chicken", amount=1.5, unit="lb", category="protein"),
            Ingredient(name="basmati rice", amount=2, unit="cup", category="grains"),
            Ingredient(name="onion", amount=2, unit="medium", category="produce"),
            Ingredient(name="tomato", amount=2, unit="medium", category="produce"),
            Ingredient(name="ginger", amount=2, unit="tbsp", category="produce"),
            Ingredient(name="garlic", amount=4, unit="cloves", category="produce"),
            Ingredient(name="cumin", amount=2, unit="tsp", category="spices"),
            Ingredient(name="coriander", amount=1, unit="tbsp", category="spices"),
            Ingredient(name="cardamom", amount=6, unit="pods", category="spices"),
            Ingredient(name="cinnamon", amount=1, unit="stick", category="spices"),
            # ... etc
        ]

        # Scale by servings
        return self._scale_recipe(base_recipe, servings)
```

### Output
```python
[
    Ingredient(name="chicken", amount=1.5, unit="lb", category="protein"),
    Ingredient(name="basmati rice", amount=2, unit="cup", category="grains"),
    Ingredient(name="cumin", amount=2, unit="tsp", category="spices"),
    # ... 10-15 more ingredients
]
```

## Flow 3: Ingredients → Products (Product Agent)

### The Challenge: Fuzzy Matching

**Problem**: Ingredient says "chicken", but products say:
- "365 by Whole Foods Market Boneless Skinless Chicken Breast"
- "Bell & Evans Chicken Thighs"
- "Katie's Best Whole Chicken"

**Solution**: Multi-stage ranking algorithm

### Stage 1: Candidate Filtering
```python
def get_candidates(self, ingredients: List[Ingredient], target_store: str = None) -> Dict[str, Product]:
    results = {}

    for ingredient in ingredients:
        # Stage 1: Find products matching ingredient name
        candidates = self._find_matching_products(ingredient)

        # Stage 2: Filter by store if specified
        if target_store:
            candidates = self._filter_by_store(candidates, target_store)

        # Stage 3: Rank and select best
        best = self._rank_and_select(candidates, ingredient)

        results[ingredient.name] = best

    return results
```

### Stage 1 Detail: String Matching
```python
def _find_matching_products(self, ingredient: Ingredient) -> List[Product]:
    candidates = []

    # Category filtering first (if ingredient has category)
    if ingredient.category:
        subset = self.df[self.df['category'] == ingredient.category]
    else:
        subset = self.df

    # Keyword matching
    keywords = ingredient.name.lower().split()

    for idx, row in subset.iterrows():
        product_text = f"{row['product_name']} {row['brand']}".lower()

        # All keywords must appear in product text
        if all(kw in product_text for kw in keywords):
            candidates.append(self._row_to_product(row))

    return candidates
```

**Example**:
```
Ingredient: "chicken" (category: "protein")

Matches:
✓ "365 Boneless Skinless Chicken Breast" (contains "chicken")
✓ "Bell & Evans Chicken Thighs" (contains "chicken")
✓ "Katie's Best Whole Chicken" (contains "chicken")

Doesn't match:
✗ "Organic Kale" (no "chicken")
✗ "Chicken Broth" (category is "pantry", not "protein")
```

### Stage 2 Detail: Store Filtering
```python
def _filter_by_store(self, candidates: List[Product], target_store: str) -> List[Product]:
    filtered = []

    for product in candidates:
        # Check if product is available at target store
        if target_store in product.available_stores:
            # Additional check: store-exclusive brands
            if product.brand in STORE_EXCLUSIVE_BRANDS:
                allowed_stores = STORE_EXCLUSIVE_BRANDS[product.brand]
                if target_store in allowed_stores:
                    filtered.append(product)
            else:
                filtered.append(product)

    return filtered
```

**Example**:
```
Target store: "FreshDirect"
Candidates:
  - "365 Chicken Breast" (brand: "365 by Whole Foods Market")
  - "Bell & Evans Chicken" (brand: "Bell & Evans")
  - "Katie's Best Chicken" (brand: "Katie's Best")

After filtering:
✓ "Bell & Evans Chicken" (available at FreshDirect)
✓ "Katie's Best Chicken" (available at FreshDirect)
✗ "365 Chicken Breast" (EXCLUSIVE to Whole Foods)
```

### Stage 3 Detail: Ranking Algorithm
```python
def _rank_and_select(self, candidates: List[Product], ingredient: Ingredient) -> Product:
    if not candidates:
        return None  # No match found

    if len(candidates) == 1:
        return candidates[0]  # Obvious choice

    # Score each candidate
    scored = []
    for product in candidates:
        score = self._calculate_quality_score(product, ingredient)
        scored.append((product, score))

    # Sort by score (highest first)
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0]  # Return best product
```

### Component-Based Scoring System (Updated February 2026)

Scoring moved from simple point accumulation to a **7-component system** (0-100 scale, higher is better):

```python
# In src/scoring/component_scoring.py

def compute_total_score(
    ingredient_name: str,
    ingredient_category: str,
    required_form: Optional[str],
    product_title: str,
    is_organic: bool,
    unit_price: float,
    all_unit_prices: list[float],
    delivery_estimate: str,
    prompt: str,
    price_outlier_penalty: int = 0,
    packaging_data: str = ""  # NEW - uses structured packaging data
) -> Tuple[int, Dict[str, int]]:
    base_score = 50

    # 1. EWG Component (-12 to +18 points)
    ewg = compute_ewg_component(ingredient_name, ingredient_category, is_organic)
    # Dirty Dozen + organic: +18
    # Dirty Dozen + conventional: -12
    # Clean Fifteen + organic: +2

    # 2. Form Fit Component (0-14 points)
    form_fit = compute_form_fit_component(required_form, product_title, ingredient_category)
    # Perfect match (fresh ginger → "ginger root"): +14
    # Acceptable (cumin seeds → "whole cumin"): +10

    # 3. Packaging Component (-4 to +6 points) - NOW USES STRUCTURED DATA
    packaging = compute_packaging_component(product_title, packaging_data)
    # Loose/paper: +6
    # Glass jar: +4
    # Plastic bag: +2
    # Clamshell: -4

    # 4. Delivery Component (-10 to 0 points)
    delivery = compute_delivery_component(delivery_estimate, prompt)
    # Slow delivery + "cook tonight" prompt: -10

    # 5. Unit Value Component (0-8 points)
    unit_value = compute_unit_value_component(unit_price, all_unit_prices)
    # Best value (lowest $/oz): +8

    # 6. Outlier Penalty (-20 or 0 points)
    outlier = -20 if price_outlier_penalty > 0 else 0
    # Prevents selecting products >2x median price

    total = base_score + ewg + form_fit + packaging + delivery + unit_value + outlier
    return max(0, min(100, total))
```

**Example Scoring (with metadata)**:
```
Ingredient: "cumin" (required_form: "seeds")

Candidates:
1. Pure Indian Foods Cumin Seeds, 3oz, $6.69, USDA Organic
   Packaging: "Glass jar with plastic cap"
   Base: 50
   EWG: +2 (organic spice, not produce)
   Form Fit: +14 (perfect match: seeds)
   Packaging: +4 (glass jar)
   Delivery: 0 (1 week, but user planning ahead)
   Unit Value: +6 (mid-range value)
   Outlier: 0
   Total: 76/100

2. Generic Cumin Powder, 2oz, $3.99, Non-organic
   Packaging: "Plastic bag"
   Base: 50
   EWG: 0 (non-organic, not produce)
   Form Fit: +2 (minor mismatch: powder vs seeds)
   Packaging: +2 (plastic bag)
   Delivery: 0
   Unit Value: +8 (cheapest option)
   Outlier: 0
   Total: 62/100

Selected: Pure Indian Foods (76 > 62)
Reason: Glass packaging (+2 pts), perfect form match (+12 pts) outweigh cheaper price
```

**Key Improvement**: Packaging scoring now uses the actual `packaging` field from CSV instead of parsing from product title, making scoring more accurate and transparent.

## Flow 4: Products → Quantities (Quantity Agent)

### The Challenge: Unit Conversion

**Problem**: Recipe says "2 tsp cumin", product is "3oz jar"

**Solution**: Convert everything to a common unit, calculate ratio

### Conversion Logic
```python
class QuantityAgent:
    CONVERSIONS = {
        # Spices (volume to weight)
        "cumin_tsp_to_oz": 0.07,  # 1 tsp cumin ≈ 0.07 oz
        "cardamom_pod_to_oz": 0.02,  # 1 pod ≈ 0.02 oz
        "cinnamon_stick_to_oz": 0.1,  # 1 stick ≈ 0.1 oz

        # General volume to weight
        "tsp_to_oz": 0.17,  # Generic approximation
        "tbsp_to_oz": 0.5,
        "cup_to_oz": 8,

        # Produce (count to weight)
        "medium_onion_to_lb": 0.5,  # 1 medium onion ≈ 0.5 lb
        "medium_tomato_to_lb": 0.4,
        "garlic_clove_to_oz": 0.1,
    }

    def calculate_quantity(self, ingredient: Ingredient, product: Product) -> int:
        # Convert ingredient amount to ounces
        needed_oz = self._convert_to_oz(ingredient)

        # Convert product size to ounces
        product_oz = self._parse_size_to_oz(product.size)

        # Calculate how many products needed
        quantity = math.ceil(needed_oz / product_oz)

        return max(1, quantity)  # At least 1
```

### Example Calculation
```python
# Ingredient: 2 tsp cumin
# Product: Cumin Seeds, 3oz

# Step 1: Convert ingredient to oz
needed_oz = 2 tsp × 0.07 oz/tsp = 0.14 oz

# Step 2: Product size already in oz
product_oz = 3 oz

# Step 3: Calculate quantity
quantity = ceil(0.14 / 3) = ceil(0.047) = 1

# Result: Buy 1 jar of 3oz cumin
```

### Edge Cases
```python
# Case 1: Recipe needs MORE than one package
# Ingredient: 2 cups flour
# Product: Flour, 5lb bag (80 oz)
needed_oz = 2 cups × 8 oz/cup = 16 oz
quantity = ceil(16 / 80) = 1  # One bag is enough

# Case 2: Bulk ingredients
# Ingredient: 2 lb chicken
# Product: Chicken breast, $7.99/lb (no fixed size)
# Solution: For per-pound items, quantity = amount needed
quantity = 2  # Buy 2 lbs

# Case 3: Fractional quantities (produce)
# Ingredient: 1/2 onion
# Product: Onions, $1.99 each
needed = 0.5 onions
quantity = ceil(0.5) = 1  # Can't buy half an onion
```

## Flow 5: Products → Cart (Orchestrator + Store Splitting)

### Multi-Store Cart Assembly
```python
# In src/orchestrator/orchestrator.py

def create_cart(self, meal_plan: str) -> CartResponse:
    # Step 1: Extract ingredients
    ingredients = self.ingredient_agent.extract(meal_plan)

    # Step 2: Match products
    products = self.product_agent.get_candidates(ingredients)

    # Step 3: Calculate quantities
    cart_items = []
    for ingredient, product in products.items():
        quantity = self.quantity_agent.calculate(ingredient, product)
        cart_items.append(CartItem(
            product=product,
            quantity=quantity,
            ingredient=ingredient
        ))

    # Step 4: Split by store
    multi_store_cart = self._split_by_store(cart_items)

    # Step 5: Generate explanations
    for item in cart_items:
        item.tags = self.explain_agent.generate_tags(item)

    return CartResponse(stores=multi_store_cart)
```

### Store Splitting Logic
```python
def _split_by_store(self, cart_items: List[CartItem]) -> Dict[str, List[CartItem]]:
    stores = {}

    for item in cart_items:
        # Determine which store this product comes from
        store = item.product.available_stores[0]  # Use first available store

        if store not in stores:
            stores[store] = []

        stores[store].append(item)

    return stores
```

**Example Result**:
```python
{
    "FreshDirect": [
        CartItem(product="365 Chicken Breast", quantity=1),
        CartItem(product="Basmati Rice", quantity=1),
        CartItem(product="Yellow Onions", quantity=1),
        CartItem(product="Tomatoes", quantity=1),
    ],
    "Pure Indian Foods": [
        CartItem(product="Cumin Seeds", quantity=1),
        CartItem(product="Coriander Seeds", quantity=1),
        CartItem(product="Cardamom Green", quantity=1),
        CartItem(product="Cinnamon Ceylon", quantity=1),
    ]
}
```

## Flow 6: Cart → Frontend (JSON Response)

### Backend Response Structure
```json
{
  "stores": {
    "FreshDirect": {
      "items": [
        {
          "catalogueName": "Boneless Skinless Chicken Breast",
          "brand": "365 by Whole Foods Market",
          "price": 7.99,
          "quantity": 1,
          "size": "per lb",
          "available": true,
          "store": "FreshDirect",
          "tags": {
            "whyPick": [
              "USDA Organic certified",
              "No antibiotics used",
              "Good price per pound"
            ],
            "tradeOffs": [
              "Costs $2/lb more than conventional"
            ]
          }
        }
      ],
      "total": 42.96
    },
    "Pure Indian Foods": {
      "items": [
        {
          "catalogueName": "Cumin Seeds (Jeera)",
          "brand": "Pure Indian Foods",
          "price": 6.69,
          "quantity": 1,
          "size": "3oz",
          "available": true,
          "store": "Pure Indian Foods",
          "tags": {
            "whyPick": [
              "Authentic Indian specialty",
              "USDA Organic",
              "Whole seeds for better flavor"
            ],
            "tradeOffs": []
          }
        }
      ],
      "total": 25.67
    }
  },
  "grandTotal": 68.63
}
```

### Frontend Rendering
```typescript
// In frontend/src/app/components/ShoppingCart.tsx

interface CartResponse {
  stores: Record<string, StoreCart>;
  grandTotal: number;
}

interface StoreCart {
  items: CartItem[];
  total: number;
}

function ShoppingCart({ cartData }: { cartData: CartResponse }) {
  return (
    <div>
      {Object.entries(cartData.stores).map(([storeName, storeCart]) => (
        <StoreSection key={storeName}>
          <h2>{storeName}</h2>
          {storeCart.items.map(item => (
            <CartItemCard
              item={item}
              onUpdateQuantity={(qty) => updateQty(item, qty)}
              onRemove={() => removeItem(item)}
              onFindSwap={() => findAlternative(item)}
            />
          ))}
          <SubTotal>{storeCart.total}</SubTotal>
        </StoreSection>
      ))}
      <GrandTotal>{cartData.grandTotal}</GrandTotal>
    </div>
  );
}
```

## Data Quality & Maintenance

### The CSV Update Cycle

1. **Product Research**: Find new products (web scraping, manual entry)
2. **CSV Update**: Add rows to `source_listings.csv`
3. **Size Verification**: Ensure `size` field is accurate (not "varies")
4. **Store Mapping**: Update `STORE_EXCLUSIVE_BRANDS` if new exclusive brands
5. **Git Commit**: Track changes in version control
6. **Backend Restart**: Reload CSV data

### Recent Example: Pure Indian Foods Size Fix

**Problem**: Many Pure Indian Foods products had `size: "varies"` instead of actual sizes

**Solution**:
```python
# update_sizes_v3.py
# Match products by (product_name, price) to get correct size
# Update source_listings.csv with sizes from pure_indian_foods_products.csv
```

**Result**: 34 products updated from "varies" to actual sizes (3oz, 2oz, etc.)

### Data Validation Rules

1. **Price must be numeric**: `$6.69` or `6.69` (parser handles both)
2. **Size must be specific**: `3oz`, `1lb`, `per lb` (not "varies" or "N/A")
3. **Brand must exist**: Cannot be empty
4. **Category must be valid**: One of: `spices`, `produce_greens`, `produce_onions`, `protein`, `grains`, etc.
5. **Exclusive brands must be in mapping**: If brand is store-exclusive, must be in `STORE_EXCLUSIVE_BRANDS`

### Data Completeness Check
```python
def validate_csv(csv_path: str):
    df = pd.read_csv(csv_path, comment='#')

    # Check for missing required fields
    required = ['product_name', 'brand', 'price', 'size', 'category']
    for field in required:
        missing = df[df[field].isna()]
        if not missing.empty:
            print(f"WARNING: {len(missing)} products missing {field}")

    # Check for "varies" in size
    varies = df[df['size'] == 'varies']
    if not varies.empty:
        print(f"WARNING: {len(varies)} products have size='varies'")
        print(varies[['product_name', 'brand', 'price']].to_string())

    # Check for invalid prices
    df['price_numeric'] = df['price'].apply(parse_price)
    invalid_prices = df[df['price_numeric'] <= 0]
    if not invalid_prices.empty:
        print(f"ERROR: {len(invalid_prices)} products have invalid prices")
```

## Performance Optimization: Caching & Indexing

### Problem: O(n) Linear Search

**Current**: For each ingredient, loop through all 353 products
```python
# Slow: O(n × m) where n=ingredients, m=products
for ingredient in ingredients:
    for product in all_products:
        if matches(ingredient, product):
            candidates.append(product)
```

### Solution 1: Category Indexing
```python
# Build index at startup
self.category_index = {}
for product in all_products:
    category = product.category
    if category not in self.category_index:
        self.category_index[category] = []
    self.category_index[category].append(product)

# Fast lookup: O(m/k) where k=number of categories
candidates = self.category_index.get(ingredient.category, [])
```

### Solution 2: Text Search Index
```python
# Build inverted index at startup
self.text_index = {}
for product in all_products:
    words = product.name.lower().split()
    for word in words:
        if word not in self.text_index:
            self.text_index[word] = set()
        self.text_index[word].add(product.id)

# Fast lookup: O(log n) per keyword
keyword_matches = [self.text_index.get(kw, set()) for kw in keywords]
candidate_ids = set.intersection(*keyword_matches)
candidates = [self.products[id] for id in candidate_ids]
```

### Solution 3: LRU Caching (Future)
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_candidates_cached(ingredient_name: str, category: str, target_store: str) -> List[Product]:
    # Expensive search logic here
    return candidates

# Subsequent calls with same args return cached result
```

## The Conscience: How Values Flow Through Data

### Dirty Dozen Prioritization
```
Input: "spinach" (category: produce_greens)
↓
Check: Spinach is #2 on Dirty Dozen list
↓
Preference: Organic spinach strongly preferred
↓
Ranking: Organic products get +20 score
↓
Result: "Organic Baby Spinach" selected over conventional
```

### Local Preference
```
Input: "onions"
↓
Available:
  - Generic Yellow Onion, $0.99/lb (conventional)
  - Lancaster Farm Fresh Coop Yellow Onion, $1.99/lb (local + organic)
↓
Scoring:
  - Generic: 10 (category) + 3 (cheaper) = 13
  - Local Co-op: 10 (category) + 5 (organic) + 8 (local) = 23
↓
Result: Local co-op onion selected (despite 2× price)
```

### Authentic Specialty Ingredients
```
Input: "cardamom" for biryani
↓
Available:
  - FreshDirect Ground Cardamom, $4.99
  - Pure Indian Foods Green Cardamom Pods, $12.99
↓
Scoring:
  - FreshDirect: 10 (category) = 10
  - Pure Indian Foods: 10 (category) + 15 (authentic brand) + 5 (whole vs ground) = 30
↓
Result: Pure Indian Foods pods selected (authenticity matters for biryani)
```

---

**Next**: [Mental Models & Design Decisions](./05-mental-models.md) - The philosophy behind the code



---

**Last Updated**: February 6, 2026 (Added metadata enrichment documentation)
