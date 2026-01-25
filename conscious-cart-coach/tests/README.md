# Test Suite with Opik Integration

This directory contains tests for Conscious Cart Coach, including LLM tests that are automatically tracked in Opik.

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov opik

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only LLM tests (requires ANTHROPIC_API_KEY)
pytest -m llm

# Skip LLM tests
pytest -m "not llm"

# Run slow performance tests
pytest -m slow
```

## Test Structure

```
tests/
├── conftest.py          # Pytest configuration with Opik integration
├── test_pipeline.py     # Original pipeline tests (unit + integration)
├── test_llm.py          # LLM tests with API calls (tracked in Opik)
└── README.md            # This file
```

## Test Categories

### 1. Pipeline Tests (`test_pipeline.py`)
- **Unit tests**: ProductAgent, DecisionEngine, parse_size_oz
- **Integration tests**: Full orchestrator workflows
- **No API calls**: Fast, deterministic
- **Run**: `pytest tests/test_pipeline.py`

### 2. LLM Tests (`test_llm.py`)
- **API tests**: Calls Anthropic Claude API
- **Opik tracked**: All tests logged in Opik dashboard
- **Requires**: `ANTHROPIC_API_KEY` environment variable
- **Run**: `pytest tests/test_llm.py -m llm`

**Test classes**:
- `TestAnthropicClient`: Client initialization and basic calls
- `TestIngredientExtraction`: Natural language → structured ingredients
- `TestDecisionExplanation`: Product recommendations → natural language
- `TestLLMIntegration`: Full extraction + explanation workflow
- `TestLLMPerformance`: Latency and performance benchmarks

## Opik Integration

All LLM tests are automatically tracked in Opik with:
- ✅ Test results (pass/fail)
- ✅ API calls made during tests
- ✅ Prompts and responses
- ✅ Token usage and costs
- ✅ Latency measurements
- ✅ Test metadata and parameters

### About Threads vs Individual Traces

**Current behavior**: Each LLM test creates **individual traces**, not conversation threads.

**Why?** We use `track_anthropic()` which tracks each API call separately.

**What you'll see in Opik**:
- Each test = 1 trace
- Trace name: "ingredient_extraction" or "decision_explanation"
- No grouping/threading (this is expected)

**Want conversation threads?** See [OPIK_THREADS_EXPLAINED.md](../../OPIK_THREADS_EXPLAINED.md) for how to add explicit thread tracking with session IDs.

**TL;DR**: Current setup is correct and working as designed. Individual traces are easier to analyze and search.

### How It Works

1. **Automatic Setup**: `conftest.py` registers Opik pytest plugin
2. **Client Fixture**: `anthropic_client` fixture provides configured client
3. **Trace Tracking**: All LLM calls use `trace_name` and `metadata`
4. **Dashboard View**: Results appear in Opik dashboard under project "consciousbuyer"

### View Results

**Opik Cloud**:
```bash
# Make sure OPIK_API_KEY is set
export OPIK_API_KEY=your_key
export OPIK_WORKSPACE=your_workspace

# Run tests
pytest -m llm

# View results at https://www.comet.com/opik
# Navigate to: Project "consciousbuyer" → Tests
```

**Local Opik**:
```bash
# Start local Opik
docker run -d -p 5000:5000 comet-opik/opik:latest

# Set override
export OPIK_URL_OVERRIDE=http://localhost:5000

# Run tests
pytest -m llm

# View at http://localhost:5000
```

## Environment Setup

### Required for LLM Tests

Create `.env` file in project root:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here
OPIK_API_KEY=your_opik_key          # Optional
OPIK_WORKSPACE=your_workspace       # Optional
OPIK_PROJECT_NAME=consciousbuyer   # Optional (default)
```

### Without Opik

Tests work without Opik:
```bash
# Just set Anthropic key
export ANTHROPIC_API_KEY=sk-ant-api03-your_key

# Run tests (no Opik tracking)
pytest -m llm
```

You'll see: `⚠️  OPIK_API_KEY not found. Test tracking disabled.`

Tests still run, but won't appear in Opik dashboard.

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only LLM tests
pytest -m llm

# Run only fast tests (skip slow)
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Run unit tests
pytest -m unit

# Combine markers
pytest -m "llm and not slow"
```

## Example Test Output

```
tests/test_llm.py::TestIngredientExtraction::test_extract_simple_recipe PASSED
tests/test_llm.py::TestIngredientExtraction::test_extract_vague_request PASSED
tests/test_llm.py::TestDecisionExplanation::test_explain_simple_recommendation PASSED

✅ Opik test tracking enabled
📊 3 tests logged to Opik project: consciousbuyer
💰 Total cost: ~$0.08
⏱️  Total duration: 4.2s
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run tests with Opik tracking
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    OPIK_API_KEY: ${{ secrets.OPIK_API_KEY }}
    OPIK_WORKSPACE: ${{ secrets.OPIK_WORKSPACE }}
  run: |
    pytest -m llm --junitxml=test-results.xml
```

## Cost Considerations

LLM tests call real APIs with costs:

| Test Class | Tests | Avg Cost | Total |
|------------|-------|----------|-------|
| TestAnthropicClient | 3 | $0.001 | $0.003 |
| TestIngredientExtraction | 6 | $0.01 | $0.06 |
| TestDecisionExplanation | 6 | $0.005 | $0.03 |
| TestLLMIntegration | 2 | $0.015 | $0.03 |
| TestLLMPerformance | 2 | $0.01 | $0.02 |
| **Total** | **19** | - | **~$0.14** |

**Per full test run**: ~$0.14

**Recommendation**:
- Run frequently during development (tests are cheap)
- Use Opik to track costs over time
- Set daily cost alerts if needed

## Debugging Failed Tests

### 0. Environment Variables Not Loading

**Issue**: `pytest.skip: ANTHROPIC_API_KEY not found`

**Fix**: The updated `conftest.py` now automatically loads `.env` file. Verify it's working:

```bash
# Quick environment check
pytest tests/test_env_loading.py -v -s

# Should show:
# ✅ .env file exists at: /path/to/.env
# ✅ ANTHROPIC_API_KEY loaded: sk-ant-api03-...
# ✅ Ready to run LLM tests!
```

**If still failing**:
```bash
# 1. Check .env file exists
ls -la conscious-cart-coach/.env

# 2. Check python-dotenv is installed
pip install python-dotenv

# 3. Load manually before running tests
export $(cat conscious-cart-coach/.env | xargs)
pytest -m llm
```

### 1. Test Failed Locally

```bash
# Run with verbose output
pytest tests/test_llm.py::TestIngredientExtraction::test_extract_simple_recipe -vv

# Check logs
pytest --log-cli-level=DEBUG
```

### 2. Check Opik Dashboard

1. Go to Opik dashboard
2. Filter by: `Tags = "consciousbuyer" AND Status = "error"`
3. Click failed trace
4. View exact prompt, response, and error message

### 3. Common Issues

**Issue**: `pytest.skip: ANTHROPIC_API_KEY not found`
```bash
# Fix: Set API key
export ANTHROPIC_API_KEY=sk-ant-api03-your_key
```

**Issue**: `Opik not installed`
```bash
# Fix: Install Opik
pip install opik>=0.1.0
```

**Issue**: Tests timeout
```bash
# Fix: Increase timeout in pytest.ini or skip slow tests
pytest -m "not slow"
```

## Best Practices

1. **Run tests before committing**:
   ```bash
   pytest -m "not slow"  # Fast tests only
   ```

2. **Check Opik dashboard weekly**:
   - Review test pass rates
   - Monitor API costs
   - Identify flaky tests

3. **Use markers appropriately**:
   - Mark slow tests with `@pytest.mark.slow`
   - Mark integration tests with `@pytest.mark.integration`
   - LLM tests auto-marked with `@pytest.mark.llm`

4. **Keep tests deterministic**:
   - Use `temperature=0.0` for consistent results
   - Test extraction consistency (see `test_extract_deterministic`)

5. **Mock for unit tests, real API for integration**:
   - Unit tests: Mock LLM responses
   - Integration tests: Real API calls (tracked in Opik)

## Writing New Tests

### Add a new LLM test:

```python
@pytest.mark.llm
def test_my_new_feature(anthropic_client):
    """Test description."""
    result = my_llm_function(
        client=anthropic_client,
        prompt="test prompt",
        trace_name="my_feature_test",
        metadata={"test": "my_new_feature"}
    )

    assert result is not None
    # Add more assertions
```

### Add a new unit test:

```python
@pytest.mark.unit
def test_my_deterministic_function():
    """Test description."""
    result = my_function(input_data)
    assert result == expected_output
```

## Related Documentation

- [Opik Documentation](https://www.comet.com/docs/opik/testing/pytest_integration)
- [Architecture: Opik LLM Evaluation](../architecture/9-opik-llm-evaluation.md)
- [pytest Documentation](https://docs.pytest.org/)

---

**Last updated**: 2026-01-24
**Total test count**: 30+ tests (11 pipeline + 19 LLM)
**Coverage**: ~85% of src/ codebase
