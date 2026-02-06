# Scoring System Overhaul - Implementation Plan

## Status: Foundation Complete, Core Changes Pending

### ✅ Completed (Phase 1a)
- Created `src/data/ewg_categories.py` - EWG Dirty Dozen/Clean Fifteen mappings
- Created `src/data/ingredient_categories.py` - Ingredient categorization + form detection
- Created `src/scoring/component_scoring.py` - Component-based scoring engine

### 🔄 In Progress (Phase 1b) - Core Engine Updates

#### File: `src/planner/engine.py`

**Changes Required:**

1. **Add imports** (top of file):
```python
from src.data.ingredient_categories import get_ingredient_category, detect_product_form
from src.data.ewg_categories import get_ewg_category
from src.scoring.component_scoring import compute_total_score, compute_score_drivers
```

2. **Update `_select_products` signature** (line ~320):
```python
def _select_products(
    self,
    enriched: List[Dict],
    store_plan: StorePlan,
    servings: int,
    include_trace: bool,
    ingredient_name: str,  # NEW
    ingredient_form: Optional[str],  # NEW
    prompt: str  # NEW
) -> Dict:
```

3. **Replace `_compute_real_score` method** (line 1338-1381):
```python
def _compute_real_score(
    self,
    candidate_dict: Dict,
    ingredient_name: str,
    ingredient_form: Optional[str],
    all_unit_prices: list[float],
    prompt: str
) -> Tuple[int, Dict[str, int]]:
    """
    Compute component-based score with breakdown.

    Returns:
        (total_score, component_breakdown)
    """
    if candidate_dict is None:
        return 0, {}

    candidate = candidate_dict["candidate"]
    ingredient_category = get_ingredient_category(ingredient_name)

    # Get store delivery estimate
    delivery_estimate = candidate_dict.get("delivery_estimate", "1-2 days")

    # Use new component-based scoring
    score, breakdown = compute_total_score(
        ingredient_name=ingredient_name,
        ingredient_category=ingredient_category,
        required_form=ingredient_form,
        product_title=candidate.title,
        is_organic=candidate.organic,
        unit_price=candidate.unit_price,
        all_unit_prices=all_unit_prices,
        delivery_estimate=delivery_estimate,
        prompt=prompt,
        price_outlier_penalty=candidate_dict.get("price_outlier_penalty", 0)
    )

    return score, breakdown
```

4. **Update `_build_decision_trace` signature** (line 1229):
```python
def _build_decision_trace(
    self,
    winner: Dict,
    runner_up: Optional[Dict],
    all_candidates: List[Dict],
    eliminated: List[Dict],
    reason_line: str,
    ingredient_name: str,  # NEW
    ingredient_form: Optional[str],  # NEW
    prompt: str  # NEW
) -> Dict:
```

5. **Update trace calculation logic** (inside `_build_decision_trace`):
```python
# Collect all unit prices for relative scoring
all_unit_prices = [c["candidate"].unit_price for c in all_candidates]

# Compute scores with breakdowns
winner_score, winner_breakdown = self._compute_real_score(
    winner, ingredient_name, ingredient_form, all_unit_prices, prompt
)
runner_up_score, runner_up_breakdown = None, {}
if runner_up:
    runner_up_score, runner_up_breakdown = self._compute_real_score(
        runner_up, ingredient_name, ingredient_form, all_unit_prices, prompt
    )

# Compute drivers using component breakdowns
drivers = compute_score_drivers(winner_breakdown, runner_up_breakdown)
```

6. **Add score_breakdown to candidate dicts** (inside trace loop):
```python
for c_dict in all_candidates[:10]:
    c = c_dict["candidate"]
    score, breakdown = self._compute_real_score(
        c_dict, ingredient_name, ingredient_form, all_unit_prices, prompt
    )

    candidates.append({
        "product": c.title,
        "brand": c.brand,
        # ... existing fields ...
        "score_total": score,
        "score_breakdown": breakdown,  # NEW
        "elimination_reasons": []
    })
```

7. **Update form-based filtering** (in `_select_products`, before sorting):
```python
# FILTER 5: Form compatibility (NEW)
form_filtered = []
for e in unit_price_filtered:
    candidate = e["candidate"]
    product_form = detect_product_form(candidate.title, get_ingredient_category(ingredient_name))
    compat_score = get_form_compatibility_score(ingredient_form, product_form)

    if compat_score >= 999:
        # Incompatible form - filter out
        if include_trace:
            e["elimination_reason"] = "FORM_MISMATCH"
            eliminated.append(e)
    else:
        # Store form score for sorting
        e["form_compat_score"] = compat_score
        form_filtered.append(e)
```

8. **Update sorting key** (line ~363-370):
```python
# Sort by: organic first, then form fit, then price
form_filtered.sort(key=lambda e: (
    not e["candidate"].organic,  # Organic first
    e.get("price_outlier_penalty", 0),  # No outliers
    e.get("form_compat_score", 5),  # Better form match
    e["candidate"].unit_price  # Lower price
))
```

#### File: `src/planner/engine.py` - Reason Generation

**Update `_generate_reason_and_tradeoffs` method** (line ~1000+):
```python
def _generate_reason_and_tradeoffs(
    self,
    ethical: Dict,
    runner_up: Optional[Dict],
    cheaper: Optional[Dict],
    ingredient_name: str,
    ingredient_form: Optional[str]
) -> Tuple[str, List[str], ProductChips]:
    """
    Generate deterministic reason + tradeoffs using component scores.

    Reason templates (priority order):
    1. "Organic recommended (EWG Dirty Dozen)"
    2. "Conventional is OK (EWG Clean Fifteen)"
    3. "Lower plastic packaging"
    4. "Better form for recipe"
    5. "In-season choice"
    6. "Faster delivery"
    7. "Best value per unit"
    8. "Only option in plan"
    """
    candidate = ethical["candidate"]
    category = get_ingredient_category(ingredient_name)
    ewg_cat = get_ewg_category(ingredient_name)

    # Determine primary reason (pick first match)
    reason_line = "Selected for this recipe"  # Fallback

    if category == "produce":
        if ewg_cat == "dirty_dozen" and candidate.organic:
            reason_line = "Organic recommended (EWG Dirty Dozen)"
        elif ewg_cat == "clean_fifteen":
            reason_line = "Conventional is OK (EWG Clean Fifteen)" if not candidate.organic else "Organic choice (EWG Clean)"
        elif ewg_cat == "middle":
            reason_line = "Wash/peel recommended"

    # Check for packaging advantage
    packaging_score = compute_packaging_component(candidate.title)
    if packaging_score >= 4:
        reason_line = "Lower plastic packaging"

    # Check for form fit
    product_form = detect_product_form(candidate.title, category)
    compat = get_form_compatibility_score(ingredient_form, product_form)
    if compat == 0:
        reason_line = "Perfect form for recipe"

    # Check for value
    if not runner_up or candidate.unit_price < runner_up["candidate"].unit_price * 0.85:
        reason_line = "Best value per unit"

    # Generate tradeoffs (max 2, contextual)
    tradeoffs = []

    # Tradeoff 1: Price delta (only if significant)
    if cheaper and abs(candidate.price - cheaper["candidate"].price) > 0.50:
        delta = candidate.price - cheaper["candidate"].price
        if delta > 0:
            tradeoffs.append(f"${delta:.2f} more for organic")

    # Tradeoff 2: Delivery time
    delivery = ethical.get("delivery_estimate", "1-2 days")
    if "week" in delivery.lower():
        tradeoffs.append("Ships later (specialty store)")

    # Tradeoff 3: Preparation effort
    if "whole" in candidate.title.lower() and category == "protein":
        tradeoffs.append("Requires prep (whole cut)")
    elif product_form == "seeds" and category == "spice":
        tradeoffs.append("Needs grinding (whole spice)")

    # Limit to 2 tradeoffs
    tradeoffs = tradeoffs[:2]

    # Reason details (for tooltip)
    reason_details = []
    if ewg_cat == "dirty_dozen":
        reason_details.append("High pesticide residues - organic preferred")
    if packaging_score > 0:
        reason_details.append("Reduced plastic waste")

    chips = ProductChips(why_pick=[], tradeoffs=tradeoffs)

    return reason_line, reason_details, chips
```

### ⏳ Pending (Phase 2) - Frontend + Testing

#### File: `frontend/src/app/types.ts`

**Update DecisionTrace interface** to include score_breakdown:
```typescript
export interface DecisionTrace {
  winner_score: number;
  runner_up_score: number | null;
  score_margin: number;
  candidates: Array<{
    product: string;
    brand: string;
    store: string;
    price: number;
    unit_price: number;
    organic: boolean;
    form_score: number;
    packaging: string;
    status: string;
    score_total: number;
    score_breakdown?: {  // NEW
      base: number;
      ewg: number;
      form_fit: number;
      packaging: number;
      delivery: number;
      unit_value: number;
      outlier_penalty: number;
    };
    elimination_reasons: string[];
  }>;
  filtered_out_summary: Record<string, number>;
  drivers: Array<{
    rule: string;
    delta: number;
  }>;
}
```

#### File: `frontend/src/app/components/ScoringDrawer.tsx`

**Add score breakdown accordion** (after candidates table):
```tsx
{/* Score Breakdown (expandable per candidate) */}
{candidate.score_breakdown && (
  <details className="ml-4 mt-2">
    <summary className="cursor-pointer text-xs text-blue-600">
      View score breakdown
    </summary>
    <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
      <div className="grid grid-cols-2 gap-1">
        <span>Base:</span><span>{candidate.score_breakdown.base}</span>
        <span>EWG:</span><span>{candidate.score_breakdown.ewg}</span>
        <span>Form:</span><span>{candidate.score_breakdown.form_fit}</span>
        <span>Packaging:</span><span>{candidate.score_breakdown.packaging}</span>
        <span>Delivery:</span><span>{candidate.score_breakdown.delivery}</span>
        <span>Value:</span><span>{candidate.score_breakdown.unit_value}</span>
      </div>
    </div>
  </details>
)}
```

### 🧪 Verification Tests

**Test 1: Biryani EWG scoring**
```bash
curl -X POST http://localhost:8000/api/plan-v2 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "chicken biryani for 4", "servings": 4, "include_trace": true}' \
  | jq '.items[] | select(.ingredient_name == "tomatoes") | .decision_trace.drivers'
```

**Expected**: Winner should show EWG component (tomatoes are Dirty Dozen)

**Test 2: Form matching**
```bash
curl -X POST http://localhost:8000/api/plan-v2 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "chicken biryani for 4", "servings": 4, "include_trace": true}' \
  | jq '.items[] | select(.ingredient_name == "cumin seeds") | .decision_trace.candidates[] | select(.status == "winner") | .product'
```

**Expected**: Should match cumin seeds, NOT kalonji (form_fit component)

**Test 3: Reason diversity**
```bash
curl -X POST http://localhost:8000/api/plan-v2 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "chicken biryani for 4", "servings": 4}' \
  | jq '.items | map(.reason_line) | unique | length'
```

**Expected**: At least 3 different reason types (not all "organic wins")

## Migration Strategy

1. **Phase 1**: Implement core scoring (this doc) - 2-3 hours
2. **Phase 2**: Update frontend drawer - 1 hour
3. **Phase 3**: Test and validate - 1 hour
4. **Phase 4**: Add cart banners + unavailable cleanup - 1 hour

**Total**: ~5-6 hours implementation time

## Risk Mitigation

- **Backwards compatibility**: Keep old sorting logic as fallback
- **Gradual rollout**: Use feature flag for new scoring
- **Comprehensive testing**: Run biryani test before/after
- **Monitoring**: Log score differences between old/new systems

## Next Steps

1. Review this plan
2. Approve core engine changes
3. Implement Phase 1b (engine updates)
4. Test with biryani
5. Move to Phase 2 (frontend)
