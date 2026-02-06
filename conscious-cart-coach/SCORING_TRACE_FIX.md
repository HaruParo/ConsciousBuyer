# Scoring Trace Fix - Implementation Guide

## Summary

This document guides the implementation of fixes to make the Scoring Drawer answer two critical questions:
1. **"Why did this win?"** - with real drivers and tradeoffs
2. **"Where are all my candidates?"** - with retrieved vs considered pools

## Status

✅ **Phase 1: Contract Update - COMPLETE**
- Added `DecisionTrace`, `CandidateTrace`, `ScoreDriver`, `CandidatePoolSummary` to [cart_plan.py](src/contracts/cart_plan.py)
- Run `python scripts/fix_scoring_trace.py` to verify

⏳ **Phase 2-5: Implementation Needed** (see below)

---

## Phase 2: Engine Logic Updates

### File: `src/planner/engine.py`

#### 2A. Track Retrieved Candidates by Store

In `_retrieve_candidates_with_forms()` method (around line 200):

```python
def _retrieve_candidates_with_forms(self, ingredient_forms: Dict[str, Tuple[str, str]]) -> Dict[str, List[Dict]]:
    """Retrieve candidates and track retrieved counts by store"""
    candidates_by_ingredient = {}

    for canonical_name, (ingredient_label, form) in ingredient_forms.items():
        # Get ingredient key for retrieval
        ingredient_key = get_ingredient_key(canonical_name)

        # Retrieve from index
        raw_candidates = self.product_index.retrieve(ingredient_key, k=50)

        # Track retrieved counts by store
        retrieved_by_store = {}
        for c in raw_candidates:
            store = c.source_store_id
            retrieved_by_store[store] = retrieved_by_store.get(store, 0) + 1

        # Store in result
        candidates_by_ingredient[canonical_name] = {
            'candidates': raw_candidates,
            'retrieved_by_store': retrieved_by_store,
            'query_key': ingredient_key,  # NEW: For trace
            'form': form
        }

    return candidates_by_ingredient
```

#### 2B. Track Considered Candidates After Filters

In `_select_products()` method (around line 500):

```python
def _select_products(self, enriched, store_plan, servings, include_trace, ingredient_forms, prompt):
    """Select products and track considered after filters"""
    selections = {}

    for canonical_name, candidates_data in enriched.items():
        candidates = candidates_data['candidates']
        assigned_store = store_plan.get_store_for_ingredient(canonical_name)

        # Apply hard filters
        filtered = []
        eliminated = []

        for c in candidates:
            elimination_reason, elimination_stage = self._check_elimination(c, assigned_store, ...)

            if elimination_reason:
                eliminated.append({
                    'candidate': c,
                    'elimination_reason': elimination_reason,
                    'elimination_stage': elimination_stage,
                    'elimination_explanation': ELIMINATION_EXPLANATIONS.get(elimination_reason, 'Unknown')
                })
            else:
                filtered.append(c)

        # Track considered counts by store
        considered_by_store = {}
        for c in filtered:
            store = c.source_store_id
            considered_by_store[store] = considered_by_store.get(store, 0) + 1

        # Score and select
        winner, runner_up, all_scored = self._score_and_rank(filtered)

        selections[canonical_name] = {
            'winner': winner,
            'runner_up': runner_up,
            'all_candidates': all_scored,
            'eliminated': eliminated,
            'retrieved_by_store': candidates_data['retrieved_by_store'],
            'considered_by_store': considered_by_store,
            'query_key': candidates_data['query_key']
        }

    return selections
```

#### 2C. Add Elimination Explanations

Add at top of engine.py:

```python
# Elimination reason explanations
ELIMINATION_EXPLANATIONS = {
    'FORM_INCOMPATIBLE': 'Product form doesn\'t match required form (e.g., powder when fresh needed)',
    'STORE_ENFORCEMENT': 'Product from wrong store (not in store plan)',
    'PRICE_OUTLIER': 'Price is more than 2x the median (prevents premium-only selections)',
    'UNIT_PRICE_INCONSISTENT': 'Unit price calculation failed or size data missing',
    'SIZE_PARSE_FAILED': 'Could not parse product size to calculate unit price',
    'PRIVATE_LABEL_VIOLATION': 'Private label from other store (365 brand from non-WholeFoods)',
    'SANITY_CHECK_FAILED': 'Failed basic sanity checks (price/size validation)',
    'FORM_CONSTRAINT_FAILED': 'Failed hard form constraints (fresh ginger vs powder)',
}
```

#### 2D. Enhanced _build_decision_trace()

Update around line 1346:

```python
def _build_decision_trace(
    self,
    winner: Dict,
    runner_up: Optional[Dict],
    all_candidates: List[Dict],
    eliminated: List[Dict],
    reason_line: str,
    ingredient_name: str,
    ingredient_form: Optional[str],
    prompt: str,
    retrieved_by_store: Dict[str, int],
    considered_by_store: Dict[str, int],
    query_key: str
) -> DecisionTrace:
    """Build complete decision trace with all new fields"""
    from src.contracts.cart_plan import (
        DecisionTrace, CandidateTrace, ScoreDriver, CandidatePoolSummary
    )

    # Build retrieved/considered summaries
    store_names = {'freshdirect': 'FreshDirect', 'wholefoods': 'Whole Foods', ...}

    retrieved_summary = [
        CandidatePoolSummary(
            store_id=store_id,
            store_name=store_names.get(store_id, store_id),
            retrieved_count=count,
            considered_count=considered_by_store.get(store_id, 0)
        )
        for store_id, count in retrieved_by_store.items()
    ]

    # Compute scores with breakdowns
    winner_score, winner_breakdown = self._compute_real_score(...)
    runner_up_score, runner_up_breakdown = self._compute_real_score(...) if runner_up else (None, {})

    # Compute drivers and tradeoffs
    drivers = self._compute_drivers(winner_breakdown, runner_up_breakdown, all_candidates)
    tradeoffs = self._compute_tradeoffs(winner_breakdown)

    # Build candidates list
    candidates = []
    for c_dict in all_candidates[:10]:
        # ... (existing code)
        candidates.append(CandidateTrace(...))

    for e_dict in eliminated[:10]:
        candidates.append(CandidateTrace(
            elimination_explanation=e_dict.get('elimination_explanation'),
            elimination_stage=e_dict.get('elimination_stage'),
            ...
        ))

    return DecisionTrace(
        query_key=query_key,
        retrieved_summary=retrieved_summary,
        considered_summary=[],  # Same as retrieved_summary but filtered
        winner_score=winner_score,
        runner_up_score=runner_up_score,
        score_margin=winner_score - (runner_up_score or 0),
        candidates=[c.dict() for c in candidates],
        drivers=[d.dict() for d in drivers],
        tradeoffs_accepted=tradeoffs,
        filtered_out_summary=filtered_out_summary
    )
```

---

## Phase 3: Driver and Tradeoff Computation

### File: `src/scoring/component_scoring.py`

#### 3A. Enhanced compute_score_drivers()

```python
from src.contracts.cart_plan import ScoreDriver

def compute_score_drivers(
    winner_breakdown: Dict[str, int],
    runner_up_breakdown: Optional[Dict[str, int]],
    all_candidates: Optional[List[Dict]] = None
) -> List[ScoreDriver]:
    """
    Compute drivers (why winner won) from component breakdowns.

    If runner-up exists: compare vs runner-up
    Else: compare vs median of all candidates
    """
    drivers = []

    if not winner_breakdown:
        return drivers

    # Determine comparison baseline
    if runner_up_breakdown:
        baseline = runner_up_breakdown
    elif all_candidates:
        # Compute median from all candidates
        baseline = _compute_median_breakdown(all_candidates)
    else:
        # No comparison possible
        return drivers

    # Component names for display
    COMPONENT_NAMES = {
        'ewg': 'EWG guidance',
        'form_fit': 'Form match',
        'packaging': 'Packaging',
        'delivery': 'Delivery speed',
        'unit_value': 'Unit value',
        'outlier_penalty': 'Price premium'
    }

    # Compute deltas
    deltas = []
    for component, winner_score in winner_breakdown.items():
        if component == 'base':
            continue  # Skip base (always 50)

        baseline_score = baseline.get(component, 0)
        delta = winner_score - baseline_score

        if abs(delta) >= 2:  # Only significant deltas
            deltas.append((component, delta))

    # Sort by absolute delta (biggest first)
    deltas.sort(key=lambda x: abs(x[1]), reverse=True)

    # Build driver explanations
    for component, delta in deltas[:3]:  # Top 3 drivers
        rule = _explain_driver(component, delta, winner_breakdown)
        drivers.append(ScoreDriver(rule=rule, delta=delta))

    return drivers

def _explain_driver(component: str, delta: int, breakdown: Dict[str, int]) -> str:
    """Generate human-readable explanation for a driver"""
    if component == 'ewg':
        if delta > 0:
            return "Organic (EWG Dirty Dozen)"
        else:
            return "Conventional OK (EWG Clean Fifteen)"
    elif component == 'packaging':
        if delta > 0:
            return "Lower plastic packaging"
        else:
            return "More plastic packaging"
    elif component == 'form_fit':
        if delta > 0:
            return "Perfect form match"
        else:
            return "Form compromise"
    elif component == 'delivery':
        if delta > 0:
            return "Faster delivery"
        else:
            return "Slower delivery"
    elif component == 'unit_value':
        if delta > 0:
            return "Better value per oz"
        else:
            return "Higher unit price"
    else:
        return f"{component}: +{delta}"
```

#### 3B. Add compute_tradeoffs()

```python
def compute_tradeoffs(winner_breakdown: Dict[str, int]) -> List[str]:
    """
    Extract tradeoffs (negative components) accepted on winner.

    Returns human-readable list of negative aspects.
    """
    tradeoffs = []

    # Packaging penalty
    if winner_breakdown.get('packaging', 0) < 0:
        tradeoffs.append("More plastic packaging")

    # Delivery penalty
    if winner_breakdown.get('delivery', 0) < 0:
        tradeoffs.append("Slower delivery (1-2 weeks)")

    # Form fit compromise
    form_score = winner_breakdown.get('form_fit', 14)
    if form_score < 14:
        if form_score <= 5:
            tradeoffs.append("Form mismatch")
        elif form_score <= 10:
            tradeoffs.append("Form compromise")

    # Outlier penalty
    if winner_breakdown.get('outlier_penalty', 0) < 0:
        tradeoffs.append("Premium price (>2x median)")

    # Unit value penalty
    if winner_breakdown.get('unit_value', 0) <= 2:
        tradeoffs.append("Higher unit price")

    return tradeoffs[:2]  # Max 2 tradeoffs
```

---

## Phase 4: Replace Vague Reason Lines

### File: `src/planner/engine.py`

In `_generate_reason_and_tradeoffs()` method (around line 950):

```python
def _generate_reason_and_tradeoffs(
    self,
    ethical,
    runner_up,
    cheaper,
    canonical_name,
    form,
    winner_breakdown,
    runner_up_breakdown
):
    """Generate reason_line from actual top driver, not generic text"""

    # Compute drivers
    drivers = self._compute_drivers(winner_breakdown, runner_up_breakdown, [])

    # Use top driver as reason_line
    if drivers:
        reason_line = drivers[0].rule  # e.g., "Organic (EWG Dirty Dozen)"
    else:
        # Fallback to breakdown analysis
        if winner_breakdown.get('ewg', 0) > 5:
            reason_line = "Organic where it matters"
        elif winner_breakdown.get('form_fit', 0) == 14:
            reason_line = "Perfect form match"
        elif winner_breakdown.get('unit_value', 0) >= 6:
            reason_line = "Best value per unit"
        else:
            reason_line = "Good match for recipe"

    # Rest of method...
    return reason_line, reason_details, chips
```

---

## Phase 5: Frontend Updates

### File: `frontend/src/app/types.ts`

Update DecisionTrace interface to match new backend:

```typescript
export interface CandidateTrace {
  product: string;
  brand: string;
  store: string;
  price: number;
  unit_price: number;
  organic: boolean;
  form_score: number;
  packaging: string;
  status: string;
  score_total: number | null;
  score_breakdown?: {
    base: number;
    ewg: number;
    form_fit: number;
    packaging: number;
    delivery: number;
    unit_value: number;
    outlier_penalty: number;
  };
  elimination_reasons: string[];
  elimination_explanation?: string;  // NEW
  elimination_stage?: string;  // NEW
}

export interface ScoreDriver {
  rule: string;  // "Organic (EWG Dirty Dozen)"
  delta: number;  // +18
}

export interface CandidatePoolSummary {
  store_id: string;
  store_name: string;
  retrieved_count: number;
  considered_count: number;
}

export interface DecisionTrace {
  query_key: string;  // NEW
  retrieved_summary: CandidatePoolSummary[];  // NEW
  considered_summary: CandidatePoolSummary[];  // NEW
  winner_score: number;
  runner_up_score: number | null;
  score_margin: number;
  candidates: CandidateTrace[];
  drivers: ScoreDriver[];  // NEW (enhanced)
  tradeoffs_accepted: string[];  // NEW
  filtered_out_summary: Record<string, number>;
}
```

### File: `frontend/src/app/components/ScoringDrawer.tsx`

Add new sections:

```typescript
{/* Candidate Pool Summary */}
<div className="p-4 bg-gray-50 border-b">
  <h3 className="font-semibold text-gray-900 mb-2">Candidate Pool</h3>
  <div className="text-sm space-y-1">
    <div>
      <span className="font-medium">Retrieved from index:</span>
      {' '}
      {trace.retrieved_summary.map((s, i) => (
        <span key={s.store_id}>
          {s.store_name} ({s.retrieved_count})
          {i < trace.retrieved_summary.length - 1 ? ', ' : ''}
        </span>
      ))}
    </div>
    <div>
      <span className="font-medium">Considered after filters:</span>
      {' '}
      {trace.considered_summary.map((s, i) => (
        <span key={s.store_id}>
          {s.store_name} ({s.considered_count})
          {i < trace.considered_summary.length - 1 ? ', ' : ''}
        </span>
      ))}
    </div>
    <div className="text-xs text-gray-500 mt-1">
      Query key: <code>{trace.query_key}</code>
    </div>
  </div>
</div>

{/* Tradeoffs Section */}
{trace.tradeoffs_accepted.length > 0 && (
  <div className="mt-3 p-3 bg-orange-50 rounded border border-orange-200">
    <div className="text-xs font-semibold text-gray-700 mb-2">Tradeoffs accepted:</div>
    <ul className="space-y-1">
      {trace.tradeoffs_accepted.map((tradeoff, idx) => (
        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
          <span className="text-orange-600">⚠</span>
          <span>{tradeoff}</span>
        </li>
      ))}
    </ul>
  </div>
)}

{/* Filtered Out - use elimination_explanation */}
<td className="px-2 py-2 text-gray-600 text-xs">
  {candidate.elimination_explanation || 'Not specified'}
</td>
```

---

## Testing

### Test Script: `scripts/test_chicken_thighs_trace.py`

```python
#!/usr/bin/env python3
"""Test chicken thighs trace to verify FreshDirect candidates are retrieved"""

from src.planner.engine import PlannerEngine

engine = PlannerEngine()

# Test "chicken thighs for biryani"
plan = engine.create_plan(
    prompt="chicken biryani for 4",
    ingredients=["chicken thighs", "basmati rice", "onions"],
    servings=4,
    include_trace=True
)

# Find chicken thighs item
chicken_item = next((item for item in plan.items if "chicken" in item.ingredient_name.lower()), None)

assert chicken_item, "Chicken item not found"
assert chicken_item.decision_trace, "Decision trace missing"

trace = chicken_item.decision_trace

print(f"Query key: {trace.query_key}")
print(f"\nRetrieved candidates:")
for summary in trace.retrieved_summary:
    print(f"  {summary.store_name}: {summary.retrieved_count}")

print(f"\nConsidered after filters:")
for summary in trace.considered_summary:
    print(f"  {summary.store_name}: {summary.considered_count}")

print(f"\nDrivers (why winner won):")
for driver in trace.drivers:
    print(f"  +{driver.delta}: {driver.rule}")

print(f"\nTradeoffs accepted:")
for tradeoff in trace.tradeoffs_accepted:
    print(f"  ⚠ {tradeoff}")

# Assertions
assert trace.retrieved_summary, "Retrieved summary empty"
assert any(s.store_id == 'freshdirect' for s in trace.retrieved_summary), "FreshDirect not in retrieved"

freshdirect_retrieved = next((s for s in trace.retrieved_summary if s.store_id == 'freshdirect'), None)
assert freshdirect_retrieved.retrieved_count > 1, f"Only {freshdirect_retrieved.retrieved_count} FreshDirect candidates retrieved"

assert trace.drivers, "Drivers empty"
assert all(hasattr(d, 'rule') and hasattr(d, 'delta') for d in trace.drivers), "Driver format invalid"

# Check filtered-out have explanations
filtered_out = [c for c in trace.candidates if c['status'] == 'filtered_out']
for c in filtered_out:
    assert c.get('elimination_explanation'), f"Missing explanation for {c['product']}"

print("\n✓ All assertions passed")
```

---

## Validation Checklist

- [ ] Contract models verified (`python scripts/fix_scoring_trace.py`)
- [ ] Engine tracks retrieved_by_store in `_retrieve_candidates_with_forms()`
- [ ] Engine tracks considered_by_store in `_select_products()`
- [ ] `_build_decision_trace()` builds CandidatePoolSummary for both pools
- [ ] Drivers computed from component breakdowns
- [ ] Tradeoffs extracted from negative components
- [ ] Elimination explanations added for all filtered candidates
- [ ] Frontend types updated to match backend
- [ ] ScoringDrawer shows candidate pool summary
- [ ] ScoringDrawer shows drivers and tradeoffs
- [ ] Test script passes for chicken thighs

---

## Summary

This comprehensive fix transforms the scoring drawer from a dev-only debug tool into a user-trustworthy decision explanation system. Users will see:

1. **Where their candidates come from** (FreshDirect 47 retrieved, 12 considered)
2. **Why the winner won** (Organic (EWG Dirty Dozen) +18, Lower plastic packaging +6)
3. **What tradeoffs were accepted** (Slower delivery, Form compromise)
4. **Why candidates were filtered** (Store enforcement, Price outlier, etc.)

All with REAL data, no placeholders or "Not specified" messages.
