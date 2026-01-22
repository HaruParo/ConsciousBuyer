# DEV_NOTE - Backend Architecture Decisions

## Why ProductAgent No Longer Tiers

Previously, ProductAgent assigned tier labels (cheaper/balanced/conscious) to products
at inventory time. This created a coupling problem: the agent needed to know the decision
logic, and any scoring change required touching both ProductAgent and DecisionEngine.

**Now:** ProductAgent returns tier-free candidates with normalized `unit_price` (per oz).
The DecisionEngine owns tier assignment after scoring. This means:
- ProductAgent is a pure data-fetcher
- Tier thresholds are computed dynamically from the candidate pool
- Adding new scoring signals doesn't require ProductAgent changes

## Recall Taxonomy

Old: Binary `clear | recalled` with Class I/II/III.

New: Structured `RecallSignal` with:
- `product_match` (bool) - Hard constraint: disqualifies in Stage 1
- `category_advisory` ("none" | "recent" | "elevated") - Soft penalty in Stage 2
- `confidence` ("high" | "medium" | "low") - For UI display
- `data_gap` (bool) - Flags stale recall data

This allows nuance: a lettuce product isn't "recalled" just because another lettuce brand
had a recall. Instead, it gets a soft "category_advisory: recent" penalty.

## Constraints-First Scoring

The DecisionEngine runs two stages:

**Stage 1 (Hard Constraints):** Disqualify candidates that fail:
- Active product recall (product_match = true)
- User's avoided brands list
- strict_safety + dirty_dozen + non-organic

**Stage 2 (Soft Scoring):** Score survivors on:
- EWG bucket (+5 dirty_dozen_organic, -20 dirty_dozen_no_organic, etc.)
- Seasonality (+15 peak, +10 available, +5 storage)
- Recall advisories (-10 elevated, -5 recent)
- Organic bonus (+8)
- Brand preference (+10)

Then: pick recommended (highest score), find cheaper_neighbor and conscious_neighbor.

## Neighbor Selection

For each ingredient, after scoring:
- **recommended** = highest-scoring viable candidate
- **cheaper_neighbor** = best-scoring candidate with lower unit_price (min score >= 30)
- **conscious_neighbor** = highest-scoring candidate with higher unit_price (or organic)

The UI stepper uses these to offer "slide left for cheaper, slide right for conscious."

## How to Run Tests

```bash
cd conscious-cart-coach
python -m pytest tests/test_pipeline.py -v
```

32 tests covering:
- `TestParseSizeOz` - Unit price normalization (oz, lb, g, kg, dozen)
- `TestProductAgent` - Candidates, sorting, aliases, no tier labels
- `TestDecisionEngineConstraints` - Recall disqualification, avoided brands, strict safety
- `TestDecisionEngineDeterminism` - Same input = same output
- `TestDecisionEngineScoring` - EWG penalties, seasonality bonus, reason_short
- `TestDecisionEngineBundles` - Cart totals and deltas
- `TestOrchestratorGating` - State machine, gates, full flow

## Key Files

| File | Role |
|------|------|
| `src/contracts/models.py` | All typed dataclasses (ProductCandidate, DecisionBundle, etc.) |
| `src/agents/product_agent.py` | Tier-free candidates with unit_price normalization |
| `src/engine/decision_engine.py` | Two-stage scoring, neighbor selection, cart bundles |
| `src/orchestrator/orchestrator.py` | Gated flow: ingredients → confirm → candidates → enrich → decide |
| `src/facts/facts_gateway.py` | RecallSignal taxonomy, auto-refresh stale tables |
| `src/opik_integration/tracker.py` | Span-per-step tracing (degrades if opik not installed) |
| `src/exporters/csv_exporter.py` | 3-file export: ingredients, candidates, bundle |
| `tests/test_pipeline.py` | 32 tests for the pipeline |

## Auto-Refresh

FactsGateway checks staleness on initialization (`auto_refresh=True`):
- recalls: 24h
- ewg: annual
- stores: monthly
- crops: annual
- sources: quarterly

If stale, it re-imports from the corresponding CSV in `data/`.
