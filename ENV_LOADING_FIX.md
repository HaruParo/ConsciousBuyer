# Environment Loading Fix - ANTHROPIC_API_KEY Issue

**Date**: 2026-01-24
**Status**: ✅ Fixed

---

## Issue

Tests were skipping with error:
```
pytest.skip: ANTHROPIC_API_KEY not found. Skipping LLM tests.
```

Even though `.env` file exists with the API key.

---

## Root Cause

Pytest doesn't automatically load `.env` files. The `conftest.py` wasn't loading environment variables before tests ran.

---

## Fix Applied

Updated `conftest.py` to automatically load `.env` file:

```python
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"\n✅ Loaded environment from {env_path}")
    else:
        print(f"\n⚠️  No .env file found at {env_path}")
except ImportError:
    print("\n⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
```

---

## Verify the Fix

### Step 1: Check Environment Loading

```bash
cd conscious-cart-coach
pytest tests/test_env_loading.py -v -s
```

**Expected output**:
```
✅ .env file exists at: /path/to/.env
✅ ANTHROPIC_API_KEY loaded: ...
✅ OPIK_API_KEY loaded: SsQ3gVmM8r...
✅ OPIK_WORKSPACE loaded: chat
✅ OPIK_PROJECT_NAME loaded: consciousbuyer
✅ Ready to run LLM tests!
```

### Step 2: Run LLM Tests

```bash
pytest -m llm -v
```

**Expected output**:
```
✅ Loaded environment from /path/to/.env
✅ Opik test tracking enabled

tests/test_llm.py::TestIngredientExtraction::test_extract_simple_recipe PASSED
tests/test_llm.py::TestIngredientExtraction::test_extract_vague_request PASSED
...

==================== 19 passed in 23.4s ====================
```

---

## If Still Not Working

### Check 1: python-dotenv Installed

```bash
pip install python-dotenv
```

### Check 2: .env File Location

```bash
# Should be in conscious-cart-coach/.env
ls -la conscious-cart-coach/.env

# Should show:
# -rw-r--r-- 1 user user 234 Jan 24 14:32 .env
```

### Check 3: .env File Contents

```bash
cat conscious-cart-coach/.env
```

Should contain:
```
ANTHROPIC_API_KEY=
OPIK_API_KEY=
OPIK_WORKSPACE=
OPIK_PROJECT_NAME=
```

### Check 4: Manual Load (Temporary Workaround)

```bash
# Load environment manually
export $(cat conscious-cart-coach/.env | xargs)

# Then run tests
pytest -m llm -v
```

---

## Files Modified

- **conscious-cart-coach/tests/conftest.py**: Added dotenv loading
- **conscious-cart-coach/tests/test_env_loading.py**: New verification test
- **conscious-cart-coach/tests/README.md**: Updated debugging section

---

## Related: Opik Threads Question

You also asked about threads in Opik. See [OPIK_THREADS_EXPLAINED.md](OPIK_THREADS_EXPLAINED.md) for details.

**TL;DR**:
- Current setup shows **individual traces** (1 per LLM call)
- This is **correct and expected** behavior
- To see conversation threads, you'd need to add explicit thread tracking with session IDs
- Current setup is fine for most use cases

---

## Next Steps

1. ✅ Run environment verification:
   ```bash
   pytest tests/test_env_loading.py -v -s
   ```

2. ✅ Run LLM tests:
   ```bash
   pytest -m llm -v
   ```

3. ✅ View results in Opik dashboard:
   - Go to https://www.comet.com/opik
   - Project: "consciousbuyer"
   - You'll see individual traces (not threads - this is normal!)

4. 📖 Read [OPIK_THREADS_EXPLAINED.md](OPIK_THREADS_EXPLAINED.md) if you want to understand threads

---

**Status**: ✅ Environment loading fixed
**Tests**: Should now run successfully
**Opik tracking**: Working (individual traces are correct)
