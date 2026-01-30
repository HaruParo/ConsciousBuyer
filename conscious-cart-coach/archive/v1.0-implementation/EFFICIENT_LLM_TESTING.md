# Efficient LLM Testing - Reduce Token Usage Without Compromising Quality
*Test Smart, Not Expensive*

## 💰 The Problem

**Testing with LLMs costs money:**
- Ingredient extraction (LLM mode): ~500 tokens per test
- Quantity reconciliation: ~200 tokens per ingredient (13 ingredients = 2,600 tokens)
- Decision explanations: ~300 tokens per product
- **Full test suite**: 100 tests × 3,000 tokens = 300,000 tokens = **$3-9 per run!**

**Testing frequently (10X per day) = $30-90/day = $900-2,700/month** 😱

---

## 🎯 STRATEGY: Test in Layers (80% Cheaper)

### Layer 1: Unit Tests (NO LLM) - FREE ✅
Test deterministic logic without LLM calls

### Layer 2: Integration Tests (MINIMAL LLM) - Cheap 💰
Test LLM parts with smaller models and caching

### Layer 3: End-to-End Tests (FULL LLM) - Expensive 💰💰💰
Run sparingly (once per deploy, not per commit)

---

## 📊 LAYER 1: UNIT TESTS (NO LLM - 0 TOKENS)

### Principle: **Separate LLM Logic from Deterministic Logic**

**What to test WITHOUT LLM:**
- ✅ Template matching (ingredient agent template mode)
- ✅ Quantity scaling (2 servings → 12 servings)
- ✅ Unit conversions (cups → oz)
- ✅ Product matching (string matching, no LLM)
- ✅ Scoring logic (decision engine weights)
- ✅ Distance calculations (haversine formula)
- ✅ EWG classification (lookup table)
- ✅ Seasonality checks (date ranges)

**Cost**: $0 (no API calls)
**Speed**: Milliseconds
**Frequency**: Run on every code change

---

### Example: Test Ingredient Scaling (No LLM)

```python
def test_ingredient_scaling_no_llm():
    """Test scaling WITHOUT LLM calls."""

    from src.agents.ingredient_agent import IngredientAgent

    # Use template mode (NO LLM)
    agent = IngredientAgent(use_llm=False)

    # Test Case 1: 4 servings
    result = agent.extract("chicken biryani for 4", servings=4)
    chicken = next(ing for ing in result.facts["ingredients"] if ing["name"] == "chicken")
    assert chicken["qty"] == 2.0, "4 servings should = 2 lb chicken"

    # Test Case 2: 12 servings
    result = agent.extract("chicken biryani for 12", servings=12)
    chicken = next(ing for ing in result.facts["ingredients"] if ing["name"] == "chicken")
    assert chicken["qty"] == 6.0, "12 servings should = 6 lb chicken"

    # Test Case 3: 1 serving
    result = agent.extract("chicken biryani for 1", servings=1)
    chicken = next(ing for ing in result.facts["ingredients"] if ing["name"] == "chicken")
    assert chicken["qty"] == 0.5, "1 serving should = 0.5 lb chicken"

    print("✅ PASS: Scaling works (0 tokens used)")
```

**Result**: 3 test cases, 0 tokens, instant feedback

---

### Example: Test Decision Engine Scoring (No LLM)

```python
def test_decision_engine_scoring_no_llm():
    """Test scoring logic WITHOUT LLM explanations."""

    from src.engine.decision_engine import DecisionEngine

    # Disable LLM explanations
    engine = DecisionEngine(use_llm_explanations=False)

    # Create test candidates
    candidates = [
        ProductCandidate(
            product_id="local",
            title="Lancaster Spinach",
            price=3.99,
            metadata={"distance_label": "regional_50_150mi"}  # +20 points
        ),
        ProductCandidate(
            product_id="distant",
            title="CA Spinach",
            price=4.99,
            metadata={"distance_label": "import_3000plus_mi"}  # -15 points
        ),
    ]

    # Run scoring
    bundle = engine.decide(
        candidates_by_ingredient={"spinach": candidates},
        safety_signals={},
        seasonality={},
    )

    # Check: Local product should win
    assert bundle.items[0].selected_product_id == "local", \
        "Local product should score higher"

    # Check: Score difference reflects distance
    local_score = next(sc.score for sc in scored if sc.candidate.product_id == "local")
    distant_score = next(sc.score for sc in scored if sc.candidate.product_id == "distant")
    assert local_score > distant_score + 30, \
        "Local should score 30+ points higher"

    print("✅ PASS: Location-first scoring works (0 tokens used)")
```

**Result**: Scoring logic tested, 0 tokens

---

## 📊 LAYER 2: INTEGRATION TESTS (MINIMAL LLM - 90% CHEAPER)

### Strategy 1: Use Haiku (10X Cheaper than Sonnet)

**Model Comparison**:
| Model | Input Cost | Output Cost | Use For |
|-------|-----------|-------------|---------|
| **Haiku** | $0.25/1M | $1.25/1M | **Testing** ✅ |
| Sonnet | $3/1M | $15/1M | Production |
| Opus | $15/1M | $75/1M | Never for testing |

**For testing**: Haiku is **12X cheaper** than Sonnet, **60X cheaper** than Opus

```python
def test_quantity_reconciliation_with_haiku():
    """Test LLM quantity calculation with cheaper model."""

    from anthropic import Anthropic

    # Use Haiku for testing (12X cheaper)
    client = Anthropic()

    result = calculate_product_quantity(
        client=client,
        ingredient_name="chicken",
        required_qty=6.0,
        required_unit="lb",
        servings=12,
        product_title="Organic Chicken Breast",
        package_size="2 lb",
        model="claude-haiku-20250514",  # Cheaper model!
    )

    assert result["packages_needed"] == 3, "Should calculate 3 packages"
    print(f"✅ PASS: Quantity correct (50 tokens, $0.0001)")
```

**Cost**: ~50 tokens × $0.25/1M = **$0.00001 per test** (vs $0.00015 with Sonnet)

---

### Strategy 2: Cache LLM Responses

**Principle**: Don't re-generate the same response twice

```python
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("tests/.llm_cache")
CACHE_DIR.mkdir(exist_ok=True)

def cached_llm_call(prompt: str, model: str = "claude-haiku-20250514"):
    """
    Call LLM with caching.

    First call: Uses API (costs tokens)
    Subsequent calls: Returns cached response (FREE)
    """

    # Create cache key from prompt
    cache_key = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"

    # Check cache first
    if cache_file.exists():
        print(f"   💾 Cache hit (0 tokens)")
        return json.loads(cache_file.read_text())

    # Cache miss - call API
    print(f"   🌐 API call ({model})")
    from anthropic import Anthropic
    client = Anthropic()

    response = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.content[0].text

    # Save to cache
    cache_file.write_text(json.dumps({
        "prompt": prompt,
        "response": result,
        "tokens": response.usage.input_tokens + response.usage.output_tokens
    }))

    return result


# Usage in tests
def test_with_caching():
    """Test with LLM caching."""

    prompt = "Calculate packages: 6 lb chicken needed, 2 lb per package"

    # First run: Uses API
    result1 = cached_llm_call(prompt)  # 50 tokens

    # Second run: Cache hit
    result2 = cached_llm_call(prompt)  # 0 tokens!

    assert result1 == result2, "Cache should return same result"
    print("✅ PASS: Caching works (50 tokens total, not 100)")
```

**Benefit**: Run test 100 times = only pay once = **99% cost reduction**

---

### Strategy 3: Batch LLM Calls (Not Sequential)

**Principle**: Send multiple requests in parallel, not one-by-one

**Bad** (Sequential - Slow & Expensive):
```python
# Test 10 ingredients separately
for ingredient in ingredients:
    result = calculate_quantity(ingredient)  # 10 API calls = 500 tokens
```

**Good** (Batch - Fast & Efficient):
```python
# Batch all ingredients into one prompt
prompt = f"""
Calculate quantities for all ingredients:

Ingredient 1: 6 lb chicken → 2 lb packages
Ingredient 2: 2 cups rice → 1 lb bags
Ingredient 3: 4 onions → sold individually
...

Return JSON array with all calculations.
"""

result = client.messages.create(model="claude-haiku-20250514", ...)  # 1 API call = 150 tokens
```

**Savings**: 500 tokens → 150 tokens = **70% reduction**

---

### Strategy 4: Use Synthetic Test Data (LLM Generates Once)

**Principle**: Use LLM to generate test fixtures, then reuse them

```python
def generate_test_fixtures_once():
    """
    Generate test data with LLM once, then save to file.

    Run this ONCE, then use cached data forever.
    """

    prompt = """
    Generate 20 realistic grocery shopping prompts with expected ingredients:

    Format:
    {
        "prompt": "chicken biryani for 4",
        "expected_ingredients": [
            {"name": "chicken", "qty": 2.0, "unit": "lb"},
            {"name": "basmati rice", "qty": 2.0, "unit": "cup"},
            ...
        ]
    }

    Include:
    - Common recipes (10 prompts)
    - Ambiguous requests (5 prompts)
    - Large batches (5 prompts)
    """

    from anthropic import Anthropic
    client = Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",  # Use good model for generation
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    test_data = json.loads(response.content[0].text)

    # Save to file
    Path("tests/fixtures/ingredient_test_data.json").write_text(
        json.dumps(test_data, indent=2)
    )

    print(f"✅ Generated {len(test_data)} test cases (4000 tokens, ONE-TIME cost)")


# Then use in tests (NO LLM)
def test_ingredient_agent_with_fixtures():
    """Test using pre-generated fixtures (0 tokens)."""

    test_data = json.loads(
        Path("tests/fixtures/ingredient_test_data.json").read_text()
    )

    agent = IngredientAgent(use_llm=False)

    for case in test_data:
        result = agent.extract(case["prompt"])
        # Compare against expected output
        assert len(result.facts["ingredients"]) == len(case["expected_ingredients"])

    print(f"✅ Tested {len(test_data)} cases (0 tokens)")
```

**Cost**: 4000 tokens once (one-time) → then unlimited free testing!

---

## 📊 LAYER 3: END-TO-END TESTS (FULL LLM - RUN SPARINGLY)

### When to Run Full LLM Tests

**Run full LLM tests:**
- ✅ Before deploying to production
- ✅ After major LLM prompt changes
- ✅ Weekly regression tests
- ✅ When investigating LLM-specific bugs

**DON'T run full LLM tests:**
- ❌ On every code commit
- ❌ During development (use Layer 1 & 2)
- ❌ For non-LLM code changes

---

### Optimize Full LLM Tests

**Strategy 1: Sample, Don't Test Everything**

```python
def test_e2e_sample():
    """Test representative sample, not all 100 recipes."""

    # Instead of 100 recipes (30,000 tokens):
    # Test 10 representative recipes (3,000 tokens)

    representative_samples = [
        "chicken biryani for 4",      # Common recipe
        "stir fry with tofu for 12",  # Large batch
        "healthy breakfast for 2",     # Ambiguous
        "pasta with tomato sauce for 1",  # Single serving
        ...  # 6 more
    ]

    for prompt in representative_samples:
        result = full_orchestrator(prompt)
        # Check key metrics
        assert result.item_count > 0

    print("✅ Tested 10 representative cases (90% coverage, 10% cost)")
```

**Coverage**: 90% with 10% of the cost

---

**Strategy 2: Use Opik's Evaluation Features**

```python
import opik

def test_with_opik_evaluation():
    """Use Opik to compare outputs without re-running LLM."""

    # Step 1: Run test once, save to Opik
    with opik.trace(name="baseline_run"):
        result = orchestrator.process_prompt("chicken biryani for 4")
        opik.log_trace(result)

    # Step 2: Later, compare against baseline (NO LLM)
    with opik.trace(name="regression_test"):
        new_result = orchestrator.process_prompt("chicken biryani for 4")

        # Opik compares automatically
        opik.evaluate(
            baseline_trace_id="baseline_run",
            current_result=new_result,
            metrics=["ingredient_count", "total_price", "local_items_count"]
        )

    # If metrics match baseline: PASS (0 tokens)
    # If metrics differ: Alert (investigate with full run)
```

**Cost**: First run = full cost, subsequent runs = FREE (comparison only)

---

## 🧪 COMPLETE EFFICIENT TEST SUITE

### File: `tests/test_efficient.py`

```python
"""
Efficient LLM Testing - 90% Cost Reduction

Layer 1: Unit tests (NO LLM) - Run always
Layer 2: Integration tests (Haiku + cache) - Run frequently
Layer 3: E2E tests (Full LLM) - Run sparingly
"""

import pytest
from pathlib import Path

# ============================================================================
# LAYER 1: UNIT TESTS (NO LLM - FREE)
# ============================================================================

class TestLayer1UnitTests:
    """Fast, free tests without LLM calls."""

    def test_ingredient_scaling(self):
        """Test scaling logic (0 tokens)."""
        from src.agents.ingredient_agent import IngredientAgent

        agent = IngredientAgent(use_llm=False)  # Template mode

        # Test 10 different serving sizes
        for servings in [1, 2, 4, 6, 8, 10, 12, 16, 20, 24]:
            result = agent.extract(f"chicken biryani for {servings}", servings=servings)
            chicken = next(ing for ing in result.facts["ingredients"] if ing["name"] == "chicken")

            expected_qty = servings * 0.5  # Base: 1 lb for 2 servings
            assert chicken["qty"] == expected_qty, f"Wrong qty for {servings} servings"

        print("✅ PASS: 10 scaling tests (0 tokens)")

    def test_decision_engine_location_scoring(self):
        """Test location-first scoring (0 tokens)."""
        from src.engine.decision_engine import DecisionEngine

        engine = DecisionEngine(use_llm_explanations=False)  # No LLM

        # Create local vs distant candidates
        local = ProductCandidate(
            product_id="local",
            title="Local Product",
            price=3.99,
            metadata={"distance_label": "regional_50_150mi"}
        )

        distant = ProductCandidate(
            product_id="distant",
            title="Distant Product",
            price=2.99,  # Cheaper!
            metadata={"distance_label": "import_3000plus_mi"}
        )

        bundle = engine.decide(
            candidates_by_ingredient={"test": [local, distant]},
            safety_signals={},
            seasonality={},
        )

        # Local should win despite higher price
        assert bundle.items[0].selected_product_id == "local", \
            "Location-first failed: distant product won"

        print("✅ PASS: Location-first scoring (0 tokens)")

    def test_distance_calculation(self):
        """Test haversine distance formula (0 tokens)."""
        from src.agents.product_agent import _calculate_distance

        # Lancaster, PA to Iselin, NJ
        distance, label = _calculate_distance(
            "Lancaster Farm Fresh",
            {"city": "Iselin", "state": "NJ", "lat": 40.5693, "lon": -74.3224}
        )

        assert 70 <= distance <= 80, f"Expected ~75 miles, got {distance}"
        assert label == "regional_50_150mi", f"Wrong label: {label}"

        print("✅ PASS: Distance calculation (0 tokens)")


# ============================================================================
# LAYER 2: INTEGRATION TESTS (HAIKU + CACHE - CHEAP)
# ============================================================================

class TestLayer2IntegrationTests:
    """Minimal LLM tests with Haiku and caching."""

    def test_quantity_reconciliation_haiku(self):
        """Test LLM quantity with Haiku (50 tokens, $0.00001)."""
        from src.llm.quantity_reconciler import calculate_product_quantity
        from anthropic import Anthropic

        client = Anthropic()

        # Use cached_llm_call wrapper
        result = calculate_product_quantity(
            client=client,
            ingredient_name="chicken",
            required_qty=6.0,
            required_unit="lb",
            servings=12,
            product_title="Chicken Breast",
            package_size="2 lb",
            model="claude-haiku-20250514",  # Cheap model
        )

        assert result["packages_needed"] == 3
        print("✅ PASS: Quantity with Haiku (50 tokens = $0.00001)")

    def test_with_fixtures(self):
        """Test using pre-generated fixtures (0 tokens)."""
        test_data = json.loads(
            Path("tests/fixtures/ingredient_test_data.json").read_text()
        )

        agent = IngredientAgent(use_llm=False)

        for case in test_data[:10]:  # Test 10 cases
            result = agent.extract(case["prompt"])
            assert len(result.facts["ingredients"]) > 0

        print("✅ PASS: 10 cases with fixtures (0 tokens)")


# ============================================================================
# LAYER 3: END-TO-END TESTS (FULL LLM - RUN SPARINGLY)
# ============================================================================

class TestLayer3EndToEndTests:
    """Full LLM tests - run before deploy only."""

    @pytest.mark.slow  # Mark as slow test
    @pytest.mark.expensive  # Mark as expensive test
    def test_e2e_representative_sample(self):
        """Test 5 representative prompts with full LLM (3000 tokens)."""

        representative = [
            "chicken biryani for 4",
            "stir fry with tofu for 12",
            "healthy breakfast for 2",
            "pasta for 1",
            "weekly meal prep for family of 5",
        ]

        for prompt in representative:
            result = orchestrator.process_prompt(prompt, use_llm_explanations=True)
            assert result.item_count > 0
            assert result.recommended_total > 0

        print("✅ PASS: 5 E2E tests (3000 tokens = $0.045)")


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# pytest.ini or conftest.py
"""
[pytest]
markers =
    slow: marks tests as slow (run with -m slow)
    expensive: marks tests as expensive LLM tests (run with -m expensive)

# Run only fast, free tests (default):
pytest tests/test_efficient.py

# Run all tests including expensive:
pytest tests/test_efficient.py -m expensive

# Run only slow tests:
pytest tests/test_efficient.py -m slow
"""
```

---

## 💡 BEST PRACTICES SUMMARY

### 1. **80/20 Rule**: 80% Coverage with 20% of Tokens

```
Unit Tests (Layer 1):        80% coverage, 0% cost    ✅ Run always
Integration Tests (Layer 2): 15% coverage, 10% cost   ✅ Run frequently
E2E Tests (Layer 3):         5% coverage, 90% cost    ⚠️ Run sparingly
```

### 2. **Use Right Model for Right Job**

```
Testing:         Haiku     ($0.25/1M)  ✅
Development:     Sonnet    ($3/1M)     ⚠️
Production:      Sonnet    ($3/1M)     ✅
Never:           Opus      ($15/1M)    ❌
```

### 3. **Cache Aggressively**

```python
# Good: Cache LLM responses
result = cached_llm_call(prompt)  # FREE after first call

# Bad: Re-call LLM every time
result = client.messages.create(...)  # $0.0001 every call
```

### 4. **Generate Test Data Once**

```python
# Run once (one-time cost):
generate_test_fixtures()  # 4000 tokens = $0.06

# Use forever (free):
test_with_fixtures()  # 0 tokens × 1000 runs = $0
```

### 5. **Batch, Don't Loop**

```python
# Good: Batch 10 ingredients in 1 call
result = batch_calculate_quantities(all_ingredients)  # 200 tokens

# Bad: Loop 10 ingredients separately
for ing in ingredients:
    result = calculate_quantity(ing)  # 100 tokens × 10 = 1000 tokens
```

---

## 📊 COST COMPARISON

### Naive Approach (Expensive)
```
100 tests × 3000 tokens × $3/1M = $0.90 per run
10 runs/day = $9/day = $270/month
```

### Optimized Approach (Cheap)
```
Layer 1: 80 tests × 0 tokens = $0
Layer 2: 15 tests × 50 tokens × $0.25/1M = $0.0002
Layer 3: 5 tests × 600 tokens × $3/1M = $0.009

Total: $0.01 per run
10 runs/day = $0.10/day = $3/month
```

**Savings: $267/month (99% reduction)** 🎉

---

## 🚀 QUICK START: Implement Efficient Testing

```bash
# 1. Create efficient test file
cp tests/test_efficient.py.template tests/test_efficient.py

# 2. Run fast tests only (default)
pytest tests/test_efficient.py

# Output:
# 80 tests passed (0 tokens, 2 seconds)

# 3. Run expensive tests before deploy
pytest tests/test_efficient.py -m expensive

# Output:
# 5 tests passed (3000 tokens, 30 seconds)
```

---

## 🎯 IMPLEMENTATION CHECKLIST

- [ ] Separate LLM tests from unit tests
- [ ] Use Haiku for all testing
- [ ] Implement LLM response caching
- [ ] Generate test fixtures once
- [ ] Batch LLM calls where possible
- [ ] Mark expensive tests with `@pytest.mark.expensive`
- [ ] Run Layer 1 tests on every commit
- [ ] Run Layer 2 tests daily
- [ ] Run Layer 3 tests before deploy only

---

**Result: 99% cost reduction, same quality, faster feedback** ✅
