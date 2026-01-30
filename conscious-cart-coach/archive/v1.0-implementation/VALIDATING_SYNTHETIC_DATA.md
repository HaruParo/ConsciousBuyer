# Validating Synthetic Data Recommendations

## The Challenge

With real product listings, you can validate quality by comparing your recommendations against what's actually available in stores. With synthetic data, you need a different approach.

**Question**: *How do you know if your algorithm is working correctly when the data is fake?*

**Answer**: Design test scenarios where you KNOW what the right answer should be, then validate your system produces it.

---

## Validation Strategy (3 Layers)

### Layer 1: Unit Tests - Known Answer Testing
**File**: `tests/test_synthetic_validation.py`

Run automated tests that verify expected behaviors:

```bash
# Run all validation tests
pytest tests/test_synthetic_validation.py -v

# Run specific test class
pytest tests/test_synthetic_validation.py::TestSpinachRecommendations -v

# Run with output to see reasoning
pytest tests/test_synthetic_validation.py -v -s
```

**What it validates:**
- ✅ CHEAPER tier picks lowest price
- ✅ CONSCIOUS tier picks local+organic
- ✅ BALANCED tier picks mid-range
- ✅ Dirty Dozen requires organic in CONSCIOUS
- ✅ Price ordering: CHEAPER < BALANCED < CONSCIOUS
- ✅ All items have clear reasoning

**Example test:**
```python
def test_cheaper_tier_picks_lowest_price(self):
    """For spinach, CHEAPER should pick sp001 ($1.99)."""
    # Run orchestrator
    # Check: Did it pick sp001?
    # Check: Is it the cheapest option?
```

---

### Layer 2: Manual Comparison Tool
**File**: `scripts/compare_recommendations.py`

Mimics how you manually compared real product listings.

#### Compare a single ingredient

```bash
python scripts/compare_recommendations.py spinach
```

**Output**:
```
================================================================================
INGREDIENT: SPINACH (servings: 2)
================================================================================

📦 AVAILABLE PRODUCTS (6 options):

  1.    Spinach Bunch Value - FreshDirect
      $1.99 (10oz) | ID: sp001

  2.    Baby Spinach - FreshDirect
      $2.99 (5oz) | ID: sp002

  3.    Baby Spinach - Fresh Express
      $3.99 (5oz) | ID: sp003

  4.  🌱 Organic Baby Spinach - Fresh Express
      $4.99 (5oz) | ID: sp004

  5.  🌱 Organic Baby Spinach - Earthbound Farm
      $5.99 (5oz) | ID: sp005

  6.  🌱 Local Organic Spinach - Lancaster Farm
      $6.49 (6oz) | ID: sp006

────────────────────────────────────────────────────────────────────────────────
🎯 RECOMMENDATION RESULTS:

CHEAPER TIER:
    Spinach Bunch Value - FreshDirect
  $1.99 (10oz) | Qty: 1
  💭 Reason: Best value per ounce

BALANCED TIER:
  🌱 Organic Baby Spinach - Fresh Express
  $4.99 (5oz) | Qty: 1
  💭 Reason: Organic quality at reasonable price

CONSCIOUS TIER:
  🌱 Local Organic Spinach - Lancaster Farm
  $6.49 (6oz) | Qty: 1
  💭 Reason: Local farm, organic, supports regional agriculture
```

**This lets you visually confirm:**
- Are all 6 products showing up?
- Did CHEAPER pick the actual cheapest option?
- Did CONSCIOUS pick the local+organic option?
- Does the reasoning make sense?

#### Compare a full cart

```bash
python scripts/compare_recommendations.py --cart "chicken biryani for 4"
```

Shows all 3 tiers side-by-side with pricing comparison.

#### Run validation checks

```bash
python scripts/compare_recommendations.py --validate
```

Runs predefined validation tests and prints ✅/❌ results.

---

### Layer 3: Scoring Breakdown Tool
**File**: `scripts/explain_scoring.py`

Shows EXACTLY why each product scored the way it did.

```bash
python scripts/explain_scoring.py spinach
```

**Output**:
```
================================================================================
SCORING BREAKDOWN: SPINACH
================================================================================

🔍 ENRICHMENT DATA:
────────────────────────────────────────────────────────────────────────────────
  Safety:
    • EWG Bucket: middle
    • ✅ No recalls
  Seasonality:
    • Status: available
    • Is Local: True
    • Bonus: +10 points
    • Spinach is locally available in NJ (Jan)

────────────────────────────────────────────────────────────────────────────────
📊 PRODUCT SCORES:

🥇 🌱 Local Organic Spinach
   Lancaster Farm | $6.49 (6oz)
   Score: 95.0 points
   Breakdown:
     • Base: 50
     • organic: +4
     • hyper_local_0_50mi: +25
     • seasonal_available: +10

🥈 🌱 Organic Baby Spinach
   Earthbound Farm | $5.99 (5oz)
   Score: 74.0 points
   Breakdown:
     • Base: 50
     • organic: +4
     • regional_50_150mi: +20

🥉 🌱 Organic Baby Spinach
   Fresh Express | $4.99 (5oz)
   Score: 74.0 points
   Breakdown:
     • Base: 50
     • organic: +4
     • regional_50_150mi: +20

4.    Baby Spinach
   Fresh Express | $3.99 (5oz)
   Score: 70.0 points
   Breakdown:
     • Base: 50
     • regional_50_150mi: +20

5.    Baby Spinach
   FreshDirect | $2.99 (5oz)
   Score: 70.0 points
   Breakdown:
     • Base: 50
     • regional_50_150mi: +20

6.    Spinach Bunch Value
   FreshDirect | $1.99 (10oz)
   Score: 70.0 points
   Breakdown:
     • Base: 50
     • regional_50_150mi: +20

================================================================================
💡 KEY INSIGHTS:

✓ Top pick: Local Organic Spinach (Lancaster Farm)
  Why: organic, hyper_local_0_50mi, seasonal_available

✓ Lowest pick: Spinach Bunch Value (FreshDirect)
  Why: (no bonuses beyond base regional score)

✓ Price range: $4.50 difference
  Cheapest: $1.99
  Most expensive: $6.49

✓ Organic options: 3/6
```

**This answers:**
- WHY did Lancaster Farm score highest? (local +25, organic +4, seasonal +10)
- WHY is FreshDirect value pack ranked low despite low price? (no bonuses)
- Is the scoring algorithm working as designed?

#### Compare two products directly

```bash
python scripts/explain_scoring.py spinach sp001 sp006
```

Head-to-head comparison of cheapest vs. most expensive.

---

## What You're Validating

### 1. **Attribute Detection**
Is the system correctly reading product attributes?

```python
# From synthetic data
{"id": "sp006", "organic": True, "brand": "Lancaster Farm"}

# Verify:
# ✅ Is it detecting organic=True?
# ✅ Is it recognizing "Lancaster" as local brand?
# ✅ Is it applying the right scoring bonuses?
```

### 2. **Scoring Weights**
Are the weights applied correctly?

```python
SCORING_WEIGHTS = {
    "hyper_local_0_50mi": 25,
    "organic": 4,
    "dirty_dozen_no_organic": -20,
}

# Verify:
# ✅ Does Lancaster Farm get +25 for location?
# ✅ Do organic products get +4?
# ✅ Does conventional strawberry get -20 penalty?
```

### 3. **Tier Selection**
Does each tier pick the right product?

| Tier | Expected Behavior | Validation |
|------|------------------|------------|
| CHEAPER | Lowest price | ✅ Check: Is it actually cheapest? |
| BALANCED | Mid-range organic | ✅ Check: Is it organic? Is price in middle? |
| CONSCIOUS | Local + organic | ✅ Check: Is it from local brand? Is it organic? |

### 4. **Safety Overrides**
Does safety trump other factors?

```bash
# Test with Dirty Dozen product
python scripts/compare_recommendations.py strawberries

# Expected:
# ✅ CONSCIOUS: Must be organic
# ✅ CHEAPER: If conventional, should show warning
```

### 5. **Reasoning Quality**
Is the system explaining WHY it made each choice?

```bash
# Check reasoning for all items
python scripts/compare_recommendations.py --cart "spinach for 2"

# Validate:
# ✅ Does CONSCIOUS mention "local" or "farm"?
# ✅ Does CHEAPER mention "value" or "price"?
# ✅ Does BALANCED mention "quality" or "organic"?
```

---

## Example Validation Workflow

### Scenario: Validate "Dirty Dozen" Handling

**Step 1**: Know the expected behavior
- Strawberries are on Dirty Dozen list
- CONSCIOUS tier MUST pick organic
- CHEAPER tier gets -20 penalty for conventional

**Step 2**: Run comparison tool
```bash
python scripts/compare_recommendations.py strawberries
```

**Step 3**: Check results
- ✅ Does CONSCIOUS pick organic strawberries?
- ✅ Does it mention "Dirty Dozen" or "organic required"?

**Step 4**: Run scoring breakdown
```bash
python scripts/explain_scoring.py strawberries
```

**Step 5**: Verify penalties
- ✅ Do conventional products show -20 penalty?
- ✅ Do organic products show +5 bonus?

**Step 6**: Add automated test
```python
def test_dirty_dozen_requires_organic():
    """CONSCIOUS must pick organic for Dirty Dozen."""
    # ... test code ...
    assert item.product.organic == True
```

---

## Using LLM-as-a-Judge

The Judge evaluates **overall cart quality**, not individual products.

```bash
# After creating a cart
python scripts/test_llm_judge.py "chicken biryani for 4"
```

**Judge evaluates:**
1. **Relevance**: Do products match the meal plan?
2. **Value**: Are prices reasonable?
3. **Ethics**: Are local/organic options prioritized?
4. **Safety**: Are recalls/Dirty Dozen handled?
5. **Clarity**: Are explanations clear?

**Example output:**
```json
{
  "overall_score": 4.2,
  "dimensions": {
    "relevance": 5,   // Perfect ingredient match
    "value": 4,       // Good prices
    "ethics": 4,      // Some local products
    "safety": 5,      // No issues
    "clarity": 4      // Clear explanations
  },
  "strengths": [
    "All products match biryani ingredients",
    "Lancaster Farm products prioritized in CONSCIOUS",
    "No recalled products"
  ],
  "improvements": [
    "Could explain spice choices better",
    "BALANCED tier could show more price savings"
  ]
}
```

---

## Red Flags to Watch For

### ❌ Bad: CHEAPER picks organic ($6.49)
**Problem**: Tier selection broken

**Debug**: Run `explain_scoring.py` to see why it scored highest

### ❌ Bad: CONSCIOUS picks FreshDirect over Lancaster Farm
**Problem**: Location scoring not working

**Debug**: Check scoring weights, verify brand detection

### ❌ Bad: Conventional strawberries in CONSCIOUS
**Problem**: EWG Dirty Dozen override not working

**Debug**: Check safety enrichment, verify penalty application

### ❌ Bad: Reasoning says "local" but product is from national brand
**Problem**: Reasoning doesn't match attributes

**Debug**: Check reason generation logic

### ❌ Bad: All 3 tiers have same total price
**Problem**: Tier differentiation broken

**Debug**: Check price-based scoring, tier assignment logic

---

## Validation Checklist

Before demo/deployment:

- [ ] Run all unit tests: `pytest tests/test_synthetic_validation.py -v`
- [ ] Validate 5 key ingredients manually (spinach, strawberries, chicken, onion, rice)
- [ ] Check Dirty Dozen handling (strawberries, spinach)
- [ ] Verify price spread: CONSCIOUS should be 1.5x-3x CHEAPER
- [ ] Test full cart: "chicken biryani for 4"
- [ ] Run LLM Judge on 3 sample carts
- [ ] Check all reasoning is clear and accurate
- [ ] Verify no products missing from any tier

---

## The Big Picture

With synthetic data, you're not validating against "real world truth" - you're validating that:

1. **Your algorithm follows its own rules** (scoring weights applied correctly)
2. **Attributes are detected properly** (organic, brand, price)
3. **Tiers differentiate meaningfully** (price spread, attribute differences)
4. **Safety overrides work** (Dirty Dozen, recalls)
5. **Reasoning matches reality** (explanations match chosen products)

These tools let you validate synthetic recommendations the same way you'd validate real ones - by systematically comparing options, understanding scoring, and checking that choices make sense.

---

## Quick Reference

```bash
# Automated tests
pytest tests/test_synthetic_validation.py -v

# Compare single ingredient
python scripts/compare_recommendations.py <ingredient>

# Compare full cart
python scripts/compare_recommendations.py --cart "<meal plan>"

# Run validation checks
python scripts/compare_recommendations.py --validate

# Explain scoring
python scripts/explain_scoring.py <ingredient>

# Head-to-head comparison
python scripts/explain_scoring.py <ingredient> <id1> <id2>
```
