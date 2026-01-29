# LLM Integration Summary

**Date**: 2026-01-24
**Status**: In Progress

## Implementation Plan

### ✅ Completed

1. **Created LLM Module** (`conscious-cart-coach/src/llm/`)
   - `client.py` - Anthropic client wrapper with retry logic
   - `ingredient_extractor.py` - LLM-powered ingredient extraction
   - `decision_explainer.py` - LLM-generated explanations
   - `__init__.py` - Module exports

2. **Updated IngredientAgent** (`conscious-cart-coach/src/agents/ingredient_agent.py`)
   - Added `use_llm` parameter to constructor
   - Implements LLM extraction with template fallback
   - Lazy loads LLM module only when needed
   - Adds `extraction_method` to facts (`"llm"` or `"template"`)

3. **Updated Data Models** (`conscious-cart-coach/src/contracts/models.py`)
   - Added `reason_llm: str | None` field to DecisionItem
   - Allows storing LLM-generated explanations alongside deterministic `reason_short`

### 🔄 In Progress

4. **Update DecisionEngine** (NEXT)
   - Add `use_llm_explanations` parameter
   - Keep scoring 100% deterministic
   - Add optional LLM explanation generation after scoring
   - Populate `reason_llm` field in DecisionItem

### ⏸️ Pending

5. **Update Orchestrator**
   - Add `use_llm` parameter
   - Pass to IngredientAgent and DecisionEngine
   - Add to UserPrefs for persistence

6. **Update UI**
   - Display LLM explanations when available
   - Fall back to `reason_short` if no LLM
   - Add toggle for LLM features

7. **Documentation**
   - Update architecture docs
   - Add cost/latency considerations
   - Document fallback behavior

## Design Principles

### 1. Scoring Remains Deterministic
- All scoring logic unchanged
- LLM only adds explanations, not decisions
- Same inputs = same scores/recommendations

### 2. Graceful Fallbacks
- LLM unavailable? Use templates/deterministic
- API errors? Log and continue
- No hard dependency on Claude API

### 3. Lazy Loading
- LLM module only imported when `use_llm=True`
- No performance impact when disabled
- Clean separation of concerns

### 4. Backward Compatible
- All LLM features optional
- Existing code works without changes
- Default: `use_llm=False`

## Usage Examples

### IngredientAgent with LLM

```python
from src.agents.ingredient_agent import IngredientAgent

# With LLM
agent = IngredientAgent(use_llm=True)
result = agent.extract("I want something healthy and seasonal")
# Uses Claude to understand vague requests

# Without LLM (default)
agent = IngredientAgent()
result = agent.extract("biryani for 4")
# Uses template matching (fast, free)
```

### DecisionEngine with LLM Explanations

```python
from src.engine.decision_engine import DecisionEngine

# With LLM explanations
engine = DecisionEngine(use_llm_explanations=True)
bundle = engine.decide(candidates_by_ingredient, safety_signals, seasonality)

# item.reason_short: "Best value per oz" (deterministic)
# item.reason_llm: "This Earthbound Farm option at $3.99 offers organic..."

# Without LLM (default)
engine = DecisionEngine()
bundle = engine.decide(...)
# Only reason_short populated, reason_llm=None
```

## Cost Considerations

### Estimated API Costs (Claude Sonnet 4.5)

**Per Request**:
- Ingredient Extraction: ~$0.01-0.02 (500-1000 tokens)
- Decision Explanation: ~$0.002-0.005 per item (100-200 tokens)

**Example Cart (10 items)**:
- Ingredient extraction: $0.015
- 10 explanations: $0.030
- **Total**: ~$0.045 per cart

**Monthly (100 carts)**:
- ~$4.50/month

**Recommendation**: Enable LLM only when:
- User explicitly requests it
- Budget allows ($50-100/month for 1000-2000 carts)
- Fallback to deterministic is acceptable

## Performance

**Latency**:
- Ingredient extraction: 1-3 seconds
- Decision explanations: 0.5-1 second per item (can parallelize)

**Recommendation**:
- Show loading indicators in UI
- Consider caching common queries
- Run explanations in background if possible

## Next Steps

1. Complete DecisionEngine LLM integration
2. Update Orchestrator to wire everything together
3. Add UI toggle for LLM features
4. Test end-to-end flow
5. Document for users
