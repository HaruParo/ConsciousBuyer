# Opik Testing Guide - Dummy Proof Edition
*How to Evaluate & Test Every Part of Conscious Cart Coach*

## 🎯 What is Opik and Why Use It?

**Opik** is like a **video recorder for your AI system**. It records:
- What went into each agent (inputs)
- What came out (outputs)
- How long it took
- Whether it succeeded or failed
- What decisions were made and why

**Think of it like this:**
- Without Opik: Your system is a black box. You only see the final cart, not how it was built.
- With Opik: You can rewind and watch every step - ingredient extraction, product matching, decision making, quantity calculation.

**Key Point**: Opik tests **EVERYTHING**, not just LLM calls:
- ✅ LLM prompts and responses
- ✅ Agent logic (template matching, scoring)
- ✅ Data transformations (ingredient scaling, unit conversions)
- ✅ Database queries (product lookups)
- ✅ Decision engine scoring (why product A beat product B)

---

## 📋 TESTING ORDER (Start Here!)

### Phase 1: Test Ingredient Agent (FIRST)
**Why first?** If this fails, everything else fails. Garbage in = garbage out.

### Phase 2: Test Product Agent
**Why second?** After ingredients are extracted, we need to find products for them.

### Phase 3: Test Safety/Seasonal Agents (Parallel)
**Why together?** These enrich product data independently, don't depend on each other.

### Phase 4: Test Decision Engine
**Why last?** Decision engine uses outputs from ALL previous agents. Test it last.

### Phase 5: Test Full Orchestrator
**Why finally?** End-to-end testing to verify all agents work together correctly.

---

## 🧪 PHASE 1: TEST INGREDIENT AGENT

### What You're Testing

**Input**: User prompt (e.g., "chicken biryani for 4")

**Output**: List of ingredients with quantities, units, categories

**Questions to Answer**:
1. Did it extract ALL ingredients? (not missing spinach, onions, etc.)
2. Are quantities correct? (4 servings = 2 lb chicken, not 0.5 lb)
3. Are units normalized? ("2 cups" vs "2 c" vs "2C")
4. Did it detect the recipe correctly? ("chicken biryani" matched template)
5. Did it scale correctly? (4 servings = 2X the base recipe for 2)

---

### Test Cases (Create These in Opik)

**Test Case 1: Simple Recipe with Servings**
```
Input: "chicken biryani for 4"

Expected Output:
{
  "ingredients": [
    {"name": "chicken", "qty": 2.0, "unit": "lb", "category": "protein"},
    {"name": "basmati rice", "qty": 2.0, "unit": "cup", "category": "grain"},
    {"name": "onions", "qty": 2.0, "unit": "large", "category": "produce_vegetables"},
    {"name": "yogurt", "qty": 0.5, "unit": "cup", "category": "dairy"},
    {"name": "ginger", "qty": 1.0, "unit": "inch", "category": "spice"},
    {"name": "garlic", "qty": 6.0, "unit": "clove", "category": "spice"},
    {"name": "cilantro", "qty": 0.5, "unit": "bunch", "category": "produce_herbs"},
    {"name": "mint", "qty": 0.25, "unit": "bunch", "category": "produce_herbs"},
    ...
  ],
  "servings": 4,
  "detected_recipe": "chicken_biryani"
}

What to Check:
- ✅ All 13 ingredients present?
- ✅ Chicken scaled to 2 lb (base is 1 lb for 2 servings, 4 servings = 2X)
- ✅ Rice scaled to 2 cups (base is 1 cup)
- ✅ Detected recipe matches template?
- ⚠️ FAIL if missing ingredients (cilantro, saffron)
- ⚠️ FAIL if wrong quantities (4 lb chicken instead of 2 lb)
```

**Test Case 2: Ambiguous Request (LLM vs Template)**
```
Input: "I want to make something healthy with chicken and spinach for 6 people"

Expected Output (LLM mode):
{
  "ingredients": [
    {"name": "chicken", "qty": 3.0, "unit": "lb", "category": "protein"},
    {"name": "spinach", "qty": 2.0, "unit": "bunch", "category": "produce_greens"},
    ...
  ],
  "servings": 6,
  "detected_recipe": "custom"
}

Expected Output (Template mode):
{
  "error": "No matching recipe template",
  "suggested_recipes": ["chicken_tikka", "chicken_stir_fry"]
}

What to Check:
- ✅ LLM mode: Extracts reasonable ingredients?
- ✅ Template mode: Suggests similar recipes?
- ✅ Quantities scaled to 6 servings?
- ⚠️ FAIL if no ingredients extracted
```

**Test Case 3: Fractional Servings**
```
Input: "chicken biryani for 1"

Expected Output:
{
  "ingredients": [
    {"name": "chicken", "qty": 0.5, "unit": "lb", "category": "protein"},
    {"name": "basmati rice", "qty": 0.5, "unit": "cup", "category": "grain"},
    ...
  ],
  "servings": 1,
  "detected_recipe": "chicken_biryani"
}

What to Check:
- ✅ Scaled down correctly? (0.5X base recipe)
- ✅ No negative quantities?
- ✅ Minimum thresholds respected? (1 pinch saffron, not 0.5 pinch)
```

---

### How to Create This Test in Opik

**Step 1: Write Test Script** (`tests/test_ingredient_agent.py`)

```python
import opik
from src.agents.ingredient_agent import IngredientAgent

# Configure Opik
opik.configure(project_name="conscious-cart-coach-tests")

def test_chicken_biryani_for_4():
    """Test Case 1: Simple recipe with servings."""

    # Start trace
    with opik.trace(name="test_ingredient_agent", tags=["ingredient", "chicken_biryani"]):
        agent = IngredientAgent(use_llm=False)  # Template mode

        # Track the agent call
        result = opik.track(
            name="extract_ingredients",
            input={"prompt": "chicken biryani for 4", "servings": 4},
            output=agent.extract("chicken biryani for 4", servings=4),
        )

        # Assertions
        ingredients = result.facts.get("ingredients", [])

        # Check 1: All ingredients present?
        expected_ingredients = ["chicken", "basmati rice", "onions", "yogurt", "ginger",
                                "garlic", "cilantro", "mint", "tomatoes", "garam masala",
                                "turmeric", "chili powder", "saffron"]
        actual_ingredient_names = [ing["name"] for ing in ingredients]

        for expected in expected_ingredients:
            assert expected in actual_ingredient_names, f"Missing ingredient: {expected}"

        # Check 2: Correct quantities?
        chicken = next((ing for ing in ingredients if ing["name"] == "chicken"), None)
        assert chicken is not None, "Chicken not found"
        assert chicken["qty"] == 2.0, f"Expected 2 lb chicken, got {chicken['qty']}"

        # Check 3: Recipe detected?
        detected_recipe = result.facts.get("detected_recipe")
        assert detected_recipe == "chicken_biryani", f"Expected chicken_biryani, got {detected_recipe}"

        print("✅ Test passed: chicken biryani for 4")

if __name__ == "__main__":
    test_chicken_biryani_for_4()
```

**Step 2: Run Test**
```bash
python tests/test_ingredient_agent.py
```

**Step 3: View in Opik Dashboard**
- Go to https://www.comet.com/opik (or your Opik URL)
- Click on "conscious-cart-coach-tests" project
- You'll see each test run with:
  - Input: {"prompt": "chicken biryani for 4", "servings": 4}
  - Output: {ingredients: [...], servings: 4, detected_recipe: "chicken_biryani"}
  - Duration: 23ms
  - Status: ✅ Success or ❌ Failed

**Step 4: Compare Runs**
- Run the test 10 times with different prompts
- Compare outputs side-by-side in Opik
- Look for patterns in failures

---

## 🧪 PHASE 2: TEST PRODUCT AGENT

### What You're Testing

**Input**: List of ingredients (from Phase 1)

**Output**: Product candidates for each ingredient

**Questions to Answer**:
1. Did it find products for ALL ingredients?
2. Are products relevant? (not returning "onion powder" for "onions")
3. Are there multiple options per ingredient? (cheap, balanced, conscious)
4. Are prices realistic?
5. Are unit prices calculated correctly? ($3.99 for 5oz = $0.798/oz)
6. **Are distances calculated?** (Lancaster PA = 75 miles from Iselin NJ)

---

### Test Cases

**Test Case 1: Common Ingredient (Chicken)**
```
Input: [{"name": "chicken", "qty": 2.0, "unit": "lb"}]

Expected Output:
{
  "candidates_by_ingredient": {
    "chicken": [
      {
        "product_id": "ch001",
        "title": "Farmer Focus Organic Boneless Chicken Breast",
        "brand": "Farmer Focus",
        "size": "1.25 lb",
        "price": 8.99,
        "unit_price": 7.19,
        "unit_price_unit": "lb",
        "organic": true,
        "metadata": {
          "distance_miles": 150,  # Check this!
          "distance_label": "regional_50_150mi"
        }
      },
      {
        "product_id": "ch002",
        "title": "Bell & Evans Chicken Breast",
        "brand": "Bell & Evans",
        "size": "1 lb",
        "price": 6.99,
        "unit_price": 6.99,
        "unit_price_unit": "lb",
        "organic": false
      },
      ...
    ]
  }
}

What to Check:
- ✅ At least 3 candidates for chicken?
- ✅ Prices span range? (cheap $4-6, mid $7-9, premium $10+)
- ✅ Unit prices correct? (price ÷ size)
- ✅ Distance populated? (metadata.distance_miles)
- ✅ Brands match real brands? (Lancaster, Vital Farms, not "FreshDirect Generic")
- ⚠️ FAIL if only 1 candidate (need options for decision engine)
- ⚠️ FAIL if distance missing (breaks location-first scoring)
```

**Test Case 2: Rare/Specialty Ingredient (Saffron)**
```
Input: [{"name": "saffron", "qty": 1.0, "unit": "pinch"}]

Expected Output:
{
  "candidates_by_ingredient": {
    "saffron": [
      {
        "product_id": "sp001",
        "title": "Burlap & Barrel Kashmir Saffron",
        "brand": "Burlap & Barrel",
        "size": "0.5 oz",
        "price": 18.99,
        "organic": true,
        "metadata": {
          "distance_miles": 3000,  # Imported (expected)
          "distance_label": "import_3000plus_mi"
        }
      }
    ]
  }
}

What to Check:
- ✅ At least 1 candidate? (rare ingredient)
- ✅ Price reflects specialty? ($15-30)
- ✅ Distance shows import? (3000+ miles expected for saffron)
- ⚠️ FAIL if no candidates (return "not found" gracefully)
```

**Test Case 3: Missing Distance Data**
```
Input: [{"name": "spinach", "qty": 1.0, "unit": "bunch"}]

Expected Output:
{
  "candidates_by_ingredient": {
    "spinach": [
      {
        ...
        "metadata": {
          "distance_miles": 150,  # Must be present!
          "distance_label": "regional_50_150mi"
        }
      }
    ]
  }
}

What to Check:
- ⚠️ FAIL if metadata.distance_miles is null or missing
- ⚠️ FAIL if distance_label is null
- ✅ All products must have distance data for location-first scoring
```

---

### How to Create This Test in Opik

```python
import opik
from src.agents.product_agent import ProductAgent

def test_product_agent_chicken():
    """Test product matching for chicken."""

    with opik.trace(name="test_product_agent", tags=["product", "chicken"]):
        agent = ProductAgent()

        ingredients = [{"name": "chicken", "qty": 2.0, "unit": "lb"}]

        result = opik.track(
            name="get_candidates",
            input={"ingredients": ingredients},
            output=agent.get_candidates(ingredients),
        )

        candidates = result.facts.get("candidates_by_ingredient", {}).get("chicken", [])

        # Check 1: At least 3 candidates?
        assert len(candidates) >= 3, f"Expected 3+ candidates, got {len(candidates)}"

        # Check 2: All have distance data?
        for candidate in candidates:
            metadata = candidate.get("metadata", {})
            assert "distance_miles" in metadata, "Missing distance_miles in metadata"
            assert "distance_label" in metadata, "Missing distance_label in metadata"

            distance = metadata["distance_miles"]
            assert distance > 0, f"Invalid distance: {distance}"

        # Check 3: Price range?
        prices = [c["price"] for c in candidates]
        assert min(prices) < 7.0, "No cheap options found"
        assert max(prices) > 9.0, "No premium options found"

        print("✅ Test passed: product agent chicken")

if __name__ == "__main__":
    test_product_agent_chicken()
```

---

## 🧪 PHASE 3: TEST SAFETY & SEASONAL AGENTS (PARALLEL)

### Safety Agent Tests

**What You're Testing**: EWG Dirty Dozen/Clean Fifteen, FDA Recalls

**Test Case: Spinach (Dirty Dozen #2)**
```
Input: [{"name": "spinach", "brand": "Lancaster Farm Fresh"}]

Expected Output:
{
  "ewg_results": {
    "spinach": {
      "bucket": "dirty_dozen",
      "rank": 2,
      "pesticide_score": 97,
      "organic_recommendation": "Required",
      "notes": ["High DDT residues"]
    }
  },
  "recall_status": {
    "spinach": {
      "product_match": false,
      "category_advisory": "none",
      "confidence": "high",
      "data_gap": false
    }
  }
}

What to Check:
- ✅ Spinach classified as "dirty_dozen"?
- ✅ Organic recommendation = "Required"?
- ✅ No active recalls?
- ⚠️ FAIL if classified as "clean_fifteen" (wrong!)
```

### Seasonal Agent Tests

**Test Case: Spinach in May (Peak Season NJ)**
```
Input: [{"name": "spinach"}], current_month: "may"

Expected Output:
{
  "seasonality": {
    "spinach": {
      "status": "peak",
      "is_local": true,
      "notes": "Peak season in NJ (March-May)"
    }
  }
}

What to Check:
- ✅ Status = "peak" in May?
- ✅ is_local = true for NJ?
- ⚠️ FAIL if status = "off" or "imported"
```

**Test Case: Spinach in January (Storage Season)**
```
Input: [{"name": "spinach"}], current_month: "january"

Expected Output:
{
  "seasonality": {
    "spinach": {
      "status": "storage",
      "is_local": true,
      "notes": "Storage season (greenhouse or stored)"
    }
  }
}

What to Check:
- ✅ Status = "storage" or "available" in January?
- ⚠️ FAIL if status = "peak" (wrong season)
```

---

## 🧪 PHASE 4: TEST DECISION ENGINE

### What You're Testing

**This is the MOST IMPORTANT test** - it determines what products the user actually sees.

**Input**:
- Product candidates (from Product Agent)
- Safety signals (from Safety Agent)
- Seasonality signals (from Seasonal Agent)
- User preferences

**Output**: Scored and ranked products with reasons

**Questions to Answer**:
1. **Is location scored FIRST?** (local products beat distant organic?)
2. Are Dirty Dozen items forced to organic?
3. Are recall products disqualified?
4. Are reasons accurate? ("Peak season local" vs "Organic option")
5. Are quantities calculated correctly? (3 packages for 6 lb chicken)
6. Are explanations clear and honest about trade-offs?

---

### Critical Test: Location-First Priority

**Test Case: Lancaster Spinach (75mi) vs California Spinach (3000mi)**

```python
Input:
candidates = [
    {
        "product_id": "sp_lancaster",
        "title": "Lancaster Farm Fresh Organic Spinach",
        "brand": "Lancaster Farm Fresh",
        "price": 3.99,
        "size": "5oz",
        "organic": True,
        "metadata": {
            "distance_miles": 75,
            "distance_label": "regional_50_150mi",  # +20 points
            "business_model": "farmer_cooperative",  # +8 points
        }
    },
    {
        "product_id": "sp_earthbound",
        "title": "Earthbound Farm Organic Spinach",
        "brand": "Earthbound Farm",
        "price": 4.99,
        "size": "10oz",
        "organic": True,
        "metadata": {
            "distance_miles": 3000,
            "distance_label": "import_3000plus_mi",  # -15 points
            "business_model": "corporate",  # +0 points
        }
    }
]

safety_signals = {
    "spinach": {
        "ewg_bucket": "dirty_dozen",  # Organic required
        "organic_recommended": True
    }
}

seasonality = {
    "spinach": {
        "status": "peak",  # +15 points for local
        "is_local": True
    }
}

Expected Output:
{
  "recommended": {
    "product_id": "sp_lancaster",
    "reason_short": "Regional (< 150mi)",  # Location reason FIRST
    "score": 95,  # +20 distance +15 peak +8 cooperative +5 dirty dozen organic
    "attributes": ["Organic", "Local", "In Season"],
    "quantity": 2,  # For 1 bunch spinach (5oz packages)
  },
  "cheaper_neighbor": null,  # Lancaster is already cheapest per oz
  "conscious_neighbor": {
    "product_id": "sp_earthbound",  # Worse score due to distance!
    "score": 60,  # -15 distance +5 dirty dozen organic
  }
}

What to Check:
- ✅ Lancaster wins despite lower total price? (location matters more)
- ✅ Reason mentions "Regional" or "Local" FIRST (not "Organic")?
- ✅ Score difference shows location impact? (95 vs 60 = 35 point gap)
- ✅ Earthbound is "conscious_neighbor" not "recommended"?
- ⚠️ FAIL if Earthbound wins (distant organic beat local!)
- ⚠️ FAIL if reason says "Organic option" first (should be "Regional")
```

### Critical Test: Dirty Dozen Override

**Test Case: Strawberries - Conventional Should Lose**

```python
Input:
candidates = [
    {
        "product_id": "sb_local_conventional",
        "title": "NJ Farm Conventional Strawberries",
        "price": 3.99,
        "organic": False,  # ❌ Dirty Dozen requires organic
        "metadata": {
            "distance_miles": 25,
            "distance_label": "hyper_local_0_50mi",  # +25 points
        }
    },
    {
        "product_id": "sb_driscoll_organic",
        "title": "Driscoll's Organic Strawberries",
        "price": 6.99,
        "organic": True,  # ✅ Meets Dirty Dozen requirement
        "metadata": {
            "distance_miles": 150,
            "distance_label": "regional_50_150mi",  # +20 points
        }
    }
]

safety_signals = {
    "strawberries": {
        "ewg_bucket": "dirty_dozen",  # Rank #1, organic REQUIRED
        "organic_recommended": True
    }
}

Expected Output:
{
  "recommended": {
    "product_id": "sb_driscoll_organic",  # Organic wins despite higher price
    "reason_short": "Organic recommended (EWG)",  # Safety overrides location
    "score": 75,
    "attributes": ["Organic", "In Season"],
  },
  "cheaper_neighbor": null,  # No conventional option for Dirty Dozen
  "conscious_neighbor": null,
}

What to Check:
- ✅ Organic wins despite being farther and more expensive?
- ✅ Conventional gets heavy penalty? (score < 30)
- ✅ Reason mentions EWG/safety?
- ⚠️ FAIL if conventional wins (health risk!)
```

### Test: Quantity Reconciliation (LLM-Guided)

**Test Case: Chicken for 12 People**

```python
Input:
ingredient = {"name": "chicken", "qty": 6.0, "unit": "lb"}
product = {
    "title": "Organic Chicken Breast",
    "size": "2 lb",
    "unit_price": 8.99,
}
servings = 12

Expected Output:
{
  "quantity": 3,  # 6 lb ÷ 2 lb per package = 3 packages
  "quantity_reasoning": "6 lb required divided by 2 lb per package = 3 packages",
  "quantity_unit_conversion": "lb to lb (direct conversion)"
}

What to Check:
- ✅ Correct calculation? (6 ÷ 2 = 3)
- ✅ Always rounds up? (6.1 lb needed = 4 packages, not 3.05)
- ✅ Reasoning is clear?
- ⚠️ FAIL if quantity = 0 or negative
- ⚠️ FAIL if fractional (2.5 packages - should round to 3)
```

---

## 🧪 PHASE 5: TEST FULL ORCHESTRATOR (END-TO-END)

### What You're Testing

**The entire pipeline from user prompt to final cart**

**Input**: "chicken biryani for 12"

**Expected Flow**:
1. Ingredient Agent: Extract 13 ingredients, scale to 12 servings
2. Product Agent: Find 3-5 candidates per ingredient
3. Safety Agent: Check EWG status, recalls
4. Seasonal Agent: Check seasonality (May = peak spinach)
5. Decision Engine: Score all, pick best based on location-first
6. Quantity Reconciler: Calculate packages needed

**Output**: Cart with 13 items, all with quantities, prices, reasons

---

### Critical End-to-End Test

```python
def test_full_orchestrator():
    """Test complete flow from prompt to cart."""

    with opik.trace(name="test_e2e_orchestrator", tags=["orchestrator", "e2e"]):
        from src.orchestrator import Orchestrator

        orch = Orchestrator(
            use_llm_extraction=False,  # Template mode
            use_llm_explanations=True,  # Enable quantity reconciliation
        )

        bundle = opik.track(
            name="process_prompt",
            input={"prompt": "chicken biryani for 12", "servings": 12},
            output=orch.process_prompt("chicken biryani for 12", servings=12),
        )

        # Check 1: All ingredients have products?
        assert bundle.item_count >= 10, f"Expected 10+ items, got {bundle.item_count}"

        # Check 2: All items have quantities?
        for item in bundle.items:
            assert item.quantity >= 1, f"{item.ingredient_name} has quantity {item.quantity}"
            assert item.quantity_reasoning, f"Missing quantity reasoning for {item.ingredient_name}"

        # Check 3: Local products scored higher?
        local_items = [item for item in bundle.items if "local" in item.reason_short.lower() or "regional" in item.reason_short.lower()]
        assert len(local_items) >= 3, "Not enough local products prioritized"

        # Check 4: Dirty Dozen items are organic?
        spinach_item = next((item for item in bundle.items if item.ingredient_name == "spinach"), None)
        if spinach_item:
            assert "organic" in spinach_item.attributes, "Spinach (Dirty Dozen) must be organic"

        # Check 5: Reasonable total price?
        total = bundle.recommended_total
        assert 50 < total < 150, f"Unrealistic total: ${total} for 12 servings"

        print(f"✅ Test passed: E2E orchestrator (${total:.2f} for 12 servings)")

if __name__ == "__main__":
    test_full_orchestrator()
```

---

## 🔍 HOW TO IDENTIFY WHICH AGENT IS MAKING MISTAKES

### Method 1: Span Drill-Down in Opik

1. **Open Opik Dashboard** → Find failed test
2. **Click on the trace** → See all spans
3. **Look at each span**:
   - `step_ingredients`: Check ingredient extraction
   - `step_candidates`: Check product matching
   - `step_enrich`: Check safety/seasonal data
   - `step_decide`: Check scoring logic

4. **Find the span with unexpected output**
5. **That's the agent making the mistake!**

**Example**:
```
Trace: "test_chicken_biryani_for_12"
  ├─ Span: step_ingredients ✅ (13 ingredients extracted)
  ├─ Span: step_candidates ❌ (only 8 ingredients matched, 5 missing!)
  ├─ Span: step_enrich ✅ (safety data loaded)
  └─ Span: step_decide ✅ (scored 8 items)

PROBLEM: Product Agent failed to find candidates for 5 ingredients
```

---

### Method 2: Compare Inputs vs Outputs

**For each span, ask:**

**Ingredient Agent**:
- Input: "chicken biryani for 12"
- Output: 13 ingredients with scaled quantities
- ❓ Are there 13 ingredients? ❓ Is chicken = 6 lb (not 2 lb)?

**Product Agent**:
- Input: 13 ingredients
- Output: Candidates for each ingredient
- ❓ All 13 ingredients have candidates? ❓ Any "not found"?

**Decision Engine**:
- Input: Candidates + safety + seasonality
- Output: Scored products with reasons
- ❓ Local products scored higher? ❓ Reasons mention location?

---

### Method 3: Add Logging to Each Agent

**Add this to every agent** (`ingredient_agent.py`, `product_agent.py`, etc.):

```python
import logging
logger = logging.getLogger(__name__)

def extract(self, prompt, servings):
    logger.info(f"[IngredientAgent] Input: prompt='{prompt}', servings={servings}")

    # ... do work ...

    logger.info(f"[IngredientAgent] Output: {len(ingredients)} ingredients extracted")
    logger.debug(f"[IngredientAgent] Ingredients: {ingredients}")

    return make_result(...)
```

**Then run with debug logging**:
```bash
export LOG_LEVEL=DEBUG
python -m src.orchestrator.orchestrator
```

**Look for mismatches**:
```
[INFO] [IngredientAgent] Input: prompt='chicken biryani for 12', servings=12
[INFO] [IngredientAgent] Output: 13 ingredients extracted
[INFO] [ProductAgent] Input: 13 ingredients
[INFO] [ProductAgent] Output: 8 ingredients matched, 5 not found  ← PROBLEM HERE!
[ERROR] [ProductAgent] Not found: saffron, cardamom, bay leaves, cloves, cinnamon
```

---

## 🏷️ LLM TAG CREATION FROM EXPLANATIONS

### What Are Tags?

**Tags** are simple labels you attach to products to explain trade-offs:

- `local-hero` = Product from < 150 miles
- `premium-price` = Costs 50%+ more than cheapest option
- `organic-required` = Dirty Dozen item (health safety)
- `best-value` = Cheapest per oz
- `seasonal-peak` = Peak harvest season now
- `imported` = > 3000 miles away
- `farmer-owned` = Farmer cooperative

### How to Generate Tags with LLM

**Prompt to LLM**:

```
Given this product decision:

Product: Lancaster Farm Fresh Organic Spinach
Price: $3.99 for 5oz ($0.798/oz)
Distance: 75 miles
Season: Peak (May)
EWG: Dirty Dozen #2 (organic recommended)
Business: Farmer cooperative

Reason chosen: "Regional (< 150mi)"

Generate 3-5 simple tags (dummy-proof) that explain:
1. Why we picked this product
2. What trade-offs exist (price, distance, organic status)
3. What makes it special

Tags must be:
- Short (2-4 words)
- Clear (no jargon)
- Actionable (user understands the trade-off)

Format: tag-name: explanation
```

**LLM Output**:

```
Tags:
1. local-hero: "From Pennsylvania (75 miles away) - minimal carbon footprint"
2. peak-season: "Harvested this week (May is peak spinach season in PA)"
3. organic-required: "Organic because spinach is #2 on Dirty Dozen (highest pesticides)"
4. farmer-owned: "From Lancaster cooperative (120 family farms own the company)"
5. fresh-pick: "Delivered next-day (picked yesterday, not stored for weeks)"
```

### How to Use These Tags

**In UI** (`ShoppingCart.tsx`):

```tsx
<div className="flex flex-wrap gap-2 mt-2">
  {item.tags?.map(tag => (
    <span
      key={tag.name}
      className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-green-100 text-green-800"
      title={tag.explanation}
    >
      {tag.icon} {tag.label}
    </span>
  ))}
</div>
```

**Example Rendering**:
```
🌟 Local Hero   🍃 Peak Season   ✅ Organic Required   👨‍🌾 Farmer-Owned
```

**On hover**: Shows full explanation

---

## 📊 OPIK DASHBOARD - WHAT TO LOOK FOR

### Key Metrics

**1. Success Rate**: % of traces that complete without errors
- Target: > 95%
- If < 90%: Check which agent is failing

**2. Latency**: Time from prompt to cart
- Target: < 5 seconds (without LLM), < 10 seconds (with LLM)
- If > 15 seconds: Optimize slow agents

**3. Agent Performance**:
```
Ingredient Agent: 95% success, 50ms avg
Product Agent: 88% success, 200ms avg  ← LOW SUCCESS!
Safety Agent: 100% success, 30ms avg
Seasonal Agent: 100% success, 25ms avg
Decision Engine: 98% success, 150ms avg
```

**4. LLM Calls**:
- Quantity Reconciliation: 13 calls per cart (1 per ingredient)
- Cost: $0.001 per cart
- Latency: 500-800ms per ingredient

---

## ✅ CHECKLIST: WHAT TO TEST

### Ingredient Agent
- [ ] Extracts all ingredients from template recipes
- [ ] Scales quantities correctly (1 serving, 4 servings, 12 servings)
- [ ] Detects recipe name correctly
- [ ] Handles ambiguous prompts gracefully (LLM mode)
- [ ] Normalizes units (cups, c, C all become "cup")

### Product Agent
- [ ] Finds candidates for all ingredients
- [ ] Populates distance data (metadata.distance_miles)
- [ ] Provides 3-5 options per ingredient (price range)
- [ ] Handles missing products gracefully ("not found" list)
- [ ] Calculates unit prices correctly

### Safety Agent
- [ ] Classifies Dirty Dozen items correctly (spinach, strawberries, etc.)
- [ ] Recommends organic for Dirty Dozen
- [ ] Checks FDA recalls
- [ ] No false positives (Clean Fifteen not marked dirty)

### Seasonal Agent
- [ ] Peak season detection (spinach in May = peak)
- [ ] Off-season detection (spinach in January = storage/off)
- [ ] Local flag set correctly (NJ/PA/NY = local)

### Decision Engine
- [ ] **Location scored FIRST** (local beats distant organic)
- [ ] Dirty Dozen forces organic (conventional heavily penalized)
- [ ] Recalls disqualify products
- [ ] Reasons accurate ("Regional" not "Organic" for Lancaster spinach)
- [ ] Quantities calculated (3 packages for 6 lb chicken ÷ 2 lb packages)

### Orchestrator (End-to-End)
- [ ] Complete cart generated (all ingredients have products)
- [ ] Reasonable total price ($50-150 for 12 servings)
- [ ] Local products prioritized
- [ ] Dirty Dozen items are organic
- [ ] Quantities make sense (not 0 or 100)

---

## 🚨 COMMON MISTAKES & HOW TO FIX

### Mistake 1: "No ingredients found in meal plan"

**Where**: Ingredient Agent

**Opik Trace**:
```
Input: "i want chicken tikka for 2"
Output: {"ingredients": [], "error": "No recipe match"}
```

**Problem**: Recipe template doesn't match user prompt

**Fix**:
1. Check `RECIPE_TEMPLATES` in `ingredient_agent.py`
2. Add "chicken tikka" to template keywords
3. Or enable `use_llm_extraction=True` for flexible matching

---

### Mistake 2: "All products showing 'distant organic' even though local"

**Where**: Product Agent not populating distance

**Opik Trace**:
```
Span: step_candidates
Output: {
  "candidates": [
    {"metadata": {"distance_miles": null}}  ← PROBLEM!
  ]
}
```

**Fix**:
1. Implement `_calculate_distance()` in ProductAgent
2. Populate `metadata.distance_miles` for ALL products
3. Test with `assert metadata["distance_miles"] > 0`

---

### Mistake 3: "Conventional strawberries winning over organic"

**Where**: Decision Engine not applying EWG override

**Opik Trace**:
```
Span: step_decide
Input: {
  "safety_signals": {"strawberries": {"ewg_bucket": "dirty_dozen"}}
}
Output: {
  "recommended": {"product_id": "conventional_strawberries"}  ← WRONG!
}
```

**Fix**:
1. Check `_apply_ewg_score()` in DecisionEngine
2. Verify `-20` penalty applied to conventional Dirty Dozen
3. Add constraint: disqualify conventional if `strict_safety=True`

---

## 📝 QUICK START: Run Your First Test

**Step 1: Install Opik**
```bash
pip install opik
```

**Step 2: Set API Key**
```bash
export OPIK_API_KEY="your-key-here"
export OPIK_ENABLED="1"
```

**Step 3: Run Test**
```bash
python tests/test_ingredient_agent.py
```

**Step 4: View Results**
- Go to https://www.comet.com/opik
- Click on "conscious-cart-coach-tests"
- See all test runs with inputs, outputs, durations

**Step 5: Find Failures**
- Filter by status: "Failed"
- Click on failed trace
- Drill down to see which span failed
- Fix the agent code
- Re-run test

---

## 🎓 SUMMARY (TL;DR)

**What is Opik?**
- Video recorder for your AI system
- Records inputs, outputs, durations, errors for every agent

**What to test?**
1. Start with Ingredient Agent (garbage in = garbage out)
2. Then Product Agent (must find products)
3. Then Safety/Seasonal Agents (parallel, independent)
4. Then Decision Engine (uses all previous outputs)
5. Finally Orchestrator (end-to-end)

**How to test?**
1. Write test script with expected inputs/outputs
2. Wrap agent calls with `opik.track()`
3. Add assertions (checks)
4. Run test, view in Opik dashboard
5. Compare runs side-by-side

**How to find mistakes?**
1. Look at Opik trace → drill down to failed span
2. Compare input vs output for each agent
3. Add debug logging to agents
4. Run test multiple times, look for patterns

**Key Tests**:
- Location-first: Local conventional beats distant organic?
- Dirty Dozen: Organic forced for strawberries/spinach?
- Quantities: 6 lb chicken = 3 packages (2 lb each)?
- Reasons: "Regional (< 150mi)" not "Organic option"?

**Success = 95%+ tests passing, < 5 sec latency, clear reasons, accurate tags**

---

*Start with Ingredient Agent tests TODAY. You'll catch 80% of bugs there.*
