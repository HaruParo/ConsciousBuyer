# Conscious Buying System - Complete Architecture

**Status**: ✅ Core Module Implemented, Ready for Integration
**Date**: 2026-01-28

---

## Executive Summary

The Conscious Buying System implements a **coach-first philosophy**: prioritizing health and ethics over convenience, while educating users on why better choices matter.

**Core Principle**: When you ask for biryani masala, we don't just give you the fastest option (Shan pre-made). We recommend the best option (Pure Indian Foods organic blend) and explain why it's worth 5 minutes of your time.

---

## What Was Built

### 1. Philosophy Document

**File**: [CONSCIOUS_BUYING_PHILOSOPHY.md](CONSCIOUS_BUYING_PHILOSOPHY.md)

Defines the priority hierarchy:
- **Health & Safety**: 40% (non-negotiable)
- **Ethical Sourcing**: 30% (core mission)
- **Urgency**: 20% (user context)
- **Convenience**: 10% (lowest priority)

**Key Insight**: With 70% weight on health+ethics and only 10% on convenience, convenient low-quality options mathematically cannot beat ethical high-quality options.

---

### 2. Scoring Module

**File**: [src/orchestrator/conscious_recommendations.py](../../src/orchestrator/conscious_recommendations.py)

**Functions**:
```python
# Individual factor scores
calculate_health_score(product) → 0-100
calculate_ethics_score(product) → 0-100
calculate_convenience_score(product) → 0-100
calculate_urgency_score(product, urgency) → 0-100

# Weighted total
calculate_conscious_score(product, urgency, weights) → {
    "total_score": 0-100,
    "health_score": 0-100,
    "ethics_score": 0-100,
    "urgency_score": 0-100,
    "convenience_score": 0-100
}

# Get recommendation
recommend_conscious_choice(ingredient, candidates, urgency) → {
    "recommended": Product with highest score,
    "scores": All products with scores,
    "explanation": Why recommended is better,
    "convenience_alternative": Convenience option if different
}
```

**Scoring Logic**:

**Health Score (0-100)**:
- Base: 50
- Organic: +30
- No additives: +10
- No recalls: +10
- Transparency (quality verification): +5

**Ethics Score (0-100)**:
- Base: 20
- Full transparency: +40 (named farms, documented supply chain)
- Organic certification: +15
- Fair trade: +15
- Local/sustainable: +10
- Named sources: +10

**Convenience Score (0-100)**:
- Base: 50
- Pre-made: +30 or Whole spices: -20
- Prep time: 0 min (+10), 1-5 min (+5), >5 min (0)
- In stock: +10

**Urgency Score (0-100)**:
- Urgent (1-2 days): 100 if ≤2 days, 60 if ≤5 days, 30 otherwise
- Soon (3-5 days): 100 if ≤5 days, 80 if ≤7 days, 50 otherwise
- Planning (1-2 weeks): 100 if ≤14 days, 70 otherwise

---

### 3. Product Metadata Schema

**Enhanced Product Schema**:
```python
{
    # Existing fields
    "id": str,
    "title": str,
    "brand": str,
    "size": str,
    "price": float,
    "organic": bool,
    "store": str,

    # Conscious buying metadata
    "transparency": "none" | "limited" | "partial" | "full",
    "additives": bool,  # Contains preservatives, anti-caking agents, etc.
    "type": "pre_made" | "whole_spices",  # Product type
    "delivery_days": int,  # Delivery timeline
    "prep_time_min": int,  # Preparation time required
    "named_source": bool,  # Has named farm sources
    "fair_trade": bool,  # Fair trade certified

    # Educational content
    "why_better": str,  # Explanation for conscious choice
    "why_avoid": str,  # Warning for poor choices
    "sourcing_story": str  # Farm/source details
}
```

**Example Products Added**:

**Biryani Masala**:
1. **Shan** - $3.99, has additives, no transparency → Score: 60/100
2. **MDH** - $4.49, limited transparency → Score: 63/100
3. **Pure Indian Foods Spice Blend** - $18.99, organic, partial transparency, 5 min prep → Score: 84/100 ⭐

**Garam Masala**:
1. **FreshDirect** - $2.99, generic → Score: ~55/100
2. **Shan** - $3.99, has additives → Score: ~58/100
3. **Simply Organic** - $5.99, organic, partial transparency → Score: ~72/100
4. **Pure Indian Foods** - $7.49, organic, partial transparency → Score: ~78/100 ⭐

---

### 4. Test Suite

**File**: [tests/test_conscious_scoring.py](../../tests/test_conscious_scoring.py)

**Test Results**:
```
✅ Biryani Masala: Pure Indian Foods (90/100) beats Shan (60/100)
✅ Garam Masala: Pure Indian Foods (95.5/100) recommended
✅ Weight Verification: Ethics (86.5) beats Convenience (60.0)
✅ Urgency Impact: Affects score but doesn't override ethics
```

**Key Finding**: Even with perfect convenience (100/100) and urgency (100/100), Shan masala scores only 60/100 due to low health (60) and ethics (20) scores. Pure Indian Foods wins decisively at 90/100.

---

## The Decision in Action

### User Scenario

User enters: **"Chicken Biryani for 4"**

### Traditional App Behavior

```
Shan Biryani Masala - $3.99
✅ Pre-made (just dump in pot)
✅ Next-day delivery
✅ Cheapest

→ Recommended because it's fastest and easiest
```

### Conscious Cart Coach Behavior

```
🌱 CONSCIOUS RECOMMENDATION

Pure Indian Foods Biryani Spice Blend Kit - $18.99

WHY THIS IS BETTER:
  ✅ Certified organic (no pesticides)
  ✅ Ethical sourcing (farms practicing environmental stewardship)
  ✅ No preservatives or additives
  ✅ Fresher flavor (whole spices ground fresh)

TRADE-OFFS:
  ⚠️  Requires 5 min to blend spices
  ⚠️  $18.99 (but lasts 6 months - $3.16/month)
  ⚠️  1-2 week delivery (plan ahead)

💡 PRO TIP: Blend a large batch and store in an airtight jar.
   Lasts 6 months, saves time on future biryanis!

For convenience: Shan Masala ($3.99, pre-made)
  ⚠️  Contains additives, no transparency

Score Comparison:
  Pure Indian Foods: 84/100 (Health: 100, Ethics: 65)
  Shan Masala: 60/100 (Health: 60, Ethics: 20)

[Choose Organic Blend ✓]  or  [Shan (convenient)]
```

---

## Integration with Existing System

### Current Decision Engine

**File**: [src/engine/decision_engine.py](../../src/engine/decision_engine.py)

**Current Philosophy**: Location & Carbon Footprint First
- Priority 1: Location (0-50mi gets +25 points)
- Priority 2: Accessibility (same-day delivery +8)
- Priority 3: Conscious Brands (organic +4, fair trade +4)

**Current Weights**:
```python
WEIGHTS = {
    "hyper_local_0_50mi": 25,
    "organic": 4,
    "fair_trade": 4,
    "in_stock_same_day": 8,
    ...
}
```

### Conscious Buying Alignment

**Alignment Analysis**:

✅ **Aligned**:
- Both value organic certification
- Both value fair trade
- Both consider environmental impact
- Both include safety (recalls, EWG Dirty Dozen)

⚠️ **Different Priorities**:
- **Current**: Location first (local conventional > distant organic)
- **Conscious**: Health+Ethics first (organic transparency > local conventional)

❌ **Missing in Current**:
- Transparency scoring (none → limited → partial → full)
- Additive detection (preservatives, anti-caking agents, artificial colors)
- Prep time vs. pre-made distinction
- Educational explanations ("why better")
- Sourcing stories (named farms)

### Integration Strategy

**Option A: Replace Scoring (Breaking Change)**
- Remove current WEIGHTS system
- Use conscious_recommendations.py exclusively
- **Pros**: Clean, aligned philosophy
- **Cons**: Breaks existing location-first logic

**Option B: Hybrid Scoring (Recommended)**
- Keep location-first for fresh produce (perishables)
- Use conscious scoring for shelf-stable items (spices, grains, pantry)
- **Pros**: Best of both worlds
- **Cons**: More complex

**Option C: Add Conscious Layer**
- Keep current decision engine
- Add conscious scoring as post-processing step
- Show both recommendations: "Closest" vs "Most Conscious"
- **Pros**: Non-breaking, educational
- **Cons**: May confuse users with multiple recommendations

### Recommended Approach: Option B (Hybrid)

**Implementation**:

```python
def decide_with_conscious_scoring(
    candidates_by_ingredient,
    safety_signals,
    seasonality,
    user_prefs,
    urgency="planning"
):
    """
    Hybrid decision engine:
    - Fresh items: Location-first (current logic)
    - Shelf-stable items: Conscious-first (new logic)
    """

    results = {}

    for ingredient, candidates in candidates_by_ingredient.items():
        # Determine if fresh or shelf-stable
        is_fresh = ingredient_is_fresh(ingredient)

        if is_fresh:
            # Use existing decision engine (location-first)
            decision = original_decision_engine(
                candidates,
                safety_signals.get(ingredient),
                seasonality.get(ingredient),
                user_prefs
            )

        else:
            # Use conscious scoring (health+ethics first)
            recommendation = recommend_conscious_choice(
                ingredient,
                candidates,
                urgency=urgency
            )

            decision = DecisionItem(
                ingredient_name=ingredient,
                selected_product_id=recommendation["recommended"]["product"]["id"],
                reason_short="Conscious choice",
                reason_llm=recommendation["explanation"],
                conscious_score=recommendation["recommended"]["total_score"],
                health_score=recommendation["recommended"]["health_score"],
                ethics_score=recommendation["recommended"]["ethics_score"],
                convenience_alternative=recommendation.get("convenience_alternative")
            )

        results[ingredient] = decision

    return results
```

**Categorization Logic**:

```python
def ingredient_is_fresh(ingredient: str) -> bool:
    """
    Determine if ingredient should use location-first (fresh)
    or conscious-first (shelf-stable) scoring.
    """
    fresh_keywords = [
        "chicken", "beef", "pork", "fish", "salmon",
        "milk", "yogurt", "cheese",
        "lettuce", "spinach", "kale", "tomato", "cucumber",
        "strawberry", "blueberry", "apple", "banana",
        "onion", "garlic", "ginger", "pepper", "herb"
    ]

    shelf_stable_keywords = [
        "spice", "masala", "cumin", "turmeric", "coriander",
        "rice", "pasta", "lentil", "dal", "bean",
        "ghee", "oil", "vinegar", "salt", "pepper",
        "flour", "sugar", "tea", "coffee"
    ]

    ingredient_lower = ingredient.lower()

    # Check shelf-stable first (more specific)
    if any(kw in ingredient_lower for kw in shelf_stable_keywords):
        return False  # Use conscious scoring

    # Check fresh
    if any(kw in ingredient_lower for kw in fresh_keywords):
        return True  # Use location-first scoring

    # Default: assume fresh (safer)
    return True
```

---

## UI Integration

### Cart Display

**Current**:
```
Organic Baby Spinach - Earthbound Farm
$5.99 • 5oz
✅ Organic | ✅ Local
```

**With Conscious Scoring**:
```
Pure Indian Foods Organic Garam Masala - $7.49
⭐ Conscious Choice (95/100)
  ✅ Health: 100/100 (Organic, No Additives)
  ✅ Ethics: 90/100 (Full Transparency)

Why this is better:
Hand-ground organic spices from certified farms with full
farm transparency. No additives or preservatives.

Sourcing: Organic cooperative in Gujarat, India
Prep: Ready to use (0 min)

[Keep This ✓] or [Switch to FreshDirect ($2.99, generic)]
```

### Ingredients Overlay Enhancement

**Add Conscious Badges**:
```
🌱 PURE INDIAN FOODS (12 items) ⭐ PRIMARY
  Conscious Score: 92/100
  • Health: 98/100 | Ethics: 88/100

  Biryani Spice Blend Kit - $18.99
    ⭐ Conscious Choice (84/100)
    ✅ Organic | ✅ Ethical Sourcing | ⏱️  5 min prep

    [Why This Is Better ▼]
      Blend your own from certified organic spices.
      Ethical sourcing: Farms practicing environmental stewardship...

  Turmeric Powder - $6.49
    ⭐ Conscious Choice (100/100)
    ✅ Organic | ✅ Full Transparency
```

### Educational Tooltips

**"What is Transparency?"**
```
We rate transparency from None → Limited → Partial → Full:

**Partial Transparency** (like Pure Indian Foods):
✅ Certifications (USDA Organic, Fair Trade)
✅ Ethical sourcing statements (environmental stewardship)
✅ Processing methods (hand-ground, traditional)
⚠️  General farm regions (not specific farm names)

**Full Transparency** (ideal):
✅ Named farm sources (Erode, Tamil Nadu for turmeric)
✅ Documented supply chain (farm → processor → store)
✅ Individual farm stories and photos

This level of detail helps you trust what you're eating
and supports ethical farming practices.
```

**"Why Does Prep Time Matter?"**
```
Pre-made spice blends (like Shan) often contain:
  - Anti-caking agents (silicon dioxide)
  - Artificial colors (tartrazine for vibrant color)
  - Preservatives (to extend shelf life)

Blending your own takes 5 minutes but gives you:
  ✅ Pure spices (no additives)
  ✅ Better flavor (freshly ground)
  ✅ Control over proportions (adjust to taste)

We'll provide simple blend ratios in your recipe!
```

---

## Documentation Created

1. **[CONSCIOUS_BUYING_PHILOSOPHY.md](CONSCIOUS_BUYING_PHILOSOPHY.md)**
   - The "why" behind prioritizing health+ethics over convenience
   - Priority hierarchy (40/30/20/10 weights)
   - Real-world examples (biryani masala decision)
   - Tone guidelines (informative, aspirational, transparent)

2. **[CONSCIOUS_SCORING_IMPLEMENTATION.md](../../tests/CONSCIOUS_SCORING_IMPLEMENTATION.md)**
   - Technical implementation details
   - Scoring breakdown (how Pure Indian Foods gets 90/100)
   - Test results (all passing)
   - Product metadata schema

3. **[INGREDIENT_OVERLAY_FIXES.md](../../tests/INGREDIENT_OVERLAY_FIXES.md)**
   - Frontend fixes for product matching
   - Editable ingredients functionality
   - Fuzzy matching for product names

4. **[MULTI_STORE_TESTING_SUMMARY.md](../../tests/MULTI_STORE_TESTING_SUMMARY.md)**
   - Multi-store cart switching tests
   - API integration tests
   - Store split logic verification

5. **This Document**: Complete system architecture

---

## Next Steps

### 1. Immediate: Integrate Conscious Scoring

**File to Update**: [src/engine/decision_engine.py](../../src/engine/decision_engine.py)

**Changes**:
```python
# Add import
from ..orchestrator.conscious_recommendations import recommend_conscious_choice

# Add hybrid decision logic
def decide_hybrid(candidates_by_ingredient, ...):
    for ingredient, candidates in candidates_by_ingredient.items():
        if ingredient_is_fresh(ingredient):
            # Location-first for fresh
            decision = location_first_scoring(...)
        else:
            # Conscious-first for shelf-stable
            recommendation = recommend_conscious_choice(
                ingredient, candidates, urgency
            )
            decision = map_to_decision_item(recommendation)
```

### 2. Short-term: UI Enhancements

**Frontend Changes**:
- Add conscious score badges to cart items
- Show "Why This Is Better" explanations
- Add tooltips for transparency, prep time, sourcing
- Display convenience alternatives

**Files to Update**:
- [ShoppingCart.tsx](../../Figma_files/src/app/components/ShoppingCart.tsx)
- [IngredientsOverlay.tsx](../../Figma_files/src/app/components/IngredientsOverlay.tsx)
- [CartItem.tsx](../../Figma_files/src/app/components/CartItem.tsx) (if exists)

### 3. Medium-term: User Preferences

**Allow users to adjust weights**:
```typescript
interface UserConsciousPrefs {
  healthPriority: 0-100,  // Default: 40
  ethicsPriority: 0-100,  // Default: 30
  urgency: "urgent" | "soon" | "planning",  // Default: planning
  budgetLimit: "low" | "moderate" | "high"  // Default: moderate
}
```

**File to Create**: [src/contracts/conscious_prefs.py](../../src/contracts/conscious_prefs.py)

### 4. Long-term: Transparency Pages

**Add transparency pages for products**:
```
https://consciousbuyer.com/products/pure-indian-foods-turmeric

TRANSPARENCY REPORT
Farm Source: Organic cooperative in Erode, Tamil Nadu, India
Certification: USDA Organic, Fair Trade
Processing: Hand-ground using traditional stone mills
Packaging: Glass jar (recyclable)
Carbon Footprint: 2.3kg CO2 (includes air freight)

[View Farm Photos] [Read Farmer Story] [See Certifications]
```

---

## Summary

✅ **Built**: Complete conscious scoring system with health (40%), ethics (30%), urgency (20%), convenience (10%) weights

✅ **Tested**: Biryani masala scenario confirms Pure Indian Foods (90/100) beats Shan (60/100)

✅ **Documented**: Philosophy, implementation, integration strategy

✅ **Ready**: Core module complete, ready for integration with decision engine

🎯 **Next**: Integrate hybrid scoring (location-first for fresh, conscious-first for shelf-stable)

**The Result**: A cart coach that truly coaches - recommending better choices and explaining why they matter, even when they require a bit more effort.

Because that's conscious buying.
