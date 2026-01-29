# Conscious Cart Coach - Usage Guide

**Date**: 2026-01-24

## Quick Start

### Installation

```bash
cd conscious-cart-coach
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Setup

Create `.env` file in project root:

```bash
# Required for LLM features (optional)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional: PostgreSQL for advanced features
# DATABASE_URL=postgresql://...

# Optional: Experiment tracking
# OPIK_API_KEY=...
```

### Run the UI

```bash
./run.sh
```

Open browser to `http://localhost:8501`

---

## Usage Modes

### Mode 1: Deterministic Only (Default)

**No API calls, no costs, fast responses**

```python
from src.orchestrator import Orchestrator

# Initialize without LLM
orch = Orchestrator()

# Process user prompt
bundle = orch.process_prompt("chicken biryani for 4")

# Results
print(f"Found {len(bundle.items)} items")
print(f"Total: ${bundle.recommended_total:.2f}")

for item in bundle.items:
    print(f"- {item.ingredient_name}: {item.reason_short}")
```

**Capabilities**:
- ✅ Template-based ingredient extraction (4 recipes)
- ✅ Product matching from store inventory
- ✅ Deterministic scoring (EWG, seasonality, price)
- ✅ 3-tier recommendations (cheaper/balanced/conscious)
- ✅ Fast (no API latency)
- ✅ Free (no API costs)

**Limitations**:
- ❌ Only handles hardcoded recipes (biryani, tikka, salad, stir_fry)
- ❌ Can't parse natural language ("I want something healthy")
- ❌ Basic explanations ("Best value per oz")

---

### Mode 2: LLM Ingredient Extraction

**Natural language understanding for prompts**

```python
from src.orchestrator import Orchestrator

# Enable LLM for ingredient extraction only
orch = Orchestrator(use_llm_extraction=True)

# Now can handle vague/natural prompts
bundle = orch.process_prompt("I want something healthy and seasonal for dinner")
# Claude extracts: spinach, tomatoes, cucumber, olive oil, etc.

# Scoring still deterministic
for item in bundle.items:
    print(f"{item.ingredient_name}: {item.reason_short}")
```

**Added Capabilities**:
- ✅ Parse natural language prompts
- ✅ Handle vague requests ("something healthy")
- ✅ Understand cuisine preferences ("Italian dinner")
- ✅ Extract from recipe descriptions

**Cost**: ~$0.01-0.02 per prompt

**Latency**: +1-3 seconds

---

### Mode 3: Full LLM (Extraction + Explanations)

**Best experience with natural language prompts and detailed explanations**

```python
from src.orchestrator import Orchestrator

# Enable both LLM features
orch = Orchestrator(
    use_llm_extraction=True,
    use_llm_explanations=True,
)

bundle = orch.process_prompt("I want a healthy dinner for my family")

# Ingredient extraction via Claude
print(f"Extracted {len(bundle.items)} ingredients")

# Scoring still deterministic, but explanations from Claude
for item in bundle.items:
    print(f"\n{item.ingredient_name}:")
    print(f"  Score: {item.score}/100")
    print(f"  Tier: {item.tier_symbol}")
    print(f"  Quick: {item.reason_short}")
    if item.reason_llm:
        print(f"  Detailed: {item.reason_llm}")
```

**Added Capabilities**:
- ✅ Natural language prompts (via Claude)
- ✅ Detailed explanations (via Claude)
- ✅ Scoring remains deterministic

**Cost**: ~$0.045 per cart (10 items)

**Latency**: +2-4 seconds total

---

## Step-by-Step Usage

```python
from src.orchestrator import Orchestrator

# Initialize (with or without LLM)
orch = Orchestrator(use_llm_extraction=True)

# Step 1: Extract ingredients
result = orch.step_ingredients("chicken biryani for 4")
ingredients = result.facts["ingredients"]
print(f"Found {len(ingredients)} ingredients")

# Step 2: User confirmation (optional)
# User can modify ingredient list here
orch.confirm_ingredients(ingredients)

# Step 3: Get product candidates
orch.step_candidates()
print(f"Found candidates for {len(orch.state.candidates_by_ingredient)} ingredients")

# Step 4: Enrich with safety/seasonal data
orch.step_enrich()

# Step 5: Make decisions
bundle = orch.step_decide()
print(f"Recommended total: ${bundle.recommended_total:.2f}")
print(f"Cheaper option: ${bundle.totals['cheaper']:.2f}")
print(f"Conscious option: ${bundle.totals['conscious']:.2f}")
```

---

## API Reference

### Orchestrator

```python
class Orchestrator:
    def __init__(
        self,
        user_id: str = "default",
        use_llm_extraction: bool = False,
        use_llm_explanations: bool = False,
        anthropic_client: Optional[Anthropic] = None,
    ):
        """
        Initialize Orchestrator.

        Args:
            user_id: User identifier for history tracking
            use_llm_extraction: Enable Claude for ingredient parsing
            use_llm_explanations: Enable Claude for decision explanations
            anthropic_client: Optional shared Anthropic client
        """

    def process_prompt(
        self,
        user_prompt: str,
        servings: int | None = None,
        auto_confirm: bool = True,
        user_prefs: UserPrefs | None = None,
    ) -> DecisionBundle:
        """Full flow: prompt → bundle"""

    def step_ingredients(self, prompt: str, servings: int | None = None) -> AgentResult:
        """Extract ingredients (step 1)"""

    def confirm_ingredients(self, ingredients: list[dict] | None = None):
        """Confirm/modify ingredients (gate)"""

    def step_candidates(self) -> AgentResult:
        """Get product candidates (step 3)"""

    def step_enrich(self) -> tuple[AgentResult, AgentResult]:
        """Add safety/seasonal data (step 4)"""

    def step_decide(self) -> DecisionBundle:
        """Make final decisions (step 5)"""
```

### DecisionBundle

```python
@dataclass
class DecisionBundle:
    items: list[DecisionItem]
    totals: dict[str, float]          # {"cheaper": 45.50, "balanced": 67.80, ...}
    deltas: dict[str, float]          # {"cheaper_vs_recommended": -15.30, ...}
    data_gaps: list[str]              # Missing data warnings
    constraint_notes: list[str]       # Hard constraints applied

    @property
    def recommended_total(self) -> float
    def cheaper_total(self) -> float
    def conscious_total(self) -> float
    def item_count(self) -> int
```

### DecisionItem

```python
@dataclass
class DecisionItem:
    ingredient_name: str
    selected_product_id: str
    tier_symbol: TierSymbol           # CHEAPER | BALANCED | CONSCIOUS
    reason_short: str                 # "Best value per oz"
    reason_llm: str | None            # "The Earthbound Farm..." (if LLM enabled)
    attributes: list[str]             # ["Organic", "Local", "In Season"]
    safety_notes: list[str]
    cheaper_neighbor_id: str | None   # Alternative product IDs
    conscious_neighbor_id: str | None
    score: int                        # 0-100 deterministic score
    evidence_refs: list[str]
```

---

## Cost & Performance

### Deterministic Mode (Default)

- **Cost**: $0 (no API calls)
- **Latency**: <100ms
- **Use When**: Budget-conscious, known recipes, fast responses needed

### LLM Extraction Only

- **Cost**: ~$0.01-0.02 per prompt
- **Latency**: +1-3 seconds
- **Use When**: Natural language prompts, unknown recipes

### Full LLM (Both Features)

- **Cost**: ~$0.045 per cart (10 items)
- **Latency**: +2-4 seconds
- **Use When**: Best user experience, detailed explanations wanted

### Monthly Cost Estimates

| Usage | Deterministic | LLM Extraction | Full LLM |
|-------|---------------|----------------|----------|
| 10 carts/month | $0 | $0.15 | $0.45 |
| 100 carts/month | $0 | $1.50 | $4.50 |
| 1000 carts/month | $0 | $15.00 | $45.00 |

---

## Testing

```bash
# Run all tests
cd conscious-cart-coach
pytest tests/ -v

# Test specific components
pytest tests/test_pipeline.py -v
pytest tests/test_decision_engine.py -v

# With coverage
pytest --cov=src tests/
```

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

**Cause**: LLM features enabled but no API key

**Solution**:
1. Create `.env` file in project root
2. Add: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. Restart application

**Or**: Disable LLM features
```python
orch = Orchestrator()  # use_llm_extraction=False by default
```

### "LLM module not available"

**Cause**: anthropic package not installed

**Solution**:
```bash
pip install anthropic>=0.18.0
```

### Slow responses with LLM

**Expected**: LLM adds 1-4 seconds latency

**Optimize**:
1. Use LLM only when needed
2. Show loading indicators in UI
3. Consider caching common queries

### High API costs

**Monitor**: Track API usage in Anthropic dashboard

**Reduce Costs**:
1. Use deterministic mode by default
2. Enable LLM only for specific users/tiers
3. Cache ingredient extractions
4. Use LLM explanations sparingly

---

## Next Steps

1. **Try deterministic mode first**: `orch = Orchestrator()`
2. **Test with known recipes**: "chicken biryani for 4"
3. **Enable LLM if needed**: Natural language prompts
4. **Monitor costs**: Check Anthropic dashboard
5. **Optimize**: Use LLM strategically based on user tier/preference
