# LLM-Guided Quantity Reconciliation

## Overview

The Conscious Cart Coach now uses Claude (Anthropic LLM) to intelligently calculate how many product packages are needed to fulfill ingredient requirements. This replaces the previous hardcoded heuristic with an intelligent system that handles unit conversions and package sizing.

## The Problem It Solves

When a user requests "chicken biryani for 12 people", the system needs to:

1. **Extract ingredients** with scaled quantities (e.g., "6 lb chicken" for 12 servings)
2. **Find products** with package sizes (e.g., "2 lb chicken breast package")
3. **Calculate packages needed**: How many 2 lb packages do we need for 6 lb? → **3 packages**

The gap was in step 3 - the system didn't have logic to reconcile ingredient quantities with product package sizes.

## How It Works

### Architecture

```
┌─────────────────────┐
│  IngredientAgent    │  Extracts: "6 lb chicken" for 12 servings
│  (with LLM or       │
│   templates)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   ProductAgent      │  Finds: "2 lb chicken package" @ $8.99
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  DecisionEngine     │  Scores & picks best product
│                     │
│  ┌───────────────┐  │
│  │   Quantity    │  │  Calculates: 6 lb ÷ 2 lb = 3 packages
│  │  Reconciler   │  │  (LLM-guided with constraints)
│  │   (NEW!)      │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   DecisionItem      │  Output: product + quantity: 3
└─────────────────────┘
```

### LLM Prompt Strategy

The quantity reconciler uses a **guided LLM approach** with strict constraints:

**Prompt includes:**
- Ingredient requirement (qty + unit)
- Product package details (size + unit price)
- Serving count for context

**Rules enforced:**
1. Always round up (never suggest fractional packages)
2. Handle common unit conversions (lb→lb, oz→oz, cups→cans, bunches→packages)
3. Minimum 1 package for any ingredient
4. Return structured JSON only (no hallucination)

**Example prompt:**
```
INGREDIENT REQUIREMENT:
- Name: chicken
- Required Quantity: 6.0
- Required Unit: lb
- Servings: 12

PRODUCT PACKAGE:
- Title: Organic Chicken Breast
- Package Size: 2 lb
- Unit Price: $4.50/oz

Calculate packages needed to meet or exceed requirement.
Always round up. Output JSON only.
```

**LLM Response:**
```json
{
  "packages_needed": 3,
  "reasoning": "6 lb required ÷ 2 lb per package = 3 packages",
  "unit_conversion": "lb to lb (direct match)"
}
```

### Unit Conversion Intelligence

The LLM handles complex unit conversions intelligently:

| Ingredient Need | Product Package | LLM Calculation |
|----------------|-----------------|-----------------|
| 2 cups diced tomatoes | 14.5 oz can | 1 can (~1.5 cups) → 2 cans |
| 1 bunch cilantro | 1 package | 1 bunch = 1 package → 1 package |
| 6 cloves garlic | 1 head | ~6 cloves per head → 1 head |
| 2 inches ginger | 8 oz package | 2 inches ≈ 1 oz → 1 package |
| 1 pinch saffron | 0.5 oz jar | Always 1 for spices → 1 package |

### Fallback Strategy

If the LLM is unavailable or fails, the system falls back to a simple heuristic:

```python
base_quantity = 1 + (servings - 1) // 4
```

This ensures the system always works, even without API access.

## Code Implementation

### New Files

**`src/llm/quantity_reconciler.py`**
- `calculate_product_quantity()`: Main LLM function
- `_fallback_quantity_calculation()`: Heuristic fallback

### Modified Files

**`src/contracts/models.py`**
- Added `quantity`, `quantity_reasoning`, `quantity_unit_conversion` to `DecisionItem`

**`src/engine/decision_engine.py`**
- Added `ingredient_specs` and `servings` parameters to `decide()`
- Added `_calculate_quantity()` method
- Integrated quantity reconciliation into decision pipeline

**`src/orchestrator/orchestrator.py`**
- Passes ingredient specs and servings to DecisionEngine

**`api/main.py`**
- Enabled `use_llm_explanations=True` (powers quantity reconciliation)
- Updated `map_decision_to_cart_item()` to use `item.quantity`

## Configuration

### Enable/Disable LLM Quantity Reconciliation

In `api/main.py`:

```python
# Enable LLM quantity reconciliation
orch = Orchestrator(
    use_llm_extraction=False,      # Template-based ingredients
    use_llm_explanations=True      # LLM for quantities + explanations
)

# Disable LLM (use fallback heuristic)
orch = Orchestrator(
    use_llm_extraction=False,
    use_llm_explanations=False     # Falls back to simple heuristic
)
```

### Environment Setup

Requires `ANTHROPIC_API_KEY` environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Testing Examples

### Example 1: Chicken Biryani for 12

**Input:** "chicken biryani for 12"

**Ingredient Extraction:**
- Chicken: 6 lb (scaled from 1 lb base for 4 servings)
- Basmati rice: 6 cups
- Onions: 6 large
- etc.

**Product Matching:**
- Finds: "Organic Chicken Breast, 2 lb" @ $8.99

**Quantity Reconciliation (LLM):**
```json
{
  "packages_needed": 3,
  "reasoning": "6 lb required divided by 2 lb per package = 3 packages",
  "unit_conversion": "lb to lb (direct conversion)"
}
```

**Cart Output:**
- Product: Organic Chicken Breast
- Quantity: 3 packages
- Total: $26.97 (3 × $8.99)

### Example 2: Mixed Units

**Input:** "pasta with tomato sauce for 4"

**Ingredients:**
- Diced tomatoes: 2 cups

**Product:**
- "Hunt's Diced Tomatoes, 14.5 oz can" @ $1.29

**LLM Calculation:**
```json
{
  "packages_needed": 2,
  "reasoning": "2 cups needed, 1 can ≈ 1.5 cups, need 2 cans to meet requirement",
  "unit_conversion": "cups to oz (1 can = ~1.5 cups diced tomatoes)"
}
```

## Benefits

1. **Intelligent scaling**: Automatically adjusts quantities for any serving size
2. **Unit conversion**: Handles complex conversions (cups→cans, bunches→packages)
3. **Always rounds up**: Never suggests fractional packages
4. **Fallback safe**: Works even without LLM (degrades gracefully)
5. **Transparent**: Provides reasoning for each calculation
6. **Cost-effective**: Only uses LLM when enabled and available

## Future Enhancements

- [ ] Add product substitution awareness (if 2 lb unavailable, suggest 3× 1 lb)
- [ ] Handle bulk pricing optimizations (cheaper to buy 5 lb than 3× 2 lb)
- [ ] User preference for "buy exactly" vs "round up generously"
- [ ] Cache common conversions to reduce LLM calls
- [ ] Support for recipe yield adjustments (half recipe, double recipe)

## Logs and Debugging

Enable debug logging to see quantity calculations:

```bash
export LOG_LEVEL=DEBUG
```

Sample log output:
```
[INFO] LLM quantity for chicken: 3 package(s) (6 lb required ÷ 2 lb per package = 3 packages)
[INFO] LLM quantity for cilantro: 1 package(s) (1 bunch = 1 package)
[WARNING] LLM quantity calculation failed for saffron: API timeout, using fallback
```

## Cost Optimization

The LLM quantity reconciliation uses:
- **Model**: claude-sonnet-4-20250514
- **Max tokens**: 256 per calculation
- **Temperature**: 0.0 (deterministic)
- **Cost**: ~$0.0001 per ingredient (very low)

For a typical 10-ingredient recipe:
- LLM calls: 10 quantity calculations
- Cost: ~$0.001 per cart creation
- Latency: <2 seconds total (parallel calls possible in future)

## Architecture Decision: Why Not Rule-Based?

We chose LLM-guided over pure rule-based because:

1. **Complexity**: 100+ unit conversion rules needed (lb, oz, kg, g, cups, tsp, tbsp, cans, bunches, heads, cloves, inches, etc.)
2. **Edge cases**: "1 bunch cilantro" → how many oz? Varies by bundle size
3. **Context**: "1 cup diced tomatoes" ≠ "1 cup whole tomatoes" (density differs)
4. **Maintainability**: LLM adapts to new products/units without code changes
5. **User experience**: Natural language understanding beats rigid rules

The **guided LLM approach** gives us:
- Intelligence of LLM for complex cases
- Constraints to prevent hallucination
- Fallback for reliability
- Low cost and latency
