# Testing Cheat Sheet - One Page Reference

## 🎯 3-Layer Testing Strategy

| Layer | Use For | Tokens | Cost | When |
|-------|---------|--------|------|------|
| **1. Unit** | Logic tests | **0** | **FREE** | Every commit ✅ |
| **2. Integration** | LLM tests | 50 (cached) | $0.00001 | Daily ✅ |
| **3. E2E** | Full flow | 3000 | $0.009 | Before deploy ⚠️ |

---

## 🚀 Quick Commands

```bash
# Fast tests (0 tokens, instant)
python tests/test_ingredient_agent_opik.py

# Include LLM tests (with caching)
python tests/test_ingredient_agent_opik.py --expensive

# View results in Opik
open https://www.comet.com/opik
```

---

## 💡 Code Templates

### Layer 1: Unit Test (0 Tokens)
```python
def test_without_llm():
    agent = IngredientAgent(use_llm=False)  # Template mode
    result = agent.extract("chicken biryani for 4", servings=4)
    assert result.chicken_qty == 2.0  # ✅ FREE
```

### Layer 2: Integration Test (Haiku + Cache)
```python
def test_with_haiku():
    result = calculate_quantity(
        ingredient="chicken",
        model="claude-haiku-20250514"  # 12X cheaper!
    )
    assert result.packages_needed == 3  # ✅ $0.00001
```

### Layer 3: E2E Test (Full LLM)
```python
@pytest.mark.expensive  # Run manually only
def test_full_flow():
    result = orchestrator.process_prompt(
        "chicken biryani for 12",
        use_llm_explanations=True
    )
    assert result.item_count >= 10  # ⚠️ $0.009
```

---

## 🔍 How to Debug Failures

### Step 1: Check Test Output
```bash
❌ FAIL: Missing ingredients: ['saffron', 'cilantro']
   → Problem: Ingredient extraction incomplete
```

### Step 2: Look at Opik Dashboard
```
Trace: "chicken biryani for 4"
  ├─ Span: extract_ingredients ✅ (13 ingredients)
  ├─ Span: get_candidates ❌ (only 8 matched) ← PROBLEM HERE!
  └─ Span: decide ✅ (scored 8 items)
```

### Step 3: Add Debug Logging
```bash
export LOG_LEVEL=DEBUG
python tests/test_ingredient_agent_opik.py
```

---

## 📊 Testing Checklist

### Before Every Commit
- [ ] Run Layer 1 tests (fast, free)
- [ ] All tests pass
- [ ] No new failures introduced

### Daily
- [ ] Run Layer 2 tests (with caching)
- [ ] Check Opik dashboard for trends
- [ ] Fix any regressions

### Before Deploy
- [ ] Run Layer 3 tests (full LLM)
- [ ] Compare with baseline
- [ ] Verify production quality

---

## 💰 Cost Calculator

```
Your Monthly Cost:

Layer 1 (Run 100X/day):
  100 runs × 0 tokens = $0.00

Layer 2 (Run 10X/day):
  10 runs × 50 tokens (cached) × $0.25/1M = $0.0001/day
  $0.0001 × 30 days = $0.003/month

Layer 3 (Run 5X/month):
  5 runs × 3000 tokens × $3/1M = $0.045/month

TOTAL: ~$0.05/month

Compare to naive approach: $270/month
Savings: 99.98% ($269.95/month)
```

---

## 🎯 What to Test Where

### Layer 1 (Unit Tests - 0 Tokens)
✅ Ingredient scaling
✅ Recipe detection
✅ Product matching
✅ Scoring logic
✅ Distance calculations
✅ Unit conversions
✅ EWG classification
✅ Seasonality checks

### Layer 2 (Integration - Haiku + Cache)
✅ Quantity reconciliation (LLM)
✅ Ambiguous prompts (LLM)
✅ Decision explanations (LLM)
✅ Tag generation (LLM)

### Layer 3 (E2E - Full LLM)
✅ Complete user flow
✅ Edge cases
✅ Production quality check
✅ Multiple agents together

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| "Too many tokens" | Use Layer 1 tests (0 tokens) |
| "Tests too slow" | Use caching + Haiku |
| "Different results" | Run Layer 3 to verify with Sonnet |
| "Cache not working" | Check `.llm_cache/` folder exists |
| "Opik not showing" | Set `OPIK_ENABLED="1"` |

---

## 📈 Expected Results

### Good Test Suite
```
Layer 1: 80 tests, 100% pass, 0 tokens, 2 seconds
Layer 2: 15 tests, 100% pass, 50 tokens (cached), 5 seconds
Layer 3: 5 tests, 100% pass, 3000 tokens, 30 seconds

Total: 100 tests, 100% pass, ~$0.05/month
```

### Red Flags
```
❌ Most tests use LLM (expensive!)
❌ No caching (paying repeatedly)
❌ Layer 3 runs on every commit (wasteful)
❌ Using Opus for testing (60X too expensive)
```

---

## 🔧 Configuration

### pytest.ini
```ini
[pytest]
markers =
    expensive: marks expensive LLM tests (run manually)

# Default: Run fast tests only
# pytest

# Run expensive tests
# pytest -m expensive
```

### Environment Variables
```bash
# Required for Opik
export OPIK_API_KEY="your-key"
export OPIK_ENABLED="1"

# Optional for debugging
export LOG_LEVEL=DEBUG

# Optional: Use Haiku for all tests
export TEST_MODEL="claude-haiku-20250514"
```

---

## 📚 Documentation Links

| Document | What It Covers |
|----------|----------------|
| [TESTING_SUMMARY.md](TESTING_SUMMARY.md) | Simple overview (this is what you read first) |
| [EFFICIENT_LLM_TESTING.md](EFFICIENT_LLM_TESTING.md) | Complete technical guide with examples |
| [OPIK_TESTING_GUIDE.md](OPIK_TESTING_GUIDE.md) | What to test in each agent |
| [test_ingredient_agent_opik.py](../tests/test_ingredient_agent_opik.py) | Working example code |

---

## ✅ Quick Wins

1. **Use template mode** → Save $200/month
2. **Add caching** → Save $50/month
3. **Switch to Haiku** → Save $15/month
4. **Mark expensive tests** → Save $5/month

**Total savings: $270/month with 5 minutes of setup**

---

**Print this page and keep it handy! 📄**
